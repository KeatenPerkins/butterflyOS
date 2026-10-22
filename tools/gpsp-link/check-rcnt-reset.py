#!/usr/bin/env python3
"""Exercise actual upstream and candidate RCNT handlers with register stubs."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
source = (root / '.cache/gpsp-link-tests/cable-core/source/serial.c').read_text()
mode = source[source.index('static u32 get_serial_mode('):source.index('uint16_t serial_mul_siocnt(')]
handler = source[source.index('cpu_alert_type write_rcnt('):source.index('cpu_alert_type write_siocnt(')]
prefix = '''
#include <stdint.h>
#include <stdio.h>
typedef uint16_t u16; typedef uint32_t u32; typedef int cpu_alert_type;
enum { REG_RCNT, REG_SIOCNT, CPU_ALERT_NONE=0, SERIAL_MODE_RFU=9 };
enum { SERIAL_MODE_NORMAL, SERIAL_MODE_MULTI, SERIAL_MODE_UART,
       SERIAL_MODE_GPIO, SERIAL_MODE_JOYBUS };
static unsigned regs[2], resets; static int serial_mode=0;
static unsigned read_ioreg(unsigned r) { return regs[r]; }
static void write_ioreg(unsigned r,unsigned v) { regs[r]=v; }
static void rfu_reset(void) {}
static void serialproto_reset(void) { resets++; }
static uint16_t serial_mul_siocnt(void) { return 8; }
'''
suffix = '''
int main(void) {
  /* GPIO -> multiplayer must reset; repeated multiplayer writes must not. */
  regs[REG_RCNT]=0x8000; regs[REG_SIOCNT]=0x2000; resets=0;
  write_rcnt(0); if (resets != 1) return 1;
  write_rcnt(0); if (resets != 1) return 2;
  /* GPIO -> normal must not reset multiplayer state. */
  regs[REG_RCNT]=0x8000; regs[REG_SIOCNT]=0; resets=0;
  write_rcnt(0); if (resets) return 3;
  /* Enabling GPIO and remaining there must not reset multiplayer state. */
  regs[REG_RCNT]=0; regs[REG_SIOCNT]=0x2000; resets=0;
  write_rcnt(0x8000); write_rcnt(0x8000); if (resets) return 4;
  return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='bf-rcnt-check-') as directory:
    d = Path(directory)
    patched = handler.replace(
        'get_serial_mode(oldval, read_ioreg(REG_RCNT))',
        'get_serial_mode(read_ioreg(REG_SIOCNT), oldval)').replace(
        'get_serial_mode(value, read_ioreg(REG_RCNT))',
        'get_serial_mode(read_ioreg(REG_SIOCNT), value)')
    assert patched != handler
    for name, body, expected in [('upstream', handler, 1), ('candidate', patched, 0)]:
        c = d / (name + '.c')
        c.write_text(prefix + mode + body + suffix)
        binary = d / name
        subprocess.run(['cc', '-std=c99', '-O0', str(c), '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)])
        assert result.returncode == expected, (name, result.returncode)
        print(name, 'exit', result.returncode)
print('RCNT transition regression reproduced upstream; candidate passes all cases')
