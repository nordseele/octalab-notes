# octalab

Creative helper functions for the **Elektron Octatrack MKI**, added to the
stock **OS 1.40C**.

octalab is about randomness, constrained chance and quick gestures: the machine
handing you a starting point you would not have chosen, in the spirit of
Oblique Strategies. It adds **no new effects and no new synthesis**; other
projects already cover that ground.

This repository publishes no firmware, no build and no flashing procedure. It
describes what octalab does, and shares what was learned about the firmware on
the way.

---

## The octalab menu: double-tap [FUNCTION]

Everything octalab adds is in one list. **Tap [FUNCTION] twice, quickly**, from
almost any screen, and the list opens over whatever you were doing. Pick a row
with the arrows, press **[ENTER]**; **[EXIT]** closes the list.

- **[FUNCTION] still works as before.** A single press, or [FUNCTION] held with
  another key, does what it always did. The menu opens only on two presses in a
  row with no other key in between.
- **The list remembers the last row you used.** A function you repeat is
  double-tap, then [ENTER].

Some functions have options. They are in **OCTALAB**, a fifth category of the
MAIN MENU (`[FUNCTION] + [MIXER]`), beside PROJECT, SYSTEM, CONTROL and MIDI:
a page of checkboxes. The options go back to their defaults at every power-on.

## Functions

✅ used on the unit and working · ⚠️ does not do what it should yet

| row | what it does | |
|---|---|---|
| `FILL POOL` | fills every empty STATIC sample slot with random audio found anywhere in the set's `AUDIO` folder | ✅ |
| `APPEND 8 FILES` | the same, for the next eight empty slots only | ✅ |
| `SHUFFLE POOL` | re-deals the loaded samples among the slots they occupy | ✅ |
| `REROLL TRACK` | replaces the sample the current track plays (static machines only) | ✅ |
| `RESET TRACK` | puts the current track's parameters back to their defaults (the choice of effects is kept, for now) | ✅ |
| `RANDOM FX` | chooses random effects for the current track | ✅ |
| `RANDOM LFO` | randomises the current track's LFOs, including what they modulate | ✅ |
| `RND SLICE LK` | meant to be the slice editor's *create random locks*; today it opens a `DELETE SLICES ?` prompt instead — **answer NO**. Being reworked | ⚠️ |
| `CREATE 16 SCENES` | fills all sixteen scenes with random locks; the OCTALAB options choose which pages. A new scene takes effect once you select it | ✅ |
| `CLEAR SCENES` | empties all sixteen scenes | ✅ |
| `CLEAR SLOTS` | empties every sample slot — there is no confirmation | ✅ |

Options page: `SC PITCH`, `SC START`, `SC LENGTH`, `SC RATE`, `SC RETRIG`,
`SC LFO`, `SC LFO DEST`, `SC AMP`, `SC FX` (what `CREATE 16 SCENES` may touch;
LFO, LFO DEST and FX are on by default) and `FILL OVERWR` (lets the pool fill
replace samples that are already loaded).

This list grows as functions are added.

## State of the project

- **One machine, one OS:** Octatrack MKI, OS 1.40C. Nothing else is supported.
- **Working today:** the menu, the options page, the pool functions, the
  track functions and the scene functions. `RND SLICE LK` is being reworked.
- **In progress:** randomising the sequencer itself — random sample locks on
  trigs, and random trigless layers.
- **Not combinable** with octamax or the standalone 1.40MIDISC in one image:
  all three use the same small free area of the firmware.
- **No build is distributed**, now or later: an image contains Elektron's OS.

## For other firmware projects

The reverse-engineering findings behind these functions — addresses, data
layouts, the traps that cost a failed build, each with its confidence level
and the image it was read from — are in **[`docs/FINDINGS.md`](docs/FINDINGS.md)**.

octalab is an independent workshop, not a fork. It reads
[octamax](https://github.com/mxldyn/octamax),
[octabam](https://github.com/sambanks/octabam),
[ems-octakit](https://github.com/emuyia/ems-octakit) and
[octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt) as reference, and
publishes only what they still mark open.

---

**MIT licensed.** These findings came from reading other people's work; nothing
here is fenced off.

*Independent, unofficial, educational. Not endorsed by, supported by, or
affiliated with Elektron. "Elektron" and "Octatrack" are trademarks of Elektron
Music Machines MAV AB, used here only to identify the hardware under study.*
