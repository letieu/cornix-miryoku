# AGENTS.md — Cornix Miryoku keymap workspace

This repo holds the user's **Miryoku layout for a Cornix keyboard** in two forms:

| Path | What |
|---|---|
| `vial/` | `.vil` layout files for the stock **RMK + Vial** firmware — this is what the user actually runs. **No flashing, ever** (see below). |
| `config/`, `build.yaml`, `.github/` | ZMK build of the same layout (alternative path, needs a one-time UF2 flash). |

The keyboard's firmware is RMK with Vial enabled (`vendorId 0x4C4B`,
`productId 0x4643`, 8×7 matrix grid, **10 layers**). Vial talks to it **over USB
only** — Bluetooth can never write a keymap or receive a firmware flash. Never
suggest flashing as a way to change a keymap.

Detailed knowledge lives in the skill
`.agents/skills/cornix-miryoku-keymap/SKILL.md` (read it before making keymap
changes) and the human docs in `README.md`, `vial/README.md`.

## User's settled preferences (do not silently change)

- QWERTY base layer (a Colemak-DH copy is also shipped).
- **Empty keys go on the outer columns** (leftmost/rightmost of the board).
  The user explicitly rejected holes next to the centre: `--drop outer` is the
  default and must stay so.
- **Cmd and Ctrl swapped** on the home row (macOS: Command under the middle
  finger, Control on the pinkie): `--swap gui,ctrl`.
- **Vim-style nav *and* mouse layers** (`MIRYOKU_NAV_VI` / `MIRYOKU_MOUSE_VI`):
  `--nav vi --mouse vi`. Both must use the same flavour, otherwise the mouse keys
  sit one column outward from the arrows and the hjkl muscle memory breaks.
- Home-row-mod tuning (.vil side): tapping term 200 ms, flow tap 150 ms,
  permissive hold on, hold-on-other-key-press off, chordal hold on (`--hrm-tune`,
  on by default). The **ZMK** side deliberately does not use a timer-first setup:
  it uses urob's "timeless" HRMs (`hml`/`hmr`: balanced flavor, 280 ms,
  quick-tap 175, require-prior-idle 150, positional lists per hand,
  `hold-trigger-on-release`). RMK cannot do positional hold-taps, so the two
  firmwares differ here by design.
- Encoder push buttons stay `KC_MUTE` / `KC_BTN3`.
- The user's own hand edits live in `USER_PATCHES` in the generator: screenshot
  `SGUI(KC_4)` and `LALT(KC_Z)` on the left outer column/palm, `CW_TOGG` and the
  MEDIA `RGB_*` keys blanked, `LCTL(KC_LEFT/UP/DOWN/RIGHT)` on the MOUSE layer's
  top row (macOS window keys instead of clipboard), scroll direction flipped on
  the MOUSE home row, and `USER00`–`USER02` on the FUN outer column.
  `vial/current.vil` is the export they came from — keep it in sync when the user
  hands over a new one instead of hand-editing a generated `.vil`.
- **Mouse keys**: RMK's Vial implementation has **no mouse-key settings** (its
  `SettingKey` enum stops at combo/morse/tap ids), so ids 9–17 in the `.vil` are
  inert — the generator still writes them for a future build. The only working
  lever is `KC_ACL0/1/2` (0.25x / 0.5x / **2x**, highest held wins) and placement
  matters: the 2x key must **not** be the outer left thumb, because that is the
  `LT5(KC_TAB)` key held to activate the MOUSE layer and never emits its own
  keycode. Shipped: middle thumb `KC_ACL2` (hold to fly), inner thumb `KC_ACL1`,
  inner palm `KC_ACL0`. RMK's fixed timing (5 px / 20 ms, 3x ramp over ~1 s,
  25 px cap) can only be changed by rebuilding and flashing the firmware.
- Shortcut combos stay `LGUI(...)` (Cmd+C/X/V/Z) even though the mod positions
  are swapped.

## Rules for changes

1. Regenerate with `vial/make_miryoku_vil.py`, never by hand-editing the grid,
   unless you are only patching a couple of cells.
2. **Always keep the user's real Vial export as `--template`** so `uid`,
   `settings`, encoder rotation, tap-dance/combo slots survive. Regenerating
   without a template injects a placeholder uid and Vial may refuse the file.
   Ask the user for `File → Save current layout` output if none exists.
3. After generating: run `python3 vial/preview.py <file>` and show the user the
   resulting picture, then tell them to load the `.vil` in Vial over USB and
   what to verify.
4. Loading a `.vil` overwrites manual edits made in Vial — warn about that and
   remind them to export first if they tuned something by hand.
5. Verify every generated keycode is a real Vial keycode (the generator does this
   against `vial/vial_names.txt`; do not bypass it).
6. Keep the shipped filenames: `vial/cornix-miryoku-qwerty.vil` and
   `vial/cornix-miryoku-colemakdh.vil`. Commit changes to this repo.

## ZMK path (alternative firmware)

- The ZMK layers are **generated from the Vial export**: `python3
  scripts/gen_zmk_keys.py` writes `config/includes/miryoku_keys_generated.h`
  (10 `MIRYOKU_LAYER_*` macros) from `vial/cornix-miryoku-qwerty.vil`, so the
  Cmd/Ctrl swap, hand edits and mouse tweaks stay identical on both sides. Never
  hand-edit the generated header; edit the `.vil` (or `USER_PATCHES`) and
  regenerate. `--vil <file> -o <header>` switches alphas.
- ZMK has no equivalent for RMK's `KC_ACL*` and `USERnn`, so those become
  `&none`; mouse speed is `ZMK_POINTING_DEFAULT_MOVE_VAL` (1250 px/s) plus the
  `&mmv` override in `config/cornix.keymap` (300 ms ramp, 8 ms reports).
- `config/cornix.keymap` owns the `keymap` node itself (no `miryoku.dtsi`): the
  layers come from `scripts/gen_zmk_keys.py` and each layer carries
  `sensor-bindings`, which Miryoku's node cannot provide - without it the rotary
  encoders do nothing. Encoders: left = volume, right = `&msc` wheel.
- LEDs: two WS2812 on SPI3 behind `EXT_POWER`, both disabled in the board
  devicetree; `config/includes/cornix_leds.overlay` (included by the per-half
  `cornix_*.overlay`) enables them, and `config/cornix_*.conf` adds the RGB
  underglow Kconfig. Keep the RGB settings out of `cornix.conf`: the dongle build
  picks that file up too and has no strip (build error "A zmk,underglow chosen
  node must be declared").
- Bluetooth: the `.vil`'s `USER00`-`USER02` are RMK custom keycodes; the generator
  maps them to `&bt BT_SEL 0/1/2` so profile switching works on ZMK.
- Split roles: the **left half is the central** and holds keymap + transform, so
  a mapping change only needs the left half reflashed. The dongle build is the
  central in a dongle setup.
- Bootloader facts (learned the hard way): the volume is named `cornix`, not
  `NICENANO`; the firmware is **no-SoftDevice** (`FLASH_LOAD_OFFSET=0x1000`, the
  stock RMK image is at 0x1000 too) so the s140 restore in the board module's
  `bootloader/README.md` is *not* needed; on newer macOS the volume mounts
  read-only (`fsck` says clean, `mount -o rw` refuses) so flash with
  `scripts/flash-uf2-raw.sh`, which exploits the bootloader parsing every
  512-byte write as a UF2 block.
- The GitHub Action is deliberately disabled (`.github/workflows/build.yml.disabled`);
  artifacts come from `scripts/build-local.sh` and live in `firmware/`.
- Build locally with `scripts/build-local.sh` (Zephyr SDK **0.16.9** and a CMake
  v3 in `~/.venvs/zmk`; SDK 0.17.x breaks Zephyr 4.1's picolibc glue).

## Out of scope unless asked

- `~/code/personal/zmk-keyboard-cornix` (the upstream board module) — read-only
  reference; keep edits here.
- Flashing, bootloader recovery, RMK/ZMK firmware builds.
