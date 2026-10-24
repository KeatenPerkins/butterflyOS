#!/usr/bin/env python3
"""Compile and execute the actual shared-port helper delivered by the RA patch."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
patch = root / 'projects/ROCKNIX/packages/emulators/libretro/retroarch/patches/0015-shared-player-one-defaults.patch'
text = patch.read_text().split('--- a/input/input_driver.c', 1)[0]
header = '\n'.join(line[1:] for line in text.splitlines()
                   if line.startswith('+') and not line.startswith('+++'))
test = r'''
#include <assert.h>
#include "butterflyos_shared_player1.h"
int main(void) {
   unsigned none[] = {0, 1, 2, 3, 4};
   unsigned one[] = {1, 0, 2, 3, 4};
   unsigned two[] = {1, 2, 0, 3, 4};
   unsigned three[] = {1, 2, 3, 0, 4};
   unsigned fallback[] = {0, 2, 1, 3, 4};
   unsigned i;
   for (i = 0; i < 5; i++) {
      assert(butterflyos_default_game_port(i, none, 5, "0") == i);
      assert(butterflyos_default_game_port(i, two, 5, NULL) == i);
      assert(butterflyos_default_game_port(i, two, 5, "invalid") == i);
      assert(butterflyos_default_game_port(i, two, 5, "0extra") == i);
      assert(butterflyos_default_game_port(i, two, 5, "-1") == i);
      assert(butterflyos_default_game_port(i, two, 5, "99999") == i);
      assert(butterflyos_default_game_port(i, one, 5, "0") == (i == 1 ? 0 : i));
      assert(butterflyos_default_game_port(i, two, 5, "0") == (i == 2 ? 0 : i));
      assert(butterflyos_default_game_port(i, three, 5, "0") == (i == 3 ? 0 : i));
      assert(butterflyos_default_game_port(i, fallback, 5, "0") == i);
   }
   return 0;
}
'''
with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    (folder / 'butterflyos_shared_player1.h').write_text(header)
    (folder / 'test.c').write_text(test)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    str(folder / 'test.c'), '-o', str(folder / 'test')], check=True)
    subprocess.run([str(folder / 'test')], check=True)
print('Shared Player 1: no pad / 1–3 external pads / fallback / invalid opt-in checks passed.')
