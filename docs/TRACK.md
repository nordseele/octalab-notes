# The current track, its slot, and RANDOMIZE PAGE

Everything here is OS 1.40C, MAIN OS sha256 `164f3122…`, load base `0x40000400`
— VA = file offset + base.

## Which track is selected ✅

`0x100b14cc`, one byte, 0..7. Three independent sources agree and none of them
required disassembling anything: octabam's `ARCHITECTURE.md` ("Globals | current
track `0x100b14cc`") and its `modules/selprobe/selprobe.s`, ems-octakit's
`GK_STOCK_CURRENT_TRACK_PRIMARY`, and octamax's `build_dual256.py`.

## Current part, current pattern 🟡 (corrected 10 Sep 2026)

`0x100b14cf` is the **part** the current pattern is linked to, not the pattern.
This page called it the pattern until 10 Sep 2026; the arithmetic below is
unchanged, only the name. The writer at `0x40062120..0x4006214e`, quoted in
octabam's `docs/firmware/EXTERNAL.md` §6 and read again here from the same
image:

```
mvzb   0x80000004,%d0          | index
mulsl  #0x8ed8,%d0             | × pattern record size
addl   0x46c82456,%d0          | + bank
...    record + 0x8e57         | the pattern's part link
moveb  %d0,0x80000003
moveb  %d0,0x100b14cf
```

So `[0x80000004]` would be the current pattern, and `0x80000003` /
`0x100b14cf` its part (octamax uses the `0x100b14cf` mirror, and that is the
one with hardware behind it). One line of evidence — a code read — hence 🟡.

**Falsifier:** switch patterns under emulation; `0x80000004` does not follow
the pattern number, or `0x100b14cf` does not follow the pattern's part link.

## Which slot that track plays ✅

The arithmetic is the OS's own, at `0x40083c64`, and octamax reproduces it in
`build_dual256.py` wave 26. The same expression appears inside `FUN_40093468`:

```
bank    = *(0x46c82456)                 | the active bank buffer
part    = *(0x100b14cf)                 | current part (see above)
track   = *(0x100b14cc)                 | 0..7
type    = *(bank + part*0x18b2 + track + 0x8eda2)          | sign-extended
slot    = *(bank + part*0x18b2 + track*5 + type + 0x8f04a) | zero-extended
```

`0x18b2` is 6322 bytes per part; the parts start at `bank + 0x8ed80`, after
the sixteen `0x8ed8`-byte pattern records. The slot byte is read **zero-extended** on
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


## Parameter storage, and the LFO's destination ✅ (8 Sep 2026)

The parameter validator `FUN_40002318` clamps every field a part holds, and its
argument turns out to be **`part = bank + part*0x18b2 + 0x8ed80`**. That is
worth stating because it converts the validator into a map: every clamp in it
names an address and the descriptor entry that bounds it.

Confirmed twice against octabam's independently derived offsets: the
validator's `part + 0x11a` block is their `Part + 0x8ee9a` (24 B/track, page 1)
and its `part + 0x2a` is their `Part + 0x8edaa` (PLAYBACK page 1).

### The 24-byte page-1 block is LFO, AMP, FX1, FX2 ✅

`bank + part*0x18b2 + 0x8ee9a + track*24`, six bytes each, and the order was
octabam's open 🟡. Two things settle it. A descriptor's range table sits at
`desc+0x6a`, and the validator bounds offset `+0` with `0x400d3860` and `+6`
with `0x400d39f2` — which are LFO's descriptor `0x400d37f6` and AMP's
`0x400d3988`, each plus `0x6a`. And a booted project reads:

```
track 0:  32 32 32   0  0  0 |  0 127 127 64 64 127 | …
          SPD1/2/3  DEP1/2/3 | ATK HOLD REL VOL BAL XVOL
```

which is an LFO at rest and an AMP at its defaults, in that order.

So the scene byte map is **PLAYBACK 0..5, LFO 6..11, AMP 12..17, FX1 18..23,
FX2 24..29**.

### The LFO destination ✅

`bank + part*0x18b2 + 0x8f072 + track*30 + n` for LFO `n` = 0..2, one byte,
**values 0..29 using the same numbering as the scene bytes** — so 18..29 aim an
LFO at the effect pages.

The validator clamps those three bytes with entry 6 of the LFO descriptor's
range table, and that entry reads **min 0, count 30**: PMTR, the only 30-valued
field on the page (`PMTR(30) WAVE(19) MULT(7) TRIG(8)`, octabam's
`PARAM_PAGES.md`, whose numbers the descriptor reproduces exactly). Entry 7 is
WAVE, count 19, and it bounds the next three bytes — so `+3..+5` are the three
waveforms.

Default is 0, which is PLAYBACK's `PTCH`. That is why three LFOs on a fresh
part all modulate pitch, and why locking `SPD`/`DEP` in a scene without touching
the destination does nothing interesting: a scene block covers page 1 only, and
PMTR is on page 2, so **the destination can only be set in the part**.


## Resetting a track ✅ (8 Sep 2026)

**Nothing in the firmware does this.** `'TRK DEFAULT'` (`0x400b3f4b`) is a slot
*type* name, sitting between `LOCK STATIC` and `LOCK FLEX`, not an action;
`'RESET TO DEFAULT'` belongs to the audio editor's trim page. The only reset
that exists is `FUN_40025848`, and it is the whole project: it clears all 0x88
flex and 0x81 static slots, resets every slot state, rewrites a 0x4c-byte block
of globals and repoints the bank.

### The defaults are in the descriptors ✅

Every page descriptor carries its six page-1 defaults at **`+0x5e`** and its
page-2 defaults at `+0x64`. That is not inferred: the FX chooser's apply
(`FUN_400526e4`) reads exactly those two when it installs a new effect.

Confirmed against live memory. The LFO descriptor `0x400d37f6` holds
`32 32 32 0 0 0` and the AMP `0x400d3988` holds `0 127 127 64 64 127` — byte for
byte what a booted project reads out of its page-1 block.

### Which descriptor ✅

| page | descriptor |
|---|---|
| PLAYBACK | `0x400d5f38[machine type]` — five entries, 0..4 |
| LFO | `0x400d37f6` |
| AMP | `0x400d3988` |
| FX1 | `0x400d5f58[FX1 id]` |
| FX2 | `0x400d5fdc[FX2 id]` |

The playback table cross-checks: its first four entries are exactly the
descriptors the parameter validator's min tables imply (`0x400d3086`,
`0x400d3218`, `0x400d33aa`, `0x400d353c`, each `desc+0x6a`).

### Where they go, relative to `part` ✅

`part = bank + part*0x18b2 + 0x8ed80`, the validator's own base.

| | |
|---|---|
| `+0x022 + track` | machine type |
| `+0x02a + track*30 + machine*6` | PLAYBACK page 1 |
| `+0x11a + track*24 + page*6` | LFO, AMP, FX1, FX2 page 1 |
| `+0x2f2 + track*30` | the three LFOs: PMTR ×3 then WAVE ×3 |
| `+0x662 + (scene*8 + track)*0x20` | that track's scene locks |

`machine*6` rather than octabam's `machine*7`: five machines × 6 fills the
30-byte per-track stride exactly, and the validator indexes the four descriptors
it clamps against at +0, +6, +0xc, +0x12.

🟡 **Page 2 of PLAYBACK, AMP, FX1 and FX2 is not located.** Only the LFO's is
(`+0x2f2`), so a reset restores the five page-1 rows, the LFO destinations and
the scene locks — which is what a user sees as the track's settings — and leaves
the page-2 fields of the other four alone.
