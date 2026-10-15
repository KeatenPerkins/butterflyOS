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
DRIVER = Path('/sys/bus/platform/drivers/rockchip-pm-config')
POWER = Path('/sys/power/mem_sleep')
UPDATE = Path('/storage/.cache/butterflyos-update/update.lock')

def command(args):
    try:
        p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12)
        return p.stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return str(e)

def snapshot():
    report = {'time': time.time(), 'mounts': command(['findmnt', '-J']),
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
    mounts = json.loads(command(['findmnt', '-J', '-o', 'SOURCE,TARGET,FSTYPE']))
    targets = []
    def walk(nodes):
        for n in nodes:
            if n.get('source', '').startswith('/dev/mmcblk') and n['fstype'] in ('ext4', 'exfat', 'vfat'):
                if n['target'] == '/storage' or n['target'].startswith(('/var/media/', '/storage/')):
                    targets.append(Path(n['target']))
            walk(n.get('children', []))
    walk(mounts['filesystems'])
    if Path('/storage') not in targets: raise RuntimeError('OS-card mount is not a known MMC filesystem')
    return sorted(set(targets))

def run_cycle():
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
            result = subprocess.run(['systemctl', 'start', 'systemd-suspend.service'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            after = snapshot()
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
                ENABLED.unlink(missing_ok=True)
                os.sync()
            except OSError: pass
            raise
        finally:
            for p, _ in probes:
                try: p.unlink()
                except OSError: pass

def main():
    if len(sys.argv)>1 and sys.argv[1]=='cycle':
        with open('/run/butterflyos-suspend-test.lock', 'w') as lock:
            try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: return 0
            print(run_cycle(), flush=True)
        return 0
    spec=importlib.util.spec_from_file_location('tool_ui', Path(__file__).with_name('butterflyos-tool-ui.py'))
    ui_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui_module)
    ui=ui_module.ToolUI('Experimental Suspend')
    try:
        while True:
            choice=ui.menu('EXPERIMENTAL SUSPEND', [
                ('Sleep now', 'Suspend to RAM; wake with power or by opening the lid'),
                ('Enable lid sleep', 'Until reboot: real lid suspend; pauses lid shutdown timer'),
                ('Disable lid sleep', 'Return to display-only lid handling'),
                ('Save diagnostics', 'Collect current kernel, battery and SD-controller information'),
                ('Back', 'Return to Tools')], 0)
            if choice is None or choice==4:return 0
            if choice==0:
                status=subprocess.run(['systemctl','start','butterflyos-suspend-test.service']).returncode
                ui.message('SUSPEND TEST', 'Returned from suspend. Check your game and both cards. Logs: '+str(ROOT) if not status else 'Suspend failed. Lid sleep disabled; inspect logs under '+str(ROOT))
            elif choice==1:
                ENABLED.parent.mkdir(parents=True,exist_ok=True);ENABLED.touch()
                ui.message('LID SLEEP ENABLED','Enabled until reboot. Close Tools and launch a game, then close the lid. Open it or press power to wake. Long and overnight tests are still required.')
            elif choice==2:
                ENABLED.unlink(missing_ok=True);ui.message('LID SLEEP DISABLED','The lid uses normal display-off behavior again.')
            elif choice==3:
                ROOT.mkdir(parents=True,exist_ok=True);p=ROOT/('manual-'+str(time.time_ns())+'.json');p.write_text(json.dumps(snapshot(),indent=2));ui.message('REPORT SAVED',str(p))
    finally:ui.close()

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:print('Suspend test error: '+str(error),file=sys.stderr);sys.exit(1)
