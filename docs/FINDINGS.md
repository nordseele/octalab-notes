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

→ [`TRIGS.md`](TRIGS.md)
