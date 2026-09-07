# Cave ledger

Where octalab's code lives inside the OS image, who owns which bytes, and the
test a region has to pass before anything ships in it.

Every address here is in OS 1.40C, MAIN OS sha256 `164f3122…`, load base `0x40000400` — VA = file
offset + base.

## The free space in OS 1.40C ✅

Runs of zero in the loaded image, with a count of every 32-bit value anywhere in
the image that points into them:

| range | size | static refs | who uses it |
|---|---:|---:|---|
| `0x401087e4 .. 0x4010c315` | 15,153 B | **0** | ~~octalab~~ — **live at runtime, unusable** |
| `0x4010cdd1 .. 0x4010fdf0` | 12,319 B | **0** | ~~octalab~~ — same verdict |
| `0x400d64da .. 0x400d7c3c` | 5,986 B | 2 | octamax (all features), octabam (`0x400d6b00`), **octalab `0x400d64e0..0x400d6671`** — contested, nearly full |
| `0x400d24d0 .. 0x400d2ce0` | 2,064 B | 1 | **octabam** — `modules/menushortcut` pins its 300-byte cave here |
| `0x4010c350 .. 0x4010c57e` | 558 B | 2 | unclaimed |

⚠️ The two tail runs looked like the prize and are not usable — see the verdict
below. The table is kept because the *method* stands: this is what the static
scan says, and the static scan is only half the test.

Two conclusions:

1. **The classic cave is not the only one, and it is the worst one.** It is
   4.6× smaller than TAIL-A, it already carries every octamax feature, and
   octabam plants its list cave at `0x400d6b00` — so an image combining those
   two projects is already impossible. octalab does not compete for it.
2. **`0x4010fdf0` is the end of the image**, which is where ems-octakit's
   bootstrap lands (`BOOTSTRAP_LOAD` in its `runtime/link.ld`). TAIL-B runs up
   to that address, so keeping it as reserve rather than filling it leaves the
   append model available later without a migration.

## The menu model, corroborated independently ✅

octabam's `tools/verify_menushortcut.py` reads a menu the same way this project
does, from its own reverse engineering:

```python
CONTROL_DESC, CONTROL_ROWS, ROW_LEN, STOCK_N = 0x400cbd54, 0x400cc5a8, 24, 6
count, rows = u32(img, CONTROL_DESC), u32(img, CONTROL_DESC + 0x18)
```

Count at +0x00, rows pointer at +0x18, 24-byte records — and on the same
descriptor this project's own survey found for AUDIO · INPUT · SEQUENCER ·
MIDI SEQUENCER. Two independent readings, identical numbers.

That matters for a specific reason: **MENUPROBE's crash was the cave and
nothing else.** The record layout it wrote was right.

It also names a technique worth copying before the next flash: that script
*boots the patched image and walks the menu out of RAM with the firmware's own
layout*. It is exactly the gate that would have caught MENUPROBE.

## octalab's claim

| block | range | budget | contents |
|---|---|---:|---|
| `LAB_MENU` | `0x400d64e0 .. 0x400d6671` | 402 B | **in use, hardware-confirmed 7 Sep 2026** — `modules/octalabmenu`: five root rows, a window descriptor, two icon planes, our list descriptor, two rows and their labels |
| ~~`LAB_A`~~ | `0x401087e4 .. 0x4010bfff` | — | **withdrawn**, live at runtime |
| ~~`LAB_SCRATCH`~~ | `0x4010c000 .. 0x4010c314` | — | **withdrawn**, same region |
| ~~`LAB_B`~~ | `0x4010cdd1 .. 0x4010fdf0` | — | **withdrawn**, same verdict |

`LAB_MENU` sits inside the contested classic cave rather than in a private
region, because that region is the only one with a hardware record: octamax has
shipped from it for months, and the two tail runs that looked far better turned
out to be live. Contested and proven beats spacious and untested. It is 402
bytes of pure data — no instruction — so the collision surface is small, but it
still belongs in the ledger: an image combining octalab with octamax needs both
sub-ranges checked, which is what a ledger is for.

Every module declares its sub-range in its own `manifest` and the build refuses
to place two modules that overlap (the idea is lifted from octabam's ledger,
`tools/remix/ledger.py` — it catches silently overlapping machine code, which is
the one class of bug that produces a unit that boots and then misbehaves).

## Before anything ships in a new region — the canary test 🟡

No static reference is necessary but **not sufficient**: a pointer computed at
runtime leaves no immediate in the image. octamax paid for that lesson twice —
an early home for the dual-256 SET-B tables sat in the heap tail and was
overwritten at runtime, and its probe counters were silently clobbered by a
region the sidecar restored on every load.

So a region is accepted only after this, on hardware:

1. Fill the candidate range with a recognisable pattern (`0xA5` bytes, or a
   32-bit counter so a partial overwrite is visible).
2. Flash, then *use the unit normally* for a full session — load a project,
   record, change patterns, save, power cycle, load again.
3. Dump the range back and compare byte for byte.

Survives untouched → the region is real, record the run in this file with the
date and what was exercised. Comes back modified → it is live data, note what
changed and drop the claim.

**Status: TAIL-A is NOT usable — answered on hardware, the expensive way.**

A build put a 405-byte menu table at `0x401087e4` and repointed a descriptor at
it. On the unit, opening that menu raised `VEC:03` (address error) at
`0x40064abc`, a `jsr (a0)` where `a0` is read from the table at record `+0x0C`.
Every record written there had `0` in that field, and a null is explicitly
skipped two instructions earlier — so the value read back was not the value
written. The region is live at runtime.

Zero static references was necessary and not sufficient, exactly as this
document said before the flash. TAIL-B is the same kind of space and inherits
the same verdict until a canary says otherwise. **Neither is usable.**

The cost was not the failed feature: the patched menu was the screen that
contains OS UPGRADE, so the unit could only be recovered over MIDI — about an
hour of SysEx.
