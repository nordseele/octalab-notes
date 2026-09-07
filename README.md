# octalab

**Helpers and creative-inspiration functions for the Elektron Octatrack, and
the tools to find room for them.** The reference points are Oblique
Strategies and randomness: the machine handing you a starting point you would
not have chosen. An independent workshop, not a fork: it stands beside
[octamax](https://github.com/mxldyn/octamax), [octabam](https://github.com/sambanks/octabam),
[ems-octakit](https://github.com/emuyia/ems-octakit) and
[octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt), reads all four as
reference, and contributes its own findings back.

Everything here is for **educational use**. **No Elektron binary is
redistributed** — you bring your own copy of the official OS and the tools read
it. That is enforced, not just promised: `tools/check_no_firmware.py` runs as a
pre-commit hook and refuses any file matching a known firmware digest, carrying
an `ELUP`/`ELEK`/SysEx magic, wearing a firmware extension, or simply being
unexplained binary — so a renamed copy does not slip past `.gitignore`.

**MIT licensed.** These findings came from reading other people's work; nothing
here is fenced off. Take what is useful.

---

## What is here now

**The FAT layer, and a recursive directory walker.** Every Octatrack RE project
lists the filesystem layer as the open gap. It is closed:
the 23-slot FS vtable at `0x46c823fa`, its three implementations and which one
the unit actually runs — and `0x40090a14`, a **recursive tree walker with a
per-entry callback** that the sample-load path already calls. Anything that has
to look at what is on the card starts there. → **[`docs/FS_LAYER.md`](docs/FS_LAYER.md)**

**27 KB of free, unreferenced space in the image.** Everyone is working inside
the same 6 KB cave at `0x400d64da` — octamax has nearly filled it and octabam
plants a cave at `0x400d6b00`, inside it. There are two much larger runs at the
tail of the image with **zero** static references to them.
→ **[`docs/CAVES.md`](docs/CAVES.md)**

**What a sample slot really is.** Writing one from scratch means getting three
things right at once, each silent when wrong: `PATH=` is bare, the length in
bars is computed from the file and must never be copied from another slot, and
half the state lives in `markers.work` — a file named in other projects but
whose layout is documented nowhere. Verified end to end: 32 slots written
entirely from the host load, preview and trig on the unit.
→ **[`docs/PROJECT_FILE.md`](docs/PROJECT_FILE.md)**

Features are being built on top of these in a workshop repository, and land
here when they have run on hardware. What is published is what is checkable.

## Quick start

```sh
python3 tools/extract_os.py ~/OCTATRACK_OS1.40C.syx out/mainos.bin
python3 tools/cave_scan.py out/mainos.bin --min 512
m68k-elf-objdump -D -b binary -m m68k:5407 --adjust-vma=0x40000400 out/mainos.bin | less
```

`extract_os.py` needs nothing but Python — no toolchain, no
`elektron-firmware-tool` — and verifies the result against the published digest
of OS 1.40C. That is the point of it: every address below is checkable with
nothing but this repository and your own copy of the official OS.

For disassembly use `m68k-elf-objdump -m m68k:5407`. Capstone's m68k decoder
also works for the FS and UI code quoted here, but it is **wrong** on the
ColdFire-only opcodes (`mvz`/`mvs`, EMAC) that fill the audio path.

## Tools

| | |
|---|---|
| `tools/extract_os.py` | your `.syx` → the MAIN OS (SysEx 7-bit → ELEK → aPLib), digest-checked |
| `tools/cave_scan.py` | free runs in the image, and `--refs LO HI` to prove a range is unreferenced |

## Docs

| | |
|---|---|
| [`docs/FS_LAYER.md`](docs/FS_LAYER.md) | the FS vtable and the directory walker |
| [`docs/PROJECT_FILE.md`](docs/PROJECT_FILE.md) | what a STATIC sample record contains, verified against the unit's own output |
| [`docs/CAVES.md`](docs/CAVES.md) | where octalab's code lives, and the canary test a region must pass |
| [`docs/SHARING.md`](docs/SHARING.md) | how findings go out, and what "verified" has to mean before they do |

## ⚠️ Before you flash anything

Nothing in this repository is endorsed by, supported by, or affiliated with
Elektron. Writing a non-official OS to real hardware puts the warranty in
question and can leave the unit unusable. Static analysis — reading,
disassembling, learning — carries no risk to the hardware and is most of what is
here.

If you do flash: keep the official `.syx` at hand. `[FUNC]` + power on →
`[TRIG 3]` (MIDI UPGRADE) recovers the unit even from a corrupt OS, because the
bootloader is never touched by an OS update. Never cut power during
`UPDATING FLASH`. Read octamax's [`FLASHING.md`](https://github.com/mxldyn/octamax/blob/main/FLASHING.md)
first — the recovery net is written up there properly.

---

*Independent, unofficial, educational. "Elektron" and "Octatrack" are trademarks
of Elektron Music Machines MAV AB, used here only to identify the hardware under
study.*
