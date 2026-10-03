# October 2 release candidate rebuild

- Source revision: `39bb3a803bd481b7a610cf2b19509b2c13d39891`.
- Command: `make docker-RK3566-Miyoo-Flip-V2`.
- Result: exit 0; all 668 main-image steps completed successfully.
- Image: `target/ROCKNIX-RK3566.aarch64-20261002-Miyoo_Flip_V2.img.gz`.
- SHA-256: `24eb2a762b55fb6aae77caf49c5450f3b3f1bf874b5cbc01016469dc0ab3aede`.
- Compressed-image integrity check and generated checksum verification passed.
- The packaged SYSTEM filesystem contains ScreenScraper as the default in
  `/usr/config/emulationstation/es_settings.cfg`. Builds without private
  developer credentials retain the RetroArch Thumbnails fallback.

The immediately preceding image's scraper/artwork test passed user testing.
This rebuild adds the fresh-install provider default; it has not yet been
flashed, hardware-tested, or uploaded as a public downloadable release.
Existing installations retain their saved provider selection.

Before publishing, verify a fresh boot selects ScreenScraper and confirm the
final artifact audit and release documentation correspond to this checksum.
