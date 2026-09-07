# Before flashing anything

This page exists because a build cost an hour of SysEx recovery, and both rules
that would have prevented it were already known and not applied. It is a
checklist, not advice: every line is answerable yes or no before the file is
written to the card.

## 1. Does this build touch the recovery path? ⚠️

**The deepest rule, and the one that actually cost the hour.**

`OS UPGRADE` is reached through `[FUNCTION] + [MIXER]` → SYSTEM. The failed
build modified the very screen that `[FUNCTION] + [MIXER]` draws. When it
crashed, it took the CF upgrade route with it, and the only way back was
`[FUNCTION]` + power → `[TRIG 3]` → MIDI UPGRADE: ~1 hour at 31250 baud.

Never make the first test of a technique the thing you would need in order to
undo it. Had the same probe gone into any other menu, a bad build would have
cost thirty seconds and a card copy.

- Does the patch touch the PROJECT/SYSTEM menu screen, its descriptors, its
  tables, or anything they call? → **the CF route is at risk; choose another
  target for the experiment, or accept the MIDI recovery in advance.**
- If the answer is unavoidably yes, have the MIDI recovery physically ready —
  interface connected, SysEx sender open, official `.syx` loaded — *before*
  flashing, not after.

## 2. Is every region this build writes to canary-proven? ⚠️

Zero static references (`tools/cave_scan.py`) says nothing points to a region
*in the image*. It says nothing about what the OS does with that memory once it
is running. Those are two different claims and only the second one matters at
runtime. See `docs/CAVES.md` — TAIL-A passed the first and failed the second,
on hardware, at the cost above.

- Is the region one that has survived a canary run (fill, use the unit for a
  full session, read back)? → if not, **the only thing that may be flashed into
  it is the canary itself**, which changes no behaviour and cannot lock anything
  out.
- `0x400d64e0 .. 0x400d7c3b` is proven — octamax has shipped from it for months
  on real units.

## 3. The ordinary checks

- The build verifies the **original bytes** at every site it patches, and reads
  every write back out of the finished image.
- The packaged file **round-trips**: `tools/extract_os.py` on the output
  reproduces the patched image byte for byte.
- The **byte count** against stock is what you expect, and no instruction was
  added that you did not intend.
- The **version string** is unique to this build, so the unit can tell you what
  it is running (`SYSTEM STATUS → OS VERSION`). The Octatrack's clock runs
  behind, so never identify a build by a file's timestamp.
- The official `.syx` is on the machine you are flashing from, and you know how
  you would send it.
- Never cut power during `UPDATING FLASH`.

## The order that follows from all this

1. **Canary first**, into any region not yet proven. No behaviour change, so no
   lockout is possible whatever happens.
2. **Then the probe**, in a proven region, in a menu that is *not* on the
   recovery path if that can be arranged.
3. **Then the feature.**

Each step is one flash and answers one question. That is slower than it feels
it should be, and it is still faster than an hour of SysEx.
