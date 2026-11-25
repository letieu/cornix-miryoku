#!/usr/bin/env python3
"""Generate a Miryoku .vil layout file for the Cornix (Vial / RMK firmware).

Vial loads saved layouts with "File > Load saved layout". The .vil must use the
same keycode grid as the firmware's vial.json (here: 8 rows x 7 cols, as shipped
with the Cornix RMK firmware), otherwise Vial mis-maps keys.

Miryoku is 36 keys (3x5+3). The Cornix has 6 main columns per half, so one
column per hand is left as KC_NO. By default (`--drop outer`) that is the outer
column of each half - the leftmost and rightmost column of the keyboard - so the
middle of the board stays fully usable. `--drop inner` empties the columns next
to the centre gap instead. Palm keys, the two inner keys and the encoder push
keys are KC_NO too; assign them in Vial if you want them.

Usage:
    python3 make_miryoku_vil.py --alphas qwerty -o cornix-miryoku-qwerty.vil
    python3 make_miryoku_vil.py --alphas qwerty --swap gui,ctrl -o out.vil
    python3 make_miryoku_vil.py --alphas colemakdh -o cornix-miryoku-colemakdh.vil

    # keep your own uid/settings/encoders: pass an export from Vial
    python3 make_miryoku_vil.py --template ~/Downloads/a.vil -o out.vil

Requires the Miryoku ZMK layer definitions (miryoku_layer_alternatives.h);
pass --headers if it is not in one of the default locations.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# --- Cornix grid (matches the vial.json shipped with the RMK firmware) ------
# rows 0-3 = left half (central), rows 4-7 = right half (peripheral)
ROWS, COLS = 8, 7
EXISTING = {(r, c) for r in range(ROWS) for c in range(COLS) if c < 6}
EXISTING |= {(2, 6), (5, 6)}          # the two inner keys
ENCODER_KEYS = [(2, 6), (5, 6)]       # push buttons of the two encoders

# QMK/Vial setting IDs (see vial-gui src/main/resources/base/qmk_settings.json)
QSID_TAPPING_TERM = "7"
QSID_PERMISSIVE_HOLD = "22"
QSID_HOLD_ON_OTHER_KEY_PRESS = "23"
QSID_CHORDAL_HOLD = "26"
QSID_FLOW_TAP = "27"

# Home-row-mod tuning written into the .vil settings block. Shortening the
# tapping term and enabling Flow Tap is what stops fast rolls from firing the
# modifiers by accident; permissive hold stays on so an intentional
# mod+key chord still resolves immediately, while "hold on other key press"
# stays off because it makes down-rolls (d then f) fire the mod.
HRM_SETTINGS = {
    QSID_TAPPING_TERM: 200,            # 250 -> 200 ms: tap/hold boundary
    QSID_FLOW_TAP: 150,                # ignore a mod on keys typed right after a tap
    QSID_PERMISSIVE_HOLD: 1,           # keep: mod+key resolves on the key's release
    QSID_HOLD_ON_OTHER_KEY_PRESS: 0,   # keep: prevents rolling misfires
    QSID_CHORDAL_HOLD: 1,              # keep: same-hand roll counts as a tap
}

# Mouse-key tuning (RMK MouseKeyConfig defaults are quite slow: 5 px every 20 ms
# after a 100 ms delay). ids follow the same QMK-settings list as above.
# Mouse tuning. NOTE: RMK exposes no mouse-key settings over Vial (its Vial
# `SettingKey` enum only covers combo/morse/oneshot/tap ids), so the .vil mouse
# settings ids below are inert on this firmware - they are kept for a future RMK
# build that implements them, and documented as such. The only lever that really
# changes pointer speed is the ACL key set underneath.
#
# RMK mouse defaults: 5 px every 20 ms after a 100 ms delay, ramping to 3x over
# 50 ticks (~1 s), clamped to 25 px per report. `KC_ACL0/1/2` multiply whatever
# the ramp produced (0.25x / 0.5x / 2x, highest held key wins):
#   start 5 px  -> ACL2 10 px, ramp max 15 px -> ACL2 30 px, clamped to 25 px.
# So holding ACL2 is the "hold to fly" key: 500 px/s at first report, 1250 px/s
# at full ramp (vs 250 / 750 px/s without it).
QSID_MOUSE_DELAY = "9"
QSID_MOUSE_INTERVAL = "10"
QSID_MOUSE_STEP = "11"
QSID_MOUSE_MAX_SPEED = "12"
QSID_MOUSE_TIME_TO_MAX = "13"
QSID_WHEEL_DELAY = "14"
QSID_WHEEL_INTERVAL = "15"
QSID_WHEEL_TIME_TO_MAX = "17"

MOUSE_SETTINGS = {
    QSID_MOUSE_DELAY: 30,        # 100 -> 30 ms: pointer starts moving sooner
    QSID_MOUSE_INTERVAL: 10,     # 20 -> 10 ms between movement reports
    QSID_MOUSE_STEP: 10,         # 5 -> 10 px per report (~4x default speed)
    QSID_MOUSE_MAX_SPEED: 5,     # 3 -> 5x accelerated top speed
    QSID_MOUSE_TIME_TO_MAX: 20,  # 50 -> 20 ticks to reach top speed
    QSID_WHEEL_DELAY: 50,        # 100 -> 50 ms
    QSID_WHEEL_INTERVAL: 40,     # 80 -> 40 ms between wheel reports
    QSID_WHEEL_TIME_TO_MAX: 15,
}

# Speed modifier keys on the MOUSE layer, on the left thumb row. Placement
# matters: (3,5) is the outer thumb, i.e. the `LT5(KC_TAB)` key that is *held* to
# activate the MOUSE layer, so a keycode there is never emitted - it must not be
# the only fast option. The three reachable ones:
#   (3,4) middle thumb (Space/Nav position) = 2x  -> hold this to move fast
#   (3,3) inner thumb (Esc/Media position) = 0.5x -> fine positioning
#   (3,2) inner palm                        = 0.25x -> pixel hunting
MOUSE_ACCEL_KEYS = {
    (3, 2): "KC_ACL0",
    (3, 3): "KC_ACL1",
    (3, 4): "KC_ACL2",
    (3, 5): "KC_ACL2",
}

# Hand edits the user made in Vial / vial.rocks that must survive a regeneration.
# They are applied on top of the Miryoku layers for both alphas sets, so a fresh
# run of this script reproduces the keymap that is actually on the keyboard.
USER_PATCHES = {
    "BASE": {
        (0, 0): "SGUI(KC_4)",      # Cmd+Shift+4: screenshot to the Desktop
        (3, 0): "LALT(KC_Z)",      # Option+Z
    },
    "NAV": {
        (5, 1): "KC_NO",           # CW_TOGG cleared: caps-word is not used
    },
    "MOUSE": {
        # clipboard slots replaced by the macOS Ctrl+arrow window/space keys
        (4, 2): "LCTL(KC_RIGHT)",
        (4, 3): "LCTL(KC_UP)",
        (4, 4): "LCTL(KC_DOWN)",
        (4, 5): "LCTL(KC_LEFT)",
        # scroll direction flipped (natural scrolling)
        (6, 3): "KC_WH_D",
        (6, 4): "KC_WH_U",
    },
    "MEDIA": {
        # RGB keys are no-ops on this RMK build, so they were blanked in Vial
        (4, 1): "KC_NO",
        (4, 2): "KC_NO",
        (4, 3): "KC_NO",
        (4, 4): "KC_NO",
        (4, 5): "KC_NO",
    },
    "FUN": {
        # outer column: Vial "Custom" keycodes USER00..USER02
        (1, 0): "USER00",
        (2, 0): "USER01",
        (3, 0): "USER02",
    },
}

# Miryoku layer order, must match U_BASE..U_FUN in miryoku_layer_list.h
LAYER_ORDER = ["BASE", "EXTRA", "TAP", "BUTTON", "NAV", "MOUSE", "MEDIA",
               "NUM", "SYM", "FUN"]
LAYER_INDEX = {n: i for i, n in enumerate(LAYER_ORDER)}

# --- Vial keycode name mapping (ZMK -> Vial) --------------------------------
KEYS = {
    "ESC": "KC_ESCAPE", "RET": "KC_ENTER", "BSPC": "KC_BSPACE",
    "DEL": "KC_DELETE", "SPACE": "KC_SPACE", "TAB": "KC_TAB",
    "LSHFT": "KC_LSFT", "LCTRL": "KC_LCTL", "LALT": "KC_LALT",
    "LGUI": "KC_LGUI", "RALT": "KC_RALT",
    "LEFT": "KC_LEFT", "RIGHT": "KC_RIGHT", "UP": "KC_UP", "DOWN": "KC_DOWN",
    "INS": "KC_INS", "HOME": "KC_HOME", "END": "KC_END",
    "PG_UP": "KC_PGUP", "PG_DN": "KC_PGDN",
    "PSCRN": "KC_PSCR", "SLCK": "KC_SCROLLLOCK", "PAUSE_BREAK": "KC_PAUSE",
    "K_APP": "KC_APP",
    "C_PREV": "KC_MPRV", "C_NEXT": "KC_MNXT", "C_VOL_DN": "KC_VOLD",
    "C_VOL_UP": "KC_VOLU", "C_STOP": "KC_MSTP", "C_PP": "KC_MPLY",
    "C_MUTE": "KC_MUTE",
    "SQT": "KC_QUOTE", "SEMI": "KC_SCOLON", "COMMA": "KC_COMMA",
    "DOT": "KC_DOT", "SLASH": "KC_SLASH", "BSLH": "KC_BSLASH",
    "GRAVE": "KC_GRAVE", "EQUAL": "KC_EQUAL", "MINUS": "KC_MINUS",
    "LBKT": "KC_LBRC", "RBKT": "KC_RBRC",
    "LBRC": "KC_LBRC", "RBRC": "KC_RBRC",
    # shifted symbols: no dedicated Vial/qmk name in this set
    "AMPS": "LSFT(KC_7)", "ASTRK": "LSFT(KC_8)", "LPAR": "LSFT(KC_9)",
    "RPAR": "LSFT(KC_0)", "EXCL": "LSFT(KC_1)", "AT": "LSFT(KC_2)",
    "HASH": "LSFT(KC_3)", "DLLR": "LSFT(KC_4)", "PRCNT": "LSFT(KC_5)",
    "CARET": "LSFT(KC_6)", "COLON": "LSFT(KC_SCOLON)",
    "PLUS": "LSFT(KC_EQUAL)", "UNDER": "LSFT(KC_MINUS)",
    "TILDE": "LSFT(KC_GRAVE)", "PIPE": "LSFT(KC_BSLASH)",
}
for _n in range(10):
    KEYS["N%d" % _n] = "KC_%d" % _n
for _n in range(1, 13):
    KEYS["F%d" % _n] = "KC_F%d" % _n
for _n in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + list("0123456789"):
    KEYS.setdefault(_n, "KC_%s" % _n)

MODS = {"LSHFT": "LSFT", "LCTRL": "LCTL", "LALT": "LALT", "LGUI": "LGUI",
        "RSHFT": "RSFT", "RCTRL": "RCTL", "RALT": "RALT", "RGUI": "RGUI"}

# Miryoku clipboard macros: macOS command-key variants (MIRYOKU_CLIPBOARD_MAC).
# Use CTRL instead of GUI for Windows/Linux: replace below with LCTL.
CLIPBOARD = {
    "U_UND": "LGUI(KC_Z)",
    "U_CUT": "LGUI(KC_X)",
    "U_CPY": "LGUI(KC_C)",
    "U_PST": "LGUI(KC_V)",
    "U_RDO": "LGUI(LSFT(KC_Z))",
}

# Home-row modifier swap: --swap gui,ctrl moves the macOS Command key from the
# pinkie column to the middle-finger column and Control to the pinkie.
SWAP_NAMES = {"lctl": "LCTL", "lalt": "LALT", "lgui": "LGUI", "lsft": "LSFT",
              "rctl": "RCTL", "ralt": "RALT", "rgui": "RGUI", "rsft": "RSFT"}
SWAP_ALIASES = {"ctrl": "lctl", "control": "lctl", "cmd": "lgui", "command": "lgui",
                "gui": "lgui", "super": "lgui", "win": "lgui", "alt": "lalt",
                "opt": "lalt", "option": "lalt", "shift": "lsft", "sft": "lsft"}

MISC = {
    "U_NA": "KC_NO", "U_NU": "KC_NO", "U_NP": "KC_NO",
    "U_BOOT": "QK_BOOT",
    "U_MS_U": "KC_MS_U", "U_MS_D": "KC_MS_D",
    "U_MS_L": "KC_MS_L", "U_MS_R": "KC_MS_R",
    "U_WH_U": "KC_WH_U", "U_WH_D": "KC_WH_D",
    "U_WH_L": "KC_WH_L", "U_WH_R": "KC_WH_R",
    "U_BTN1": "KC_BTN1", "U_BTN2": "KC_BTN2", "U_BTN3": "KC_BTN3",
    "U_RGB_TOG": "RGB_TOG", "U_RGB_EFF": "RGB_MOD", "U_RGB_HUI": "RGB_HUI",
    "U_RGB_SAI": "RGB_SAI", "U_RGB_BRI": "RGB_VAI",
    # no Vial equivalent in RMK builds: leave empty, set these in the Vial GUI
    "U_EP_TOG": "KC_NO",
    "&u_out_tog": "KC_NO",
}

TO_LAYER = {
    "&u_to_U_BASE": "BASE", "&u_to_U_EXTRA": "EXTRA", "&u_to_U_TAP": "TAP",
    "&u_to_U_BUTTON": "BUTTON", "&u_to_U_NAV": "NAV", "&u_to_U_MOUSE": "MOUSE",
    "&u_to_U_MEDIA": "MEDIA", "&u_to_U_NUM": "NUM", "&u_to_U_SYM": "SYM",
    "&u_to_U_FUN": "FUN",
    "&u_caps_word": "CW_TOGG",
}


# --- Miryoku header parsing -------------------------------------------------
def parse_layers(headers):
    """Return {MACRO_NAME: [40 zmk tokens]} for every alternative we need."""
    text = headers.read_text()
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        stripped = line.rstrip()
        m = re.match(r"#define\s+(MIRYOKU_ALTERNATIVES_\w+)\s*(.*)$", stripped)
        if m:
            if cur:
                out[cur] = _split(buf)
            cur = m.group(1)
            buf = [m.group(2)]
            continue
        if cur is None:
            continue
        if stripped.endswith("\\"):
            buf.append(stripped[:-1])
        else:
            buf.append(stripped)
            out[cur] = _split(buf)
            cur, buf = None, []
    if cur:
        out[cur] = _split(buf)
    return out


def _split(lines):
    body = " ".join(lines).replace("\\", " ")   # drop macro line continuations
    # tokens are comma separated; U_MT(MOD, KEY) contains a comma
    toks, depth, cur = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            toks.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        toks.append(cur.strip())
    return [t for t in toks if t and not t.startswith("#")]


def translate(tokens):
    """ZMK binding tokens -> Vial keycode strings (one per Miryoku key)."""
    out = []
    for tok in tokens:
        tok = tok.strip()
        if tok.startswith("&kp "):
            key = tok[4:].strip()
            out.append(KEYS.get(key, "KC_NO"))
        elif tok.startswith("U_MT("):
            inner = tok[5:-1].split(",")
            mod = MODS[inner[0].strip()]
            out.append("%s_T(%s)" % (mod, KEYS.get(inner[1].strip(), "KC_NO")))
        elif tok.startswith("U_LT("):
            inner = tok[5:-1].split(",")
            layer = TO_LAYER["&u_to_" + inner[0].strip()]
            out.append("LT%d(%s)" % (LAYER_INDEX[layer], KEYS.get(inner[1].strip(), "KC_NO")))
        elif tok.startswith("&u_bt_sel_"):
            out.append("KC_NO")
        elif tok in CLIPBOARD:
            out.append(CLIPBOARD[tok])
        elif tok in MISC:
            out.append(MISC[tok])
        elif tok in TO_LAYER:
            target = TO_LAYER[tok]
            out.append("TO(%d)" % LAYER_INDEX[target] if target in LAYER_INDEX else target)
        else:
            raise SystemExit("untranslated Miryoku token: %r" % tok)
    return out


# --- Placement --------------------------------------------------------------
# Miryoku's 40 layer args are ordered:
#   0-4    left pinkie..inner      5-9   right INNER..pinkie
#   10-14  left pinkie..inner      15-19 right INNER..pinkie
#   20-24  left pinkie..inner      25-29 right INNER..pinkie
#   32,33,34 left thumbs (outer..inner)   35,36,37 right thumbs (inner..outer)
# The Cornix matrix columns run outer -> inner on the left (0..5) and
# inner -> outer on the right (5..0), thumbs sit at columns 3,4,5.

def place(keys40, drop="outer"):
    """Place Miryoku's 40 args into the Cornix 8x7 grid."""
    grid = {}
    # leave either the innermost column (off=0) or the outermost one (off=1) empty
    off = 0 if drop == "inner" else 1
    for r, base in enumerate((0, 10, 20)):
        for c in range(5):                      # left: pinkie(0) -> inner(4)
            grid[(r, c + off)] = keys40[base + c]
        for i in range(5):                      # right args 0..4 = inner -> pinkie
            grid[(r + 4, (4 - i) + off)] = keys40[base + 5 + i]
    # thumbs: left (3,3)(3,4)(3,5) outer->inner, right (7,5)(7,4)(7,3)
    for i in range(3):
        grid[(3, 3 + i)] = keys40[32 + i]
        grid[(7, 5 - i)] = keys40[35 + i]
    return grid


def alt_name(base, variant):
    """MIRYOKU_ALTERNATIVES_<base>[_<variant>], 'default' picks the plain macro."""
    variant = (variant or "default").upper()
    return base if variant == "DEFAULT" else "%s_%s" % (base, variant)


def build_layers(alt, alphas, drop, nav="default", mouse="default"):
    base = translate(alt["MIRYOKU_ALTERNATIVES_BASE_" + alphas])
    # miryoku_zmk defines EXTRA as the same alphas with empty thumbs
    extra = list(base)
    for i in (30, 31, 32, 33, 34, 35, 36, 37, 38, 39):
        extra[i] = "KC_NO"
    src = {
        "BASE": base,
        "EXTRA": extra,
        "TAP": translate(alt["MIRYOKU_ALTERNATIVES_TAP_" + alphas]),
        "BUTTON": translate(alt["MIRYOKU_ALTERNATIVES_BUTTON"]),
        "NAV": translate(alt[alt_name("MIRYOKU_ALTERNATIVES_NAV", nav)]),
        "MOUSE": translate(alt[alt_name("MIRYOKU_ALTERNATIVES_MOUSE", mouse)]),
        "MEDIA": translate(alt["MIRYOKU_ALTERNATIVES_MEDIA"]),
        "NUM": translate(alt["MIRYOKU_ALTERNATIVES_NUM"]),
        "SYM": translate(alt["MIRYOKU_ALTERNATIVES_SYM"]),
        "FUN": translate(alt["MIRYOKU_ALTERNATIVES_FUN"]),
    }
    layers = []
    for name in LAYER_ORDER:
        keys = src[name]
        if len(keys) < 40:
            raise SystemExit("layer %s short: %d keys" % (name, len(keys)))
        grid = place(keys, drop)
        layer = []
        for r in range(ROWS):
            row = []
            for c in range(COLS):
                if (r, c) not in EXISTING:
                    row.append(-1)
                else:
                    row.append(grid.get((r, c), "KC_NO"))
            layer.append(row)
        layers.append(layer)
    return layers


def make_swapper(pair):
    """Swap two modifiers in mod-tap and standalone-mod keycodes.

    Modded keycodes such as LGUI(KC_C) are left untouched: those are shortcut
    combos (Cmd+C), not the position of the modifier.
    """
    if not pair:
        return lambda code: code
    def norm(x):
        x = x.strip().lower()
        return SWAP_NAMES[SWAP_ALIASES.get(x, x)]

    a, b = [norm(x) for x in pair.split(",")]

    def swap(code):
        if code == "KC_" + a:
            return "KC_" + b
        if code == "KC_" + b:
            return "KC_" + a
        for src, dst in ((a, b), (b, a)):
            m = re.fullmatch(src + r"_T\((.*)\)", code)
            if m:
                return "%s_T(%s)" % (dst, m.group(1))
        return code

    return swap


# --- validation -------------------------------------------------------------
def validate(layers, names_path):
    names = {ln.strip() for ln in names_path.read_text().splitlines() if ln.strip()}
    ok_pattern = re.compile(
        r"^(?:[A-Z_]+)\((?:[A-Z_]+\((?:[A-Z_]+\(?[A-Z0-9_]*\)?)\)?|[A-Z0-9_]+|[0-9]+)\)$"
        r"|^[A-Z_]+\([0-9]+,[A-Z0-9_]+\)$")
    bad = []
    for li, layer in enumerate(layers):
        for r, row in enumerate(layer):
            for c, k in enumerate(row):
                if k == -1 or k in names:
                    continue
                if re.match(r"^[LR][A-Z]{3}_T\(KC_\w+\)$", k) or \
                   re.match(r"^LT[0-9]+\(KC_\w+\)$", k) or \
                   re.match(r"^TO\([0-9]+\)$", k) or \
                   re.match(r"^(LSFT|LGUI|LCTL|LALT|RSFT|RGUI|RCTL|RALT|SGUI)\(KC_\w+\)$", k) or \
                   re.match(r"^LGUI\(LSFT\(KC_\w+\)\)$", k) or \
                   re.match(r"^USER[0-9]{2}$", k):
                    continue
                bad.append((li, r, c, k))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alphas", default="qwerty",
                    help="qwerty (default), colemakdh, colemak, dvorak, workman, halmak, ...")
    ap.add_argument("--drop", choices=["outer", "inner"], default="outer",
                    help="which of the 6 main columns to leave empty: 'outer' (leftmost/"
                         "rightmost column, default) or 'inner' (next to the centre gap)")
    ap.add_argument("--headers", type=Path, help="path to miryoku_layer_alternatives.h")
    ap.add_argument("--template", type=Path,
                    help="existing .vil keeping uid/settings/encoders (e.g. your own export)")
    ap.add_argument("--nav", default="default", choices=["default", "vi", "invertedt"],
                    help="Nav layer flavour: 'vi' keeps arrows on the home row next to the"
                         " centre (vim hjkl muscle memory), 'invertedt' swaps arrows/paging")
    ap.add_argument("--mouse", default="default", choices=["default", "vi", "invertedt"],
                    help="Mouse layer flavour, same choices as --nav")
    ap.add_argument("--swap", metavar="MOD1,MOD2",
                    help="swap two modifiers on the home row and layer mod clusters,"
                         " e.g. 'gui,ctrl' to put Cmd under the middle finger on macOS;"
                         " accepts gui/ctrl/alt/shift with optional l/r prefix")
    ap.add_argument("--no-mouse-tune", dest="mouse_tune", action="store_false",
                    help="keep the template's mouse-key speed settings and do not add the"
                         " mouse acceleration keys to the MOUSE layer")
    ap.add_argument("--no-hrm-tune", dest="hrm_tune", action="store_false",
                    help="keep the tapping/flow-tap values from the template instead of"
                         " the tuned home-row-mod preset")
    ap.add_argument("--encoder-clicks", default="KC_MUTE,KC_BTN3",
                    help="keycodes for the two encoder push buttons, 'x,y' (default: KC_MUTE,KC_BTN3);"
                         " use 'none,none' to leave them empty")
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    headers = args.headers
    if headers is None:
        for cand in [HERE / "miryoku_layer_alternatives.h",
                     HERE.parent / "miryoku_zmk/miryoku/miryoku_babel/miryoku_layer_alternatives.h"]:
            if cand.exists():
                headers = cand
                break
    if headers is None or not headers.exists():
        raise SystemExit("miryoku_layer_alternatives.h not found; pass --headers")

    alt = parse_layers(headers)
    alphas = args.alphas.upper()
    layers = build_layers(alt, alphas, args.drop, args.nav, args.mouse)
    swap = make_swapper(args.swap)
    layers = [[[swap(k) if isinstance(k, str) else k for k in row] for row in layer]
              for layer in layers]

    clicks = [x.strip() for x in args.encoder_clicks.split(",")]
    if len(clicks) != len(ENCODER_KEYS):
        raise SystemExit("--encoder-clicks needs %d values" % len(ENCODER_KEYS))
    for layer in layers:
        for (r, c), value in zip(ENCODER_KEYS, clicks):
            layer[r][c] = value

    for layer_name, cells in USER_PATCHES.items():
        for (r, c), code in cells.items():
            layers[LAYER_INDEX[layer_name]][r][c] = code

    template = json.loads(args.template.read_text()) if args.template else None
    if template is not None:
        template["layout"] = layers
    else:
        template = {
            "version": 1,
            "uid": 16882930253541522617,
            "layout": layers,
            "encoder_layout": [[["KC_VOLD", "KC_VOLU"], ["KC_WH_U", "KC_WH_D"]]] * len(layers),
            "layout_options": 0,
            "macro": [[] for _ in range(32)],
            "vial_protocol": 6,
            "via_protocol": 9,
            "tap_dance": [["KC_NO", "KC_NO", "KC_NO", "KC_NO", 250] for _ in range(8)],
            "combo": [["KC_NO"] * 5 for _ in range(8)],
            "key_override": [],
            "alt_repeat_key": [],
            "settings": {"2": 50, "6": 1000, "7": 250, "18": 20, "19": 20,
                         "22": 1, "23": 0, "26": 1, "27": 120},
        }

    if args.hrm_tune:
        settings = template.setdefault("settings", {})
        settings.update(HRM_SETTINGS)
    if args.mouse_tune:
        settings = template.setdefault("settings", {})
        settings.update(MOUSE_SETTINGS)
        for (r, c), code in MOUSE_ACCEL_KEYS.items():
            layers[LAYER_INDEX["MOUSE"]][r][c] = code

    bad = validate(layers, HERE / "vial_names.txt")
    if bad:
        print("unknown keycodes:", bad, file=sys.stderr)
        return 1

    args.out.write_text(json.dumps(template, indent=1) + "\n")
    print("%s: %d layers, alphas=%s, drop=%s" % (args.out, len(layers), alphas, args.drop))
    return 0


if __name__ == "__main__":
    sys.exit(main())
