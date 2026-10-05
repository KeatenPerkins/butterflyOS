# ButterflyOS release procedure

Alpha releases are public test builds. A stable release is the maintainer's
designation that the documented features and supported hardware are ready for
normal use. GitHub does not require a separate certification or repository;
the release is based on an immutable source tag and published without the
prerelease flag, then selected as Latest.

1. Review device testing, resolve release-blocking defects, and freeze scope.
   Record the tested build and any changes added afterward without claiming
   that earlier device tests qualify a new binary.
2. Choose a public version. The first stable release is `v1.0.0`; subsequent
   bug fixes use `v1.0.x` and feature releases use `v1.x.0`. This is a project
   versioning convention, not a claim of stable APIs for inherited components.
3. Commit the source and documentation. Reserve a numeric updater build ID
   greater than every published update; the updater currently uses YYYYMMDD
   values independently of the public version. v1.0.0 reserves `20261006`;
   v1.0.1 reserves `20261007`.
4. Build the full Flip V2 image from that recorded commit. Extract matching
   SYSTEM/KERNEL from the release tar and generate the narrow update package
   using `scripts/butterflyos-update-package.py`.
5. Verify image integrity, filesystems, package contents, version/device stamps,
   source hashes, update checksums, new feature assets, and private-content
   exclusions. Refresh the package-license manifest and exact artifact audit.
6. Create a draft GitHub release targeting the recorded source, with the full
   `.img.gz`, checksum, update `.tar`, checksum, update manifest, and release
   build/license records. Verify every uploaded asset before publication.
7. Publish without the prerelease flag and mark Latest. Confirm release and
   updater discovery. Do not initiate an update on a user's device merely to
   test discovery; the user controls installation.
8. Report the release link, installed build ID, update steps, and any remaining
   testing limits. Keep known issues and recovery instructions current.

Stable is separate from LTS. An LTS label needs an explicit support period,
supported hardware, and a policy for maintenance and security fixes.

GitHub reference: [Managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
