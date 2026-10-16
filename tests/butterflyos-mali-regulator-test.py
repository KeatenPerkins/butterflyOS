#!/usr/bin/env python3
"""Exercise the patched driver's actual power helpers with fake regulator APIs."""
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT/'sources/mali-bifrost/mali-bifrost-39da994bb6fc8819e5e8c1873907dd21d17e53c1.tar.gz'
PATCH = ROOT/'projects/ROCKNIX/devices/RK3566/patches/mali-bifrost/003-balance-regulator-references.patch'
REL = 'product/kernel/drivers/gpu/arm/midgard/'

def function(source, name):
    start = source.index('static void '+name+'(')
    end = source.index('\n}', start)+2
    return source[start:end]

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    with tarfile.open(ARCHIVE) as archive:
        for rel in ('mali_kbase_defs.h', 'mali_kbase_core_linux.c',
                    'platform/devicetree/mali_kbase_runtime_pm.c'):
            member = next(m for m in archive.getmembers() if m.name.endswith('/'+REL+rel))
            p = base/REL/rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(archive.extractfile(member).read())
    subprocess.run(['patch', '--batch', '-p1', '-i', str(PATCH)], cwd=base, check=True)
    source = (base/REL/'platform/devicetree/mali_kbase_runtime_pm.c').read_text()
    code = r'''
#include <assert.h>
#include <stdbool.h>
#define CONFIG_REGULATOR 1
#define BASE_MAX_NR_CLOCKS_REGULATORS 2
struct regulator { int refs, fail_on, fail_off; };
struct clk { int refs; };
struct kbase_device {
    struct regulator *regulators[2]; bool regulator_enabled[2];
    unsigned nr_regulators, nr_clocks; struct clk *clocks[2]; void *dev;
};
static int regulator_enable(struct regulator *r) {
    if (r->fail_on) return -1; ++r->refs; return 0;
}
static int regulator_disable(struct regulator *r) {
    if (r->fail_off) return -1;
    assert(r->refs>0); --r->refs; return 0;
}
static void clk_prepare_enable(struct clk *c) { ++c->refs; }
static void clk_disable_unprepare(struct clk *c) { --c->refs; }
#define dev_err(...) ((void)0)
'''
    core = (base/REL/'mali_kbase_core_linux.c').read_text()
    start = core.index('\t/* Runtime PM starts active.')
    init = core[start:core.index('\n#endif', start)]
    start = core.index('clocks_probe_defer:')
    cleanup = core[core.index('\n', start)+1:core.index('\n\treturn err;', start)]
    code += 'static void regulator_put(struct regulator *r) { (void)r; }\n'
    code += 'static int init_refs(struct kbase_device *kbdev) { unsigned i; int err;\n'
    code += init+'\nreturn 0;\nclocks_probe_defer:\n'+cleanup+'\nreturn err;\n}\n'
    code += function(source, 'enable_gpu_power_control')+'\n'
    code += function(source, 'disable_gpu_power_control')+'\n'
    code += r'''
int main(void) {
    /* One unrelated OPP consumer keeps the physical supply enabled. */
    struct regulator r={.refs=1};
    struct kbase_device d={.regulators={&r}, .nr_regulators=1};
    disable_gpu_power_control(&d); assert(r.refs==1);
    enable_gpu_power_control(&d); assert(r.refs==2 && d.regulator_enabled[0]);
    enable_gpu_power_control(&d); assert(r.refs==2);
    disable_gpu_power_control(&d); assert(r.refs==1 && !d.regulator_enabled[0]);
    disable_gpu_power_control(&d); assert(r.refs==1);
    /* Failed enable must not acquire ownership or authorize a disable. */
    r.fail_on=1; enable_gpu_power_control(&d);
    assert(r.refs==1 && !d.regulator_enabled[0]);
    disable_gpu_power_control(&d); assert(r.refs==1);
    r.fail_on=0; enable_gpu_power_control(&d); assert(r.refs==2);
    /* Failed disable retains ownership, allowing a later retry. */
    r.fail_off=1; disable_gpu_power_control(&d);
    assert(r.refs==2 && d.regulator_enabled[0]);
    r.fail_off=0; disable_gpu_power_control(&d);
    assert(r.refs==1 && !d.regulator_enabled[0]);
    /* Startup already owns a reference, matching runtime-active state. */
    assert(init_refs(&d)==0);
    enable_gpu_power_control(&d); assert(r.refs==2);
    disable_gpu_power_control(&d); disable_gpu_power_control(&d);
    assert(r.refs==1);
    /* Failed startup of a second regulator releases the first reference. */
    struct regulator r2={.refs=1}, r3={.refs=1, .fail_on=1};
    struct kbase_device failed={.regulators={&r2,&r3}, .nr_regulators=2};
    assert(init_refs(&failed)==-1);
    assert(r2.refs==1 && r3.refs==1 && !failed.regulator_enabled[0]);
    /* Repeated resume/runtime-idle/system-suspend sequences. */
    for (int i=0;i<100;i++) {
        enable_gpu_power_control(&d); disable_gpu_power_control(&d);
        disable_gpu_power_control(&d); assert(r.refs==1);
    }
    return 0;
}
'''
    (base/'test.c').write_text(code)
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                    str(base/'test.c'), '-o', str(base/'test')], check=True)
    subprocess.run([str(base/'test')], check=True)
print('GPU regulator ownership checks passed (real patched helpers; simulated hardware).')
