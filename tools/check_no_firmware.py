#!/usr/bin/env python3
"""Refuse to commit anything that could be Elektron's firmware.

    python3 tools/check_no_firmware.py            # check what git has staged
    python3 tools/check_no_firmware.py --all      # check every tracked file
    python3 tools/check_no_firmware.py --install  # install it as a pre-commit hook

`.gitignore` is a convention: `git add -f`, a stray copy under a new name, or a
`.syx` pasted into a docs folder all walk straight past it.  This looks at what
is actually about to be committed and refuses on three independent signals, so
a file has to beat all of them to get through:

  1. **Known digests.** The official OS 1.40C artifacts, by sha256 — the .syx,
     the .bin, the ELEK container and the MAIN OS itself.
  2. **Magic bytes.** `ELUP` (the .bin transport), `ELEK` (the container), and
     a SysEx file opening `F0 00 20 3C` (Elektron's manufacturer id).
  3. **Shape.** Any file over 64 KB that is not text, and any file whose
     extension is one the firmware travels in.

A patch is fine — a hunk carries the bytes it replaces, not the image.  What is
refused is a copy of the image itself, in any transport.
"""
import argparse, hashlib, pathlib, subprocess, sys

# Official OS 1.40C, in every transport it ships or unpacks into.
KNOWN = {
    "164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e": "MAIN OS 1.40C",
    "0a8d2d2b35c2cc78fa338576adc1af0cbc094cef973255103165c73edd87f2b6": "OCTATRACK_OS1.40C.syx",
    "1412b10f4dad76287081cf547933b97d3a56f731ef7c851a0c7656ac0face88a": "ELEK container 1.40C",
    "370c55a3dad3996b8e4b46400a205066fdaf185ad4d0255a3a3f835060573ff0": "OCTATRACK_OS1.40C_dist.zip",
}
MAGIC = ((b"ELUP", "ELUP .bin transport"),
         (b"ELEK", "ELEK container"),
         (b"\xf0\x00\x20\x3c", "Elektron SysEx"))
SUSPECT_SUFFIX = {".syx", ".bin", ".elup", ".elek"}
BIG = 64 * 1024


def offences(path: pathlib.Path):
    """Every reason this file must not be committed."""
    out = []
    if not path.is_file():
        return out
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest in KNOWN:
        out.append(f"is {KNOWN[digest]} (sha256 {digest[:16]}…)")
    for magic, what in MAGIC:
        if data[:len(magic)] == magic:
            out.append(f"starts with the {what} magic")
    if path.suffix.lower() in SUSPECT_SUFFIX:
        out.append(f"has a firmware-transport extension ({path.suffix})")
    if len(data) > BIG:
        try:
            data.decode()
        except UnicodeDecodeError:
            out.append(f"is {len(data)//1024} KB of binary")
    return out


def listed(mode):
    if mode == "all":
        cmd = ["git", "ls-files", "-z"]
    else:
        cmd = ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return [pathlib.Path(p.decode()) for p in raw.split(b"\0") if p]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="check every tracked file")
    ap.add_argument("--install", action="store_true", help="install as .git/hooks/pre-commit")
    a = ap.parse_args()

    if a.install:
        hook = pathlib.Path(".git/hooks/pre-commit")
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text("#!/bin/sh\nexec python3 tools/check_no_firmware.py\n")
        hook.chmod(0o755)
        print(f"installed {hook} — every commit is now checked")
        return 0

    bad = [(p, o) for p in listed("all" if a.all else "staged") if (o := offences(p))]
    if bad:
        print("REFUSED — no Elektron firmware may be committed to this repository:\n",
              file=sys.stderr)
        for path, why in bad:
            print(f"  {path}", file=sys.stderr)
            for reason in why:
                print(f"      {reason}", file=sys.stderr)
        print("\nUnstage it (git restore --staged <file>) and keep your copy outside the\n"
              "repository, or under a path .gitignore covers.", file=sys.stderr)
        return 1

    n = len(listed("all" if a.all else "staged"))
    print(f"clean — {n} file{'s' if n != 1 else ''} checked, no firmware")
    return 0


if __name__ == "__main__":
    sys.exit(main())
