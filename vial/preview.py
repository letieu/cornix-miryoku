#!/usr/bin/env python3
"""Print a Miryoku/Cornix .vil as a readable keyboard picture.

    python3 vial/preview.py vial/cornix-miryoku-qwerty.vil          # all layers
    python3 vial/preview.py file.vil --layer 3                      # one layer
    python3 vial/preview.py file.vil --settings                     # + QMK settings

The Cornix grid is 8x7 (rows 0-3 = left half, rows 4-7 = right half, columns
0-5 per half plus two inner keys at column 6 of rows 2 and 5). The right half is
printed left-to-right the way it sits on the desk, i.e. column 5 first.
"""

import argparse
import json
from pathlib import Path

NAMES = ["BASE", "EXTRA", "TAP", "BUTTON", "NAV", "MOUSE", "MEDIA", "NUM", "SYM", "FUN"]
SETTING_NAMES = {
    "2": "combo term", "6": "one-shot timeout", "7": "TAPPING TERM",
    "18": "tap code delay", "19": "tap hold caps delay", "22": "PERMISSIVE HOLD",
    "23": "HOLD ON OTHER KEY PRESS", "25": "quick tap term", "26": "CHORDAL HOLD",
    "27": "FLOW TAP",
}


def row_text(row):
    return "  ".join("·" if k in ("KC_NO", -1) else k for k in row)


def dump(data, layer_filter=None, show_settings=False):
    layers = data["layout"]
    for idx, layer in enumerate(layers):
        if layer_filter is not None and idx != layer_filter:
            continue
        name = NAMES[idx] if idx < len(NAMES) else "LAYER%d" % idx
        print("=== %s (layer %d) ===" % (name, idx))
        for r in range(4):
            left = layer[r][:6]
            right = layer[r + 4][:6][::-1]
            print("r%d | %-60s | %s" % (r, row_text(left), row_text(right)))
        enc = "%s / %s" % (layer[2][6], layer[5][6])
        print("     encoder push buttons: %s" % enc)
        print()
    if show_settings:
        print("=== QMK settings (Vial: QMK Settings tab) ===")
        for k, v in sorted(data.get("settings", {}).items(), key=lambda kv: int(kv[0])):
            print("  %-28s (id %-2s) = %s" % (SETTING_NAMES.get(k, "?"), k, v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vil", type=Path)
    ap.add_argument("--layer", type=int, help="only print this layer index")
    ap.add_argument("--settings", action="store_true", help="also print the settings block")
    args = ap.parse_args()
    dump(json.loads(args.vil.read_text()), args.layer, args.settings)


if __name__ == "__main__":
    main()
