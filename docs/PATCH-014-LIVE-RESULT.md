# Patch 014 live result — 2026-09-23

Ruby/Ruby link test with `.20` hosting and `.17` joining progressed through repeated paired serialize/unserialize operations. Every interrupt guard reported `request0=1 request1=1 ack0=1 ack1=1`; `.17` eventually crashed and `.20` disconnected cleanly.

GDB captured `.17` terminating with `SIGSEGV` in:

```
_enqueueEvent -> _lockstepEvent -> mTimingTick -> GBAProcessEvents -> _mCoreThreadRun
```

At the same time, another mGBA worker was in `GBASIOLockstepDriverSetMode` via `_switchMode -> GBAIOWrite -> GBAStore16 -> ARMRunLoop`. This is a new mGBA link-thread race in the lockstep event queue/state restore path, not the previous interrupt/deadlock/assertion failure and not a Mali/graphics fault.

Next investigation: keep both workers quiescent until the restored lockstep driver, event queue, and timing state are fully re-established. Audit `_enqueueEvent`/`_lockstepEvent` lifetime and prevent either worker from enqueueing against the old queue while the other changes link mode. Repeat the same test under GDB after the fix.

The temporary GDB launcher on `.17` was restored to the normal `/usr/bin/retroarch` launcher.
