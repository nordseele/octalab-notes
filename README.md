# octalab

Creative helper functions for the **Elektron Octatrack**, added to the stock
**OS 1.40C** — built and tested on an Octatrack MKI.

octalab works with **randomisation as a source of inspiration** — the way the
MIDI tools and generators of a DAW like Ableton Live hand you a variation, a
fill or a sequence to react to: a starting point you would not have chosen,
generated in one gesture, then yours to keep, edit or throw away. It adds **no
new effects and no new synthesis**; other projects already cover that ground.

This repository publishes no firmware, no build and no flashing procedure. It
describes what octalab does, and shares what was learned about the firmware on
the way.

---

## Part of octabam's remixer

octalab is built as a **module of [octabam](https://github.com/sambanks/octabam)'s
remixer**, the project that composes the community's Octatrack modifications
into one image built from the user's own 1.40C. The work to get there is done:
octalab is a ColdFire DRAM module — its code lives in octabam's memory reserve,
loaded at boot by octabam's loader — and it touches the OS in only a handful of
places, each declared to the remixer so that it can refuse a collision with
another module. It runs on an Octatrack MKI through octabam's loader (first
flash 11 Sep 2026, in daily use since), and it builds and boots beside
ems-octakit's Kits under octabam's emulator.

**The functions are not available to the public yet.** The module is not
published while the main development is under way — the functions and the way
they are played are still changing from one build to the next. It will be
offered through octabam's remixer when it settles.

## The octalab menu: double-tap [FUNCTION]

Everything octalab adds is in one list. **Tap [FUNCTION] twice, quickly**, from
almost any screen, and the list opens over whatever you were doing. It has one
row per subject — the sample pool, the LFOs, the effects, the scenes, the
trigs, the track — and each row shows one action:

- **LEVEL** (or the up/down arrows) moves between rows;
- **[LEFT] / [RIGHT]** choose the row's action — `<` and `>` show where they
  lead, and they stop at the ends rather than wrapping around;
- **[ENTER]**, or **pressing LEVEL**, runs it; **[EXIT]** closes the list.

- **An action that erases asks first** (YES/NO), always sits last on its row,
  and the row goes back to its first action afterwards.
- **[FUNCTION] still works as before.** A single press, or [FUNCTION] held with
  another key, does what it always did. The menu opens only on two presses in a
  row with no other key in between.
- **The list remembers the last row, and each row its last action.** A
  function you repeat is double-tap, then [ENTER].
- **Nothing underneath moves** while the list is open, and everything is back
  to normal once it closes.

The list holds the **one-gesture functions** — the ones that need no setting.
Functions that are played with an amount (how dense, how far from the current
value) will get a page of their own, where the result shows as you turn the
knob (see the roadmap).

Some functions have options. They are in **OCTALAB**, a fifth category of the
MAIN MENU (`[FUNCTION] + [MIXER]`), beside PROJECT, SYSTEM, CONTROL and MIDI:
a page of checkboxes. The options go back to their defaults at every power-on.

## UI workflow improvements

Shortcuts that make the stock workflow shorter, without a menu.

| gesture | what it does | |
|---|---|---|
| **[TRIG] + [BANK]** in grid recording | opens the **audio editor on the sample locked on that trig** — or, if the trig has no sample lock, on the sample the track's machine plays. In the stock OS [BANK] ignores the held trig and opens the bank selection; here it goes straight to the sample you are working on, and the trig stays as it was when you let go. [BANK] alone, or outside grid recording, works as before | ✅ |

## Functions

✅ = used on the unit and working, changes kept across a power cycle.

| function | what it does | |
|---|---|---|
| **pool** | | |
| `FILL POOL` | fills every empty STATIC sample slot with random audio found anywhere in the set's `AUDIO` folder | ✅ |
| `SHUFFLE POOL` | re-deals the loaded samples among the slots they occupy | ✅ |
| `CLEAR POOL` | empties every sample slot, after a YES/NO | ✅ |
| **LFO** | | |
| `RANDOM LFO` | randomises the current track's LFOs, including what they modulate and their waveforms | ✅ |
| **FX** | | |
| `RANDOM FX` | chooses random effects for the current track | ✅ |
| **scenes** | | |
| `GENERATE SCENES` | fills scenes 2 to 16 with random locks, the OCTALAB options choosing which pages; **scene 1 stays blank**, so a clean scene is always there. The new scenes play at once | ✅ |
| `CLEAR SCENES` | empties all sixteen scenes, after a YES/NO | ✅ |
| **trigs** | | |
| `RANDOM P-LOCKS` | gives every normal (red) trig of the current track a random parameter lock for each parameter ticked in the OCTALAB options (`PL …`), always inside that parameter's own range. The locks are ordinary ones | ✅ |
| `RANDOM SMP LOCKS` | gives every normal (red) trig of the current track a sample lock to a random sample from the pool | ✅ |
| `CLEAR P-LOCKS` | removes every parameter lock of the current track in the current pattern; trigs and sample locks stay. There is no stock operation for it | ✅ |
| `CLEAR SMP LOCKS` | removes every sample lock of the current track in the current pattern | ✅ |
| **track** | | |
| `INIT TRACK` | puts the current track back the way a new project starts it: every parameter page, FX1 on FILTER and FX2 on DELAY, its sample slot, its scene locks. The trigs stay — a clean sound under the same sequence | ✅ |

The trig functions start deliberately simple — every trig, the whole range —
so that what stays musical can be heard on the unit before it is refined.

Options page:
- `SC PITCH`, `SC START`, `SC LENGTH`, `SC RATE`, `SC RETRIG`, `SC LFO`,
  `SC LFO DEST`, `SC AMP`, `SC FX` — what `GENERATE SCENES` may touch (LFO,
  LFO DEST and FX on by default);
- `FILL OVERWR` — lets the pool fill replace samples that are already loaded;
- `PL PITCH`, `PL START`, `PL LENGTH`, `PL RATE`, `PL RETRIG`, `PL LFO`,
  `PL AMP`, `PL FX1`, `PL FX2` — which parameters `RANDOM P-LOCKS` locks
  (FX1 and FX2 on by default).

## Roadmap

- **More workflow shortcuts** in the spirit of [TRIG] + [BANK].
- **A sequencer edit page for generation.** Generating trigs — euclidean
  rhythms, pattern maps in the spirit of Mutable Instruments Grids, trigless
  locks spread over a share of the steps — is played with amounts, and wants
  to be *seen*: the trigs appearing as the encoder turns. It gets its own page,
  laid out like the audio editor, with the data encoders, where functions can
  be added one by one. (A first trigless-lock generator ran on the unit in the
  popup; it moves to that page.)
- **Controlled randomness** — variations around the current values rather
  than a fresh draw; ranges and density.
- **More one-gesture functions** for the LFO and effect rows.
- **Undo** for octalab's functions, randomised scenes included.

## State of the project

- **Machines:** built and tested on an Octatrack MKI running OS 1.40C. The
  MKII runs the same OS 1.40C image, so octalab should work there as well —
  not tested yet. No other OS version.
- **Working today:** everything in the functions table, on the unit, through
  octabam's loader.
- **No build is distributed**, now or later: an image contains Elektron's OS.
  When the module is published, it will be built by each user from their own
  stock OS through octabam's remixer.

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
