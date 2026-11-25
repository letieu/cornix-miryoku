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
| `config/cornix.keymap` | Includes Miryoku, the generated layers and the mouse/hold-tap overrides |
| `config/includes/miryoku_cornix.h` | Maps Miryoku's 36 keys onto the Cornix 50-position transform (outer columns dead) |
| `config/includes/miryoku_keys_generated.h` | **Generated** layer contents from `vial/cornix-miryoku-qwerty.vil` - do not edit by hand |
| `scripts/gen_zmk_keys.py` | `.vil` -> `MIRYOKU_LAYER_*` macros, so the ZMK build carries the Vial layout |
| `scripts/build-local.sh` | Local west build of all five artifacts (see below) |
| `scripts/flash-uf2-raw.sh` | Flash a UF2 when macOS mounts the bootloader volume read-only |
| `scripts/prepare-rollback.sh` | Collects the stock RMK UF2s + current `.vil` into a rollback folder |
| `FLASHING.md` | Step-by-step flashing / recovery guide for both halves |
| `config/west.yml` | Pulls in ZMK main, the Cornix board module, and miryoku_zmk |
| `config/cornix.conf` | Kconfig for the halves - enables `CONFIG_ZMK_POINTING` so the MOUSE layer's `&mmv`/`&msc`/`&mkp` behaviors exist |
| `config/cornix_dongle_adapter.conf` | Same for the dongle build (the dongle is the central that sends the mouse reports) |
| `build.yaml` | Artifacts: left, right, dongle-left, dongle, settings-reset |

## Mapping notes

Miryoku uses 5 columns per hand; the Cornix has 6, so the **outermost** column of
each half is `&none` (same as the Vial layout - keep it that way), plus the two
inner keys and the 3+3 palm keys are unused:

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

Verified working on macOS 27.3 / arm64 (all five artifacts build, see sizes below).

```bash
# 1. host deps for Zephyr 4.1
brew install cmake ninja gperf dtc wget libmagic

# 2. west + a CMake v3 (Zephyr 4.1's FindZephyr-sdk.cmake breaks on CMake 4)
python3 -m venv ~/.venvs/zmk && source ~/.venvs/zmk/bin/activate
pip install -U west "cmake==3.31.6"

# 3. Zephyr SDK - MUST be 0.16.9 (what ZMK's CI image uses). 0.17.x ships a
#    picolibc whose sys/lock.h collides with Zephyr 4.1:
#    "conflicting types for '__lock___libc_recursive_mutex'"
cd ~
for f in zephyr-sdk-0.16.9_macos-aarch64_minimal.tar.xz \
         toolchain_macos-aarch64_arm-zephyr-eabi.tar.xz; do
  curl -sLO "https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.9/$f"
done
tar xf zephyr-sdk-0.16.9_macos-aarch64_minimal.tar.xz
tar xf toolchain_macos-aarch64_arm-zephyr-eabi.tar.xz -C zephyr-sdk-0.16.9
~/zephyr-sdk-0.16.9/setup.sh -c

# 4. build (first run also runs `west init`/`west update`, ~2 GB, be patient)
./scripts/build-local.sh left right
```

Notes:

- Activate the venv (`source ~/.venvs/zmk/bin/activate`) in every new shell; the
  script only checks that `west` is on `PATH` and auto-detects `~/zephyr-sdk-0.16.*`.
- The SDK bundle on its own is only the setup script; the arm toolchain is a
  separate 94 MB download (step 3). Never run `setup.sh` without arguments - it
  goes interactive and appears to hang.
- Verified artifact sizes: left 269 KB flash / 74 KB RAM, right & ph_left 192 KB /
  38 KB, dongle 273 KB / 82 KB, settings_reset 58 KB.
- The dongle build disables the display (`config/cornix_dongle_adapter.conf`):
  the adapter shield sets `CONFIG_ZMK_DISPLAY=y` but the panel lives on the
  optional `cornix_dongle_eyelash` shield, so without that overlay the build dies in
  `src/display/main.c`.
- Verify the mouse build actually happened:
  `grep -E 'CONFIG_ZMK_POINTING|CONFIG_INPUT=' build/left/zephyr/.config`, and the
  overlay: `grep -A8 'mmv: mouse_move' build/left/zephyr/zephyr.dts`
  (expect `time-to-max-speed-ms = < 0x12c >`, `trigger-period-ms = < 0x8 >`).
- Incremental builds take ~1 min per target; `west build -d build/left` alone
  re-runs the last configuration.

## Reverting to the stock RMK firmware

The nice_nano bootloader cannot read the installed firmware back out, so the
stock UF2s are the only way home. They ship with the board module:
`zmk-keyboard-cornix/rmkfw/V1.6.zip` and `V1.6.99测试版.zip`, each containing
`cornix-left.uf2` + `cornix-right.uf2` (confirmed RMK builds - the images carry
`vial:f64c2b3c` and RMK source paths).

```bash
./scripts/prepare-rollback.sh        # -> ~/Downloads/cornix-rollback/
ZIP=../zmk-keyboard-cornix/rmkfw/V1.6.99测试版.zip ./scripts/prepare-rollback.sh
```

That folder ends up with the stock left/right UF2s, a ZMK `settings_reset` UF2, the
current `.vil` and `ROLLBACK.txt` with checksums. Recovery is then:

1. Per half: USB-C in, **double-tap RESET**, a volume named `cornix` appears, drag
   the UF2 on (or use `scripts/flash-uf2-raw.sh` if macOS mounts it read-only). The bootloader sits in a protected part of the chip and no UF2 here
   touches it, so this escape hatch works even if the flashed firmware is
   completely dead (no USB, no BLE, nothing).
2. If you came from ZMK, flash `settings_reset` to one half first, then the stock
   firmware - stale NVS/BLE bonds are the usual cause of "it powers on but types
   nothing".
3. On the host, delete the old Bluetooth entry for the keyboard and re-pair.
4. Vial over USB -> **File → Load saved layout** -> `cornix-miryoku-qwerty.vil`
   (Vial rewrites the whole keymap and the QMK settings block, so RMK's leftover
   storage does not matter).

Do this once now, before flashing anything: having the folder ready is what makes
a bad flash a two-minute problem instead of a lost evening.

## Flashing

1. Build with GitHub Actions (push, or run the workflow manually).
2. Download the artifact zip for each role.
3. USB-C cable into a half, double-tap RESET, drag the matching `.uf2` onto the
   `cornix` volume. Firmware is writeable over USB only, never over BLE.
4. If you are switching firmware family (e.g. from stock RMK), flash
   `cornix_miryoku_reset.uf2` to a half first, then its firmware, then re-pair.
