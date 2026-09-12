# octalab — findings index

For other firmware projects and their agents. Each entry is a finding that the
upstream repositories still marked open when it was written, with a pointer to
the document that carries the evidence.

**The image.** Every address is in OS 1.40C, MAIN OS sha256 `164f3122…`,
1,112,560 bytes, load base `0x40000400` — VA = file offset + base. An address
without that identity means nothing.

**Confidence.** ✅ verified (hardware, or runtime observation) · 🟡 inferred,
with the experiment that would falsify it · ⚠️ a trap: a plausible wrong answer.
Each document marks its own claims; this index does not upgrade any of them.

**No Elektron binary is redistributed here**, in any form.

---

## The filesystem layer ✅

The 23-slot FS vtable at `0x46c823fa`, its three implementations and which one
the unit actually runs; and `0x40090a14`, a **recursive tree walker with a
per-entry callback** that the stock sample-load path already calls.

⚠️ The walker enumerates a whole directory *before* invoking the callback, so
the entry register holds the **last** entry, not the current one.

→ [`FS_LAYER.md`](FS_LAYER.md)

## The tail of the image is not free space ⚠️

Two runs at the tail, 15,153 B and 12,288 B, hold zeros in the image and have
**zero** static references pointing into them. Both are written at runtime.
Code placed in the first produced a `VEC:03` address error in the menu draw
loop on hardware.

The finding is the inference rule: *no static references* means nothing is
**known** to point at a region, not that nothing writes to it. Only a canary
run settles it. The shared 6 KB cave at `0x400d64da` is the one region with a
hardware record, and several projects claim parts of it.

→ [`CAVES.md`](CAVES.md)

## The MAIN MENU tables — a category with no new instruction ✅

A fifth top-level category beside PROJECT / SYSTEM / CONTROL / MIDI, built from
data: rows, a list descriptor and an icon. Runs on a MKI.

- A row whose **action is null is a section heading** the cursor skips.
- `[ENTER]` dispatches on the **page id at `+0x14`**, and falls through to the
  action at `+0x08` only when that id is 0.
- A list descriptor is **inert until initialised at boot**; one built by hand
  needs `+0x10`, the visible-row count, or its pane draws empty.
- The window descriptor at `+0x04` is the category's **icon**.

→ [`MENU.md`](MENU.md)

## Loading a sample into a slot ✅

`ot_static_slot_load` is **half** of it. Its one caller is the storage-job
dispatcher, which follows it with a post-load and two refreshes; without them a
slot displays its name and size, shows no BPM, and will neither preview nor
trig. A refused load stamps a per-slot status record rendered as
`ERROR: <reason> : <name>`, which clearing the name does not undo. `-0x10` is
*no extension at all* (a directory name), distinct from `-0x1e`, a wrong one.

→ [`SLOT_LOADING.md`](SLOT_LOADING.md)

## The current track, and the slot it plays ✅

The selected track is one byte; the slot it plays is an arithmetic step through
the active bank buffer, and the machine-type byte in the middle says whether
the track plays from the static pool at all. Also: where `RANDOMIZE PAGE`
lives, what it takes, and what is still unknown about calling it.

→ [`TRACK.md`](TRACK.md)

## What a sample slot is, on the card ✅

`PATH=` is stored **bare**; the length in bars is **computed from the file**
and must never be copied from another slot; half the state lives in
`markers.work`. Verified end to end — 32 slots written from the host, then
loaded, previewed and trigged on the unit.

⚠️ `^KEY=.*$` eats the `\r` of these CRLF files. Anchor on `[^\r\n]*`.

→ [`PROJECT_FILE.md`](PROJECT_FILE.md)

## Trigs: the step masks, and where a sample lock lives ✅

The four placeable trig types each own one 64-bit step mask. After the masks,
each track holds **64 step records of 32 bytes** from `TRAC + 0x59`; the
**sample lock is byte 31**: `bank + pattern*0x8ed8 + track*0x91a + 0x78 +
(step-1)*0x20`, `0xff` = none. The stock store is `0x40040ee0(slot)`, the LOCK
picker's callback, which takes its steps from `0x460d174a`/`0x460d174c` and
also writes a second copy at `0x1001614e`. Called from outside the picker it
works on hardware. (Also: *create random locks* is a stock slice-editor
function, but its handler paired by position was wrong ❌.)

→ [`TRIGS.md`](TRIGS.md)

## Current pattern, current part, machine type ✅

`[0x80000004]` (mirror `0x100b14d0`) is the current pattern and `0x100b14cf`
(mirror `0x80000003`) the current part — measured under emulation by the
firmware's own project loader, and consistent with how every reader in the
image uses them. Machine type 0 is STATIC, 1 FLEX: the LOCK picker titles
itself from it.

→ [`TRACK.md`](TRACK.md)

## octabam's DRAM loader boots on a MKI ✅

An image built by octabam's remixer (origin `9a49f21`) — its loader appended
at `0x4010fdf0`, reached from the boot site `0x4000050c`, depacking a ColdFire
DRAM unit into the platform reserve at the bottom of the audio page arena
(`0x40a955e0`, 10 MiB) — **ran on an Octatrack MKI** on 11 Sep 2026, with a
module hooked by one detour, one poke and one grown table, and the FX2 chooser
rebuilt with the fourteen stock effects (15 rows, the long list at
`0x400d7bbc`). octabam's own notes (10 Sep) list their ColdFire pipeline as
unflashed and every test as MKII: this is the MKI data point.

⚠️ On that image the audio pool's Flex list reads **FREE MEM 71.4 MB** — the
10 MiB reserve is gone from the pool — but the **MEMORY page still shows an
85.5 MB total** (visible when changing RESERVE LENGTH): its total does not
follow the rewritten arena geometry. The page count 14,602 (`0x0000390a`)
appears as a word at 18 places in stock and most stay untouched; which one the
page reads is not yet pinned.

## Input maps and the encoders ✅

A screen owns keys and knobs by registering an input map
(`0x40031494` / off `0x4003146c`), and maps are **layers**: every registration
rebuilds two RAM tables — keys `0x46c7d8de + code*0x18`, encoders
`0x46c7dede + enc*0x14` — and the last map registered wins. A key field of -1
lets the layer below through; an encoder listed with a null handler is
**swallowed**, which is how a popup locks the knobs over the page behind. An
encoder handler is `(encoder, delta)`; **A..F = 0..5, LEVEL = 6**, press codes
`0x38..0x3e`; arrows `0x33 0x20 0x34 0x21`, ENTER `0x31`, EXIT `0x32`. Run on a
MKI: a map of octalab's own on top of the stock list's drives LEVEL, the arrows
and encoder A, and the tables return to stock when it comes off.

→ [`INPUT.md`](INPUT.md)

## A part lives three times, and a reboot reloads the SRAM copy ✅

A part (`0x18b2` bytes) is held as the bank's working part
(`bank + 0x8ed80 + part*0x18b2`), the saved part (`bank + 0x9504a + …`) and
an **SRAM copy at `0x100a4ece + part*0x18b2`** — the one the unit comes back
with after a power cycle, synced to the card or not (patterns have theirs at
`0x1001614e`). The stock parameter writer `0x40054cd8` writes the bank and
the copy; a direct write to the bank alone is lost at the next boot (measured
on a MKI: randomised scenes gone, the scene selector kept). The stock setter
`0x40029a4c(src, part)` writes both, sets the part-edited bits (`bank +
0x95048`, `0x100b145e`) and the dirty flags, and re-applies the current part
to the engine with `0x40009094(bank, part)` — which also copies scenes A/B
(indexes at `part + 0x10/0x11`) into the live copy `0x80000ed4`: a scene
written this way plays at once. Given the working part as its own source it
commits in place. Run on a MKI (12 Sep 2026): scenes live at once and kept
across a reboot.

## Pattern length and scale 🟡 code read

As the scale page `0x40047d08` reads them: `pattern + 0x8e55` is the scale
mode (0 normal, 1 per track), `pattern + 0x8e53` the length and `+0x8e54`
the scale in normal mode; per track `TRAC + 0x50` the length and `+0x51` the
scale; `pattern + 0x8e50` the master length (short, −1 = INF). Pattern =
`bank + p*0x8ed8`.

## [TRIG]+[BANK] in grid recording, and the held-trig bookkeeping 🟡

Grid recording is `0x460d1736 != 0` (the trig keys' dispatcher `0x40060ce0`);
[BANK] ignores held trigs; stock [TRACK]+[BANK] opens the audio editor with
`0x4006de34(type, slot)` + `0x4006e160()`; the bookkeeping that keeps a held
trig in place after an edit is `FUN_4004f5f8`'s. Code read and emulator; the
hook built on it is not yet run on a unit.

→ [`INPUT.md`](INPUT.md) §9

→ [`TRIGS.md`](TRIGS.md)
