# The FAT layer and the recursive directory walker

Closes the gap that every Octatrack RE repository lists as open —
octamax's and octabam's `COVERAGE.md` both say *"ATA/CF storage ✅ … **Missing: FAT layer (vtable `_DAT_46c82xxx`)**"*,
and with it the blocker on any feature that has to look at what is on the card:
random sample-pool fill, pool shuffle, per-slot reroll, filtered import.

Verified against stock **OS 1.40C** MAIN OS (one image for both MKI and MKII;
the runtime observations here were made on a **MKI**),
sha256 `164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e`
(1,112,560 B, base `0x40000400`), by direct disassembly. Markers: ✅ read off the
disassembly · 🟡 inference, with the falsifier named.

---

## 1. The FS vtable is 23 slots at `0x46c823fa .. 0x46c82452` ✅

Three initialisers install three complete implementations of the same 23-slot table.
The one the running unit uses is **variant B** — independently confirmed: `NOTES.md`
observed at runtime that the load path's open is `0x4001b724 = *(0x46c823fa)`, and
variant B is the table that puts `0x4001b724` in that slot.

| initialiser | installs | what it is |
|---|---|---|
| `0x40014524` | `0x4001b8xx`–`0x4001c2xx` | variant A — 6 slots are `moveq #-1 ; rts` stubs |
| `0x40014636` | `0x40016f5c`–`0x4001b778` | **variant B — the live FAT implementation** |
| `0x40014750` | (third set) | variant C |

Variant B, slot by slot (address of the vtable word → the function it holds):

```
46c823fa 4001b724   46c82412 4001b778   46c8242a 4001b570   46c82442 40016f5c
46c823fe 40016f74   46c82416 40018444   46c8242e 4001b4f4   46c82446 4001abbc
46c82402 40018a84   46c8241a 40018060   46c82432 4001b3f4   46c8244a 40018174
46c82406 4001aff4   46c8241e 40018a0c   46c82436 40018788   46c8244e 4001aa34
46c8240a 4001b0ac   46c82422 40019900   46c8243a 4001a0e8   46c82452 40018314
46c8240e 4001b478   46c82426 40018e40   46c8243e 4001858c
```

Slots named so far:

| slot | signature | evidence |
|---|---|---|
| `0x46c8242a` | `open(path, mode) -> fd` (`d0 < 0` = error) | the buffered open `FUN_40016864` calls it at `0x4001688e` with the caller's path and mode string ✅ |
| `0x46c823fa` | the load path's open / existence probe | `NOTES.md` runtime observation + this table ✅ |
| `0x46c8241e` | file size | ems-octakit reads this slot as `SizeFunction` (`runtime/persistence.c`) ✅ |
| `0x46c82442` `0x46c8244e` `0x46c8241a` `0x46c8243a` | the four the tree walker drives — see §2 | ✅ |

`0x46c82456` is **not** part of the table: it is the bank pointer (1224 refs;
ems-octakit calls it `GK_STOCK_BANK_POINTER`).

**Side effect worth collecting:** `DESIGN_BANKPAGE.md` deferred the sibling-existence
check because *"that vtable is uninitialized in the static image → not emulator-testable"*.
It is testable now — seed the emulator with variant B's 23 words and the FS calls resolve.

---

## 2. `0x40090a14` — a recursive directory tree walker, with a callback ✅

```c
int walk(const char *path, int *dirs, int *files, int mode, void (*progress)(void));
```

Arguments read at `0x40090a1c` (`a5`=dirs, `a4`=files, `d6`=mode, `a6`=progress; the
path is arg 0). Confirmed against three call sites, all pushing five arguments and
popping `0x14`.

What it does, from the disassembly:

- Keeps **two explicit component stacks** in the globals `0x46070e44` and `0x46038e40`
  (helpers: `0x40021884` init · `0x4002188c` push · `0x40021904` pop · `0x40021974`
  empty?; 0x1c-byte records, depth cap `0x1ffe`). That is the recursion — it descends
  the whole tree, it is not one directory deep.
- Skips `'.'` (`0x400b70a4`) and `'..'` (`0x400b401d`) ✅.
- Counts as it goes: `(*dirs)++` per directory, `(*files)++` per file — the pairing is
  fixed by the caller at `0x4006c702`, which prints them through
  `'%d DIRS AND %d FILES'` (`0x400b675c`) ✅.
- Calls `progress()` once per entry when the pointer is non-null (`jsr (a6)` at
  `0x40090b26` and `0x40090b84`) ✅. No arguments — the current path is in the walker's
  stacks, not passed.
- `mode` gates the destructive half: with `mode == 0` it additionally calls slot
  `0x46c8241a` per file and `0x46c8243a` per directory; with **`mode == 1` it only
  walks and counts** ✅. 🟡 Those two slots are `unlink`/`rmdir` — inferred from the
  caller being the DELETE DIRECTORY confirmation and from ordering (files first, then
  the directory). **Falsifier:** call `walk` with `mode = 0` on a scratch folder in the
  emulator and see whether the folder survives. Do not run that on a card you care
  about until it has.

### Who already calls it ✅

| caller | call |
|---|---|
| `0x4006be48` | file manager |
| `0x4006c704` | `walk(path, &d, &f, 1, 0)` — the "%d DIRS AND %d FILES" confirmation |
| `0x40084a34` | `walk(path, &d, &f, 1, 0)` — **inside the sample-load path** |
| `0x40084a6a` | `walk(path, &d, &f, 0, cb)` — same function, acting, with a callback |
| `0x40084ada` | ditto |

The sample loader already walks directories. A pool feature is not introducing a new
capability to the firmware; it is re-aiming one it uses.

---

## 3. What this unlocks — random pool fill

The chain is now complete end to end, with no unknown left:

```
walk(dir, &nd, &nf, 1, count_cb)          pass 1: how many candidates          §2
walk(dir, &nd, &nf, 1, pick_cb)           pass 2: reservoir-sample N of them   §2
  -> path of each pick, read from the walker's component stacks (0x46070e44)
resetslot_0x40099148(slot)                initialise the slot                  NOTES
write path at SETTINGS + slot*0x448 + 0   0x100d5b30 static / 0x100b14f0 flex  NOTES
FUN_40093980(slot, 1)                     load it                              NOTES
```

Notes for the build:

- **STATIC, not FLEX.** Static slots stream from the card, so filling 256 of them costs
  no pool RAM; flex loads into the shared 85 MB and a random fill would blow it.
- **Free-slot predicate** is the AED's: `STATE@8 == 0` means the slot has content
  (`0x4006db38`).
- **A card written by a Mac is half junk.** macOS leaves an AppleDouble sidecar
  (`._Name.wav`) beside every file it touches on FAT: 1,330 of them against 1,361 real
  audio files on the card measured here. They carry an audio extension and are not
  audio, so any enumeration — host tool or firmware walker — has to skip a leading
  `._` or half of what it offers the user is noise.
- **Paths** are stored relative — `'../AUDIO/name.wav'` — and the loader **does**
  resolve a multi-level one ✅. No experiment was needed in the end: three of the
  author's own working projects, written by the unit itself, carry a loaded STATIC slot
  reading `PATH=../AUDIO/Breaks & Drum Loops Collection VOL-1/Brent Dowe - Put Your
  Hand In The Hand.wav` — nested, spaces, ampersand, 60-character name. So a pool fill
  may draw from the whole tree under `AUDIO/`, not just its top level.
- **`PATH=` is stored bare — no quotes, no escaping** ✅, exactly as printed above.
  Beware of `NOTES.md`, which renders paths as `'../AUDIO/name.wav'`: those quotes are
  that document's prose convention, not bytes in the file. Writing them into a record
  makes every slot come back `FILE NOT FOUND` on a RELOAD — measured, on hardware, at
  the cost of one run. Because nothing is quoted, an apostrophe in a filename needs no
  escaping.
- **Cave.** Not the contested `0x400d6xxx` one — octalab's code goes in `LAB_A`
  (`0x401087e4`, 14,364 B, zero static references), see `docs/CAVES.md`.

---

## 4. Reproducing this

```sh
python3 tools/extract_os.py <your OCTATRACK_OS1.40C.syx> out/mainos.bin
# VA 0x40000400 == file offset 0, so the addresses above read directly:
m68k-elf-objdump -D -b binary -m m68k:5407 --adjust-vma=0x40000400 out/mainos.bin \
    | sed -n '/^40090a14/,/^40090b94/p'        # the walker
m68k-elf-objdump -D -b binary -m m68k:5407 --adjust-vma=0x40000400 out/mainos.bin \
    | sed -n '/^40014636/,/^40014756/p'        # the live vtable initialiser
```

`tools/extract_os.py` is a Python port of the ems-octakit decoder (SysEx 7-bit unpack →
ELEK container → aPLib depack) and reproduces the published sha256 exactly, so the
addresses above are checkable from a clean clone plus your own `.syx`.

The listings behind this document were produced with capstone, which decodes
ColdFire-only opcodes (`mvz`/`mvs`, EMAC) wrongly — harmless for the FS and UI code
here, **not** for anything in the audio hot path. Use `m68k-elf-objdump -m m68k:5407`
for anything you intend to trust twice.
