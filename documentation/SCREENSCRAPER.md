# ScreenScraper

ButterflyOS supports ScreenScraper in EmulationStation when release developer
credentials are injected during the frontend build. Users select ScreenScraper
in the Scraper menu. A personal ScreenScraper account is optional; availability,
quotas, and anonymous access are controlled by ScreenScraper.

Developer credentials are separate from personal account fields. Do not enter
the developer password in the GUI's personal account/password fields.

## Private build setup

The release builder supplies `.config/screenscraper.json` in the repository
root, containing `devid` and `devpassword` string fields. This directory is
ignored by Git. Keep the JSON readable only by the builder. The debug password
is not needed and is not included.

The frontend package generates `ButterflyScreenScraperCredentials.h` inside
the ignored build directory. The generated header stores XOR-obfuscated data
and decodes it inside the application. This deters plaintext string discovery;
the client includes the decoding key, so it does not provide true secrecy.
The private JSON is not installed in the image. Requests identify ButterflyOS
as the client, and artwork-download debug logs omit request URLs.

Without the private JSON, clean builds omit ScreenScraper support and retain
RetroArch Thumbnails. Adding or rotating credentials requires rebuilding
EmulationStation; a cached package does not automatically detect private-file
content changes. Clean that package before rebuilding if only credentials
changed. Never commit private credentials or include them in diagnostic bundles.

## October 2 verification

- The existing full image did not contain ScreenScraper API support.
- Developer authentication and Pokémon Yellow ROM lookup succeeded without a
  personal-account login; box artwork downloaded successfully (826,701 bytes).
- The rebuilt frontend contains ScreenScraper API support. A binary scan found
  neither the plaintext developer login nor password.
- The rebuilt frontend is running on .20 and ScreenScraper is selected. Original
  frontend and settings backups are retained under `/storage/.config/`.
- The live executable is
  `/storage/.config/butterflyos/emulationstation-screenscraper-anonymous-20261002`,
  bind-mounted over `/usr/bin/emulationstation`. It disappears on reboot.
- Initial GUI testing failed with HTTP 403 and the French message "Erreur de
  login". The frontend queried `ssuserInfos.php` without a personal login to
  discover the permitted thread count. A direct probe confirmed this endpoint
  returns 403 while the same developer credentials successfully obtain game
  data from `jeuInfos.php` (HTTP 200).
- The frontend now uses one request thread when personal-account fields are
  absent, avoiding the personal-account check. Complete personal logins still
  use the account endpoint to determine their permitted thread count.
- The user confirmed GUI scraping works after the anonymous-account fix.
  Artwork retention across a clean frontend restart and HDMI changes remains
  to be verified.
- These changes are included in the October 2 image with SHA-256
  `5db66e6a010360bba1351be1649b1dce8fda3db780807e40b842056191b62847`.

## Test flow

Open Start → Scraper, confirm ScreenScraper as the provider, and scrape one
game. Check that its artwork appears, restart the frontend normally, then
connect/disconnect HDMI and check the same artwork again. Do not rename ROMs
or saves to obtain artwork: the provider can identify supported games by name
and/or ROM hashes. Do not publish logs containing account information.

## Staged fixes after the October 2 image test

- The user confirmed artwork appears after replacing linked `gamelist.xml`
  files with regular copies on the live device. EmulationStation's file cache
  rejects symlinks in its regular-file check, silently skipping second-card
  metadata. Patch 041 checks the canonical file while retaining the original
  system-relative paths, so the shared game lists do not need to be duplicated.
- DNS failures were previously treated as successful empty scraper results.
  Patch 042 propagates network I/O errors from both lookup and media download,
  stops the batch with a readable Wi-Fi/retry message, and leaves failed and
  unmatched games unmarked so an unscraped-only retry can select them again.
- Completed batches report matched, not-found, and failed counts. Matched means
  a metadata result was accepted, not proof that every possible artwork type
  exists. Partial media-download failure does not accept the result.
- Both patches pass zero-fuzz dry-run application to the current frontend
  sources. They are staged source changes only: compilation, offline-scrape
  error handling, successful retries, linked-list refresh, and HDMI/reboot
  retention must be tested in the next build. No rebuild or live deployment of
  these patches has been performed.
