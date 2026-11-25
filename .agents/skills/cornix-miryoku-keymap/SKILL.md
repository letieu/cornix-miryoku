---
name: cornix-miryoku-keymap
description: Change, regenerate, inspect or debug the Miryoku keymap of the user's Cornix split keyboard (Vial .vil files, RMK firmware, or the alternative ZMK build). Use for any request to remap keys, move modifiers, edit layers, tune home-row mods/tapping term, add macros/combos, or explain what a key does.
---

# Cornix Miryoku keymap

The user's keyboard is a **Cornix** (3×6 columns per half + 6 bottom-row keys per
half + 2 inner keys, 50 keys, 2 encoders), running the stock **RMK firmware with
Vial support**. The Miryoku layout is shipped as `.vil` files that get loaded
into Vial over USB — no compiling, no flashing.

Read `references/hardware.md` (matrix map, which cells exist, finger columns)
and `references/vil-format.md` (`.vil` schema, keycode notation, settings IDs)
before editing. Everything below assumes the repo checkout that contains this
skill at `~/code/personal/cornix-miryoku`.

## Decide the path first

| Request | Path |
|---|---|
| "change a key / layer / modifier / timing" (normal case) | regenerate or patch the `.vil`, user loads it in Vial over USB |
| "why does this key do X" / "show me my layout" | `python3 vial/preview.py <file>` and explain |
| "I want it on ZMK / flash firmware" | `config/cornix.keymap` + `config/includes/miryoku_cornix.h`, GitHub Actions or `scripts/build-local.sh`, UF2 over USB — never over Bluetooth. Layers come from `scripts/gen_zmk_keys.py` (generated from the `.vil`), so keep the `.vil` as the source of truth. The ZMK path is also the only way to get real mouse-speed tuning: `&mmv` (`time-to-max-speed-ms`, `acceleration-exponent`, `delay-ms`, `trigger-period-ms`) needs `CONFIG_ZMK_POINTING=y` from `config/cornix.conf` |

## Standard workflow for a keymap change

1. **Get the current keymap as the template.** Ask the user for a fresh export
   (*Vial → File → Save current layout*) if their manual tweaks must be kept, or
   reuse the newest `.vil` in `vial/` / `~/Downloads`. Never regenerate without
   `--template`: the generator falls back to a placeholder `uid`, settings and
   encoder mapping, and Vial can then reject the file.
2. **Regenerate with the settled options** (`AGENTS.md` has the rationale):

   ```bash
   python3 vial/make_miryoku_vil.py \
       --alphas qwerty --swap gui,ctrl --nav vi --mouse vi \
       --template <their-export.vil> -o vial/cornix-miryoku-qwerty.vil
   ```

   Same for `--alphas colemakdh` → `vial/cornix-miryoku-colemakdh.vil`.
3. **One-off tweaks** (a single key, a `USER00`-style custom keycode, macros):
   edit the JSON directly, e.g. set `data["layout"][layer][row][col] = "KC_ESC"`.
   Keep the grid shape (8 rows × 7 cols), keep `-1` in cells that do not exist,
   keep `uid`/`settings`. Python one-liner:
   `python3 - <<'EOF' ... json.load / modify / json.dump(indent=1) ... EOF`.
4. **Validate**: run the generator's checks (it exits non-zero on an unknown
   keycode) or `python3 vial/preview.py <file> --settings`, and confirm:
   - 10 layers, each 8 rows × 7 columns,
   - `-1` only in `(r,6)` for `r ∉ {2,5}`,
   - home row still reads `LCTL_T/LALT_T/LGUI_T/LSFT_T` (left) and the mirror,
   - settings unchanged unless intended.
5. **Commit** (`git -C ~/code/personal/cornix-miryoku commit`), then tell the
   user: load the `.vil` in Vial over USB (*File → Load saved layout*), and what
   to check afterwards. Remind them the load overwrites any manual Vial edits.

## Generator reference (`vial/make_miryoku_vil.py`)

| Flag | Meaning |
|---|---|
| `--alphas qwerty\|colemakdh\|colemak\|dvorak\|workman\|halmak\|…` | base layer, suffix of `MIRYOKU_ALTERNATIVES_BASE_<X>` |
| `--drop outer` (default) | empty the outer column of each half; `--drop inner` empties the columns next to the centre (upstream Miryoku placement) |
| `--swap gui,ctrl` | swap two modifiers in mod-taps and standalone mods; accepts `gui/ctrl/alt/shift`, `cmd`, `opt`, `l/r` prefixes. Modded shortcuts `LGUI(KC_C)` are never swapped |
| `--nav vi\|invertedt`, `--mouse vi\|invertedt` | alternate Miryoku nav/mouse layers (`MIRYOKU_NAV_VI` = vim style) |
| `--hrm-tune` / `--no-hrm-tune` | write the tuned home-row-mod settings (default on) |
| `--mouse-tune` / `--no-mouse-tune` | write the mouse-key settings block (delay 30, interval 10, step 10, max speed 5x, wheel 40/50 — **inert on RMK**, which has no Vial mouse settings) and put `KC_ACL0/1/2` on the MOUSE layer's left thumbs (default on) |
| `--encoder-clicks KC_MUTE,KC_BTN3` | encoder push buttons on every layer |
| `--template <vil>` | reuse `uid`, settings, encoders, macros, tap-dance, combos |
| `-o <out.vil>` | output path |

Layer definitions come from the vendored
`vial/miryoku_layer_alternatives.h` (miryoku_zmk, MIT). The generator raises
`untranslated Miryoku token: …` when Miryoku grows a keycode it cannot map — add
the mapping to `KEYS`/`MISC`/`CLIPBOARD` in the script.

### The user's hand edits: `USER_PATCHES`

Anything the user changed by hand in Vial or vial.rocks is recorded in the
`USER_PATCHES` dict in `make_miryoku_vil.py` (`{layer name: {(row, col): keycode}}`)
and applied on top of every generated layer, for all alphas sets. Currently:
BASE `(0,0)=SGUI(KC_4)` screenshot, `(3,0)=LALT(KC_Z)`; NAV `(5,1)=KC_NO`
(caps word); MOUSE top row `LCTL(KC_LEFT/UP/DOWN/RIGHT)`, home row scroll
`KC_WH_D`/`KC_WH_U` flipped; MEDIA `RGB_*` blanked; FUN outer column
`USER00`–`USER02`.

When the user hands over a fresh export (`vial/current.vil` or a `~/Downloads`
file), diff it against the generated file **after normalising keycode aliases**
(`KC_LCTRL`==`KC_LCTL`, `KC_LSHIFT`==`KC_LSFT`, `KC_INSERT`==`KC_INS`,
`KC_PGDOWN`==`KC_PGDN`, `KC_LBRACKET`==`KC_LBRC`, `KC_PSCREEN`==`KC_PSCR`,
`KC_APPLICATION`==`KC_APP`, `SGUI(KC_X)`==`LGUI(LSFT(KC_X))`) — Vial rewrites
those spellings, they are not real changes. Encode the real differences in
`USER_PATCHES` rather than editing the `.vil`.

## Pitfalls that have already bitten

- Vial works over **USB only**; Bluetooth is not a config path.
- Layer **numbering matters**: Miryoku's `LT<n>()`/`TO(n)` reference
  `0 BASE, 1 EXTRA, 2 TAP, 3 BUTTON, 4 NAV, 5 MOUSE, 6 MEDIA, 7 NUM, 8 SYM, 9 FUN`.
  Insert/remove a layer and every layer-tap pointer moves.
- Mouse speed: RMK implements **no** mouse-key Vial settings — check
  `rmk-types/src/protocol/vial.rs` `SettingKey`: only `0x02, 0x06, 0x07, 0x12,
  0x13, 0x16, 0x17, 0x19, 0x1A, 0x1B` exist, which is exactly the settings block
  a real export contains. Ids 9–17 are therefore inert; RMK's timing is
  compile-time (`MouseKeyConfig`: 5 px / 20 ms, 3x ramp over 50 ticks, 25 px cap),
  so only changing them needs a firmware build (out of scope, no flashing).
- `KC_ACL0/1/2` multiply the ramped step by 0.25x / 0.5x / **2x**, highest held
  wins. Placement is what matters: the outer left thumb is `LT5(KC_TAB)`, held to
  activate the MOUSE layer, so whatever keycode sits there never fires. 2x must be
  the middle thumb (`(3,4)`), 0.5x the inner thumb (`(3,3)`), 0.25x a palm key.
- `--nav vi` without `--mouse vi` leaves the mouse keys one column outward from
  the arrows (the user noticed immediately); always pass both.
- Keycode spellings in an export differ from the generator's (`KC_LCTRL` vs
  `KC_LCTL`, `SGUI(Z)` vs `LGUI(LSFT(KC_Z))`); normalise before diffing, then put
  real changes into `USER_PATCHES`.
- `USER00`–`USER31` (Vial's Custom section) and `SGUI(...)` are accepted by the
  validator; add new wrapper families there if a patch uses them.
- The dead column is **deliberate** (user preference, outer columns). Do not
  "fix" it back to the centre.
- Miryoku's `&bt` / output-toggle / external-power keys have no Vial keycode;
  they are `KC_NO` and are meant to be picked in Vial's *Custom* section
  (`USER00…` on this firmware). `CW_TOGG`, `RGB_*`, `QK_BOOT` are written but may
  be no-ops depending on the RMK build.
- The `.vil` cannot carry per-key tapping-term overrides; HRM behaviour is the
  global QMK settings block plus whatever the firmware implements. On the ZMK
  side the same integers live on `&u_mt`/`&u_lt` in `config/cornix.keymap`.
- ZMK flashing: the bootloader volume is `cornix` (not `NICENANO`), the firmware
  is no-SoftDevice so the s140 restore is unnecessary, and newer macOS mounts
  the volume read-only - use `scripts/flash-uf2-raw.sh`. Only the left/central
  half needs a keymap change.
- `scripts/gen_zmk_keys.py` raises on a Vial keycode it cannot translate; add
  the mapping there instead of hand-editing `config/includes/miryoku_keys_generated.h`.
