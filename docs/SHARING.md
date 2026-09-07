# Sharing findings

Four repositories, four people, one binary. Nobody has to merge anything for the
work to compound — but only if a finding travels in a form the others can check
without trusting you.

## What a finding has to carry

A shared address is worth nothing on its own. Every claim in this repository
carries, and every claim sent elsewhere should carry:

1. **The exact image it was read from** — `OS 1.40C`, MAIN OS
   sha256 `164f3122…`, base `0x40000400`. An address means nothing without it.
2. **How it was read** — disassembly, runtime observation, emulator, hardware.
3. **A confidence marker and, when it is an inference, its falsifier.** The
   convention the other repos already use: ✅ verified, 🟡 inferred + the
   experiment that would prove it wrong. `docs/FS_LAYER.md` marks the
   `mode = 0` semantics 🟡 and names the test; that is the shape.
4. **The command that reproduces it**, from a clean clone plus the reader's own
   `.syx`. This is why `tools/extract_os.py` has no dependencies: a finding
   nobody can re-derive is a rumour.

A finding that fails one of these is a note to self, not a contribution. The
cost of getting this wrong is concrete: octamax's log records an emulator that
"confirmed" a voice type of 4 because the harness had seeded that value, and a
fix built on it was blind-wrong until a hardware log exposed it.

## What is public, and what is not

The workshop repository is private. `public/` is a separate git repository with
its own remote and no shared history, and it contains exactly the files named in
`publish.list` — an allowlist, so a file reaches the public side only by being
named, never by being finished-looking.

The line between them is not "polished vs rough", it is:

- **A finding goes out** once it carries the four things above. A finding does
  not need a working feature behind it; `docs/FS_LAYER.md` was published with no
  code attached, because the addresses are checkable on their own.
- **A feature goes out when it has run on hardware.** Not when it assembles, not
  when the emulator is green — the log of this machine is full of fixes that
  were emulator-green and hardware-wrong. Publishing an untested patch invites
  someone to flash it.
- **Nothing goes out to reserve credit.** The dated document in the private
  repository already establishes who found what, and it can be shown to anyone
  at any time.

`python3 tools/publish.py` shows what would move; `--apply` writes it; the
commit inside `public/` is a separate, deliberate act.

## Where it goes

- **Here first.** The finding lands in `docs/` as its own document, with the
  above. That is the citable artifact.
- **Then a pointer to the repos it helps.** An issue or discussion on the
  upstream repo, short, saying what the finding is and linking the document —
  not a pull request. These are personal repositories with their own
  architectures; a PR asks someone to adopt your structure, an issue hands them
  a fact they can use however they like.
- **The forums, when it is user-facing.** Elektronauts is where the people who
  would actually run the feature are.

## Taking, as opposed to giving

Cite where it came from, inline, at the point of use — repo, file, and what it
gave you. `docs/FS_LAYER.md` credits octamax's `NOTES.md` for the runtime
observation that pinned which of the three FS vtables is live; that observation
is what turned a table read off the disassembly into a verified fact, and saying
so costs one sentence.

Copying code is different from citing an address: it carries the source's
licence. Check it before, and prefer re-deriving to pasting.

## What octalab has to give back right now

`docs/FS_LAYER.md` and `docs/CAVES.md` are new to all four repositories. The
first closes a gap that both octamax's and octabam's `COVERAGE.md` list as open.
The second matters to two of them immediately — octamax has nearly filled the
6 KB cave, and octabam's list cave at `0x400d6b00` sits **inside** it, so an
image combining those two projects is already impossible; there are 27 KB
unreferenced at the tail of the same binary.
