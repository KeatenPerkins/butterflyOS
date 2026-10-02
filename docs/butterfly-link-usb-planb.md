# Butterfly Link USB-C transport (Plan B)

Historical emulator-link research. This does not describe the installed
save-transfer Butterfly Link app. See [the current user guide](../documentation/BUTTERFLY_LINK.md).

The Miyoo Flip's lower/front USB-C connector can run as a CDC-NCM peripheral
when the image uses the Plan B device tree. The upper/rear connector remains a
USB host. The link helper assigns a private point-to-point network:

- host/rear device: `169.254.42.1` on `usb0`
- peripheral/front device: `169.254.42.2` on `gadget`

`butterflyos-link-usb up host` and `up peripheral` are reversible. `down`
clears the temporary address and unbinds the CDC gadget. The UI uses the host
role for `Host a Session` and the peripheral role for `Join a Session`; the
host setup waits in the background so the joiner can activate its gadget.

USB is only the transport. USB-C sessions use the single-core mGBA SIO mode for
Gen3 compatibility testing, while Wi-Fi sessions continue using the existing
dual-core/input-relay mode. ROMs are never transferred. Lower USB latency does
not by itself correct a game-level handshake mismatch, so this mode is selected
explicitly for the cable test.

The Plan B image intentionally forces the lower connector to
`dr_mode = "peripheral"`. Keep a normal ButterflyOS card available if the
front connector is needed for ordinary USB host accessories.
