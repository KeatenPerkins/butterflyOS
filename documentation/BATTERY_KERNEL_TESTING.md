# Flip V2 battery-driver investigation

Development work started October 8, 2026, after v1.0.3 publication.
Experimental kernel changes are not a published battery fix.

## Evidence and first change

The saved closed-lid run fell from 97% to 78% in one hour with Wi-Fi enabled.
The later normal shutdown recorded 77%, approximately 2,297,232 µAh. After about
53 minutes powered off, boot reported 93%, approximately 2,787,776 µAh.
These readings show the reported estimate increased; they do not measure
powered-off current or establish a corresponding gain/loss of physical charge.

The running kernel is 7.0.2. Its RK817 driver reinitializes state of charge from
power-on voltage when the off-time register reaches three ten-minute units, or
when the charge counter is invalid. The old counter is then replaced, preventing
userspace from inspecting the original boot decision afterward. That policy is
a plausible explanation for the observed upward jump, pending a boot capture.

The first test patch is
`projects/ROCKNIX/devices/RK3566/patches/linux/0032-power-supply-rk817-boot-gauge-diagnostics.patch`:

- Correct the stored state-of-charge sanity limit from 10,000 to 100,000.
  The driver stores thousandths of a percent; 100,000 represents 100%.
  This mismatch is a real defect, but correcting it alone does not remove
  the later off-time voltage-based recalibration.
- Check boot register-read and voltage-to-capacity lookup errors before using
  their results, avoiding stale/uninitialized data on these paths.
- Emit one bounded `boot gauge:` kernel record with initialization reason,
  raw counter, saved percentage, off-time count, voltage estimate and selected
  initial charge. There is no new periodic polling or logging loop.

The existing charge-counter latching fix and off-state SYS_CAN_SD patch remain
in place. A read-only snapshot of .17 showed register 0xe6 at 0x40, with
SYS_CAN_SD clear. No additional PMIC register writes were made during diagnosis.
The initial test retains the 30-minute recalibration policy and existing
charging voltage/current settings.

## Local artifacts and validation

Artifacts are kept under
`/home/keaten/Documents/ButterflyOS-Battery-Kernel-20261008/`, outside the release
build. The test source is an isolated copy of the actual 7.0.2 build tree and
uses the pinned build container and existing toolchain. The production kernel
cache and published v1.0.3 image are not modified.

The driver compiled successfully with additional compiler warnings enabled.
Kernel checkpatch passed with zero errors/warnings, excluding upstream
submission sign-off checking for this local test patch. Compilation establishes
build validity, not hardware correctness. Any test kernel must complete its
own build and artifact checks before installation.

The isolated full kernel build also completed successfully. Its ARM64 Image
contains the diagnostic marker, uses kernel release 7.0.2 and has the same
configuration and all 13,159 exported kernel-symbol versions as the original.
`KERNEL-battery-diagnostic`, its checksums, the known-good
`KERNEL-original-20261010` and `verification.json` are in the artifact directory.
The diagnostic kernel was installed on .17 on October 8. Its first normal
reboot passed with no failed systemd services. The boot record retained the
charge-counter estimate (saved 80.490%, selected 80.366%, off_count=0), and the
first displayed reading was 80%. Both the active kernel and boot-partition
rollback copy matched their expected SHA-256 hashes. Captures are in
`device-tests/17-first-boot/` under the artifact directory. Long-off, charging
and gameplay qualification remain pending. The kernel has not been published.

## First device tests

Use .17 for development. Keep the known-good kernel and its checksum available
on the PC and boot card before trying a kernel replacement. This experiment
changes the SD boot kernel, not the internal preloader. A kernel boot test
requires a reboot; the driver is built in and cannot be replaced live.

1. Start around 60–80% charge, unplug USB power, and keep the same brightness,
   Wi-Fi and idle-menu conditions. A test starting at 100% may hide an upward
   percentage correction. Record the current percentage, voltage and charge.
2. Test a normal restart and a short powered-off interval first. Confirm the
   diagnostic boot record appears and normal charging/gameplay still work.
3. Record a baseline, shut down normally, remain unplugged for 45–60 minutes,
   then boot and collect the early reading, boot record and a settled reading.
4. Compare the pre-reset counter estimate with the selected voltage-based
   estimate and the last shutdown reading. Keep logs from separate runs.

Useful read-only commands after boot:

```sh
journalctl -k -b --no-pager | grep 'boot gauge:'
cat /sys/class/power_supply/battery/uevent
cat /sys/class/power_supply/charger/uevent
```

`saved_soc_milli_pct=77000` means 77%; `off_count=3` corresponds to approximately
30 minutes. `source=charge-counter` means the existing counter was selected;
`source=off-time-voltage` means the long-off policy selected power-on voltage.
`source=invalid-counter` or `battery-initialization` identifies recovery paths.
Sentinel values of -1/0 mean that a field was not read on that branch, not an
actual measurement of zero. Capture the full line, not just the percentage.

The existing temporary battery recorder can collect before/after values once
reinstalled on the test card. A charger connected during either phase prevents
a meaningful powered-off drain comparison. No software can log measurements
while this device is fully powered off.

## First long-off result on .17

The October 8 normal shutdown/boot interval was about 52 minutes. The boot
record reported `off_count=5` and `source=off-time-voltage`: saved state of
charge was 77.434%, but the 3.96517 V power-on reading selected 84% and reset
the charge counter to 2520 mAh. USB power was disconnected. This confirms an
upward correction of approximately 6.6 percentage points from the long-off
voltage policy.

The retained counter before that reset was 2016 mAh (67.2%), which was also
below the saved percentage. This does not independently prove physical
off-state drain, and simply retaining that counter would introduce a downward
correction in this run. Counter retention/calibration needs investigation
alongside the voltage policy. Captures and analysis are in
`device-tests/17-long-off/` under the artifact directory.

## Short-off comparison on .17

The next shutdown-to-boot log interval was approximately 6 minutes 42 seconds,
including shutdown/startup. With `off_count=0`, the driver selected
`source=charge-counter`: saved charge was 81.235%, the retained counter was
2398 mAh, and selected charge was 79.933%. The first reachable display was 79%.
USB was disconnected and no failed services were reported. Captures are in
`device-tests/17-short-off/` under the artifact directory.

There was no voltage-based upward correction. The smaller counter decrease
still combines shutdown/startup consumption, possible physical off-state drain
and gauge behavior; this test cannot separate those causes. Investigate counter
behavior and PMIC shutdown state before changing the long-off policy.

## Counter and shutdown follow-up

Read-only PMIC snapshot on .17 showed OFF_SOURCE=0x08 (DEV_OFF),
CHRG_TERM=0x40 (SYS_CAN_SD clear), and identical CAL_OFFSET/IOFFSET values
0x8049. The DTS sense resistor is 10 mOhm, matching the locally archived
stock firmware's sample_res=10. These checks do not measure physical off-state
current. The long and short saved-SOC-to-counter differences correspond to
approximately 357 and 350 mA across their entire shutdown/boot intervals;
these are gauge-derived averages, not measured off-state current.

The SYS_CAN_SD comment's charger-monitoring explanation is not established by
the datasheet. The datasheet describes permission to turn off system voltage;
Rockchip U-Boot selects it using vsys-off-shutdown. However, the archived Flip
hardware investigation documents direct-current tests supporting clearing it.
Keep the existing setting while investigating; do not reverse it from the
register description alone.

Sources: [RK817 datasheet, pp. 125 and 133](https://rockchip.fr/RK817%20datasheet%20V2.1.pdf),
[Rockchip U-Boot PMIC driver](https://github.com/rockchip-linux/u-boot/blob/next-dev/drivers/power/pmic/rk8xx.c).
Local historical current tests are in butterflyOS-tools/miyoo-flip-reference/
docs/miyoo-flip-power-off-investigation.md, section 18.

A temporary .17-only systemd recorder now captures power readings and PMIC
registers at service startup and shutdown, preserving each record under its
boot ID in /storage/battery-kernel-captures. It performs no periodic polling
and writes no PMIC registers. Source copies are in the diagnostic artifact
folder's capture-tools directory; this recorder is not part of the OS build.
The first startup record was taken when installed during an existing boot
(uptime 433 seconds), not at actual boot. Subsequent startup records occur
normally during boot. Disable with systemctl disable --now
butterflyos-battery-capture.service when testing ends (stopping it records a
final shutdown-labelled snapshot even without powering off).

A controlled normal restart validated both hooks. At shutdown capture,
charge was 2256.640 mAh; kernel boot retained 2250 mAh, and the automatic
startup capture 25 seconds after shutdown capture read 2247.696 mAh. The
full capture-to-capture difference was 8.944 mAh, approximately 0.30% of
3000 mAh. Kernel-saved SOC was 75.129%, selected SOC 75.000%.
This is substantially smaller than the extended-off counter differences.
Archive: device-tests/17-recorder-restart/ under the artifact directory.
The next short powered-off test can use these hooks without depending on
SSH timing; independent current measurement is still required to establish
physical off-state drain definitively.

## Automatically captured ten-minute-off comparison

The next shutdown/startup captures were 20:25:00 and 20:36:42 UTC on October 8
(11m42s including shutdown/startup). Charge fell from 2219.316 to 2148.796 mAh,
with displayed percentages 74% and 72%. The 70.520 mAh difference corresponds
to 2.351 percentage points. The driver selected charge-counter, off_count=1,
saved SOC=73.885%, selected SOC=71.700%; USB was disconnected.

Compared with the 8.944 mAh normal-restart baseline, this confirms additional
counter loss that increases with the powered-off interval. It does not
independently measure physical battery loss. Both snapshots had e6=40 and
OFF_SOURCE=08; CAL_OFFSET matched IOFFSET (8042 before, 8046 after).
Captures and calculations: device-tests/17-ten-minute-off/.

Repeated shutdown timings have now established the pattern. An independent
battery-current measurement or controlled same-device stock-firmware
comparison is more useful than another equivalent timed shutdown for
separating real drain from gauge behavior.

## Decision after measurement

If a sane retained counter is repeatedly replaced by a substantially higher
voltage estimate, test a board-specific, reversible policy that preserves or
bounds the correction. Keep first-initialization and invalid-counter recovery.
If the counter itself drifts, investigate its retention and calibration before
removing the voltage fallback. Do not simply clamp the displayed percentage.

Qualify the eventual policy with short and long off intervals, normal restarts,
partial charging, a complete charge, lower charge levels and multiple devices.
Do not infer improved runtime or charging hardware behavior from smoother
percentages. Real off-state drain and charging/LED behavior are separate tests.

Linux documents the distinction between charge, voltage, capacity and hardware
calibration in the [power supply class documentation](https://www.kernel.org/doc/html/latest/power/power_supply_class.html).

## Second experiment: counter-first boot with voltage sanity bounds

Cross-device research found ROCKNIX PR [3305](https://github.com/ROCKNIX/distribution/pull/3305),
merged September 20, 2026, with RK817 boot corrections evaluated on the RG353M
and GKD Pixel2. ButterflyOS already carries the SYS_CAN_SD clearing change.
Patch 0032 corrects the saved SOC limit in our first diagnostic kernel.

Experimental patch 0033 adapts the counter-first selection and boot voltage
sanity bounds from Chris Morgan and Jacob Cook's work. It retains checked
register reads, the counter-latch helper, existing charging limits and the
shutdown drain fix. It stops replacing the counter with PWRON_VOL merely
because OFF_CNT reaches three. Positive counters are capped at full charge;
invalid counters use saved SOC. Suspiciously low counters may use saved SOC
when the live voltage bound permits it. While discharging, voltage at or below
the battery's minimum overrides stale saved SOC and selects zero.

The ten-percentage-point band is a heuristic, not calibration. The charging
and discharging bounds depend on the Flip's existing OCV table. This change
may address large startup jumps; it does not automatically correct the small
counter drop measured during the ten-minute test, and does not prove lower
physical powered-off current. True-suspend corrections, periodic rested OCV
recalibration and user-space percentage smoothing are not part of this test.

A bounded `boot policy:` log includes source, retained counter, saved SOC,
live voltage, voltage-table estimate, charger status and selected charge.
Local artifacts, host policy checks and full build records are under
`ButterflyOS-Battery-Kernel-20261008/`. The original diagnostic source and
published kernel remain intact. Twelve policy scenarios and range invariants
exercise the actual selection helper extracted from the driver.

Qualification must cover warm reboot, ten-minute off, one-hour off, charging
while off followed by boot, and low-battery gameplay with normal shutdown.
Do not judge success by display stability alone. Compare the pre-initialization
counter, saved estimate, live voltage, charging status and resulting estimate,
and check charging reliability and low-battery warnings. Each boot test has
its own preserved capture folder. A new test kernel is not a release-qualified
battery fix until device testing is complete.

## October 9 live results and cable-status refresh

Patch 0033 passed warm boot and a ten-minute powered-off test, but did not
eliminate the short-interval counter decrease. In a subsequent one-hour
unplugged test, the user observed 84% before shutdown and 83% after startup.
Automatic snapshots were 59 minutes 58 seconds apart and both initially read
84%. The boot record selected `saved-voltage-bound`: saved SOC was 83.878%,
the retained counter was 2172 mAh (72.4%), and the live voltage table gave
88%. The policy preserved the saved estimate instead of accepting the low
counter or replacing the percentage with the voltage-table estimate.
This avoids the large upward jump in this trial; counter disagreement remains,
and the reset means exported before/after charge readings cannot establish
physical off-state consumption.

Frontend patches 058 and 059 request a redraw when battery data changes and
check status every two seconds. The original enhanced idle loop could leave
the indicator stale until controller input or screen wake. Both patches were
built and tested live. The two-second interval still initially produced roughly
four seconds of visible cable-change latency.

Quarter-second test sampling showed charger `online` became true 5.27 seconds
before battery status changed to `Charging`. Driver inspection found an
immediate IRQ read followed by eight-second periodic refreshes: an early
negative current reading could remain cached until the next monitor tick.
Patch 0034 schedules the existing worker one second after cable changes,
serializes property refreshes through that worker, and publishes notifications
after updating the readings. It initializes work before registering IRQs and
preserves normal eight-second monitoring and charging limits.

The isolated full kernel build passed, configuration and exported kernel
symbol CRCs matched the previous test kernel, and patch checks passed.
After installation on .17, normal boot passed with no failed services. The
first unplug test updated battery status 0.88 seconds after the online change;
replug took 1.18 seconds, compared with the prior 5.27 seconds. The user
observed icon disappearance in about 2.5–3 seconds and appearance in about
two seconds, then confirmed better responsiveness in repeated use.

These changes are committed for further development, not yet published.
Charging completion, off-state charging, low-battery gameplay, and additional
device coverage remain to be qualified. Test recorders remain local tools and
are not included in the OS image. Local logs, verified kernel artifacts, and
rollback copies are preserved under the battery artifact directory.
