#!/usr/bin/env python3
"""Disassemble the MAIN OS by virtual address.  VA 0x40000400 == file offset 0.

    python3 tools/otdis.py 0x40090a14 +0x180
    python3 tools/otdis.py 0x40090a14 0x40090b94

Backends, in order of preference:

  m68k-elf-objdump -m m68k:5407   the right answer.  ColdFire-exact, same tool
                                  the other repos use.  Install a m68k-elf
                                  binutils (brew: `brew install m68k-elf-binutils`).
  capstone CS_ARCH_M68K           fallback.  Fine for FS, UI and menu code;
                                  WRONG on ColdFire-only encodings (mvz/mvs and
                                  the EMAC ops), which are all over the audio
                                  hot path.  Never trust it there.

The backend in use is announced on the first call, so a listing is never
anonymous.
"""
import os, pathlib, shutil, subprocess, sys, tempfile

BASE = 0x40000400
DEFAULT_IMAGE = pathlib.Path(os.environ.get("OTDIS_IMG", "out/mainos.bin"))
_announced = set()


def _objdump(chunk, va):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(chunk)
        tmp = f.name
    try:
        out = subprocess.run(
            ["m68k-elf-objdump", "-D", "-b", "binary", "-m", "m68k:5407",
             f"--adjust-vma=0x{va:x}", tmp],
            capture_output=True, text=True).stdout
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)
    rows = []
    for line in out.splitlines():
        head = line.strip().split(":", 1)[0]
        try:
            int(head, 16)
        except ValueError:
            continue
        rows.append(line.rstrip())
    return rows


def _capstone(chunk, va):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_M68K,
                     capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_040)
    rows = []
    for ins in md.disasm(chunk, va):
        raw = ins.bytes.hex()
        rows.append(f"{ins.address:08x}  {raw:<16}  {ins.mnemonic:<10} {ins.op_str}")
    return rows


def dis(va0, va1, image=DEFAULT_IMAGE):
    image = pathlib.Path(image)
    if not image.exists():
        sys.exit(f"{image} not found — run tools/extract_os.py first")
    chunk = image.read_bytes()[va0 - BASE:va1 - BASE]
    if shutil.which("m68k-elf-objdump"):
        backend, fn = "m68k-elf-objdump -m m68k:5407", _objdump
    else:
        try:
            import capstone  # noqa: F401
        except ImportError:
            sys.exit("no backend: install m68k-elf binutils, or `pip install capstone`")
        backend, fn = "capstone m68k (ColdFire-only opcodes decode WRONG)", _capstone
    key = (image, backend)
    if key not in _announced:
        _announced.add(key)
        print(f"[otdis] {image} via {backend}", file=sys.stderr)
    return fn(chunk, va0)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    a = int(sys.argv[1], 0)
    b = sys.argv[2]
    b = a + int(b[1:], 0) if b.startswith("+") else int(b, 0)
    for row in dis(a, b):
        print(row)
