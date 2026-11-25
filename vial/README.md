# Miryoku for the Cornix in Vial (no flashing)

Miryoku on the stock/RMK **Vial** firmware. Nothing gets flashed: dropping the
`.vil` file into Vial writes the keymap into the keyboard over USB and it stays
there.

| File | What it is |
|---|---|
| `cornix-miryoku-qwerty.vil` | 10 Miryoku layers, QWERTY base |
| `cornix-miryoku-colemakdh.vil` | 10 Miryoku layers, Colemak Mod-DH base |

Shipped options: outer columns empty, **Cmd/Control swapped** (macOS: Command on
the middle finger, Control on the pinkie) and the **vim-style Nav layer**
(`MIRYOKU_NAV_VI` + `MIRYOKU_MOUSE_VI`: arrows/pointer on the home row next to
the centre, paging/scroll on the row below - both layers on the same fingers). Shortcut combos such as `LGUI(KC_C)` are untouched - they stay Cmd.
| `make_miryoku_vil.py` | generator (translates Miryoku ZMK layer definitions to Vial keycodes) |
| `vial_names.txt` | Vial keycode names, used for offline validation |
| `miryoku_layer_alternatives.h` | vendored from [miryoku_zmk](https://github.com/manna-harbour/miryoku_zmk) (MIT), the source of the 10 layer definitions |
| `preview.txt` | human-readable dump of the generated layers |

All metadata (uid, settings, encoder rotation, tap-dance/combo slots) is copied
from a real Vial export of this keyboard, so the files load without complaints.
Only `layout` (the keymap) differs.

## Load it

1. Connect the Cornix with the USB-C cable (Vial never works over Bluetooth).
2. Open Vial, make sure it detects the keyboard, and unlock it if it asks.
3. **File → Load saved layout**, pick `cornix-miryoku-qwerty.vil`.
4. Everything is written to the keyboard immediately. Test typing; tweak any key
   in Vial's UI afterwards (each change is saved to the keyboard as well).

Before loading, keep a backup of your current keymap: **File → Save current
layout**. (`~/Downloads/a.vil` from this session is such a backup.)

## What Miryoku maps to on the Cornix

Miryoku is 36 keys (3×5+3); the Cornix has 6 main columns per hand, so one
column per hand has nothing on it:

| Cornix position | Miryoku role |
|---|---|
| columns 1–5 of each half (pinkie → inner) | 5 Miryoku columns per hand |
| **column 0 of each half** (leftmost / rightmost of the keyboard) | Miryoku has no use for it, so it stays empty - except two hand-placed keys on the left: `SGUI(KC_4)` (⌘⇧4 screenshot) on the top row and `LALT(KC_Z)` (⌥Z) on the outer palm key. Regenerate with `--drop inner` to empty the columns next to the centre gap instead |
| thumb fans columns 3,4,5 | Esc(Media) Space(Nav) Tab(Mouse) ǀ Enter(Sym) Bspc(Num) Del(Fun) |
| 3+3 palm keys, inner keys | mostly `KC_NO` - free real estate, drop something useful in via Vial (the shared list in `make_miryoku_vil.py`, `USER_PATCHES`, carries the ones already in use: `LALT(KC_Z)` on the left palm, `USER00`–`USER02` on the FUN layer's outer column) |
| 2 encoder push buttons | kept as `KC_MUTE` / `KC_BTN3` on every layer (they were that in your export) |

Layers: `0 BASE, 1 EXTRA, 2 TAP, 3 BUTTON, 4 NAV, 5 MOUSE, 6 MEDIA, 7 NUM, 8 SYM, 9 FUN`
— the numbering Miryoku's own `LT<n>()`/`TO(n)` references expect. Your firmware
already reports 10 layers, so no firmware change is needed.

## Home-row-mod tuning

The files also carry tuned QMK/Vial settings (Vial → *QMK Settings* tab) so the
home-row mods stop misfiring during fast rolls:

| Setting | Before | Now | Why |
|---|---|---|---|
| Tapping Term | 250 ms | **200 ms** | earlier tap/hold decision, fewer accidental modifiers |
| Flow Tap | 120 ms | **150 ms** | a modifier is ignored on keys typed right after a tap (fixes fast rolls) |
| Permissive Hold | on | on | an intentional mod+key chord still resolves on the key's release |
| Hold On Other Key Press | off | off | left off on purpose: it makes down-rolls (D then F) fire the modifier |
| Chordal Hold | on | on | same-hand rolls count as taps |

Tune to taste live in Vial's *QMK Settings* panel - no reflash needed. If a key
taps when you meant a hold (or the reverse), move Tapping Term by ±20 ms; that is
the single dial that matters. Note that Chordal Hold / Flow Tap only do something
if the installed RMK build implements them - if the keyboard ignores them, the
tapping term is still applied.

## Mouse keys

Two different things are at play, and only one of them is configurable from a
`.vil` on this firmware:

**1. RMK's timing is compile-time and the .vil cannot change it.** RMK exposes no
mouse-key settings over Vial - its `SettingKey` enum only covers combo, morse,
one-shot and tap ids (`2, 6, 7, 18, 19, 22, 23, 25, 26, 27`, exactly the ids this
keyboard reports). The mouse ids (`9`-`17`, delay/interval/step/max speed/ticks to
max) are still written into the files for a future RMK build, but today they are
ignored: that is why raising them changed nothing. RMK's fixed defaults are

| | |
|---|---|
| initial delay | 100 ms after the key goes down before the pointer moves |
| repeat interval | 20 ms per report |
| step | 5 px, accelerating to **3x** after 50 ticks (~1 s of holding) |
| clamp | 25 px per report |

So "hold and it speeds up" already happens - it just tops out at 750 px/s.

**2. The ACL keys are the lever that works**, and they multiply whatever the ramp
produced: `KC_ACL0` = 0.25x, `KC_ACL1` = 0.5x, `KC_ACL2` = **2x** (if several are
held the fastest wins). Held with the left thumb while the right hand steers:

| Key | Keycode | Effect |
|---|---|---|
| middle thumb (Space/Nav position) | `KC_ACL2` | 10 px per report at first, 25 px/s clamp at full ramp -> 500 -> 1250 px/s. **Hold this to fly.** |
| inner thumb (Esc/Media position) | `KC_ACL1` | half speed for fine aiming |
| inner palm | `KC_ACL0` | quarter speed, pixel hunting |
| outer thumb (the `LT5(KC_TAB)` key that holds the layer) | `KC_ACL2` | never fires - it is busy holding the layer |

Before this fix the three thumbs were `ACL0/ACL1/ACL2` left to right, which put
the *only* fast key on the layer-hold thumb: every reachable accel key then made
the pointer **slower**. That is why the mouse still felt bad after the settings
bump. `--no-mouse-tune` drops the settings block, the ACL keys and nothing else.

If even 1250 px/s is too slow, the fix has to happen in the firmware
(`BehaviorConfig::mouse_key`: `repeat_interval_ms` 20 -> 8,
`move_delta` 5 -> 10, `max_speed` 3 -> 4, `ticks_to_max` 50 -> 15,
`move_max` 25 -> 60) - that means building and flashing RMK, which is out of
scope for this repo.

## Known gaps (nothing fatal, all fixable in the Vial UI)

- Miryoku's `&bt` / output-toggle keys are `KC_NO`: RMK's custom keycodes come
  from the firmware, so pick them from Vial's **Custom** section (the FUN layer's
  outer column already uses `USER00`–`USER02` for that).
- `U_EP_TOG` (external power) has no equivalent → `KC_NO`.
- `CW_TOGG` (caps word) is blanked to `KC_NO` in the shipped files, and so are the
  `RGB_*` keys on the MEDIA layer: this RMK build does not implement them.
- The EXTRA layer equals BASE with empty thumbs, which is exactly what
  `miryoku_zmk` generates for QWERTY/Colemak-DH.
- Clipboard keys use the macOS variant (`LGUI` = ⌘). For Windows/Linux edit
  `CLIPBOARD` in `make_miryoku_vil.py` to `LCTL(...)` and regenerate.

## Hand edits that live in the generator

Changes made in Vial / vial.rocks are recorded in `USER_PATCHES` in
`make_miryoku_vil.py`, so a regeneration reproduces the keymap that is actually
on the keyboard instead of silently reverting to stock Miryoku:

| Layer | Key | Keycode | What it is |
|---|---|---|---|
| BASE | top row, outer-left | `SGUI(KC_4)` | ⌘⇧4 screenshot |
| BASE | outer palm, left | `LALT(KC_Z)` | ⌥Z |
| NAV | home row, outer-left | `KC_NO` | caps word removed |
| MOUSE | top row (right hand) | `LCTL(KC_LEFT/UP/DOWN/RIGHT)` | macOS window / desktop-space keys instead of the clipboard shortcuts |
| MOUSE | home row (right hand) | `KC_WH_D`, `KC_WH_U` | scroll direction flipped (ids 3 and 4 of the right home row) |
| MEDIA | top row (right hand) | `KC_NO` | `RGB_*` blanked |
| FUN | outer column, left | `USER00`–`USER02` | firmware custom keycodes |

Add a row there rather than editing a generated `.vil` by hand, otherwise the
next regeneration loses it. `vial/current.vil` is the export these were taken
from and doubles as a safe `--template`.

## Regenerate

```bash
# exactly what was shipped (vial/current.vil is the export used as template)
python3 make_miryoku_vil.py --alphas qwerty --swap gui,ctrl --nav vi --mouse vi \
        --template current.vil -o cornix-miryoku-qwerty.vil

# variations
python3 make_miryoku_vil.py --alphas colemakdh --swap gui,ctrl --nav vi --mouse vi
python3 make_miryoku_vil.py --alphas qwerty                      # default Miryoku mods/nav
python3 make_miryoku_vil.py --alphas qwerty --swap gui,lsft      # Command on the index finger
python3 make_miryoku_vil.py --alphas qwerty --nav invertedt --mouse vi
python3 make_miryoku_vil.py --alphas qwerty --drop inner         # empty the centre columns
python3 make_miryoku_vil.py --alphas qwerty --encoder-clicks none,none
```

`--alphas` accepts any `MIRYOKU_ALTERNATIVES_BASE_*` suffix: `qwerty`,
`colemak`, `colemakdh`, `dvorak`, `workman`, `halmak`, `beakl15`, `azerty`, …
The generator exits with an error if a Miryoku token has no Vial translation and
validates every produced keycode against `vial_names.txt`.
