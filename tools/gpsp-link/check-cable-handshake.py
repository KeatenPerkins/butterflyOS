#!/usr/bin/env python3
"""Compile the actual client update path against a delayed-host scenario."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
original = root / '.cache/gpsp-link-tests/cable-core/source/serial_proto.c'
patch = root / 'tools/gpsp-link/cable-handshake-wait.patch'
prefix = '''
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
#define MAX_QPACK 128
#define MAX_FPACK 512
#define SRPT_DEBUG_LOG(...)
#define STATE_PREINIT 0
#define STATE_HANDSHAKE 1
#define STATE_CONNECTED 2
#define SEQ_HANDSHAKE_TOKENS 18
#define SLAVE_IRQ_CYCLES_C 28672
#define SLAVE_IRQ_CYCLES_H 280064
#define SLAVE_HANDSHAKE 0xB9A0
#define MASTER_HANDSHAKE 0x8FFF
#define NET_SERPOKE_HEADER 0x4d504b31
#define netorder32(x) (x)
#define REG_SIOMULTI0 0
#define REG_SIOMLT_SEND 4
static unsigned netplay_client_id=1, connected_messages;
static u16 regs[5];
static u16 read_ioreg(unsigned r) { return regs[r]; }
static void write_ioreg(unsigned r,u16 v) { regs[r]=v; }
static void serialpoke_senddata(u16 state,const u16 *p) {
  if (state==STATE_CONNECTED) connected_messages++;
}
static void unpack16(u16 *out,const u32 *in,unsigned count) {
  for (unsigned i=0;i<count;i++) out[i]=0;
}
static int ismemzero(const void *ptr, unsigned bytes) {
  const u8 *p=ptr; while (bytes--) if (*p++) return 0; return 1;
}
'''
suffix = '''
int main(void) {
  serstate.poke.peer[0].state=STATE_CONNECTED;
  serstate.poke.peer[1].state=STATE_CONNECTED;
  regs[REG_SIOMLT_SEND]=SLAVE_HANDSHAKE;
  for (unsigned i=0;i<19;i++) serialpoke_update(SLAVE_IRQ_CYCLES_C+1);
  if (serstate.poke.peer[1].state!=STATE_HANDSHAKE) return 1;
  unsigned before=connected_messages;
  /* Host's old CONNECTED status remains visible during network delay. */
  for (unsigned i=0;i<6;i++) {
    if (serialpoke_update(SLAVE_IRQ_CYCLES_C+1)) return 2;
    if (serstate.poke.peer[1].state!=STATE_HANDSHAKE) return 3;
  }
  if (connected_messages!=before) return 4;
  /* A real host handshake followed by CONNECTED must still resume. */
  serstate.poke.peer[0].state=STATE_HANDSHAKE;
  if (!serialpoke_update(SLAVE_IRQ_CYCLES_H+1)) return 5;
  serstate.poke.peer[0].state=STATE_CONNECTED;
  if (!serialpoke_update(SLAVE_IRQ_CYCLES_C+1)) return 6;
  if (serstate.poke.peer[1].state!=STATE_CONNECTED) return 7;
  if (regs[0]!=MASTER_HANDSHAKE) return 8;
  if (connected_messages!=before+1) return 9;
  /* Normal payload updates remain possible after that handshake. */
  regs[REG_SIOMLT_SEND]=0;
  if (!serialpoke_update(SLAVE_IRQ_CYCLES_C+1)) return 10;
  /* Receive batching must not hide a real handshake followed by CONNECTED. */
  regs[REG_SIOMLT_SEND]=SLAVE_HANDSHAKE;
  for (unsigned i=0;i<19;i++) serialpoke_update(SLAVE_IRQ_CYCLES_C+1);
  if (serstate.poke.peer[1].state!=STATE_HANDSHAKE) return 11;
  u32 packet[6]={NET_SERPOKE_HEADER,STATE_HANDSHAKE,0,0,0,0};
  serialpoke_net_receive(packet,sizeof(packet),0);
  packet[1]=STATE_CONNECTED;
  serialpoke_net_receive(packet,sizeof(packet),0);
  if (!serialpoke_update(SLAVE_IRQ_CYCLES_C+1)) return 12;
  if (serstate.poke.peer[1].state!=STATE_CONNECTED) return 13;
  return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='bf-handshake-check-') as directory:
    d = Path(directory)
    candidate = d / 'serial_proto.c'
    candidate.write_text(original.read_text())
    subprocess.run(['patch', str(candidate), str(patch)], check=True, capture_output=True)
    for name, source, expected in [('upstream', original, 2), ('candidate', candidate, 0)]:
        s = source.read_text()
        state = s[s.index('static union {'):s.index('// Serial-Poke:')]
        update = s[s.index('bool serialpoke_update('):s.index('void serialpoke_net_receive(')]
        c = d / (name + '.c')
        receive = s[s.index('void serialpoke_net_receive('):s.index('// Serial-AdvWrs:')]
        c.write_text(prefix + state + update + receive + suffix)
        binary = d / name
        subprocess.run(['cc', '-std=c99', '-O0', str(c), '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)])
        assert result.returncode == expected, (name, result.returncode)
        print(name, 'exit', result.returncode)
print('Stale-host reconnect reproduced upstream; wait candidate passes delayed handshake')
