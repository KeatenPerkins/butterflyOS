# SD Card Info

Open **Tools → SD Card Info** to check the ButterflyOS card and optional second
game card. The tool is available in normal mode in builds containing it.

It shows:

- Each card's physical capacity, formatted storage size, used space, available
  space, and percentage used.
- Whether each card is detected and mounted, and whether its filesystem is
  mounted read/write or read-only.
- Filesystem type, mount location, and partition device.
- Combined available space without counting the same mounted filesystem twice.
- OS-card space available for updates. Space on the second card cannot be used
  to download or stage an OS update. Three GiB is the usual guide; the updater
  checks the exact release requirement.

The interface uses Butterfly Link's graphical style. Use the D-pad to scroll,
**A** to select, and **B** to go back. An overview opens first, followed by
separate OS-card, game-card, and update-space pages, plus **Refresh**,
**Save**, and **Close** actions. No keyboard is required. A themed terminal
dialog remains available if graphical initialization fails.
Saved reports go to `/storage/.config/system/sd-card-reports/`.

The check reads mount information, filesystem counters, and kernel-provided
card capacity. It does not scan directories, hash files, run filesystem checks,
format cards, change mounts, or test write access by creating a file. An
inserted but unmounted card has no available-space figure until it is mounted.
Read/write status describes the mount; it does not guarantee that every file
or directory is writable. The OS boot partition being read-only is normal.

Sizes use GiB (1,073,741,824 bytes), which differ from the decimal GB advertised
on cards. Formatted storage is smaller than the physical card capacity because
partitioning and filesystem metadata take space. Available space can also be
smaller than total free space because some filesystems reserve blocks.

Folder sizes, game counts, duplicate detection, speed benchmarks, and card
health checks are not part of this fast overview. Those need separate scans or
additional diagnostics. Free space alone does not establish card health.

This tool is included starting with ButterflyOS v1.0.2 (build `20261008`).
