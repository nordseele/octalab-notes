# The input layer — how a gesture reaches code

What it takes to summon a screen from anywhere, instead of navigating to it.
Read `docs/MENU.md` first: that covers the menu *tree*, this covers what opens
things.

Everything here is read out of OS 1.40C (`sha256 164f3122…`, base
`0x40000400`), except where it cites a repo.

---

## 1. Key bindings are data ✅

A gesture is dispatched through a table of **26-byte keymap records**. There are
two, back to back:

| table | records | contains |
|---|---:|---|
| `0x400bfbf6 .. 0x400c01f3` | 59 | no code `0x1c` |
| `0x400c01f4 .. 0x400c083f` | 62 | codes `0x1c..0x1f`, `0x1c` being the dedicated MAIN MENU key |

🟡 **The second is the MKII's and the first the MKI's** — inferred, from
octabam's `MAINMENU.md` §7 identifying `0x1c` as the MKII's dedicated MAIN MENU
key, which the MKI's panel does not have. **Falsifier, and it is free:** patch a
binding in the first table only and press the key on a MKI. If it fires, the
inference holds.

The record, decoded here:

```
+0x00  u8   input code          +0x0a  fn 3    (often the same fn again)
+0x01  u8   0                   +0x0e  ptr     sub-map / per-key data
+0x02  fn   press handler       +0x12  fn 5
+0x06  fn   release handler     +0x16  fn 6, then a u16 tail
```

Both tables end with a `0xff` sentinel record and are exactly full, so a new
record means relocating the table — which is not needed, because a binding is
one pointer.

Neither table is referenced by its own first byte. Both are reached from
**20-byte input-map nodes** at `0x400c090e` and `0x400c0922`, each pointing at
its table's **FUNCTION record** rather than at record 0 — so the walk starts
there. 20 bytes is `GK_STOCK_INPUT_MAP_DESCRIPTOR_SIZE` in ems-octakit's
`runtime/abi.inc`, and `INPUT_MAP_REGISTER` is `0x40031494`: a screen registers a
map and the firmware dispatches through it. That is how octakit binds its pages,
and it is screen-scoped. **The keymap tables are the global layer underneath.**

## 2. The panel codes, and what is already taken ✅

From the MKI table, grouped:

| codes | handler | what |
|---|---|---|
| `0x00..0x0f` | `0x40060ce0` | the sixteen trig keys |
| `0x10..0x17` | `0x40040250` | the eight track keys |
| `0x22..0x26` | `0x4005578c` | five more, one handler |
| `0x38..0x3e` | `0x4004ecfc` | **the seven encoder presses** — six data encoders and LEVEL |
| `0x2d` | `0x4004e954` / `0x400568e4` | FUNCTION, and the only record carrying a sub-map pointer (`0x400bfa1e`) |
| `0x2e` `0x2f` | `0x4005a044` `0x4007af80` | PATTERN, BANK |
| `0x19` `0x1a` | `0x4004348c` | a mirrored pair — the arrows |

**`0x3e` (LEVEL press) is not free**, which is worth knowing before designing
around it. `0x4004ecfc` serves all seven presses and special-cases `0x3e`:

```
if (code == 0x3e) { if (!MIDI_MODE) 0x46c7d2c0 = 0x14; }
else if (code - 0x38 <= 7) 0x46c7d244[code - 0x38 + 1] = 0x14;
```

`0x46c7d2c0` is read from seven sites (`0x4004e8ce`, `0x400555e0`, `0x4005691e`,
`0x4007c586`…), so pressing LEVEL does something: 🟡 it looks like the
"show this value on screen" flag every Elektron box has on an encoder press.
A binding that *replaces* the handler removes that; a binding that **wraps** it
— do ours, then jump to `0x4004ecfc` — keeps it.

## 3. Two stock popup engines, both callable ✅

Neither has to be written.

**Yes/no dialog** — `FUN_4006d57c(title, n_lines, lines[], 3, handler)`, with
`YES → handler(0)`, `NO → handler(1)`. 89 call sites; the signature is octamax's
and octabam's, in both their `NOTES.md`. This is OS UPGRADE's own confirm box.

**Scrolling list with callbacks** — the one that matches what we want, and
ems-octakit's LOAD KIT / SAVE KIT list is built on it (`runtime/v3_ui.S`):

| | |
|---|---|
| open / close | `0x4006d94c` / `0x4006d754` |
| confirm / cancel-return | `0x4006d8f4` / `0x4006d782` |
| refresh | `0x4006d784` |
| **its input map** | `0x400ce0c4` |
| popup create / frame draw | `0x4005829c` / `0x40056f4c` |
| title draw | `0x40057c84` |

The important part is the input map: opening the list **registers
`0x400ce0c4`**, so up/down, [ENTER] and [EXIT] are handled by stock code. A
list of our own is labels plus a confirm callback, not a screen to write.

## 4. The native trig-mode popup — the reference UX ✅

`[FUNCTION]` + `[UP]`/`[DOWN]` opens a temporary overlay to pick the trig mode.
Its label array is at **`0x400d0230`**, six entries:

```
STANDARD · CHROMATIC · SLOTS · SLICES · QUICK MUTE · DELAY CTRL
```

preceded at `0x400d021c` by `{0x0c, 0x05, 0x01, 0x400d0274, 0x400d02a4}`, which
the array points back at from `0x400d0248` (🟡 uninterpreted — the popup's own
descriptor, most likely). It sits in the same region as
`GK_STOCK_TEXT_EDITOR_INPUT_MAP` (`0x400d071c`), which is where per-screen input
maps live.

This is the model to copy: an overlay that owns the input while open, closes on
[EXIT], and leaves no trace in the menu tree.

## 5. The firmware detects double presses, generically ✅

This is the finding that decided the shortcut. The page-key handler at
`0x400557c2` does it in the clear, and the track-key handler repeats it:

```
if (0x400c0aac == this keycode  &&  0x460d5de0 <= 14)   -> double press
else  0x400c0aac = this keycode ;  0x460d5de0 = 0
```

| | |
|---|---|
| `0x400c0aac` | the last tracked keycode |
| `0x460d5de0` | ticks since it was pressed — incremented (saturating) by the display loop at `0x40052204`, and **reset by any tracked key** |
| `0x40033e20` | the stock reset: `0x400c0aac = -1 ; 0x460d5de0 = 0` |
| window | **14 ticks** — the same one the track-key double press that opens the audio pool uses |

Reusing these globals rather than a private timer is smaller *and* more correct.
Press FUNC+A then FUNC+B quickly: A's handler has already overwritten
`0x400c0aac`, so the second FUNCTION sees no match and nothing opens. The stock
mechanism supplies "no other key in between" for free — exactly the condition a
bare double-tap needs.

## 6. What was ruled out, and why ❌

**The LEVEL encoder press.** `0x3e` is not free — `0x4004ecfc` serves all seven
encoder presses and special-cases LEVEL to raise the value display. That much
could be wrapped. What killed it is physical: the encoder is sensitive enough
that a brief press often moves the value, so "click, unless you turned it"
misfires roughly one time in three. Measured on the unit. A shortcut that fails
that often is not a shortcut.

**A FUNCTION *combo*** through the sub-map at `0x400bfa1e` — not needed once the
double press was found, and the structure stays undecoded.

## 7. What shipped: double-tap [FUNCTION] ✅

octalab's shortcut. FUNCTION's press field in **both** keymap tables
points at a 94-byte stub in the cave, which applies the §5 test and then tail-
calls one of two stock addresses — `0x40064c18`, the menu opener, on a double
tap, or `0x4004e954`, the stock FUNCTION handler, on anything else. FUNCTION
therefore remains FUNCTION, which for a modifier key is the requirement.

`0x40064c18` **toggles** (it checks the menu window handle `0x400cbf4c` and
closes if one is open), takes no arguments, and is what the MKII's dedicated
MAIN MENU key reaches from its own keymap record by a bare `bra` at
`0x40064d78`. Calling it from a keymap handler is the stock pattern, not a new
one.

Before opening, the stub writes the root descriptor's `+0x08` and `+0x0c` — the
cursor and selection fields `docs/MENU.md` decodes — and the focus cell at
`0x400cbda8`, so the gesture lands *on* the OCTALAB pane instead of at the top
of the tree.

⚠️ All three add the first **executable code** octalab ships. Everything to date
has been data. `docs/BEFORE_FLASHING.md` applies with full force, and the stub
must be disassembled back out of the built image before it goes anywhere near a
card.

## 8. Input maps and encoders — the popup's own keys ✅ code, emulator (v21, 11 Sep 2026)

**A screen owns keys and encoders by registering a map, and maps are layers.**
`INPUT_MAP_REGISTER 0x40031494(map)` / `0x4003146c(map)` add and remove a
20-byte map `{next, keys, encoders, 0, marker}`; each call rebuilds two RAM
tables from every registered map, head to tail (`FUN_4003125c`):

| table | per | fields |
|---|---|---|
| keys `0x46c7d8de` | code × 0x18 | +0 press · +4 release · +8 repeat · +0xc sub-maps · +0x10 held (`FUN_4003171c(code)`) |
| encoders `0x46c7dede` | encoder × 0x14 | +0 turn handler `(encoder, delta)` |

The last map registered wins. In a 26-byte key record a field of -1 keeps the
layer below; a 22-byte encoder record is copied whole, so **an encoder listed
with a null handler is swallowed**. That is why nothing turns with a popup up:
the scrolling list's map `0x400ce0c4` lists all seven encoders, null. The
manual's "knobs not used by an active menu retain their function" is the other
case — a map that simply does not list them (TEMPO lists only LEVEL).

Codes: UP 0x33 · DOWN 0x20 · LEFT 0x34 · RIGHT 0x21 · ENTER 0x31 · EXIT 0x32 ·
encoder presses 0x38..0x3e. Encoders: A..F = 0..5 (🟡 A = 0 from record order),
**LEVEL = 6** (four stock handlers, among them CONTROL → INPUT's noise gate).
Stock handlers multiply the delta by 7 when the knob is pushed while turned.

**The popup (v21) puts a map of its own on top of the list's** when it opens
(`octalab_open`, the stub's exit): LEVEL turned moves between rows through the
stock `0x4007edb0` + refresh, **ignored while LEVEL is held** — the §6
measurement, a press wobbling the knob, turned into a rule; the LEVEL press and
ENTER confirm, EXIT cancels, and all three take our map off first; LEFT/RIGHT
choose the row's action; encoder A sets a value (0..100, ×10 pushed) on an
action that takes one, and is swallowed elsewhere. B..F stay locked. Any of our
handlers that finds our list gone takes the map off and passes the event to
whoever holds that key now, so a map left behind by an unusual close costs one
check. All of it ran on a MKI (OLB25, 11 Sep 2026): LEVEL = 6, A = 0, our map
on top, and every key and knob back to stock once the popup closes.

**Two stock models for richer screens**, not used yet: PATTERN SETTINGS (a
113×58 popup `0x4005829c(0x71, 0x3a, …)`, its own map `0x400d113c`, its own
draw `FUN_40082f40`: title, two columns of standard list descriptors, the right
one with values) and TRACK TRIG EDIT (`FUN_4007b780`).
