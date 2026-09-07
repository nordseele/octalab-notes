# `project.work` — what a STATIC sample record actually contains

Everything here was read off files the Octatrack wrote itself, and every rule
was checked by making the unit write a record for a file of known length and
comparing it to one produced by hand.

**Measured on an Octatrack MKI running OS 1.40C** (`VERSION=19`,
`OS_VERSION=R0178     1.40C`). The two models share one OS image — the same
`.syx` flashes both, and the updater's only model gate refuses versions below
`0156` on a MKI — so everything here about *files* should hold on a MKII as
well. What is **not** shared is the panel: key bindings differ between the
models (ems-octakit binds LOAD KIT to `PART` on MKII and to `FUNC`+`MIDI` on
MKI), so any finding about keys or shortcuts is model-specific and is not
claimed here. Markers: ✅
verified against the unit's own output · 🟡 inferred, falsifier named.

**Confirmed end to end on hardware.** 32 STATIC slots written entirely from the
host — paths, lengths, marker records, checksums — load, preview and trig on
the unit, indistinguishable from slots loaded through its own browser. Three
things had to be right at once, and each one wrong was silent in a different
way: a quoted path (FILE NOT FOUND), a cloned `TRIM_BARSx100` (300 BPM, inert),
and a missing marker record (30 BPM, inert).

## The record ✅

```
[SAMPLE]
TYPE=STATIC
SLOT=040
PATH=../AUDIO/Strictly_Drums_Volume_2/C11.wav
TRIM_BARSx100=3200
TSMODE=2
LOOPMODE=0
GAIN=48
TRIGQUANTIZATION=-1
[/SAMPLE]
```

Nine lines, CRLF, and **that is the whole record** — a slot loaded by hand
through the unit's own file browser produces exactly these fields, no more.
The file is `[SECTION] KEY=VALUE` text with `[META]`, `[SETTINGS]`, `[STATES]`
and one `[SAMPLE]` block per loaded slot.

### `PATH=` is bare ✅

No quotes, no escaping, spaces and `&` and apostrophes straight through.
Relative to the project directory, and **multi-level paths resolve**:
`../AUDIO/some folder/deeper/name.wav` is what the unit itself writes.

Beware of octamax's `NOTES.md`, which renders paths as `'../AUDIO/name.wav'`:
those quotes are that document's prose convention. Writing them into a record
makes every slot read `FILE NOT FOUND` on a RELOAD.

### `TRIM_BARSx100=` is computed from the file, and must not be copied ✅

The length of the sample **in bars at the project tempo, rounded to the nearest
power of two, capped at 32 bars**, times 100:

```
bars = 2 ** round(log2(seconds × TEMPOx24 / 24 / 240))     # 4 beats/bar, 60 s/min
TRIM_BARSx100 = 100 × min(32, bars)
```

Checked against five records the unit wrote, across two projects and two
tempos:

| file | duration | project tempo | bars at tempo | 2^round | unit wrote |
|---|---:|---:|---:|---:|---:|
| `C11.wav` | 92.504 s | 102.54 | 39.523 | 32 | **3200** |
| `Spooky Tooth - Wating…` | 35.561 s | 102.54 | 15.194 | 16 | **1600** |
| `System Audio   2026…` | 150.475 s | 102.54 | 64.292 | 64 → cap | **3200** |
| `Brent Dowe - Put Your…` | 11.568 s | 102.54 | 4.943 | 4 | **400** |
| `Afrique - Kissing My Love` | 17.073 s | 94.00 | 6.687 | 8 | **800** |

Then confirmed the other way round: the same three files were written into two
slots each — one by the unit, one by `poolfill_host.py` computing the value —
and the pairs agree exactly (2↔41, 33↔40, 23↔42).

🟡 **The cap rests on one point** (`System Audio`, 64.29 bars → 32). **Falsifier:**
load a file longer than ~64 bars at the project tempo and see whether the unit
writes 3200 or 6400.

🟡 **The floor is a guess.** No sample short enough has been through the unit;
below a quarter bar the ×100 encoding stops being an integer. **Falsifier:**
load a one-shot of a few hundred milliseconds and read what it writes.

**Why this field matters more than it looks.** It is not decoration: it is how
the unit knows the sample's own tempo. Clone it from another slot and the unit
computes a nonsense tempo from a length that does not match the audio — 32
files of every length declared as 4 bars all read **300 BPM**, the ceiling, and
the slots would neither trig nor preview. The files loaded fine; nothing in the
project file looked wrong. Only the unit could say so.

## A slot lives in TWO files — `markers.work` is the other half ✅

`project.work` names the sample. **`markers.work` carries its length**, and a
slot that exists only in the first is inert: no error, no missing file, just a
slot that will not trig, will not preview, and reads 30 BPM.

```
16-byte header       "FORM" 00 00 00 00 "DPS1SAMP"
264 records x 784    136 flex (128 + 8 recorders), then 128 static
8-byte trailer       last 2 bytes = sum(body) & 0xFFFF, body = the 264 records

STATIC slot n   ->   offset 16 + (136 + n - 1) * 784
record + 10     ->   the sample's length in FRAMES, 4 bytes big-endian
```

Verified three ways. The offsets predict every populated record in a real file
(slot 1 at `0x1a090`, slot 42 at `0x21e20`). The value at `+10` is exactly the
frame count of the WAV for three samples the unit loaded itself — 4,079,440 /
1,568,236 / 6,635,946, matching their headers to the frame. And the trailer's
checksum recomputes to the stored `0x458b` on an untouched file.

**What the unit does with a slot that has no marker record:** it falls back to
**64 frames** — about 1.5 ms — writes `TRIM_BARSx100=0` back into
`project.work` on the next save, and displays the minimum tempo. That fallback
is what a hand-written pool looks like from the inside, and it is silent.

`project.strd` and `markers.strd` are the saved copies of those two files. A
RELOAD reads them, so both pairs move together.

`markers.work` is named in octabam's emulator (`LOAD PROJECT` reads it) and in
passing in octamax's dual-256 work, but its layout is documented nowhere. This
is new.

## A nested `PATH=` works for STATIC — contrary evidence, and a likely reconciliation

octabam's `tools/ot_project.py` carries a note measured 7 Sep 2026:

> the STATIC slot byte is 0-based like the FLEX one […]; a STATIC `[SAMPLE]`
> entry's PATH is a **BARE filename** (`"PLUCK.wav"`), and the
> `../AUDIO/<dir>/<file>` form — which the FLEX entries of Sam's projects use —
> **loads as an EMPTY slot for STATIC**.

On OS 1.40C that is not what this unit does, on two independent counts:

1. **The machine writes nested paths itself.** Three of this card's projects
   have a loaded STATIC slot reading
   `PATH=../AUDIO/Breaks & Drum Loops Collection VOL-1/Brent Dowe - Put Your Hand In The Hand.wav`
   — written by the Octatrack, not by a tool — and it loads and plays.
2. **32 slots written entirely from the host, all nested, all work.** They load,
   preview (FUNC+ENTER in the pool) and trig.

**A reconciliation that fits both observations.** "Loads as an EMPTY slot" is
exactly the symptom this document describes above for a slot with **no
`markers.work` record**: no error, no missing file, a slot that is simply inert.
It is reached by writing a `[SAMPLE]` entry and nothing else — which is what a
tool that touches only `project.work` produces, whatever path form it uses. So
the observation may be real and its cause elsewhere.

**Falsifier, cheap for anyone with a unit:** take a STATIC slot the machine
itself loaded through its browser from a sub-folder, and read its `PATH=`. If it
is nested, the bare-filename rule cannot be general. Then write the same nested
path by hand *with* a marker record and see whether it plays.

🟡 Version is the remaining variable: the note may have been measured on OS
1.40B, everything here is 1.40C.

## The unit owns these files while a project is loaded ⚠️

External edits **are** read — that is settled, three times over: a bad path
produced FILE NOT FOUND, fixing it made the files load, and a changed
`TRIM_BARSx100` changed what the display did. The unit is not ignoring the
file.

But it also **writes it back**. The Octatrack auto-saves the loaded project
from RAM more or less continuously (the owner of this card never presses SAVE
PROJECT), so an edit to the *currently loaded* project is overwritten from a
RAM state that does not contain it. That is how `TRIM_BARSx100` came back as
`0`: the values were read, the length was not in RAM, and the recomputed zero
was written over them.

**Do not date this by mtime.** The unit stamps files with its own RTC, which
runs behind wall clock (octamax's notes measured about five hours on a sidecar
file). A file the unit rewrote *after* an external edit can carry an *earlier*
timestamp, which reads exactly like "my write never landed". Compare content,
not times.

So: switch the unit to another project, or power it off, before editing the
files of a project it is holding. It is not a locking problem; it is
ownership.

## Method, since it is the transferable part

Both bugs above were found the same way, and neither was findable by reasoning:

1. Have the unit write a record for a file whose properties you know.
2. Write your own record for **the same file**.
3. Diff them byte for byte.

Two rounds of that, at one RELOAD each, settled a format that static analysis
had got wrong twice. Ask the machine; do not ask a note about the machine.
