# Miryoku for the Cornix in Vial (no flashing)

Miryoku on the stock/RMK **Vial** firmware. Nothing gets flashed: dropping the
`.vil` file into Vial writes the keymap into the keyboard over USB and it stays
there.

| File | What it is |
|---|---|
| `cornix-miryoku-qwerty.vil` | 10 Miryoku layers, QWERTY base |
| `cornix-miryoku-colemakdh.vil` | 10 Miryoku layers, Colemak Mod-DH base |
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
| **column 0 of each half** (leftmost / rightmost of the keyboard) | `KC_NO` — the empty column is on the outside, the centre stays fully usable. Regenerate with `--drop inner` to empty the columns next to the centre gap instead |
| thumb fans columns 3,4,5 | Esc(Media) Space(Nav) Tab(Mouse) ǀ Enter(Sym) Bspc(Num) Del(Fun) |
| 3+3 palm keys, inner keys | `KC_NO` — free real estate, drop something useful in via Vial |
| 2 encoder push buttons | kept as `KC_MUTE` / `KC_BTN3` on every layer (they were that in your export) |

Layers: `0 BASE, 1 EXTRA, 2 TAP, 3 BUTTON, 4 NAV, 5 MOUSE, 6 MEDIA, 7 NUM, 8 SYM, 9 FUN`
— the numbering Miryoku's own `LT<n>()`/`TO(n)` references expect. Your firmware
already reports 10 layers, so no firmware change is needed.

## Known gaps (nothing fatal, all fixable in the Vial UI)

- Miryoku's `&bt` / output-toggle keys are `KC_NO`: RMK's custom keycodes come
  from the firmware, so pick them from Vial's **Custom** section (your current
  keymap uses `USER00`–`USER02` on its BT layer — those are the same slots).
- `U_EP_TOG` (external power) has no equivalent → `KC_NO`.
- `CW_TOGG` (caps word) and `RGB_*` keys are written; if the RMK build does not
  implement them they simply do nothing.
- The EXTRA layer equals BASE with empty thumbs, which is exactly what
  `miryoku_zmk` generates for QWERTY/Colemak-DH.
- Clipboard keys use the macOS variant (`LGUI` = ⌘). For Windows/Linux edit
  `CLIPBOARD` in `make_miryoku_vil.py` to `LCTL(...)` and regenerate.

## Regenerate

```bash
python3 make_miryoku_vil.py --alphas colemakdh --template ~/Downloads/a.vil \
        -o cornix-miryoku-colemakdh.vil
python3 make_miryoku_vil.py --alphas qwerty --drop outer      # pinkie column unused instead
python3 make_miryoku_vil.py --alphas qwerty --encoder-clicks none,none
```

`--alphas` accepts any `MIRYOKU_ALTERNATIVES_BASE_*` suffix: `qwerty`,
`colemak`, `colemakdh`, `dvorak`, `workman`, `halmak`, `beakl15`, `azerty`, …
The generator exits with an error if a Miryoku token has no Vial translation and
validates every produced keycode against `vial_names.txt`.
