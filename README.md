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
| `config/cornix.keymap` | Self-contained keymap: generated layers, HRMs, mouse speed, encoders |
| `config/includes/miryoku_cornix.h` | Maps Miryoku's 36 keys onto the Cornix 50-position transform (outer columns dead) |
| `config/includes/miryoku_keys_generated.h` | **Generated** layer contents from `vial/cornix-miryoku-qwerty.vil` - do not edit by hand |
| `scripts/gen_zmk_keys.py` | `.vil` -> `MIRYOKU_LAYER_*` macros, so the ZMK build carries the Vial layout |
| `scripts/build-local.sh` | Local west build of all five artifacts (halves get `-DSHIELD=cornix_indicator`) |
| `scripts/flash-uf2-raw.sh` | Flash a UF2 when macOS mounts the bootloader volume read-only |
| `scripts/prepare-rollback.sh` | Collects the stock RMK UF2s + current `.vil` into a rollback folder |
| `FLASHING.md` | Step-by-step flashing / recovery guide for both halves |
| `config/west.yml` | Pulls in ZMK main, the Cornix board module, and miryoku_zmk |
| `config/cornix.conf` | Kconfig for the halves - enables `CONFIG_ZMK_POINTING` so the MOUSE layer's `&mmv`/`&msc`/`&mkp` behaviors exist |
| `config/cornix_dongle_adapter.conf` | Same for the dongle build (the dongle is the central that sends the mouse reports) |
| `build.yaml` | Artifacts: left, right, dongle-left, dongle, settings-reset |
| `firmware/` | Prebuilt UF2s tracked in git (+ `SHA256SUMS`, provenance in `firmware/README.md`) |
| `config/cornix.conf` | Kconfig: pointing + ZMK Studio |

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

### Browser back / forward (replaces the three-finger swipe)

On the **NAV** and **MOUSE** layers the two free left cells of the inner column
(`(1,5)` home row, `(2,5)` bottom row - the inner neighbour of the left index)
are `Cmd+[` = **back** and `Cmd+]` = **forward**, the shortcuts Safari, Chrome
and Firefox all use on macOS. Hold the NAV thumb (`LT4(SPACE)`) or the MOUSE
thumb (`LT5(TAB)`) and the left inner-index finger goes back/forward with one
keypress - no trackpad, no mouse. They come from `USER_PATCHES` in
`vial/make_miryoku_vil.py`, so the `.vil` (Vial/RMK path) carries them too.

```
   NAV / MOUSE, left half
   r0 | ·   QK_BOOT  TO(2)    TO(1)    TO(0)   ·
   r1 | ·   KC_LCTL  KC_LALT  KC_LGUI  KC_LSFT  Cmd+[   <- back
   r2 | ·   ·        RALT     TO(7/8)  TO(4/5)  Cmd+]   <- forward
```

## Vial / no-flash option

If the keyboard is still on the stock **RMK + Vial** firmware you do not need
any of the above: load `vial/cornix-miryoku-qwerty.vil` (or
`-colemakdh.vil`) in Vial over USB and the keymap is written to the keyboard
without flashing. See [vial/README.md](vial/README.md).

## Mouse keys (ZMK path)

Miryoku's MOUSE layer is built on ZMK's pointing behaviors, which are only
compiled in with `CONFIG_ZMK_POINTING=y` - `config/cornix.conf` and
`config/cornix_dongle_adapter.conf` enable it. Without them the layer is dead.

Speed is a first-class setting in ZMK (`zmk,behavior-input-two-axis`): the
`&mmv` timing override at the end of `config/cornix.keymap`, plus the
`ZMK_POINTING_DEFAULT_MOVE_VAL` ceiling (2400 px/s, defined at the top of the
same file because the binding parameter *is* the max speed):

| Property | ZMK default | Miryoku | Shipped here |
|---|---|---|---|
| `acceleration-exponent` | 1 | 1 | **1** (0 = constant, 2 = jerk) |
| `time-to-max-speed-ms` | 300 | **1500** | **200** - full speed after 0.2 s |
| `delay-ms` | – | 0 | **0** |
| `trigger-period-ms` | 16 | 16 | **8** - ~125 reports/s |

Max speed is the *binding value*: `MOVE_UP` expands to
`MOVE_Y(-ZMK_POINTING_DEFAULT_MOVE_VAL)`, so the ceiling comes from that macro
at the top of `config/cornix.keymap`. ZMK's own default is **600 px/s** and that
is what the earlier builds actually ran - the 1250 in old notes came from
`miryoku_zmk`, which `config/west.yml` no longer pulls in. 600 px/s is ~4x
slower than a real mouse, so pointing felt sluggish no matter what the `&mmv`
ramp was set to. Shipped: **2400 px/s** (`#define
ZMK_POINTING_DEFAULT_MOVE_VAL 2400`) - a 60 ms tap travels ~100 px, a hold
reaches full speed in 200 ms.

Scroll is tuned separately, because `&msc` takes its value as a **rate**, not a
step: it emits `SCRL_VAL * trigger-period-ms / 1000` wheel detents per 16 ms tick
and carries the fraction over. Upstream's `ZMK_POINTING_DEFAULT_SCRL_VAL 10`
therefore means *one notch every 100 ms* - and a tap shorter than 100 ms scrolls
nothing at all, which is why the MOUSE layer's scroll keys felt slow and laggy
while still "working". Shipped: **40** (one notch per 25 ms, ~40 notches/s held)
with `&msc { acceleration-exponent = <0>; delay-ms = <0> }` so the very first
tick already carries a usable fraction. 20 = gentle, 80 = fast.

To try a different feel, change those two macros (`2400`, `40`) and rebuild; no
behaviour in the keymap needs touching. Remember the ceiling applies to every `&mmv` key in the layer, since
they all share those `MOVE_*` bindings.

Trade-off against the Vial path: every mouse tweak here means a rebuild plus a
flash of both halves (or the dongle), whereas the `.vil` route is instant but
capped at RMK's compile-time timing. See [vial/README.md](vial/README.md#mouse-keys)
for the RMK numbers.

## ZMK Studio (Vial-like keymap UI)

The firmware is built with `CONFIG_ZMK_STUDIO=y` and the `studio-rpc-usb-uart`
snippet, so after flashing you can remap keys live - no rebuild, no reflash:

1. Plug the **left half** in over USB.
2. Open <https://zmk.studio/> in Chrome/Edge (or the native app for macOS).
3. Pick the `Cornix` serial device, edit any key/layer, done.

Caveats, and why it is not a full Vial replacement:

- It assigns behaviors/keycodes to keys and renames layers. Combos, macros,
  tap-dance contents, timing (tapping term, `&mmv`) and pointing config are
  **devicetree only** - change those here in `config/` and rebuild.
- Studio writes to NVS. Once you edit in Studio, the compiled keymap is ignored
  until you press **"Restore Stock Settings"** in Studio - so treat the repo as
  the source of truth, tweak in Studio only for experiments.
- Unlocking: this build has `ZMK_STUDIO_LOCKING` off, so no `&studio_unlock` key
  is needed.

## Home-row mods: "timeless" configuration

The ZMK build uses urob's *Timeless Home Row Mods* instead of a plain 200 ms
timer — `hml`/`hmr` in `config/cornix.keymap`:

| Property | Value | Effect |
|---|---|---|
| `flavor` | `balanced` | hold fires as soon as another key is pressed *and released* while the mod is held, so you rarely wait for the timer |
| `tapping-term-ms` | 280 | only matters for a lone mod press or a same-hand mod+alpha chord |
| `quick-tap-ms` | 175 | repeated taps stay taps |
| `require-prior-idle-ms` | 150 | a mod pressed right after another key resolves as tap instantly (flow tap) |
| `hold-trigger-key-positions` | opposite half + thumbs | a same-hand roll can never become a mod |
| `hold-trigger-on-release` | on | same-hand mod+mod chording still works |

`scripts/gen_zmk_keys.py` binds the left home-row mod-taps to `&hml` and the
right ones to `&hmr` (they need mirrored position lists). Layer-taps keep
Miryoku's `tap-preferred` with the `.vil` timings, since a thumb-held layer
should not depend on the same-hand rule.

The Vial/RMK firmware on the keyboard still uses tapping term 200 +
permissive-hold + unilateral-tap: RMK's `MorseMode` is a single exclusive enum,
so it cannot express positional hold-taps. Try `QMK Settings → Tapping Term 280`
there if you want the timings to match more closely.

## Hardware: encoders, LEDs, Bluetooth

These are the things the stock RMK firmware did that ZMK does not do by default.
All three are wired up now:

**Encoders** — ZMK needs `sensor-bindings` on *every* keymap layer, which is why
including Miryoku's own `keymap` node left them dead. `config/cornix.keymap` owns
the keymap node and gives each layer:

```c
sensor-bindings = <&inc_dec_kp C_VOL_DN C_VOL_UP>, <&enc_scroll SCRL_UP SCRL_DOWN>;
```

Left knob = volume (clockwise down, as in the `.vil`), right knob = mouse wheel
via a small `zmk,behavior-sensor-rotate-var` wrapper around `&msc`. The knob
pushes are the two inner keys (`&kp C_MUTE`, `&mkp MB3`), carried over from the
`.vil`.

**LEDs** — the board has two WS2812 chips per half on SPI3 behind an `EXT_POWER`
rail, both `status = "disabled"` in the board devicetree. Rather than a
meaningless always-on underglow, the halves are built with the board's
**`cornix_indicator`** shield and the `zmk-rgbled-widget` module
(`config/west.yml`): the LEDs show battery level and split-connection state, and
the widget turns the power rail off 1 s after the animation ends
(`CONFIG_RGBLED_WIDGET_EXT_POWER_TIMEOUT_MS`). `CONFIG_ZMK_RGB_UNDERGLOW` stays
off, so there is no red glow competing with the indicator.

**Checking the battery** — three ways, in order of convenience:

1. **Left palm, middle key (`&ind_bat`)** — blinks each half's battery colour in
   turn (green ≥80 %, yellow ≥20 %, red below, threshold constants in
   `CONFIG_RGBLED_WIDGET_BATTERY_LEVEL_*`). The central also reports the
   peripheral's level (`CONFIG_RGBLED_WIDGET_BATTERY_SHOW_PERIPHERALS=y`), so one
   press covers both halves; a magenta blink means that part is disconnected.
2. **Left palm, inner key (`&ind_con`)** — connection/profile state (green/red/
   blue/yellow/magenta = BT profile 0-4, cyan = USB).
3. **Passive**: each half blinks its own level on boot, and below 5 % it blinks
   red whenever the level changes.

macOS only ever sees the *central's* battery (HID battery report), so for numbers
use the LEDs; there is no per-half percentage in the host UI or in ZMK Studio.

**Bluetooth** — the `.vil`'s `USER00`–`USER02` on the FUN outer column were the
RMK custom keycodes for Bluetooth slots. The generator now maps them to ZMK's
real behaviours (`&bt BT_SEL 0/1/2`), so profile switching works again; `&out
OUT_USB/OUT_BLE` and `&bt BT_CLR` can be added anywhere you like.

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
- **Changing snippets (or the config overlays) needs `PRISTINE=1`** - Zephyr
  ignores a changed `SNIPPET` on an existing build directory ("The build
  directory must be cleaned pristinely when changing snippet"). Studio's
  `studio-rpc-usb-uart` snippet is exactly this case; without a pristine build
  the firmware silently gets no USB serial endpoint and `zmk.studio` cannot
  connect.
- The script pins the Zephyr **0.16.x** SDK even if your shell exports a 0.17.x
  `ZEPHYR_SDK_INSTALL_DIR` (0.17 breaks Zephyr 4.1's picolibc).

## Reverting to the stock RMK firmware

The nice_nano bootloader cannot read the installed firmware back out, so the
stock UF2s are the only way home. They ship with the board module:
`zmk-keyboard-cornix/rmkfw/V1.6.zip` and `V1.6.99测试版.zip`, each containing
`cornix-left.uf2` + `cornix-right.uf2` (confirmed RMK builds - the images carry
`vial:f64c2b3c` and RMK source paths).

```bash
./scripts/prepare-rollback.sh        # -> firmware/rollback/ (git-ignored)
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

1. Build with `./scripts/build-local.sh all` (already done: `firmware/` holds the
   images). The GitHub Action is **disabled** - `.github/workflows/build.yml.disabled`;
   rename it back to `build.yml` to build in the cloud instead.
2. Download the artifact zip for each role.
3. USB-C cable into a half, double-tap RESET, drag the matching `.uf2` onto the
   `cornix` volume. Firmware is writeable over USB only, never over BLE.
4. If you are switching firmware family (e.g. from stock RMK), flash
   `cornix_miryoku_reset.uf2` to a half first, then its firmware, then re-pair.
