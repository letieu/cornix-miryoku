# .vil file format (Vial → RMK firmware)

A `.vil` is JSON. Vial writes it with *File → Save current layout* and loads it
with *File → Load saved layout*; both happen over USB and land in the keyboard's
settings flash.

## Top-level keys (keep all of them)

```json
{
  "version": 1,
  "uid": 16882930253541522617,        // keyboard UID from the device - MUST come from a real export
  "layout": [ [8 rows x 7 cols], ... 10 layers ],
  "encoder_layout": [[["KC_VOLD","KC_VOLU"],["KC_WH_U","KC_WH_D"]], ... one entry per layer ],
  "layout_options": 0,
  "macro": [[], ... 32 slots ],
  "vial_protocol": 6,
  "via_protocol": 9,
  "tap_dance": [["KC_NO","KC_NO","KC_NO","KC_NO",250], ... 8 slots ],
  "combo": [["KC_NO","KC_NO","KC_NO","KC_NO","KC_NO"], ... 8 slots ],
  "key_override": [],
  "alt_repeat_key": [],
  "settings": { "7": 200, ... }       // QMK setting id -> value
}
```

`layout[layer][row][col]` is either a keycode string or `-1` for a cell that
does not exist on this board (see `hardware.md` for the mask).

## Keycode notation Vial accepts

- Plain QMK ids and their aliases: `KC_Q`, `KC_SPACE`/`KC_SPC`,
  `KC_BSPACE`/`KC_BSPC`, `KC_ENTER`/`KC_ENT`, `KC_ESCAPE`/`KC_ESC`,
  `KC_NO`, `KC_TRNS`, `KC_BTN1`, `KC_MS_U`, `KC_WH_D`, `RGB_TOG`, `CW_TOGG`,
  `QK_BOOT`, …
- Layer/masked forms: `LT0…LT15(KC_X)`, `TO(n)`, `MO(n)`, `TG(n)`, `DF(n)`,
  `OSL(n)`, `LSFT_T(KC_X)` / `LCTL_T` / `LALT_T` / `LGUI_T` / `R…` variants,
  `TD(n)`.
- Modded keys, nestable: `LGUI(KC_C)`, `LSFT(KC_7)`, `LGUI(LSFT(KC_Z))`.
- Anything Vial's parser does not know is silently useless — validate new
  names against `vial/vial_names.txt` (Vial keycode ids+aliases scraped from
  vial-gui) before shipping.

Symbols without their own QMK name in this set are written as shifted keys:
`LSFT(KC_7)` = `&`, `LSFT(KC_SCOLON)` = `:`, `LSFT(KC_MINUS)` = `_`,
`LSFT(KC_GRAVE)` = `~`, `LSFT(KC_BSLASH)` = `|`.

## Settings ids seen on this keyboard

| id | Setting | Shipped value |
|---|---|---|
| 2 | combos time-out | 50 |
| 6 | one-shot key release timeout | 1000 |
| 7 | **Tapping Term** | 200 |
| 18 | tap code delay | 20 |
| 19 | tap hold caps delay | 20 |
| 22 | **Permissive Hold** | 1 |
| 23 | **Hold On Other Key Press** | 0 |
| 26 | **Chordal Hold** | 1 |
| 27 | **Flow Tap** | 150 |

Ids come from vial-gui `src/main/resources/base/qmk_settings.json`; the keyboard
may ignore settings its RMK build does not implement. Tapping Term is the dial
that always matters for home-row mods; the user can also change all of them live
in Vial's *QMK Settings* tab.

## Gotchas

- A `.vil` replaces everything: layers, encoders, macros, tap-dance, combos and
  settings. Ask the user to export before loading if they tuned in the GUI.
- `uid` mismatch makes Vial refuse or warn. Always generate from a real export.
- The keyboard reports 10 layers; layer indices above 9 cannot be used and layer
  numbering must match Miryoku's (`0 BASE … 9 FUN`) because `LTn/TO(n)` encode
  them.
