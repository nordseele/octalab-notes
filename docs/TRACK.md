# The current track, its slot, and RANDOMIZE PAGE

Everything here is OS 1.40C, MAIN OS sha256 `164f3122…`, load base `0x40000400`
— VA = file offset + base.

## Which track is selected ✅

`0x100b14cc`, one byte, 0..7. Three independent sources agree and none of them
required disassembling anything: octabam's `ARCHITECTURE.md` ("Globals | current
track `0x100b14cc`") and its `modules/selprobe/selprobe.s`, ems-octakit's
`GK_STOCK_CURRENT_TRACK_PRIMARY`, and octamax's `build_dual256.py`. The current
pattern is `0x100b14cf` (octabam also records `0x80000003`, which
`FUN_40093468` reads; octamax uses the `0x100b14cf` mirror and that is the one
with hardware behind it).

## Which slot that track plays ✅

The arithmetic is the OS's own, at `0x40083c64`, and octamax reproduces it in
`build_dual256.py` wave 26. The same expression appears inside `FUN_40093468`:

```
bank    = *(0x46c82456)                 | the active bank buffer
pat     = *(0x100b14cf)                 | current pattern
track   = *(0x100b14cc)                 | 0..7
type    = *(bank + pat*0x18b2 + track + 0x8eda2)          | sign-extended
slot    = *(bank + pat*0x18b2 + track*5 + type + 0x8f04a) | zero-extended
```

`0x18b2` is 6322 bytes per pattern. The slot byte is read **zero-extended** on
purpose, so a value ≥ 128 survives.

**Machine type 0 is STATIC** 🟡. `FUN_40093468` — the voice re-arm the storage
job posts after any slot change — walks the eight tracks and only touches a
track whose type byte is `0`, which is exactly the set of tracks playing from
the static pool. `REROLL TRACK` gates on the same test and leaves every other
track alone, because a non-static track's slot byte indexes the FLEX settings
array instead.

**Falsifier:** REROLL TRACK does nothing on a track that plainly is a static
machine.

`0x4006de34(type, slot)` is the OS's own publisher for the pair, if a feature
ever needs to *change* which slot a track plays rather than what is in it.

## RANDOMIZE PAGE 🟡 — decoded, deliberately not wired

The firmware does have it: the strings `'RANDOMIZE PAGE'` (`0x400b48a9`),
`'RANDOMIZE'` (`0x400b53a5`) and `'CREATE RANDOM LOCKS'` (`0x400b6c38`) are all
in the image.

`'RANDOMIZE PAGE'` is referenced from `0x4005cb9a`, inside the function that
starts at **`0x4005b9c0`** — which ems-octakit's `abi.inc` already names
`GK_STOCK_RANDOMIZE_PAGE_WRITER` and calls from its own randomize module.

What is settled about it:

- **It takes no arguments.** Its prologue reads no stack parameters; it works
  from `0x400bcd14` and the UI globals.
- **It is reached only through a table.** One pointer, at `0x400bab22` — there
  is no `jsr 0x4005b9c0` anywhere in the image, so the gesture dispatches
  through that entry.

What is **not** settled, and why no menu row calls it yet: it reads the current
*page* from UI state, and octalab's popup is not a parameter page. Calling it
from there would be a guess about what the machine is showing, and guesses of
exactly that shape have cost two flashes already
(`modules/poolfill/ONDEVICE.md` §7 and §8).

**The next step is one experiment**, and it is cheap: boot under emulation, set
the current track and page the way a parameter screen leaves them, call
`0x4005b9c0`, and read the track's parameter block before and after. If the
values change and nothing faults, the row is a `jsr` and a refresh.
