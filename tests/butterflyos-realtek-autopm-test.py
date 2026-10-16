#!/usr/bin/env python3
"""Compile the patched USB acquire/release blocks against simulated kernel APIs."""
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT/'sources/RTL8733BU/RTL8733BU-c46aa25e237cb43f33390cf58eee5c69d9b32883.tar.gz'
PATCH = ROOT/'projects/ROCKNIX/packages/linux-drivers/RTL8733BU/patches/005-balance-usb-autopm-reference.patch'
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    with tarfile.open(ARCHIVE) as archive:
        member = next(m for m in archive.getmembers() if m.name.endswith('/os_dep/linux/usb_intf.c'))
        p=base/'os_dep/linux/usb_intf.c';p.parent.mkdir(parents=True)
        p.write_bytes(archive.extractfile(member).read())
    subprocess.run(['patch', '--batch', '-p1', '-i', str(PATCH)], cwd=base, check=True)
    source=p.read_text()
    start=source.index('/* 2012-07-11 Move here')
    acquire=source[source.index('#if', start):source.index('\n\t/* set mac addr */', start)]
    start=source.index('static void rtw_usb_primary_adapter_deinit(')
    start=source.index('#ifdef CONFIG_BT_COEXIST\n\tif (1 == pwrctl->autopm_cnt)', start)
    release=source[start:source.index('\n\trtw_free_drv_sw', start)]
    code=r'''
#include <assert.h>
#define CONFIG_BT_COEXIST 1
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define LINUX_VERSION_CODE KERNEL_VERSION(7,0,2)
#define RTW_INFO(...) ((void)0)
struct usb_interface { int refs, get_result; };
struct pwrctrl_priv { int autopm_cnt; };
struct dvobj_priv { struct pwrctrl_priv power; struct usb_interface *pusbintf; };
#define dvobj_to_pwrctl(d) (&(d)->power)
#define adapter_to_dvobj(d) (d)
static int usb_autopm_get_interface(struct usb_interface *i) {
    if (i->get_result<0) return i->get_result;
    ++i->refs; return i->get_result;
}
static void usb_autopm_put_interface(struct usb_interface *i) {
    assert(i->refs>0); --i->refs;
}
'''
    code+='static void acquire(struct dvobj_priv *dvobj, struct usb_interface *pusb_intf) {\n'+acquire+'\n}\n'
    code+='static void release(struct dvobj_priv *padapter) { struct pwrctrl_priv *pwrctl=&padapter->power;\n'+release+'\n}\n'
    code+=r'''
int main(void) {
    int results[]={0,1,-1,-13,-19};
    for (unsigned n=0;n<sizeof(results)/sizeof(results[0]);n++) {
        struct usb_interface intf={.refs=3,.get_result=results[n]};
        struct dvobj_priv dev={.power={.autopm_cnt=9},.pusbintf=&intf};
        acquire(&dev,&intf);
        assert(dev.power.autopm_cnt==(results[n]>=0));
        assert(intf.refs==3+(results[n]>=0));
        release(&dev); assert(intf.refs==3 && dev.power.autopm_cnt==0);
        release(&dev); assert(intf.refs==3 && dev.power.autopm_cnt==0);
    }
    return 0;
}
'''
    (base/'test.c').write_text(code)
    subprocess.run(['cc','-Wall','-Wextra','-Werror',str(base/'test.c'),'-o',str(base/'test')],check=True)
    subprocess.run([str(base/'test')],check=True)
print('Realtek USB reference checks passed (actual patched blocks; simulated kernel APIs).')
