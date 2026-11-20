# Flip update channels

Open **Start → System Settings → Update Channel**. **Stable** is the
default. Switch to **Development** on a test card, then choose
**Update ButterflyOS** to check that channel.

Both channels use GitHub releases from the Flip repository. Stable uses
the existing public release format. Development uses published GitHub
prereleases tagged `development-<build>`, with the same
`butterflyos-update.json` and matching update archive as Stable.
Development tags are excluded from Stable checks.

Build a candidate from the development source branch and publish it as a
prerelease when the test image is ready. Give each candidate an update build
number newer than the number already installed on the test card. The updater
compares the existing date-based build numbers, so two candidates with the
same number cannot update over each other.

After testing, publish the approved build through the normal Stable release
process. Switching back to Stable changes which releases the updater checks.
A Flip running a newer Development build has to wait for a newer Stable build
to update over the air.
