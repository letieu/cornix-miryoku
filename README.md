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
| `config/cornix.conf` | Kconfig for the halves - enables `CONFIG_ZMK_POINTING` so the MOUSE layer's `&mmv`/`&msc`/`&mkp` behaviors exist |
| `config/cornix_dongle_adapter.conf` | Same for the dongle build (the dongle is the central that sends the mouse reports) |
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

## Mouse keys (ZMK path)

Miryoku's MOUSE layer is built on ZMK's pointing behaviors, which are only
compiled in with `CONFIG_ZMK_POINTING=y` - `config/cornix.conf` and
`config/cornix_dongle_adapter.conf` enable it. Without them the layer is dead.

Speed is a first-class setting in ZMK (`zmk,behavior-input-two-axis`), overridden
at the end of `config/cornix.keymap`:

| Property | ZMK default | Miryoku | Shipped here |
|---|---|---|---|
| `acceleration-exponent` | 1 | 1 | **1** (0 = constant, 2 = jerk) |
| `time-to-max-speed-ms` | 300 | **1500** | **300** - full speed after 0.3 s |
| `delay-ms` | – | 0 | **0** |
| `trigger-period-ms` | 16 | 16 | **8** - ~125 reports/s |

Max speed is the binding value: Miryoku sets `ZMK_POINTING_DEFAULT_MOVE_VAL`
to **1250 px/s** (scroll 100), which is already ~1.7x what the RMK firmware does
without an `ACL2` key held. To go beyond that you need your own behavior with a
bigger value - the commented example at the bottom of `config/cornix.keymap`
shows how.

Trade-off against the Vial path: every mouse tweak here means a rebuild plus a
flash of both halves (or the dongle), whereas the `.vil` route is instant but
capped at RMK's compile-time timing. See [vial/README.md](vial/README.md#mouse-keys)
for the RMK numbers.

## Build locally (no GitHub Actions)

`scripts/build-local.sh` reproduces what the workflow does: it creates a west
workspace (`$ZMK_WORKSPACE`, default `~/zmk-cornix-ws`), syncs `config/` into it
(the manifest is `config/west.yml`), fetches ZMK + Zephyr + the board module +
`miryoku_zmk`, and runs `west build` per artifact with `-DZMK_CONFIG`.

```bash
./scripts/build-local.sh                # left + right
./scripts/build-local.sh all            # left right ph_left dongle reset
./scripts/build-local.sh dongle         # one target
PRISTINE=1 ./scripts/build-local.sh all # clean rebuild
```

Output: `~/zmk-cornix-ws/build/<target>/zephyr/zmk.uf2`.

### One-time toolchain setup (macOS, Apple Silicon)

```bash
# 1. host deps for Zephyr 4.1
brew install cmake ninja gperf dtc wget libmagic

# 2. west in a venv
python3 -m venv ~/.venvs/zmk && source ~/.venvs/zmk/bin/activate
pip install -U west

# 3. Zephyr SDK - only the ARM toolchain is needed; 0.17.4 matches Zephyr 4.1
curl -LO https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.17.4/zephyr-sdk-0.17.4_macos-aarch64_minimal.tar.xz
tar xf zephyr-sdk-0.17.4_macos-aarch64_minimal.tar.xz -C ~/
~/zephyr-sdk-0.17.4/setup.sh          # sets ZEPHYR_SDK_INSTALL_DIR

# 4. build (first run also runs `west init`/`west update`, ~2 GB, be patient)
./scripts/build-local.sh left right
```

Notes:

- Activate the venv (`source ~/.venvs/zmk/bin/activate`) in every new shell; the
  script only checks that `west` is on `PATH`.
- If your CMake is v4 and Zephyr trips over `libmetal`, install `cmake@3` and put
  it in front of `PATH`.
- `west sdk install -t arm-zephyr-eabi` is an alternative to step 3 once the
  workspace exists; it picks the SDK version Zephyr asks for.
- Verify the mouse build actually happened:
  `grep CONFIG_ZMK_POINTING build/left/zephyr/.config`.
- Incremental builds take ~1 min per target; `west build -d build/left` alone
  re-runs the last configuration.

## Flashing

1. Build with GitHub Actions (push, or run the workflow manually).
2. Download the artifact zip for each role.
3. USB-C cable into a half, double-tap RESET, drag the matching `.uf2` onto the
   `NICENANO` volume. Firmware is writeable over USB only, never over BLE.
4. If you are switching firmware family (e.g. from stock RMK), flash
   `cornix_miryoku_reset.uf2` to a half first, then its firmware, then re-pair.
