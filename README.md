# octalab

Creative helper functions for the **Elektron Octatrack**, added to the stock
**OS 1.40C** — built and tested on an Octatrack MKI.

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
almost any screen, and the list opens over whatever you were doing. It has one
row per subject — the sample pool, the scenes, the trigs, the track… — and
each row shows one action:

- **LEVEL** (or the up/down arrows) moves between rows;
- **[LEFT] / [RIGHT]** choose the row's action — `<` and `>` show where they
  lead, and they stop at the ends rather than wrapping around;
- **[ENTER]**, or **pressing LEVEL**, runs it; **[EXIT]** closes the list;
- a function that takes an amount shows it on its row, and **encoder A** sets it.

- **An action that erases asks first** (YES/NO), always sits last on its row,
  and the row goes back to its first action afterwards.
- **[FUNCTION] still works as before.** A single press, or [FUNCTION] held with
  another key, does what it always did. The menu opens only on two presses in a
  row with no other key in between.
- **The list remembers the last row, and each row its last action.** A
  function you repeat is double-tap, then [ENTER].
- **Nothing underneath moves** while the list is open: the other knobs stay
  locked, as in every Octatrack popup, and everything is back to normal once it
  closes.

Some functions have options. They are in **OCTALAB**, a fifth category of the
MAIN MENU (`[FUNCTION] + [MIXER]`), beside PROJECT, SYSTEM, CONTROL and MIDI:
a page of checkboxes. The options go back to their defaults at every power-on.

## Functions

Grouped by what they act on. How they are split into rows is still moving
(the next build gives LFO, FX and trigs rows of their own).
✅ = used on the unit and working.

| function | what it does | |
|---|---|---|
| **pool** | | |
| `FILL POOL` | fills every empty STATIC sample slot with random audio found anywhere in the set's `AUDIO` folder | ✅ |
| `SHUFFLE POOL` | re-deals the loaded samples among the slots they occupy | ✅ |
| `CLEAR POOL` | empties every sample slot, after a YES/NO | ✅ |
| **track** | | |
| `INIT TRACK` | puts the current track back the way a new project starts it: every parameter page, FX1 on FILTER and FX2 on DELAY, its sample slot, its scene locks. The trigs stay — a clean sound under the same sequence | ✅ |
| `RANDOM FX` | chooses random effects for the current track | ✅ |
| `RANDOM LFO` | randomises the current track's LFOs, including what they modulate | ✅ |
| **scenes** | | |
| `GENERATE SCENES` | fills scenes 2 to 16 with random locks, the OCTALAB options choosing which pages; **scene 1 stays blank**, so a clean scene is always there. A new scene takes effect once you select it | ✅ |
| `CLEAR SCENES` | empties all sixteen scenes | ✅ |
| **trigs** | | |
| `RANDOM SMP LOCKS` | gives every normal (red) trig of the current track, in the current pattern, a sample lock to a random sample from the pool. Trigless trigs are left alone; the locks are ordinary ones, kept across pattern changes and editable as usual | ✅ |
| `RANDOM P-LOCKS` | gives every normal (red) trig of the current track a random parameter lock for each parameter ticked in the OCTALAB options (`PL …`), always inside that parameter's own range. The locks are ordinary ones: CLEAR TRIG LOCKS and live recording treat them as usual | ✅ |

The trig functions are **in development**: they start deliberately simple —
every trig, the whole range — so that what stays musical and useful can be
heard on the unit before it is refined. Controlled randomness (variations
around the current value, ranges, density) comes next.

Options page:
- `SC PITCH`, `SC START`, `SC LENGTH`, `SC RATE`, `SC RETRIG`, `SC LFO`,
  `SC LFO DEST`, `SC AMP`, `SC FX` — what `GENERATE SCENES` may touch (LFO,
  LFO DEST and FX on by default);
- `FILL OVERWR` — lets the pool fill replace samples that are already loaded;
- `PL PITCH`, `PL START`, `PL LENGTH`, `PL RATE`, `PL RETRIG`, `PL LFO`,
  `PL AMP`, `PL FX1`, `PL FX2` — which parameters `RANDOM P-LOCKS` locks
  (FX1 and FX2 on by default).

This list grows as functions are added.

## Roadmap

- **More trig functions** — clearing a track's parameter locks, trigless
  locks (randomised, then generated), random trig conditions, and *controlled*
  randomness: variations around the current values rather than a fresh draw.
- **Generating trig sequences, perhaps whole patterns — not only at random.**
  Euclidean rhythms, or pattern maps in the spirit of Mutable Instruments
  Grids, so that what comes out is surprising but still makes musical sense.
  Reusing well-loved existing code would be the fun way to do it, if the
  firmware's memory and the licences allow.
- **A key combination on a held trig** — open the audio editor on the sample
  locked on that trig; randomise that one trig.
- **Undo** for octalab's functions, randomised scenes included.

## State of the project

- **Machines:** built and tested on an Octatrack MKI running OS 1.40C. The
  MKII runs the same OS 1.40C image, so octalab should work there as well —
  not tested yet, reports welcome. No other OS version.
- **Working today:** everything in the functions table.
- **Built to coexist — and now a module of octabam's remixer.** octalab builds
  as a ColdFire DRAM module of [octabam](https://github.com/sambanks/octabam)'s
  remixer: its code lives in octabam's memory reserve rather than in the
  firmware's small free areas, and it changes only three things in the OS (a
  hook on the [FUNCTION] press, the MAIN MENU's category count and category
  list). That build **runs on an Octatrack MKI** (11 Sep 2026). Combined with
  ems-octakit's Kits it builds and boots under octabam's emulator, with no
  collision; that image has not been flashed yet. The module itself is not
  published yet.
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
