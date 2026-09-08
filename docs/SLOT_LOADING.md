# Loading a sample into a slot

OS 1.40C, MAIN OS sha256 `164f3122…`, load base `0x40000400` — VA = file offset
+ base. Everything below ran on a MKI.

The two settings arrays are octamax's finding (`HOTSWAP_DESIGN.md`): STATIC at
`0x100d5b30`, FLEX at `0x100b14f0`, stride `0x448`, the name at offset 0, and a
slot is free when that first byte is 0. What follows is what happens *around*
them.

## `ot_static_slot_load(slot, keep_trim)` is half of it ✅

`0x40093980`. It resolves the name, validates the file and streams it, and
returns 1. It has **exactly one caller in the whole image** — `0x40084c1a`,
inside the storage-job dispatcher at `0x4008445c`, whose `case 1` is "load a
STATIC slot". That case is the real sequence:

```c
rc = ot_static_slot_load(slot, keep_trim);
if (rc >= 1) {
    if (keep_trim == 0) FUN_40099148(0, slot);   // 0 = STATIC, 1/4 = FLEX
    else                FUN_40099680(0, slot);
    if (flag)           FUN_4008fb58(settings, 0, slot);
}
FUN_40093468(0xffffffff);      // re-arm the eight tracks' voices
FUN_4009da20(0xffffffff);      // refresh what displays them
```

**Calling only the loader gives a slot that displays and will not play.** The
name and the size appear in the audio pool, the BPM column stays empty, and the
slot will neither preview nor trig. `FUN_40093468` walks the eight tracks and
posts a type-`0xe` message per track into the audio engine's queue; without it
the engine still describes the slots as they were.

The one field that changes when the post-load runs is `0x46c93a24 + slot*4`.
The tempo pair at `settings+0x10c`/`+0x10e` is written by the loader itself
(through `FUN_40099680`), so it is *not* a way to tell the two apart.

**`keep_trim = 0` makes the firmware derive the trim/loop window from the file.**
The bulk project loader passes 1 because its trim came from `project.work`; a
file with no stored trim wants 0.

## A refused load leaves a visible error ✅

The loader writes its verdict into a per-slot status record:

| | |
|---|---|
| base | `0x46c90a78 + slot*0x2c` |
| `+0x08` | state — 0 idle, 2 loading, **3 error** |
| `+0x0c` | the error code |
| `+0x14` | a generation counter |
| `+0x24` | the open file handle |

and the audio pool renders it as `ERROR: <reason> : <name>` using the format at
`0x400b7248`. `FUN_4001fcb8(code)` is the whole code→string table. The two that
matter when feeding it filenames:

- **`-0x10` INVALID FILENAME** — `FUN_400204cc` found *no* extension at all.
  A **directory name** produces exactly this.
- **`-0x1e` INVALID FILETYPE** — an extension that is not WAV/AIF/AIFF/AIFC.

Clearing the name byte does **not** clear that record, so a rejected candidate
stays on screen until the slot is properly cleared.

## Clearing a slot ✅

`FUN_40025288(kind, slot)` — what the EDIT menu's CLEAR SLOT runs. For STATIC:

```c
FUN_40093814(slot);            // close the open file handle, and drop this slot
                               // from every trig and slice table on all 8 tracks
FUN_40020950(record, 0x448);   // then zero the whole settings record
```

Doing it by hand instead **leaks the file handle**, because closing it lives
inside `FUN_40093814`; the symptom is `MAX OPEN FILES` after enough failures.

## The audio folder is folders ⚠️

A real set's `<set>/AUDIO/` holds subdirectories, not files — 13 folders and
zero files on the unit this was measured on, with all 1362 audio files one level
down. Anything enumerating one level finds only directory names, and every one
of them comes back `-0x10`.
