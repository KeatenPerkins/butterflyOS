#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Experimental suspend, controller UI and per-cycle diagnostics. Never remount storage."""
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/storage/.config/butterflyos/suspend-tests')
ENABLED = Path('/storage/.config/butterflyos/experimental-lid-suspend.enabled')
DISABLED = ENABLED.with_name('experimental-lid-suspend.disabled')
DRIVER = Path('/sys/bus/platform/drivers/rockchip-pm-config')
POWER = Path('/sys/power/mem_sleep')
UPDATE = Path('/storage/.cache/butterflyos-update/update.lock')

def set_lid_sleep(enabled):
    ENABLED.parent.mkdir(parents=True, exist_ok=True)
    if enabled:
        DISABLED.unlink(missing_ok=True)
        ENABLED.touch()
    else:
        DISABLED.touch()
        ENABLED.unlink(missing_ok=True)

def command(args):
    try:
        p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12)
        return p.stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return str(e)

def snapshot():
    report = {'time': time.time(), 'mounts': Path('/proc/self/mountinfo').read_text(),
              'kernel': command(['journalctl', '-k', '-b', '-n', '300', '--no-pager'])}
    for pattern in ('/sys/kernel/debug/mmc*/ios', '/sys/power/mem_sleep', '/sys/power/pm_async',
                    '/sys/class/power_supply/*/uevent', '/sys/class/devfreq/*/governor', '/sys/class/devfreq/*/cur_freq', '/sys/class/devfreq/*/min_freq', '/sys/class/devfreq/*/max_freq'):
        import glob
        for name in glob.glob(pattern):
            try: report[name] = Path(name).read_text()
            except OSError as e: report[name] = str(e)
    return report

def writable(path):
    return not bool(os.statvfs(path).f_flag & os.ST_RDONLY)

def probe_targets():
    # Probe only actual local MMC filesystems; never a mergerfs view or ROM file.
    targets = []
    def unescape(value):
        return re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), value)
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left, right = line.split(' - ', 1)
        fields, filesystem = left.split(), right.split()
        target = unescape(fields[4])
        source = unescape(filesystem[1])
        if source.startswith('/dev/mmcblk') and filesystem[0] in ('ext4', 'exfat', 'vfat'):
            if target == '/storage' or target.startswith(('/var/media/', '/storage/')):
                targets.append(Path(target))
    if Path('/storage') not in targets: raise RuntimeError('OS-card mount is not a known MMC filesystem')
    return sorted(set(targets))

WAKE_IRQ_NAMES = ('rk805_pwrkey_fall', 'rk805_pwrkey_rise',
                  'rk817_plug_in', 'rk817_plug_out', 'Lid')


def wake_inputs():
    """Observe charger changes and user wake events; missing data fails open."""
    result = {'irqs': {}, 'lid_closed': None, 'charger_online': None}
    try:
        for line in Path('/proc/interrupts').read_text().splitlines():
            columns = line.partition(':')[2].split()
            if not columns or columns[-1] not in WAKE_IRQ_NAMES:
                continue
            counts = []
            for column in columns:
                if not column.isdecimal(): break
                counts.append(int(column))
            if counts: result['irqs'][columns[-1]] = sum(counts)
        online = Path('/sys/class/power_supply/charger/online').read_text().strip()
        if online in ('0', '1'): result['charger_online'] = int(online)
        for event in Path('/sys/class/input').glob('event*'):
            if (event/'device/name').read_text().strip() != 'gpio-keys-hall': continue
            query = subprocess.run(['evtest', '--query', '/dev/input/'+event.name,
                                    'EV_SW', 'SW_LID'], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=2)
            if query.returncode in (0, 10): result['lid_closed'] = query.returncode == 10
            break
    except (OSError, subprocess.TimeoutExpired):
        pass
    return result


def same_user_inputs(before, after):
    names = ('rk805_pwrkey_fall', 'rk805_pwrkey_rise', 'Lid')
    return (before.get('lid_closed') is True and after.get('lid_closed') is True
            and all(name in before.get('irqs', {}) and name in after.get('irqs', {})
                    and before['irqs'][name] == after['irqs'][name] for name in names))


def charger_only_wake(before, after):
    if not same_user_inputs(before, after): return False
    if before.get('charger_online') not in (0, 1) or after.get('charger_online') not in (0, 1):
        return False
    changed = before['charger_online'] != after['charger_online']
    for name in ('rk817_plug_in', 'rk817_plug_out'):
        if name not in before.get('irqs', {}) or name not in after.get('irqs', {}): return False
        changed = changed or before['irqs'][name] != after['irqs'][name]
    return changed


def run_lid_cycles():
    # Each retry goes through all normal storage checks and charging LED hooks.
    # Never retry unknown wakes, user wakes, or more than three cable changes.
    retries, rapid, pending_inputs = 0, 0, None
    while True:
        completed = run_cycle(pending_inputs)
        if completed is None: return
        cycle = Path(completed)
        print(str(cycle), flush=True)
        report = json.loads((cycle/'after.json').read_text())
        before, after = report['wake_inputs_before'], report['wake_inputs_after']
        if not ENABLED.exists() or not charger_only_wake(before, after): return
        rapid = rapid + 1 if report['sleep_elapsed_seconds'] < 5 else 0
        if retries >= 3 or rapid >= 2:
            print('Charger wake retry limit reached; staying awake until next lid close', flush=True)
            return
        time.sleep(3)  # Let cable status settle and allow a user wake to win.
        current = wake_inputs()
        if (not ENABLED.exists() or not same_user_inputs(after, current)
                or current.get('charger_online') != after.get('charger_online')):
            print('Charger wake retry cancelled by changed lid, power or charging state', flush=True)
            return
        pending_inputs = current
        retries += 1
        print('Charger change while lid closed; returning to deep sleep (%d/3)' % retries, flush=True)


def run_cycle(retry_inputs=None):
    if not DRIVER.exists():
        raise RuntimeError('Experimental firmware suspend driver is absent')
    update = UPDATE
    update.parent.mkdir(parents=True, exist_ok=True)
    with update.open('a+') as update_lock:
        try: fcntl.flock(update_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('Update active; suspend deferred')
        targets = probe_targets()
        ROOT.mkdir(parents=True, exist_ok=True)
        cycle = ROOT / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()))
        cycle.mkdir()
        probes = []
        try:
            for target in targets:
                if not writable(target): raise RuntimeError(str(target) + ' is read-only')
                p = target / ('.butterfly-suspend-probe-' + cycle.name)
                data = os.urandom(4096)
                with p.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
                probes.append((p, data))
            before = snapshot()
            cursor_text = command(['journalctl', '-k', '-b', '-n', '0', '--show-cursor', '--no-pager'])
            cursor = cursor_text.partition('-- cursor: ')[2].strip()
            (cycle/'before.json').write_text(json.dumps(before, indent=2))
            (cycle/'state').write_text('SUSPEND REQUESTED; absent after.json means resume was not recorded\n')
            subprocess.run(['journalctl', '--sync'], check=False)
            os.sync()
            # Explicitly select deep. No fallback to s2idle / freeze.
            POWER.write_text('deep')
            wake_before = wake_inputs()
            if retry_inputs is not None and (not ENABLED.exists()
                    or not same_user_inputs(retry_inputs, wake_before)
                    or wake_before.get('charger_online') != retry_inputs.get('charger_online')):
                (cycle/'state').write_text('CANCELLED: lid, power or charging state changed before automatic re-sleep\n')
                print('Automatic re-sleep cancelled before suspend', flush=True)
                return None
            sleep_started = time.clock_gettime(time.CLOCK_BOOTTIME)
            result = subprocess.run(['systemctl', 'start', 'systemd-suspend.service'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            sleep_elapsed = time.clock_gettime(time.CLOCK_BOOTTIME) - sleep_started
            wake_after = wake_inputs()
            after = snapshot()
            after['wake_inputs_before'] = wake_before
            after['wake_inputs_after'] = wake_after
            after['sleep_elapsed_seconds'] = sleep_elapsed
            after['systemctl_returncode'] = result.returncode
            after['systemctl_output'] = result.stdout
            after['new_kernel_messages'] = command(['journalctl', '-k', '-b', '--after-cursor=' + cursor, '--no-pager']) if cursor else after['kernel']
            after['storage_error_detected'] = bool(re.search(r'mmc.*(?:error -110|card .* removed)|EXT4-fs.*(?:error|abort)|Buffer I/O error|I/O error, dev mmc', after['new_kernel_messages'], re.I))
            after['checks'] = []
            for p, data in probes:
                ok = writable(p.parent) and p.read_bytes() == data
                if ok:
                    with p.open('ab') as f: f.write(b'resumed'); f.flush(); os.fsync(f.fileno())
                    ok = p.read_bytes() == data + b'resumed'
                after['checks'].append({'mount': str(p.parent), 'read_write_verified': ok})
                if not ok: raise RuntimeError('Storage probe failed: ' + str(p.parent))
            (cycle/'after.json').write_text(json.dumps(after, indent=2))
            (cycle/'state').write_text('RETURNED; inspect kernel log and storage checks before acceptance\n')
            os.sync()
            if result.returncode: raise RuntimeError(result.stdout)
            if after['storage_error_detected']: raise RuntimeError('Kernel storage error detected after wake; lid sleep disabled')
            return str(cycle)
        except Exception as error:
            try:
                (cycle/'error.json').write_text(json.dumps({'error': str(error), 'diagnostics': snapshot()}, indent=2))
                set_lid_sleep(False)
                os.sync()
            except OSError: pass
            raise
        finally:
            for p, _ in probes:
                try: p.unlink()
                except OSError: pass

def main():
    if len(sys.argv)>1 and sys.argv[1]=='set-lid-sleep':
        if len(sys.argv) != 3 or sys.argv[2] not in ('on', 'off'):
            raise ValueError('Expected set-lid-sleep on|off')
        set_lid_sleep(sys.argv[2] == 'on')
        return 0
    if len(sys.argv)>1 and sys.argv[1]=='cycle':
        with open('/run/butterflyos-suspend-test.lock', 'w') as lock:
            try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: return 0
            run_lid_cycles()
        return 0
    spec=importlib.util.spec_from_file_location('tool_ui', Path(__file__).with_name('butterflyos-tool-ui.py'))
    ui_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui_module)
    ui=ui_module.ToolUI('Experimental Suspend')
    try:
        while True:
            choice=ui.menu('EXPERIMENTAL SUSPEND', [
                ('Sleep now', 'Suspend to RAM; wake with power or by opening the lid'),
                ('Enable lid sleep', 'Suspend on lid close; remembers choice after reboot'),
                ('Disable lid sleep', 'Return to display-only lid handling'),
                ('Save diagnostics', 'Collect current kernel, battery and SD-controller information'),
                ('Back', 'Return to Tools')], 0)
            if choice is None or choice==4:return 0
            if choice==0:
                status=subprocess.run(['systemctl','start','butterflyos-suspend-test.service']).returncode
                ui.message('SUSPEND TEST', 'Returned from suspend. Check your game and both cards. Logs: '+str(ROOT) if not status else 'Suspend failed. Lid sleep disabled; inspect logs under '+str(ROOT))
            elif choice==1:
                set_lid_sleep(True)
                ui.message('LID SLEEP ENABLED','Enabled, including after reboot. Close Tools and launch a game, then close the lid. Open it or press power to wake. Long and overnight tests are still required.')
            elif choice==2:
                set_lid_sleep(False);ui.message('LID SLEEP DISABLED','The lid uses display-off behavior, including after reboot. Enable lid sleep here to restore suspend.')
            elif choice==3:
                ROOT.mkdir(parents=True,exist_ok=True);p=ROOT/('manual-'+str(time.time_ns())+'.json');p.write_text(json.dumps(snapshot(),indent=2));ui.message('REPORT SAVED',str(p))
    finally:ui.close()

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:
        if len(sys.argv) > 1 and sys.argv[1] == 'cycle':
            try: set_lid_sleep(False)
            except OSError: pass
        print('Suspend test error: '+str(error),file=sys.stderr)
        sys.exit(1)
