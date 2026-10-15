import hashlib, subprocess, tempfile, sys
from pathlib import Path
# Usage: python3 tests/butterflyos-gen3-cross-family-swap-test.py HELPER LEFT_SAVE RIGHT_SAVE
# Uses temporary outputs only; supply saves with occupied box 0 / slot 0.
helper=sys.argv[1]
left,right=map(Path,sys.argv[2:4])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect(p):
    lines=subprocess.check_output([helper,'inspect','--save',str(p)],text=True).splitlines()
    return [x for x in lines if x.startswith(('generation=','save_type=','trainer_','party_record\t','box_record\t'))]
def swap(a,b,c,d):
    subprocess.run([helper,'swap-gen3','--left',str(a),'--left-box','0','--left-slot','0','--right',str(b),'--right-box','0','--right-slot','0','--output-left',str(c),'--output-right',str(d)],check=True)
before=[digest(left),digest(right)]
a,b=inspect(left),inspect(right)
with tempfile.TemporaryDirectory(prefix='butterfly-cross-gen3-') as temp:
    c,d,e,f=[Path(temp)/n for n in ['emerald.srm','leafgreen.srm','roundtrip-emerald.srm','roundtrip-leafgreen.srm']]
    swap(left,right,c,d)
    aa,bb=inspect(c),inspect(d)
    ai=next(i for i,x in enumerate(a) if x.startswith('box_record\t0\t0\t'))
    bi=next(i for i,x in enumerate(b) if x.startswith('box_record\t0\t0\t'))
    expected_a=a.copy();expected_b=b.copy()
    expected_a[ai]=b[bi];expected_b[bi]=a[ai]
    assert aa==expected_a and bb==expected_b,'unexpected trainer, party or PC record change'
    swap(c,d,e,f)
    assert inspect(e)==a and inspect(f)==b,'roundtrip mismatch'
    assert [digest(left),digest(right)]==before,'source saves changed'
print('PASS: cross-family swap, full PC/party/trainer preservation, reverse swap, sources unchanged')
