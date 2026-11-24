# Miryoku for the Cornix

ZMK firmware that puts the [Miryoku](https://github.com/manna-harbour/miryoku)
layout on the Cornix (`jzf/cornix_*` boards from
[hitsmaxft/zmk-keyboard-cornix](https://github.com/hitsmaxft/zmk-keyboard-cornix)).

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

## Flashing

1. Build with GitHub Actions (push, or run the workflow manually).
2. Download the artifact zip for each role.
3. USB-C cable into a half, double-tap RESET, drag the matching `.uf2` onto the
   `NICENANO` volume. Firmware is writeable over USB only, never over BLE.
4. If you are switching firmware family (e.g. from stock RMK), flash
   `cornix_miryoku_reset.uf2` to a half first, then its firmware, then re-pair.
