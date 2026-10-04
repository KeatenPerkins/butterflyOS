# ButterflyOS v0.2.4 — menu polish and PortMaster in Tools

Update build for Miyoo Flip V2, with device version `20261005`. This identity
is reserved for this release so devices running v0.2.3 (`20261004`) can update.

- Added **Start → System Settings → Update ButterflyOS** in normal mode.
- Filled the rounded menu panel with a uniform blue background and removed
  the duplicate line above the version footer.
- Removed decorative lines from the Games, Settings, and Tools home cards.
- Centered game artwork vertically in its frame across systems.
- Added **X: Search** and **Y: Add/Remove Favorite** hints to game selection
  screens, preserving existing controls.
- Made **PortMaster** visible in normal Tools, using the new ship artwork.
  Installed ports appear under **Games → Ports**; some require game files
  supplied by the user. Game compatibility testing on the Flip V2 is pending.
- Updated Butterfly Link documentation to remove the resolved Yellow-to-Crystal
  issue and show its icon under the feature heading.

OS source commit: `c7820b0042d4bb3c8a9e1a99462455c9d1d093b4`. The online update retains the updater and boot
installer fixes from v0.2.3. Package checks do not replace testing the new
menus and PortMaster on the device.

On an installed v0.2.3 device, save and exit games, connect to Wi-Fi and
front-port power, then use **Start → Updates & Downloads → Start Update**
(enable Advanced Mode if necessary). Wait for **Update is ready / Reboot to
apply**, then use **Start → Quit → Restart System** after downloading and
verification finish. The update menu's Apply Update shortcut only restarts the
menu in this release; its device-reboot correction is queued for the next build.
After installation, confirm version `20261005`; subsequent updates
can be started from **Start → System Settings → Update ButterflyOS**.

The download is about **1.3 GB**; allow **at least 3 GB free on the OS card**
for download and installation. See [How to update](UPDATES.md#how-to-update)
for the full procedure.

Back up important saves before updating. Keep power connected and leave the
OS card inserted during installation. Older v0.2.1 installations require the
migration described in [v0.2.3 release notes](RELEASE_NOTES_v0.2.3.md).

Validation: the release build completed and all seven offline updater tests
passed. The finished package passed manifest, size, SHA-256, archive-content,
device identity, and internal checksum checks. Extracted OS files matched the
current updater, theme, home-card artwork, PortMaster launcher, and supplied
ship artwork. The compiled menu includes the new update option; the packaged
PortMaster runtime and X/Y help icons are present. This release's installation
and PortMaster games still need to be tested on the device.

Archive SHA-256:

```text
3c3820f0d334a08f9bb598320529c7cfeabd332cf148fe3e8f980a84fbbbf9b2
```
