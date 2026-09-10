#!/usr/bin/env python3
"""Generate a license manifest from a completed ButterflyOS target build."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ASSIGNMENT = re.compile(r'^\s*(PKG_NAME|PKG_VERSION|PKG_LICENSE|PKG_SITE)="([^"]*)"', re.M)
TARGET_JOB = re.compile(r"^DONE\s+\d+\s+\d+\s+\S+\s+([^\s:]+):target\b", re.M)


def package_metadata(root: Path) -> dict[str, list[dict[str, str]]]:
    packages: dict[str, list[dict[str, str]]] = {}
    package_files: list[Path] = []
    for source_tree in (root / "packages", root / "projects"):
        if source_tree.is_dir():
            package_files.extend(source_tree.rglob("package.mk"))
    for package_file in sorted(package_files):
        text = package_file.read_text(encoding="utf-8", errors="replace")
        values = dict(ASSIGNMENT.findall(text))
        name = values.get("PKG_NAME")
        if not name or "$" in name:
            continue
        values["path"] = str(package_file.relative_to(root))
        packages.setdefault(name, []).append(values)
    return packages


def clean(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ") or "Not declared"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--joblog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release", default="Unspecified release")
    args = parser.parse_args()

    root = args.root.resolve()
    joblog = args.joblog.resolve()
    output = args.output.resolve()
    built = sorted(set(TARGET_JOB.findall(joblog.read_text(errors="replace"))))
    metadata = package_metadata(root)

    rows: list[tuple[str, str, str, str, str]] = []
    unresolved: list[str] = []
    for name in built:
        candidates = metadata.get(name, [])
        if not candidates:
            unresolved.append(name)
            rows.append((name, "Not resolved", "Not resolved", "Not resolved", "Not resolved"))
            continue
        item = candidates[0]
        rows.append((
            name,
            item.get("PKG_VERSION", "Not declared"),
            item.get("PKG_LICENSE", "Not declared"),
            item.get("PKG_SITE", "Not declared"),
            item["path"],
        ))

    lines = [
        f"# {args.release} package license manifest",
        "",
        "Generated from the completed target build job log and `package.mk` metadata.",
        "A declaration is an audit starting point, not proof that every bundled file has",
        "been licensed correctly. Dynamic shell expressions may require manual review.",
        "",
        f"- Target packages recorded: {len(built)}",
        f"- Package definitions not resolved automatically: {len(unresolved)}",
        "",
        "| Package | Version/revision | Declared license | Upstream site | Definition |",
        "|---|---|---|---|---|",
    ]
    lines.extend(
        f"| `{clean(name)}` | `{clean(version)}` | {clean(license_name)} | "
        f"{clean(site)} | `{clean(path)}` |"
        for name, version, license_name, site, path in rows
    )
    if unresolved:
        lines.extend(["", "## Unresolved package definitions", ""])
        lines.extend(f"- `{name}`" for name in unresolved)
    lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
