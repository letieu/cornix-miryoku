# Prebuilt firmware

Built from this repository — this folder is the source of truth for flashing, the
same bits as `gh workflow run` would produce (only the compiler host differs).

| File | Board / shield | Flash / RAM | Use |
|---|---|---|---|
| `left-central.uf2` | `cornix_left//zmk` + `studio-rpc-usb-uart` | 276 K / 82 K | left half, standard split — **the central** |
| `right-peripheral.uf2` | `cornix_right//zmk` + `cornix_indicator` | 200 K / 44 K | right half (peripheral) |
| `left-peripheral-dongle.uf2` | `cornix_ph_left//zmk` | 200 K / 44 K | left half when a dongle is the central |
| `dongle-central.uf2` | `nice_nano//zmk` + `cornix_dongle_adapter` | 264 K / 82 K | USB dongle build (display off) |
| `settings-reset.uf2` | `cornix_right//zmk` + `settings_reset` | 58 K | clears NVS / BLE bonds |

Contents: ZMK `main` + `zmk-keyboard-cornix` (no `miryoku_zmk` needed any more),
layers generated from `vial/cornix-miryoku-qwerty.vil` (`scripts/gen_zmk_keys.py`),
urob-style timeless home-row mods, `&mmv` mouse-speed override, rotary encoders
(volume / wheel), battery/connection LED indicators (`cornix_indicator` shield),
Bluetooth profile keys,
and **ZMK Studio** for live remapping over USB. No SoftDevice — the image links at `0x1000`,
like the stock RMK firmware.

## Provenance

| | |
|---|---|
| repo commit | `aefc946` (see `git log -- firmware/`) |
| ZMK revision | `main` |
| Zephyr | 4.1.0 |
| Zephyr SDK | 0.16.9 (`arm-zephyr-eabi`) |
| host | macOS arm64, CMake 3.31.6 |
| checksums | `SHA256SUMS` |

## Flashing

See [`../FLASHING.md`](../FLASHING.md). Short version, per half
(`cornix` volume = bootloader, double-tap RESET):

```bash
sudo scripts/flash-uf2-raw.sh firmware/left-central.uf2     # left half
sudo scripts/flash-uf2-raw.sh firmware/right-peripheral.uf2 # right half
```

Only the left half needs reflashing for keymap changes — the right half is a
peripheral and does not compile the keymap.

## Rebuilding

```bash
source ~/.venvs/zmk/bin/activate
./scripts/build-local.sh all      # rebuilds and refreshes this folder + SHA256SUMS
```

Never edit a UF2 by hand; change the `.vil` (or `config/`), regenerate, rebuild.
Stock RMK rollback images are collected by `scripts/prepare-rollback.sh` into
`firmware/rollback/`, which is git-ignored on purpose (vendor binaries).
