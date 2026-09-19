# ButterflyOS network and cloud package audit

This audit covers the Miyoo Flip V2 image. Sizes are the uncompressed binaries
in the September 19 development image and are not the exact compressed-image
savings.

| Component | Approx. binaries | Current purpose | Recommendation |
|---|---:|---|---|
| Simple HTTP Server | 2.2 MiB | ButterflyOS Web File Transfer on ports 80/8080 | Keep. This is the tested beginner-friendly transfer workflow. |
| OpenSSH | — | SSH/SCP and advanced administration | Keep, disabled until the user enables SSH and sets a password. |
| Samba | multiple shared libraries and daemons | Windows-style network shares and discovery | Keep for Alpha 2 only if its UI remains available; disable `nmbd` discovery by default to avoid WORKGROUP conflicts. Reassess after measuring the full package footprint. |
| Tailscale | 46 MiB | Managed mesh VPN and remote access | Remove from the Flip base image. It has no ButterflyOS onboarding or tested user workflow and duplicates advanced SSH/VPN use cases. Consider a future optional package. |
| rclone | 61 MiB | Scripted cloud save backup/restore | Remove from the beginner base image unless cloud backup is promoted to a supported feature. Existing RCLONE tools must be hidden/removed at the same time. |
| Syncthing | 24 MiB | Continuous peer-to-peer folder synchronization | Remove from the beginner base image. It has no ButterflyOS setup flow and exposes another authenticated web service when enabled. Consider a future optional package. |
| rsync | — | Local/remote file copying and internal maintenance | Keep. It is used broadly and is not itself a resident cloud service. |
| ZeroTier | excluded already | Mesh VPN | Continue excluding it from the Flip image. |
| WireGuard kernel support/tools | conditional | VPN plumbing and a Tailscale dependency | Remove the tools with Tailscale. Disable the kernel module if no retained package needs it. |
| OpenVPN | currently conditional/off | Traditional VPN client | Leave excluded. |

Decision recorded September 19, 2026: remove Tailscale, rclone, and Syncthing
from the Miyoo Flip V2 base image. Their launchers and password-management
hooks are removed or made conditional. The decision does not affect Web File
Transfer, SSH/SCP, or rsync.

## Dependency conclusion

The ButterflyOS Web File Transfer is implemented by `simple-http-server`; it
does not require Tailscale, rclone, Syncthing, Samba, or ZeroTier. Removing the
three large standalone binaries therefore does not break the tested web upload
workflow, Wi-Fi, SSH/SCP, game-card support, scraping, or multiplayer.

Tailscale, rclone, and Syncthing total roughly 131 MiB uncompressed. Actual
image savings will be smaller because the root filesystem is compressed.

## Release policy

- Network-facing services stay off until the user explicitly enables them.
- ButterflyOS must never ship user credentials, cloud tokens, or reusable API
  secrets.
- Optional remote-access or synchronization packages need a clear UI workflow,
  a threat-model note, an uninstall path, and a maintenance owner before they
  return to the public image.
- Removing a package also requires removing or hiding every menu entry and help
  reference that would otherwise launch it.
