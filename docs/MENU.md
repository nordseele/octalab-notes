# The OCTALAB menu — where the functions will live

⚠️ **Keys are model-specific.** The menu *tables* below are in the shared OS
image and apply to both models, but MKI and MKII do not have the same panel and
ems-octakit had to bind its pages differently on each. Everything here about
key combinations is about a **MKI**.

A page on the unit holding octalab's own functions, each with its parameters.
Design note, nothing built yet.

## Why not PERSONALIZE

The obvious home is wrong twice over. It is nearly full — 19 of 20 entries after
octamax's slice playhead — and its entries are **checkboxes**. A function like
poolfill has arguments: which folder, how many slots, which slot range, reroll.
A boolean cannot carry those.

## The firmware already has a menu framework ✅

It does not have to be built. `FUN_4006d57c` is a **generic scrollable
menu/dialog constructor** with **89 call sites** — every action menu in the
firmware goes through it:

```
FUN_4006d57c(title, n_options, char **options, default, confirm_callback)
```

octamax identified it and reconstructed the signature; ems-octakit's
`runtime/abi.inc` names its state, which is what shows it is a real menu rather
than a yes/no box — per-item **callbacks**, a selection, and scrolling:

| what | address |
|---|---|
| label array | `0x460e5e2c` |
| callback array | `0x460e5e28` |
| item count | `0x460e5e48` |
| selection / absolute selection | `0x460e5e34` / `0x460e5e40` |
| visible count, state | `0x460e5e44`, `0x460e5e38` |
| scroll up / down | `0x4007ec7c` / `0x4007eca4` (44 and 46 call sites) |
| popup create / frame draw | `0x4005829c` / `0x40056f4c` |
| popup object table | `0x46c7d34c`, stride `0x38` |

All four references to the label/callback/count/selection globals sit inside
`0x4006d7ea .. 0x4006d9c4`, i.e. inside the constructor itself. So an OCTALAB
menu is **a call with our own labels and our own callbacks**, not a framework.

## And a second, richer precedent

ems-octakit did not stop at a menu: its LOAD KIT / SAVE KIT pages have a name
prompt (7 characters), copy / paste / clear / **undo** on slots, an asterisk
marker for unassigned entries, and they are opened by rebinding existing keys
(`PART` opens LOAD KIT, `FUNC`+`PART` SAVE KIT, `FUNC`+`CUE` reloads). Read
`runtime/ui.S`, `runtime/v3_ui.S` and `runtime/stock_ui.S` before designing our
own page — the hard parts are solved there, under its own licence.

## A menu of our own, made only of data ✅ — running on hardware, 7 Sep 2026

`modules/octalabmenu/`, confirmed on a **MKI** running OS 1.40C. OCTALAB is a
**fifth top-level category** beside PROJECT / SYSTEM / CONTROL / MIDI — a list
descriptor, a rows table, an icon and one extra root row, all in a cave, and
**not one instruction added to the firmware**. The stock tree does the opening,
the drawing, the scrolling and the closing.

What the unit does: `[FUNCTION]`+`[MIXER]` opens the menu, OCTALAB sits under
MIDI with its own icon, the arrows reach it, its two rows appear in the right
pane and can be hovered, `[ENTER]` does nothing on them (they carry the shared
`rts` and no page id), `[EXIT]` closes, and reopening returns to the same row.
That last part is worth stating: the position is remembered because the focus
pointer at `0x400cbda8` reads our descriptor's `+0x04`/`+0x08` back — a
descriptor built by hand behaves as stock all the way through the nav engine,
not merely at draw time.

Three builds, and each failure named a different field. They are worth keeping
in that order, because each one is a rule you cannot read off the layout.

### The two record types

```
list descriptor (0x1c B)              row (0x18 B)
  +0x00  item count                     +0x00  label pointer
  +0x04  scroll: first visible row       +0x04  window descriptor (root rows only)
  +0x08  cursor within the window        +0x08  action fn
  +0x0c  absolute selection              +0x0c  right-column value getter
  +0x10  how many rows are VISIBLE       +0x10  child descriptor (root rows only)
  +0x14  item count again                +0x14  page id
  +0x18  rows pointer
```

The stride is confirmed from code (octabam `MAINMENU.md` §1: the engine computes
`d3*32 − d3*8`). The registry of nine descriptors runs `0x400cbcac..0x400cbda7`;
the root is the last, at `0x400cbd8c`.

### 1. A null action means "section heading" 🔴 measured on hardware

A row whose `+0x08` is 0 is drawn and then **skipped by the cursor** — that is
what makes the `0x17`-glyph separators in the PROJECT table unselectable. Build
1 copied the root's rows, which do carry null actions, and produced an OCTALAB
that appeared under METRONOME and that the arrows would not land on.

Every real leaf carries `0x400648f8`, a bare `rts`. **The action is what makes a
row selectable; it does not have to do anything.**

### 2. [ENTER] reads the page id, not the child pointer 🔴 measured on hardware

Build 2 was hoverable and dead. Two dispatch mechanisms share one row, and
octabam decoded both on 31 Aug (`MAINMENU.md` §3): the key handler at
`0x40064e64` reads `+0x14` on keycode `0x31`; ids 1..15 open the matching entry
of the menu-state table at `0x400cbdac`, and **id 0 falls through to calling the
action at `+0x08`**. CONTROL's own rows are the proof — all six carry the shared
`rts` and ids 2..7.

So a row inside a pane cannot descend: `+0x10` is never read there. It belongs
to the root's row shape, which is the mirror image of a leaf — window descriptor
and child, no action, no id. And the id path is closed to us: all 15 states are
occupied, with live data behind the table.

**Hence a category rather than a row.** Copy the four root rows to a cave,
append ours, repoint `0x400cbda4`, bump the count at `0x400cbd8c` — the move
octabam prices in §5 and octamax already proved on the PERSONALIZE arrays. It is
also one keypress deep instead of two.

### 3. A descriptor ships inert; it is initialised at boot ✅ (octabam §1 marks +0x08..+0x14 🟡)

Build 3's first attempt drew OCTALAB in the category column with an **empty
second pane**, and a descriptor cloned byte-for-byte into the cave failed where a
stock one worked — which looked like the engine validating the address. It is
not. Descriptors are filled in at boot by a run of calls at
`0x40064c70..0x40064d1e`:

```
init(&desc + 4, visible, count)             init = 0x4007ec60

  clr.l   desc+0x04     scroll
  clr.l   desc+0x08     cursor within the window
  clr.l   desc+0x0c     absolute selection
  move.l  visible ->    desc+0x10           7 for submenus, 5 for the root, 2 for the demo menus
  move.l  count   ->    desc+0x14
```

`+0x0c` is named by the scroll routines either side of it: `0x4007ec7c`
decrements `+0x08`, carries into `+0x04` at the top of the window, and stores
`+0x04 + +0x08` into `+0x0c`.

Our descriptor is not in that run, so it must **ship already initialised**. With
`+0x10` left at zero the pane has zero visible rows and draws nothing. That was
the whole bug.

Two useful consequences. The run is guarded by `tst.l 0x400cbda0` — the root's
own `+0x14` — so it happens exactly once; and it passes the **count field**
rather than an immediate, so the root's new count of 5 is picked up for free.

### The window descriptor is the category's icon ✅ (octabam §8 lists it undecoded)

`{0x13, 0x09, 0x01, plane0, plane1}` — 19 wide, 9 tall — where a plane is 19
words each holding one **column byte** in the high byte, bit 0 at the top.
Rendered: PROJECT is a folder, SYSTEM a chip, CONTROL a speaker with waves, MIDI
a keyboard. `plane1` is `0xff80` in all four, so it is a constant rather than
image data.

### ⚠️ This build edits the root, which is the recovery screen

`[FUNCTION]`+`[MIXER]` opens it and OS UPGRADE lives under SYSTEM inside it. A
root that will not draw costs an hour of MIDI SysEx — it already did once.
What makes it acceptable: the four stock rows are
copied byte for byte and asserted afterwards, every pointer added addresses a
clone of a structure the firmware already renders, and the emulator renders the
root with the cursor on each of the five categories — including SYSTEM reaching
OS UPGRADE — before anything is written to a card.

## Better than a key combo: the PROJECT menu is a data table ✅

Hunting for a free key combination is the wrong fight — even with the audio pool
open, the background combos (FUNC+PATTERN, FUNC+EXIT…) still fire, so nothing is
locally free and a new binding would have to be globally free.

It is not needed. The PROJECT menu is a plain table of 24-byte records at
`0x400cc308`, laid out `{label_ptr, 0, handler_ptr, 0, 0, 0}`. Section headings
are records whose label is padded with `\x17` glyphs and whose handler is null:

```
0x400cc308  ──PROJECT──
0x400cc320  CHANGE            -> 0x40063e48
0x400cc338  SAVE              -> 0x40063890
0x400cc350  RELOAD            -> 0x400635d4
0x400cc368  SYNC TO CARD      -> 0x400637e8
0x400cc380  SAVE TO NEW       -> 0x40063618
0x400cc398  EXPORT TO SET     -> 0x40063508
0x400cc3b0  ──SET──
0x400cc3c8  CHANGE            -> 0x400639a0
0x400cc3e0  ──SAMPLES──
0x400cc3f8  COLLECT SAMPLES   -> 0x4006354c
0x400cc410  PURGE SAMPLES     -> 0x400634c4
0x400cc428  ──BANKS──
0x400cc440  SAVE CUR BANK     -> 0x40063838
0x400cc458  RELOAD CUR BANK   -> 0x40063590
0x400cc470  NOT AVAILABLE / IN DEMO MODE   (the demo-mode menu, pointed at
0x400cc488                                  separately from 0x400cbce0)
```

The table is reached through `0x400cbcc4`. **There is already a `──SAMPLES──`
section**, holding COLLECT and PURGE — which is exactly where a function that
fills the pool belongs, semantically and visually. A user finds it where they
would look for it, with no combination to learn and nothing rebound.

Adding an entry is adding a 24-byte record and adjusting the count. That is the
technique octamax already proved on the PERSONALIZE arrays: append the entry,
change the item-count immediate (`moveq #17` → `#18` at `0x40068fb2`), done.

🟡 **To pin before writing:** how the list length is bounded — a count in the
registry near `0x400cbcc4`, or a sentinel. `0x400cbcac` holds `15`, and this
table has exactly 15 records, which is suggestive but sits next to a *different*
table pointer. **Falsifier:** change that 15 to 14 in a diagnostic build and see
whether RELOAD CUR BANK disappears from the menu.

## What poolfill would ask for

| parameter | how it is picked |
|---|---|
| source folder | the file browser, which already navigates the card — pick a folder instead of a file. Handlers around `0x40078b1a`, and the tree walker is `0x40090a14` (`docs/FS_LAYER.md`) |
| how many slots | a number, the way any stepped parameter is dialled |
| slot range | STATIC 1-128, or 129-256 on a dual-256 image |
| go / reroll | the confirm callback; reroll redraws the same count with a new seed |

The folder picker is the one piece with no precedent to copy, and it is also the
piece that makes the difference musically — drawing from `chunks/` gives a
coherent pool, drawing from all of `AUDIO/` gives a lucky dip. Both are wanted.

## Open

- **Which key combination opens it.** Everything else has a precedent; this does
  not, and it has to be one nobody's fingers already use.
- Whether the menu can be entered while the sequencer runs, or only stopped.
- Whether a fill should be undoable on the unit (octakit has undo on kit slots —
  the same idea would need the previous slot records kept somewhere).

## The popup's title, and the refresh detour ✅ (8 Sep 2026)

The scrolling callback list (`0x4006d94c`) takes no caption, and a title drawn
once after the call does not survive: the refresh clears its region before it
draws, so the first scroll erases the caption. Two builds died that way before
the answer turned out to be the one ems-octakit already uses for its LOAD KIT
list (`runtime/v3_ui.S`) — **draw the title from the refresh path, every pass.**

### What the opener stores, and the guard that follows from it ✅

Decompiled `FUN_4006d94c(count, selection, arg3, labels[], handlers[])`:

| | |
|---|---|
| `0x460e5e2c` | **`labels[]`** — the argument, stored |
| `0x460e5e28` | `handlers[]` |
| `0x460e5e30` | the popup object (`+0x24` width, `+0x28` height) |
| `0x460e5e34` | the third argument — a selection field, **not** a caption |
| `0x460e5e38` · `0x460e5e40` · `0x460e5e44` · `0x460e5e48` | first visible · absolute selection · visible count · total |

and the box it creates is `height = min((count + 1) * 7, 0x23)`, with row *i*
drawn at `height - 9 - 7i`.

`0x460e5e2c` is what makes a global detour safe. Hooking the refresh means
running for **every** scrolling-callback list in the firmware, and comparing
that word against our own array answers "is this our list?" exactly — while
clearing itself, because opening any other list overwrites it. A flag of our own
would have to be cleared when the popup closes, and [EXIT] goes to stock code.

### The detour ✅

The refresh at `0x4006d784` opens with two **position-independent** instructions:

```
4006d784:  4fef ffe8   lea    %sp@(-24),%sp
4006d788:  48d7 3c0c   moveml %d2-%d3/%a2-%a5,%sp@
4006d78c:              <- the continue point
```

so they can be re-executed from the cave, which is what makes a 6-byte `jmp` at
the head safe. `0x4006d78c` is the same continue point ems-octakit uses.

The hook then: shrink the object to the row height, call the stock refresh so
the rows are drawn into what is left, restore the full height, and draw the
title into the band with `0x40057c84(object, text, 0)`. Measured under
emulation: title at `y=23`, rows at `y=12` and `y=5`, and the title is present
again after a second refresh — which is the check the one-shot versions failed.

### What actually calls the refresh ✅

**Nothing in the image references `0x4006d784` absolutely.** A scan for
`jsr`/`jmp` against that address, or for the bare word, comes back empty — which
reads exactly like a detour placed on a function nobody calls. It is called five
times, all by relative branches (`0x4006d8da`, `0x4006d8ee`, `0x4006d932`,
`0x4006d946`, `0x4006da1a`), because they are inside the same module.

Two of them are the point: the handlers the stock input map registers for
up and down,

```
4006d924:  pea 0x460e5e38 ; jsr 0x4007eca4 ; addq #4,%sp ; bra.w 0x4006d784
4006d938:  pea 0x460e5e38 ; jsr 0x4007ec7c ; addq #4,%sp ; bra.w 0x4006d784
```

tail-branch straight into it. So a finger on [UP]/[DOWN] goes through the hook,
which is the thing that had to be true and was nearly taken on faith: the first
version of the check called the refresh directly, and that proves the hook works
when called, not that anything calls it.

🟡 **Falsifier:** if the title still disappears on the unit, the refresh is
reached by a path that does not go through `0x4006d784`, and the hook belongs on
whatever the input map at `0x400ce0c4` actually dispatches to.


## The stock CLEAR SLOT, and the YES/NO dialog's real call site ✅ (8 Sep 2026)

`FUN_40025288(kind, slot)` is what the unit runs to empty a sample slot —
`kind` 0 is STATIC, 1 and 4 are FLEX. For STATIC it is two steps:

```c
FUN_40093814(slot);              // tear down: close the file handle the loader
                                 // opened, and drop this slot from every trig
                                 // and slice table across the eight tracks
FUN_40020950(record, 0x448);     // then zero the whole settings record
```

It has one caller worth reading, at `0x40021cb4` — the EDIT menu's CLEAR SLOT,
which is also the clearest example in the image of the stock **YES/NO dialog**
that `docs/INPUT.md` §3 gives the signature for:

```
40021c9c:  pea 0x400b3733        | "CLEAR SLOT" — the title
40021ca2:  jsr 0x4006d57c        | after pea 3, pea lines[], pea 2, pea title
40021cb4:  tst.l %sp@(4)         | the handler: 0 is YES
           bne.s  <return>       | NO — do nothing at all
           move.l 0x460be9ec,%sp@-   | slot
           move.l 0x460be9e8,%sp@-   | kind
           jsr    0x40025288
           jsr    0x4006dbdc
           jmp    0x40077b00     | redraw the audio pool page
```

So the confirmed shape is `FUN_4006d57c(title, n_lines, lines[], 3, handler)`
with the answer arriving as the handler's **first stack argument**, 0 for YES —
which is what `docs/INPUT.md` and both upstream `NOTES.md` say, now with a call
site to read it off.

Note what the UI does *not* do here: it never posts the voice re-arm
(`FUN_40093468`). `FUN_40093814` has already dropped the slot from the trig and
slice tables, so there is nothing left pointing at it.
