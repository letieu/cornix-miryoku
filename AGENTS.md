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
- Home-row-mod tuning: tapping term 200 ms, flow tap 150 ms, permissive hold on,
  hold-on-other-key-press off, chordal hold on (`--hrm-tune`, on by default).
- Encoder push buttons stay `KC_MUTE` / `KC_BTN3`.
- **Mouse keys are tuned faster than RMK's defaults** (`--mouse-tune`): delay 40 ms,
  interval 14 ms, step 7 px, max speed 4x, and the left thumbs on the MOUSE layer
  hold `KC_ACL0/ACL1/ACL2` so speed can be halved/boosted on the fly.
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

## Out of scope unless asked

- `~/code/personal/zmk-keyboard-cornix` (the upstream board module) — read-only
  reference; keep edits here.
- Flashing, bootloader recovery, RMK/ZMK firmware builds.
