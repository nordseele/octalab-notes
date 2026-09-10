# Trigs: what they are in the data, and what already exists

OS 1.40C, MAIN OS sha256 `164f3122…`, load base `0x40000400`.

## The storage ✅ (octabam)

A track's trigs are **eight 64-bit big-endian step masks at an 8-byte stride**,
at the head of the track's record in the pattern: bit `step-1`, so byte 7 bit 0
is step 1. `refs/octabam/tools/ot_project.py` reads and writes them in bank
files, and `emu_frames.poke_trig` sets one in RAM through the bank pointer at
`0x46c82456`.

| mask | what |
|---|---|
| `0x00` | note trigs ✅ |
| `0x20` + `0x28` + `0x30` | a **recorder trig** — all three at once ✅ |
| `0x08` `0x10` `0x18` `0x38` | ⬜ not identified |
| `0x40` `0x48` | **not masks** — they read as a run of `0xaa` |

The recorder-trig line is hardware-settled (octabam, `docs/RTOS_FORK.md`,
6 Sep 2026): a byte-exact baseline, one `[TRIG]` press on the unit, and a diff
of the two bank files showed exactly those three bits.

## The families, named by the firmware itself ✅

The copy/clear menus name what the masks must be:

```
TRACK TRIGS · TRIG LOCKS · SWING TRACK · SLIDE TRACK · REC TRIGS
```

each with a MIDI twin (`CLEAR MIDI TRACK TRIGS`, `COPY MIDI SWING TRACK`, …).
Five families for eight masks, and `REC TRIGS` is already known to cost three of
them, which leaves the count plausible without proving the assignment.

## `CREATE RANDOM LOCKS` already exists ✅🟡

The firmware has both `CREATE RANDOM LOCKS` (`0x400b6c38`) and `CREATE LINEAR
LOCKS` (`0x400b6c24`), in the **slice editor's** list, beside `ADD SLICE HERE`
and `CREATE SLICE GRID`. So "randomise the locks on the trigs that are there"
is a stock feature, not something to write.

🟡 The handlers are read by adjacency, not by the layout equation our own popup
satisfies — this list's strings live in the general pool rather than after the
handler array, so the pairing below is inference:

| row | handler 🟡 |
|---|---|
| ADD SLICE HERE | `0x40071f00` |
| DELETE ALL SLICES | `0x40072058` |
| CREATE SLICE GRID | `0x40072dac` |
| CREATE LINEAR LOCKS | `0x40072cfc` |
| **CREATE RANDOM LOCKS** | **`0x40072004`** ❌ see below |
| CHANGE VIEW | `0x40072cb8` |

**Falsifier:** call `0x40072004` with a sample loaded and the locks do not
change, or something else does.

**It fired — hardware, 10 Sep 2026 (build OLB20).** Called from octalab's
popup, `0x40072004` opens a `DELETE SLICES ?` prompt, and no lock visibly
changes. Two readings, neither settled: the adjacency pairing is off by one
(the prompt matches `DELETE ALL SLICES`), or the function needs the slice
editor's own state. Treat the whole table above as unreliable until a handler
is tied to its row by a reference rather than by position.

⚠️ It is the *slice* editor's, so it randomises slice locks and reads the
editor's own state. Calling it from a menu that is not that editor is the same
bet the popup title and the first RANDOM FX both lost.

## RND SAMPLE LOCKS — the store, called from outside the picker ✅ (hardware, 10 Sep 2026)

octalab's first trig function gives every red trig (mask `0x00`) of the
current track, in the current pattern, a sample lock to a random slot among
those loaded in the track's pool (STATIC for machine type 0, FLEX for 1; any
other machine is left alone). It writes nothing itself. For each step it:

1. sets `0x460d174c` to the step's page (0, 16, 32, 48) and the 16-bit held-key
   mask `0x460d174a` to that one step,
2. calls the stock store `0x40040ee0(slot)`,

and afterwards puts both globals back. The store does the rest — bank byte,
second copy at `0x1001614e`, dirty flags, the "step has a lock" bitmaps
(`0x400339d8` → `0x46c7d48c`), screen refresh. On the unit the locks behave
exactly like hand-placed ones and survive a pattern change. Trigless trigs are
not touched: they do not retrigger the sample.


## Sample locks — the trail, and where it stops 🟡 (8 Sep 2026)

Both upstream repos mark "Trig types / p-locks / sample locks" ⬜ **not
decompiled**, so this is open ground. The gesture is `[TRIG]` held plus
`[UP]`/`[DOWN]` in REC mode, and following it gets most of the way.

**The picker.** `FUN_40024d88(track, current_slot, context)` opens the
slot-choosing popup: it reads the track's machine type to decide the range
(`0x81` slots for STATIC, `0x89` for FLEX), titles the window `LOCK STATIC` or
`LOCK FLEX` (`0x400b3f60` / `0x400b3f6c`), and hands its callback
`FUN_40024b84`. `FUN_40024854` is the row renderer — it is where `TRK DEFAULT`
(`0x400b3f4b`) is drawn for a step with no lock.

Two callers open it: `0x400435a0` and `0x4005892e`.

**The gesture handler** is the function at **`0x400434d8`**. Its prologue is the
familiar one — `a1 = *(0x46c82456)` (the bank blob), track from `0x100b14cc`,
part from `0x100b14cf`, machine type at `+0x8eda2` — and at `0x40043578` it
reads the lock itself:

```
moveb %a1@(0x78,%d0:l),%d1        | d0 = ((a0 + step) << 5) + d6 + d3
```

So **per-step records at a stride of 0x20**, with the sample lock a byte inside
one, based near the head of the blob at `+0x78`. The `<<5` and the bit-scan
above it (`neg`/`and` to isolate the held trig key, then `31 - n`) are the step
index being turned into a record offset.

✅ **Settled (10 Sep 2026).** `d3` = current pattern (`0x100b14d0`) × `0x8ed8`,
`d6` = track × `0x91a`, `a0` = the page's first step (`0x460d174c`), and the
held trig key comes from the 16-bit mask `0x460d174a`:

```
lock(p, t, s) = bank + p*0x8ed8 + t*0x91a + 0x78 + (s-1)*0x20
```

The gesture passes `0x40040ee0` as the picker's third argument, and the picker
calls it with the new slot when the selection changes. **That is the store**:
for each held step it writes the byte above and the same byte of a second copy
at `0x1001614e + p*0x8ed8 + t*0x91a + …`, raises the dirty flags, then
rebuilds the per-step "has a lock" bitmaps (`FUN_400339d8`) and refreshes the
screen. Value = slot 0..127 (FLEX also 128..135, the recorder buffers), `0xff`
= none. Three independent lines: the code (read and store), the real bank
files (next section), and the store run under emulation — one byte moves, at
`+0xb8` for step 3.

**The cheaper confirmation, either way**: baseline a project on the card, set a
sample lock on a known step and track, save, and diff the two `bank01.work`
files. That is how octabam settled the recorder trig, it needs no disassembly,
and the card mounts from the workshop.


## Four placeable trig types, one mask each ✅ (8 Sep 2026)

Measured on a project with one of every trig type on track 3 (`PROJECT 260908B`,
bank 1, pattern A01):

```
T3  mask 0x00  steps 1, 2, 14, 15, 16
T3  mask 0x08  steps 7, 8, 13
T3  mask 0x10  step 4
T3  mask 0x18  step 9
```

Four types, four masks, disjoint steps — and they are exactly the four the
sequencer ORs together for its "is there anything on this step" test
(`0x4009d382..9a`, octabam). Named by the person who placed them, from the trig
LED colours:

| mask | trig type | LED |
|---|---|---|
| `0x00` | **trig** | red |
| `0x08` | **trigless trig** | bright green |
| `0x10` | **trigless lock** 🟡 | dimmer green |
| `0x18` | **one-shot trig** | orange |

`0x00` was already settled independently — octabam's rig project reads its note
trigs there. 🟡 on `0x10` is the placer's own tentative reading, and the falsifier
is cheap: place one deliberately and see which mask moves.

This is new to all four upstream repositories: octamax and octabam both mark
"Trig types / p-locks / sample locks" ⬜ in their COVERAGE.

⚠️ **Reading the masks needs both IFF headers.** `trac_off` is
`0x16 + pattern*0x8eec + 8 + track*0x922 + 9` — the PTRN chunk's 8-byte header
*and* the TRAC's 9. Dropping them lands on the `PTRN`/`TRAC` tags themselves,
and the result still looks like plausible trig patterns rather than obvious
garbage: every pattern reads identical and track *n* shows *n−1*. octabam's
docstring warns about the +9 specifically; this cost a pass anyway.

## After the masks: per-step arrays with 0xff for "no lock" 🟡

The masks occupy `+0x00..+0x3f`. What follows, in the same TRAC record:

| | |
|---|---|
| `+0x40..+0x47` | `aa aa aa …` |
| `+0x48..+0x4f` | zeros |
| `+0x50..+0x57` | a short header — `10 02 00 ff 00 01 00 00` on this track |
| `+0x58` onward | long runs of **`0xff`**, with isolated real values |

✅ **They are not arrays: they are 64 step records of 32 bytes**, from `+0x59`
(`FUN_400339d8` walks exactly `+0x59 + s*0x20`, 32 bytes, to flag a step as
locked). Byte 31 of each is the sample lock, so the two "isolated values" were
sample locks all along: `+0x98` is step 2's (a red trig) and `+0x138` step 7's
(a trigless trig). Read this way, the test track carries locks on steps 2, 7,
8, 14, 15, 16 — every one a step with a trig; the earlier one-byte reading saw
none of them. 🟡 Bytes 0..30 are presumably the parameter locks, likely in the
scene numbering (PLAYBACK 0..5, LFO 6..11, AMP 12..17, FX1 18..23, FX2 24..29);
one card diff with a known p-lock settles it.
