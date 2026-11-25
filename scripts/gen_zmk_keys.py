#!/usr/bin/env python3
"""Generate ZMK layer macros from a Vial .vil export.

The ZMK build (config/cornix.keymap) uses miryoku_zmk, whose layers come from
MIRYOKU_ALTERNATIVES_* macros in the module. miryoku_layer_selection.h honours
MIRYOKU_LAYER_<NAME> if it is already defined, so this script writes those
defines from the .vil the user actually runs - mod swaps, hand edits, mouse and
scroll tweaks all carry over, and there is no second place to keep in sync.

    python3 scripts/gen_zmk_keys.py                        # qwerty
    python3 scripts/gen_zmk_keys.py --vil vial/cornix-miryoku-colemakdh.vil \
            -o config/includes/miryoku_keys_colemakdh.h

Vial keycodes map to ZMK bindings:
    KC_A                -> &kp A
    LCTL_T(KC_A)        -> &mt LCTL A          (mod-tap)
    LT5(KC_TAB)         -> &lt 5 TAB           (layer-tap, layer numbers match)
    TO(0)               -> &to 0
    LGUI(KC_C)          -> &kp LG(C)
    SGUI(KC_4)          -> &kp LG(LS(N4))
    KC_MS_U             -> &mmv MOVE_UP
    KC_WH_D             -> &msc SCRL_DOWN
    KC_BTN1             -> &mkp MB1
    QK_BOOT             -> &bootloader
    KC_ACL0/1/2, USERnn -> &none  (no ZMK equivalent: RMK-only features)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

LAYERS = ["BASE", "EXTRA", "TAP", "BUTTON", "NAV", "MOUSE", "MEDIA", "NUM",
          "SYM", "FUN"]

# --- Vial -> ZMK basics -----------------------------------------------------
BASIC = {
    "KC_ESCAPE": "ESC", "KC_ENTER": "RET", "KC_BSPACE": "BSPC", "KC_DELETE": "DEL",
    "KC_SPACE": "SPACE", "KC_TAB": "TAB",
    "KC_MINUS": "MINUS", "KC_EQUAL": "EQUAL", "KC_LBRC": "LBKT",
    "KC_RBRC": "RBKT", "KC_BSLASH": "BSLH", "KC_SCOLON": "SEMI",
    "KC_QUOTE": "SQT", "KC_GRAVE": "GRAVE", "KC_COMMA": "COMMA",
    "KC_DOT": "DOT", "KC_SLASH": "SLASH",
    "KC_LEFT": "LEFT", "KC_RIGHT": "RIGHT", "KC_UP": "UP", "KC_DOWN": "DOWN",
    "KC_HOME": "HOME", "KC_END": "END", "KC_PGUP": "PG_UP", "KC_PGDN": "PG_DN",
    "KC_INS": "INS",
    "KC_PSCR": "PSCRN", "KC_PAUSE": "PAUSE_BREAK", "KC_SCROLLLOCK": "SCROLLLOCK",
    "KC_APP": "K_APP",
    "KC_MUTE": "C_MUTE", "KC_VOLD": "C_VOL_DN", "KC_VOLU": "C_VOL_UP",
    "KC_MNXT": "C_NEXT", "KC_MPRV": "C_PREV", "KC_MPLY": "C_PLAY_PAUSE",
    "KC_MSTP": "C_STOP",
    "KC_LALT": "LALT", "KC_LCTL": "LCTL", "KC_LGUI": "LGUI", "KC_LSFT": "LSFT",
    "KC_RALT": "RALT", "KC_RCTL": "RCTL", "KC_RGUI": "RGUI", "KC_RSFT": "RSFT",
    "KC_NO": "&none",
}
for _l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    BASIC["KC_" + _l] = _l
for _d in "0123456789":
    BASIC["KC_" + _d] = "N" + _d
for _i in range(1, 13):
    BASIC["KC_F%d" % _i] = "F%d" % _i

MOUSE = {
    "KC_MS_L": "&mmv MOVE_LEFT", "KC_MS_D": "&mmv MOVE_DOWN",
    "KC_MS_U": "&mmv MOVE_UP", "KC_MS_R": "&mmv MOVE_RIGHT",
    "KC_WH_L": "&msc SCRL_LEFT", "KC_WH_D": "&msc SCRL_DOWN",
    "KC_WH_U": "&msc SCRL_UP", "KC_WH_R": "&msc SCRL_RIGHT",
    "KC_BTN1": "&mkp MB1", "KC_BTN2": "&mkp MB2", "KC_BTN3": "&mkp MB3",
    "QK_BOOT": "&bootloader",
    # RMK-only keycodes with no ZMK equivalent
    "KC_ACL0": "&none", "KC_ACL1": "&none", "KC_ACL2": "&none",
    "USER00": "&none", "USER01": "&none", "USER02": "&none",
    "CW_TOGG": "&caps_word",
}

MOD_SYMBOL = {"LGUI": "LG", "LCTL": "LC", "LALT": "LA", "LSFT": "LS",
              "RGUI": "RG", "RCTL": "RC", "RALT": "RA", "RSFT": "RS"}

# Miryoku K index (0..39) -> .vil (row, col) with the outer columns dropped.
# Inverse of place() in vial/make_miryoku_vil.py.
def k_to_cell(k: int):
    if k < 5:
        return (0, 1 + k)
    if k < 10:
        return (4, 5 - (k - 5))
    if k < 15:
        return (1, 1 + (k - 10))
    if k < 20:
        return (5, 5 - (k - 15))
    if k < 25:
        return (2, 1 + (k - 20))
    if k < 30:
        return (6, 5 - (k - 25))
    if k in (30, 31, 38, 39):
        return None                      # not present on this board
    if k < 35:
        return (3, 3 + (k - 32))         # left thumb fan
    return (7, 5 - (k - 35))             # right thumb fan


def translate(code: str) -> str:
    if code == "KC_NO":
        return "&none"
    if code in MOUSE:
        return MOUSE[code]
    if code in BASIC:
        return "&kp " + BASIC[code]

    m = re.fullmatch(r"TO\((\d+)\)", code)
    if m:
        return "&to " + m.group(1)

    m = re.fullmatch(r"(LCTL|LSFT|LALT|LGUI|RCTL|RSFT|RALT|RGUI)_T\((KC_\w+)\)", code)
    if m:
        mod = MOD_SYMBOL[m.group(1)]
        if mod in ("LG", "LC", "LA", "LS", "RG", "RC", "RA", "RS"):
            mod = {"LG": "LGUI", "LC": "LCTL", "LA": "LALT", "LS": "LSFT",
                   "RG": "RGUI", "RC": "RCTL", "RA": "RALT", "RS": "RSFT"}[mod]
        return "&mt %s %s" % (mod, translate(m.group(2))[4:])

    m = re.fullmatch(r"LT(\d)\((KC_\w+)\)", code)
    if m:
        return "&lt %s %s" % (m.group(1), translate(m.group(2))[4:])

    # modifier-wrapped keys, possibly nested: LGUI(LSFT(KC_Z)), SGUI(KC_4)
    m = re.fullmatch(r"(S?L?A?G?U?I?)\((.*)\)", code)
    if code.startswith(("LGUI(", "LCTL(", "LALT(", "LSFT(", "RGUI(", "RCTL(",
                        "RALT(", "RSFT(", "SGUI(")):
        outer, inner = code.split("(", 1)
        inner = inner[:-1]
        if outer == "SGUI":
            inner_bind = translate(inner)
            if inner_bind.startswith("&kp "):
                return "&kp LG(LS(%s))" % inner_bind[4:]
        if outer in MOD_SYMBOL:
            inner_bind = translate(inner)
            if inner_bind.startswith("&kp "):
                return "&kp %s(%s)" % (MOD_SYMBOL[outer], inner_bind[4:])

    raise SystemExit("no ZMK translation for Vial keycode %r" % code)


def build(vil_path: Path):
    data = json.loads(vil_path.read_text())
    grid = data["layout"]
    if len(grid) != len(LAYERS):
        raise SystemExit("%s: expected %d layers, found %d"
                         % (vil_path, len(LAYERS), len(grid)))
    out = {}
    for name, layer in zip(LAYERS, grid):
        keys = []
        for k in range(40):
            cell = k_to_cell(k)
            keys.append("&none" if cell is None else translate(layer[cell[0]][cell[1]]))
        out[name] = keys
    return out


def render(layers) -> str:
    lines = [
        "// GENERATED by scripts/gen_zmk_keys.py - do not edit.",
        "// Layers taken from the Vial export, in Miryoku's K order, so the mod",
        "// swaps / hand edits / mouse tweaks of the .vil apply to the ZMK build.",
        "//",
        "// RMK-only keycodes (KC_ACL0/1/2, USERnn, CW_TOGG, RGB_*) become &none:",
        "// ZMK has no per-key mouse acceleration and no RMK custom keycodes.",
        "#pragma once",
        "",
    ]
    for name in LAYERS:
        keys = layers[name]
        lines.append("#define MIRYOKU_LAYER_%s \\" % name)
        for i in range(0, 40, 5):
            chunk = ", ".join(keys[i:i + 5])
            if i < 35:
                lines.append("  %-72s\\" % (chunk + ","))
            else:
                lines.append("  %s" % chunk)
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vil", type=Path,
                    default=REPO / "vial/cornix-miryoku-qwerty.vil")
    ap.add_argument("-o", "--out", type=Path,
                    default=REPO / "config/includes/miryoku_keys_generated.h")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print the header instead of writing it")
    args = ap.parse_args()

    layers = build(args.vil)
    text = render(layers)
    if args.show:
        print(text)
    else:
        args.out.write_text(text)
        print("%s: %d layers -> %s" % (args.vil, len(layers), args.out))


if __name__ == "__main__":
    sys.exit(main())
