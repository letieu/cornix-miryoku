# Miryoku for the Cornix

ZMK firmware that puts the [Miryoku](https://github.com/manna-harbour/miryoku)
layout on the Cornix (`jzf/cornix_*` boards from
[hitsmaxft/zmk-keyboard-cornix](https://github.com/hitsmaxft/zmk-keyboard-cornix)).

## Agent / automation notes

`AGENTS.md` records the settled preferences (outer columns empty, Cmd/Control
swap, vim nav, HRM timings) and the rules for changing the keymap. The skill at
`.agents/skills/cornix-miryoku-keymap/` carries the deeper how-to (matrix map,
`.vil` format, generator flags); run `/skill:cornix-miryoku-keymap` from this
folder in pi to force-load it.

Handy: `python3 vial/preview.py vial/cornix-miryoku-qwerty.vil --settings`
prints the whole layout as a keyboard picture without needing Vial.

## Files

| File | Purpose |
|---|---|
| `config/cornix.keymap` | Includes Miryoku; put layout options (`#define MIRYOKU_ALPHAS_QWERTY`, ...) here |
| `config/includes/miryoku_cornix.h` | Maps Miryoku's 36 keys onto the Cornix 50-position transform |
| `config/west.yml` | Pulls in ZMK main, the Cornix board module, and miryoku_zmk |
| `build.yaml` | Artifacts: left, right, dongle-left, dongle, settings-reset |

## Mapping notes

Miryoku uses 5 columns per hand; the Cornix has 6, so the innermost main column
is `&none`, plus the two inner keys and the 3+3 palm keys are unused:

```
   pinkie ring middle index inner  x   x  inner index middle ring pinkie
   pinkie ring middle index inner  x   x  inner index middle ring pinkie
   pinkie ring middle index inner  x x x x  inner index middle ring pinkie
                    palm palm palm  T  T  T  T  T  T palm palm palm
```

To drop the outer pinkie column instead, move the `XXX` placeholders in
`config/includes/miryoku_cornix.h` to the start of the left rows and the end of
the right rows.

## Vial / no-flash option

If the keyboard is still on the stock **RMK + Vial** firmware you do not need
any of the above: load `vial/cornix-miryoku-qwerty.vil` (or
`-colemakdh.vil`) in Vial over USB and the keymap is written to the keyboard
without flashing. See [vial/README.md](vial/README.md).

## Flashing

1. Build with GitHub Actions (push, or run the workflow manually).
2. Download the artifact zip for each role.
3. USB-C cable into a half, double-tap RESET, drag the matching `.uf2` onto the
   `NICENANO` volume. Firmware is writeable over USB only, never over BLE.
4. If you are switching firmware family (e.g. from stock RMK), flash
   `cornix_miryoku_reset.uf2` to a half first, then its firmware, then re-pair.
