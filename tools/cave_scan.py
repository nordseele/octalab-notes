#!/usr/bin/env python3
"""Find free space in the MAIN OS image, and prove a candidate is unreferenced.

    python3 tools/cave_scan.py out/mainos.bin              # every run >= 128 B
    python3 tools/cave_scan.py out/mainos.bin --min 1024   # only the big ones
    python3 tools/cave_scan.py out/mainos.bin --refs 0x4010cdd1 0x4010fdf0

A run of zeros is a *candidate* cave.  It becomes a usable one only when
nothing in the image points into it: --refs scans the whole image for 32-bit
values landing in the range, which catches `lea (abs)`, `pea`, `move.l #imm`
and any pointer table entry.  Zero hits means no *static* reference; it does
not prove the region is never written at runtime by a computed pointer.  The
acceptance test for that is the canary run in docs/CAVES.md.
"""
import argparse, pathlib, sys

BASE = 0x40000400


def zero_runs(img, minlen):
    runs, i, n = [], 0, len(img)
    while i < n:
        if img[i]:
            i += 1
            continue
        j = i
        while j < n and not img[j]:
            j += 1
        if j - i >= minlen:
            runs.append((BASE + i, j - i))
        i = j
    return runs


def refs_into(img, lo, hi, step=2):
    """Every 32-bit big-endian value in the image that lands inside [lo, hi)."""
    hits = []
    for off in range(0, len(img) - 4, step):
        v = int.from_bytes(img[off:off + 4], "big")
        if lo <= v < hi:
            hits.append((BASE + off, v))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=pathlib.Path)
    ap.add_argument("--min", type=int, default=128, help="smallest run to report")
    ap.add_argument("--refs", nargs=2, metavar=("LO", "HI"),
                    help="instead: count references into this VA range")
    a = ap.parse_args()
    img = a.image.read_bytes()

    if a.refs:
        lo, hi = (int(x, 0) for x in a.refs)
        hits = refs_into(img, lo, hi)
        print(f"0x{lo:08x}..0x{hi:08x}  ({hi - lo} B)  {len(hits)} static references")
        for site, val in hits[:40]:
            print(f"  0x{site:08x} -> 0x{val:08x}")
        if not hits:
            print("  none — no static pointer lands in this range")
        return 0 if not hits else 1

    runs = zero_runs(img, a.min)
    print(f"{a.image}: {len(img)} B, VA 0x{BASE:08x}..0x{BASE + len(img):08x}")
    print(f"{len(runs)} zero-runs >= {a.min} B\n")
    print(f"{'start':>10} {'end':>10} {'size':>7}   refs")
    for start, length in sorted(runs, key=lambda r: -r[1]):
        n = len(refs_into(img, start, start + length)) if length >= 512 else None
        print(f"0x{start:08x} 0x{start + length:08x} {length:7d}   "
              f"{'-' if n is None else n}")
    print(f"\ntotal {sum(l for _, l in runs)} B in runs >= {a.min} B")
    print("refs counted only for runs >= 512 B; use --refs for any single range")
    return 0


if __name__ == "__main__":
    sys.exit(main())
