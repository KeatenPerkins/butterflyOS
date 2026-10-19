#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the real systemd lifecycle with temporary units and short intervals.

Run explicitly as root on a systemd test device, passing the candidate timer.
No production units or game files are changed.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timer', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Run explicitly as root on the systemd test device.')
    source = args.timer.read_text()
    # Scale the candidate intervals without replacing its scheduling strategy.
    assert 'OnActiveSec=3min' in source and 'OnUnitInactiveSec=5min' in source
    scaled = source.replace('OnActiveSec=3min', 'OnActiveSec=1s').replace(
        'OnUnitInactiveSec=5min', 'OnUnitInactiveSec=1s').replace('AccuracySec=30s', 'AccuracySec=100ms')
    name = 'butterflyos-save-backup-check-%d' % os.getpid()
    service = Path('/run/systemd/system') / (name + '.service')
    timer = service.with_suffix('.timer')
    folder = Path(tempfile.mkdtemp(prefix=name + '-'))
    marker, ticks = folder / 'enabled', folder / 'ticks'
    try:
        service.write_text('[Unit]\nConditionPathExists=%s\n[Service]\nType=oneshot\n'
                           'ExecStart=/bin/sh -c "echo tick >> %s"\n' % (marker, ticks))
        timer.write_text(scaled.replace('[Timer]\n', '[Timer]\nUnit=%s.service\n' % name))
        run('systemctl', 'daemon-reload')
        run('systemctl', 'start', name + '.timer')
        time.sleep(2)
        assert not ticks.exists(), 'Disabled backup unexpectedly executed'
        marker.touch()
        # This is the same re-arm operation used by the on-device enable action.
        run('systemctl', 'restart', name + '.timer')
        deadline = time.monotonic() + 12
        count = 0
        while time.monotonic() < deadline:
            count = len(ticks.read_text().splitlines()) if ticks.exists() else 0
            if count >= 3:
                break
            time.sleep(0.2)
        assert count >= 3, 'Timer did not repeat after enabling: %d runs' % count
        properties = run('systemctl', 'show', name + '.timer', '-p', 'TimersMonotonic',
                         '-p', 'NextElapseUSecMonotonic')
        assert 'OnActiveUSec=' in properties and 'OnUnitInactiveUSec=' in properties
        print('PASS: disabled run skipped; enable/restart produced %d automatic runs' % count)
        print(properties.strip())
    finally:
        subprocess.run(['systemctl', 'stop', name + '.timer', name + '.service'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        service.unlink(missing_ok=True)
        timer.unlink(missing_ok=True)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        shutil.rmtree(folder)


if __name__ == '__main__':
    main()
