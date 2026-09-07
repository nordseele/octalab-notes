# octalab — findings

Reverse-engineering notes on the **Elektron Octatrack MKI, OS 1.40C**. This
repository publishes *findings only*: what was read out of the firmware and
verified, in a form another project can check. It is not a tutorial, it carries
no build or flashing procedure, and it ships no code.

**The goal of octalab** is to add *creative* functions to the stock firmware:
randomness and constrained chance, and the instant capture of a musical idea
before it evaporates — the machine handing you a starting point you would not
have chosen, in the spirit of Oblique Strategies. **No new effects and no new
synthesis**: three other projects already cover that ground. That is why the
findings below are about the menu, the filesystem and the sample pool rather
than the audio path.

An independent workshop, not a fork. It stands beside
[octamax](https://github.com/mxldyn/octamax),
[octabam](https://github.com/sambanks/octabam),
[ems-octakit](https://github.com/emuyia/ems-octakit) and
[octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt), reads all four as
reference, and publishes here only what those four still mark open.

**The image.** Every address below is in OS 1.40C, MAIN OS
sha256 `164f3122…`, 1,112,560 bytes, load base `0x40000400` — VA = file offset
+ base. An address without that identity means nothing.

**No Elektron binary is redistributed here**, in any form.
---

## The filesystem layer ✅

The gap every Octatrack RE project lists as open. The 23-slot FS vtable at
`0x46c823fa`, its three implementations and which one the unit actually runs;
and `0x40090a14`, a **recursive tree walker with a per-entry callback** that the
stock sample-load path already calls.

Trap: the walker enumerates a whole directory *before* invoking the callback, so
the entry register holds the **last** entry, not the current one.

→ [`docs/FS_LAYER.md`](docs/FS_LAYER.md)

## The tail of the image is not free space ⚠️

Two runs at the tail, 15,153 B and 12,288 B, hold zeros in the image and have
**zero** static references pointing into them. Both are written at runtime.
Code placed in the first produced a `VEC:03` address error in the menu draw
loop on hardware.

The finding is the inference rule, not the addresses: *no static references*
means nothing is **known** to point at a region, not that nothing writes to it.
Only a canary run — fill, exercise the unit, read back — settles it. The shared
6 KB cave at `0x400d64da` is the one proven region, and octabam's list cave sits
**inside** the range octamax is filling, so those two images already cannot be
combined.

→ [`docs/CAVES.md`](docs/CAVES.md)

## The MAIN MENU tables — adding a category with no new instruction ✅

A fifth top-level category beside PROJECT / SYSTEM / CONTROL / MIDI, built
entirely from data: rows, a list descriptor and an icon. Runs on a MKI; the
stock tree opens, draws, scrolls and closes it.

Three rules, each closing something still marked open upstream, each paid for
by a build that failed on the unit:

- A row whose **action is null is a section heading** the cursor skips.
- `[ENTER]` dispatches on the **page id at `+0x14`**, and only falls through to
  the action at `+0x08` when that id is 0 — so a row inside a pane cannot
  descend, whatever its child pointer says.
- A list descriptor is **inert until initialised at boot**; one built by hand
  needs `+0x10`, the visible-row count, or its pane draws empty.

The window descriptor at `+0x04` turns out to be the category's **icon**
(octabam's MAINMENU.md marks `+0x08..+0x14` uninterpreted and its section 8
lists this one undecoded).

→ [`docs/MENU.md`](docs/MENU.md)

## What a sample slot actually is ✅

Three things must be right at once and each is silent when wrong: `PATH=` is
stored **bare**, with no quotes; the length in bars is **computed from the
file** and must never be copied from another slot; and half the state lives in
`markers.work`, a file named in other projects but whose layout is documented
nowhere. Verified end to end — 32 slots written from the host, then loaded,
previewed and trigged on the unit.

Parsing trap: `^KEY=.*$` eats the `\r` of these CRLF files. Anchor on
`[^\r\n]*`.

→ [`docs/PROJECT_FILE.md`](docs/PROJECT_FILE.md)

---

**MIT licensed.** These findings came from reading other people's work; nothing
here is fenced off.

*Independent, unofficial, educational. Not endorsed by, supported by, or
affiliated with Elektron. "Elektron" and "Octatrack" are trademarks of Elektron
Music Machines MAV AB, used here only to identify the hardware under study.*
