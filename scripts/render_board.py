#!/usr/bin/env python3
"""Draw a picture of the Cornix itself (top view, two halves, real key geometry).

The geometry is the `LAYOUT_50` block of the board module's metadata
(zmk-keyboard-cornix, Apache-2.0), vendored as `scripts/cornix_layout50.json`
so this script runs standalone. Nothing here is guessed: the column stagger,
the 0.25u/0.3u row offsets and the 12/23 degree thumb rotations are the board's
own coordinates.

    # a plain picture of the keyboard -> images/cornix-board.png
    python3 scripts/render_board.py --out images/cornix-board.png

    # same picture, with the base layer of a .vil printed on the caps
    python3 scripts/render_board.py --vil vial/cornix-miryoku-qwerty.vil \
        --out images/cornix-base-layer.png

The SVG is rasterised with headless Chrome (already on every Mac); `--svg` keeps
the vector version instead.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEOMETRY = HERE / "cornix_layout50.json"

U = 96.0            # px per key unit (before the 2x device scale factor)
GAP = 1.15          # extra gap between the halves, in key units (looks like the real thing)
PAD = 0.55          # case border around the outermost keys
CASE_RADIUS = 0.3
CAP_INSET = 0.055   # gap between neighbouring keycaps
CAP_RADIUS = 0.15

BG = "#f4f5f7"
CASE_TOP = "#3a3d45"
CASE_BOTTOM = "#24262c"
CAP_TOP = "#fdfdfe"
CAP_BOTTOM = "#e7e9ee"
CAP_EDGE = "#c9cdd6"
LEGEND = "#33363d"
LEGEND_DIM = "#7b8090"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]

# ---------------------------------------------------------------- keycodes ----
SYMBOLS = {
    "LCTL": "\u2303", "LSFT": "\u21e7", "LALT": "\u2325", "LGUI": "\u2318",
    "RCTL": "\u2303R", "RSFT": "\u21e7R", "RALT": "\u2325R", "RGUI": "\u2318R",
}
NAMES = {
    "SPACE": "Spc", "BSPACE": "\u232b", "ENTER": "\u23ce", "ESCAPE": "Esc",
    "ESCAPE_": "Esc", "TAB": "Tab", "MUTE": "Mute", "DELETE": "Del",
    "QUOTE": "'", "COMMA": ",", "DOT": ".", "SLASH": "/", "BSLASH": "\\",
    "SCLN": ";", "SCOLON": ";", "LBRC": "[", "RBRC": "]", "LCBR": "{", "RCBR": "}",
    "MINS": "-", "EQL": "=", "GRV": "`", "TILD": "~", "PIPE": "|", "PLUS": "+",
    "UNDS": "_", "COLON": ":", "DQUO": "\"", "EXLM": "!", "AT": "@", "HASH": "#",
    "DLR": "$", "PERC": "%", "CIRC": "^", "AMPS": "&", "ASTR": "*", "LPRN": "(",
    "RPRN": ")", "LBRACKET": "[", "RBRACKET": "]", "LEFT": "\u2190",
    "RIGHT": "\u2192", "UP": "\u2191", "DOWN": "\u2193", "HOME": "Home",
    "END": "End", "PGUP": "PgUp", "PGDN": "PgDn", "BTN1": "M1", "BTN2": "M2",
    "BTN3": "M3", "WH_U": "W\u2191", "WH_D": "W\u2193", "ACL0": "0.25x",
    "ACL1": "0.5x", "ACL2": "2x", "MPLY": "\u23f5", "MFFD": "\u23ed",
    "MRWD": "\u23ee", "VOLD": "V\u2193", "VOLU": "V\u2191", "PSCR": "PrtSc",
    "NONUS_HASH": "#", "NONUS_BSLASH": "\\",
}
MODTAP = {"LCTL": "\u2303", "LSFT": "\u21e7", "LALT": "\u2325", "LGUI": "\u2318",
          "RCTL": "\u2303", "RSFT": "\u21e7", "RALT": "\u2325", "RGUI": "\u2318"}


def kc_name(code: str) -> str:
    """KC_FOO / KC_1 -> something readable on a keycap."""
    if not code.startswith("KC_"):
        return code
    name = code[3:]
    if name in NAMES:
        return NAMES[name]
    if len(name) == 1:
        return name
    if re.fullmatch(r"F\d{1,2}", name):
        return name
    return name.capitalize()


def format_key(code: str) -> tuple[str, str]:
    """Vial keycode -> (legend, small legend above it)."""
    code = str(code).strip()
    if code in ("-1", "KC_NO"):
        return "", ""
    if code == "KC_TRNS":
        return "\u25bd", ""
    m = re.fullmatch(r"(LCTL|LSFT|LALT|LGUI|RCTL|RSFT|RALT|RGUI)_T\((KC_\w+)\)", code)
    if m:
        return kc_name(m.group(2)), MODTAP[m.group(1)]
    m = re.fullmatch(r"LT(\d+)\((KC_\w+)\)", code)
    if m:
        return kc_name(m.group(2)), "L" + m.group(1)
    m = re.fullmatch(r"MO\((\d+)\)", code)
    if m:
        return "", "L" + m.group(1)
    m = re.fullmatch(r"(LCTL|LSFT|LALT|LGUI|RCTL|RSFT|RALT|RGUI)\((KC_\w+)\)", code)
    if m:
        return kc_name(m.group(2)), MODTAP[m.group(1)]
    m = re.fullmatch(r"SGUI\((KC_\w+)\)", code)
    if m:
        return kc_name(m.group(1)), "\u21e7\u2318"
    m = re.fullmatch(r"(\w+)\((KC_\w+)\)", code)
    if m:                                    # any other wrapper: keep the inner key
        return kc_name(m.group(2)), m.group(1)[:4]
    m = re.fullmatch(r"USER(\d+)", code)
    if m:
        return "U" + m.group(1), ""
    return kc_name(code), ""


# ---------------------------------------------------------------- geometry ----
def load_keys() -> list[dict]:
    keys = json.loads(GEOMETRY.read_text())["unit_keys"]
    for k in keys:
        row, col = (int(v) for v in k["m"].split(","))
        k["row"], k["col"] = row, col
        k["dx"] = GAP if row >= 4 else 0.0     # push the right half over a little
    return keys


def corners(k: dict, inset: float = 0.0) -> list[tuple[float, float]]:
    x, y = k["x"] + k["dx"] + inset, k["y"] + inset
    size = 1.0 - 2 * inset
    pts = [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]
    if "r" in k:
        a = math.radians(k["r"])
        rx, ry = k["rx"], k["ry"]
        ca, sa = math.cos(a), math.sin(a)
        pts = [(rx + (px - rx) * ca - (py - ry) * sa,
                ry + (px - rx) * sa + (py - ry) * ca) for px, py in pts]
    return pts


def half_bounds(keys: list[dict], right: bool) -> tuple[float, float, float, float]:
    pts = [p for k in keys if (k["row"] >= 4) == right for p in corners(k)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) - PAD, min(ys) - PAD, max(xs) + PAD, max(ys) + PAD


def cap_svg(k: dict, legend: str, sub: str) -> str:
    i = CAP_INSET
    x, y = k["x"] + k["dx"] + i, k["y"] + i
    s = 1.0 - 2 * i
    rot = f' transform="rotate({k["r"]:g} {k["rx"]:g} {k["ry"]:g})"' if "r" in k else ""
    parts = [
        f'<g{rot}>',
        f'<rect x="{x:.4f}" y="{y:.4f}" width="{s:.4f}" height="{s:.4f}" '
        f'rx="{CAP_RADIUS}" fill="url(#capGrad)" stroke="{CAP_EDGE}" stroke-width="0.012"/>',
    ]
    if legend or sub:
        cx, cy = x + s / 2, y + s / 2
        cls = "main" if len(legend) <= 2 else ("main3" if len(legend) == 3 else "main4")
        if sub and legend:
            parts.append(f'<text class="sub" x="{cx:.4f}" y="{cy - 0.06:.4f}">{sub}</text>')
            parts.append(f'<text class="{cls}" x="{cx:.4f}" y="{cy + 0.19:.4f}">{legend}</text>')
        elif legend:
            parts.append(f'<text class="{cls}" x="{cx:.4f}" y="{cy + 0.11:.4f}">{legend}</text>')
        else:
            parts.append(f'<text class="sub" x="{cx:.4f}" y="{cy + 0.11:.4f}">{sub}</text>')
    parts.append("</g>")
    return "".join(parts)


def render(keys: list[dict], labels: dict[tuple[int, int], tuple[str, str]], title: bool) -> str:
    left = half_bounds(keys, False)
    right = half_bounds(keys, True)
    x0, y0 = min(left[0], right[0]), min(left[1], right[1])
    x1, y1 = max(left[2], right[2]), max(left[3], right[3])
    w, h = x1 - x0, y1 - y0
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * U:.0f}" height="{h * U:.0f}" '
        f'viewBox="{x0:.4f} {y0:.4f} {w:.4f} {h:.4f}">',
        "<defs>",
        f'<linearGradient id="capGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{CAP_TOP}"/><stop offset="1" stop-color="{CAP_BOTTOM}"/>'
        "</linearGradient>",
        f'<linearGradient id="caseGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{CASE_TOP}"/><stop offset="1" stop-color="{CASE_BOTTOM}"/>'
        "</linearGradient>",
        '<filter id="capShadow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="0.035" stdDeviation="0.03" flood-color="#000" flood-opacity="0.28"/>'
        "</filter>",
        "<style>",
        f'.main,.main3,.main4{{font:600 0.30px "Helvetica Neue",Helvetica,Arial,sans-serif;fill:{LEGEND};'
        'text-anchor:middle;dominant-baseline:middle}',
        '.main3{font-size:0.235px}.main4{font-size:0.19px}',
        f'.sub{{font:500 0.165px "Helvetica Neue",Helvetica,Arial,sans-serif;fill:{LEGEND_DIM};'
        'text-anchor:middle;dominant-baseline:middle}',
        "</style>",
        "</defs>",
        f'<rect x="{x0:.4f}" y="{y0:.4f}" width="{w:.4f}" height="{h:.4f}" fill="{BG}"/>',
    ]
    # case slabs
    for b in (left, right):
        bx, by, bx1, by1 = b
        out.append(
            f'<rect x="{bx:.4f}" y="{by:.4f}" width="{bx1 - bx:.4f}" height="{by1 - by:.4f}" '
            f'rx="{CASE_RADIUS}" fill="url(#caseGrad)"/>'
        )
        out.append(
            f'<rect x="{bx + 0.1:.4f}" y="{by + 0.1:.4f}" width="{bx1 - bx - 0.2:.4f}" '
            f'height="{by1 - by - 0.2:.4f}" rx="{CASE_RADIUS - 0.08:.4f}" fill="none" '
            'stroke="#ffffff" stroke-opacity="0.07" stroke-width="0.015"/>'
        )
        for sx, sy in ((bx + 0.17, by + 0.17), (bx1 - 0.17, by + 0.17),
                       (bx + 0.17, by1 - 0.17), (bx1 - 0.17, by1 - 0.17)):
            out.append(f'<circle cx="{sx:.4f}" cy="{sy:.4f}" r="0.045" fill="#0f1115" '
                       'fill-opacity="0.75"/>')
    # keycaps
    out.append('<g filter="url(#capShadow)">')
    for k in keys:
        legend, sub = labels.get((k["row"], k["col"]), ("", ""))
        out.append(cap_svg(k, legend, sub))
    out.append("</g>")
    if title:
        out.append(f'<text class="sub" x="{(x0 + x1) / 2:.4f}" y="{y1 - 0.02:.4f}" '
                   f'style="font-size:0.17px;fill:#9aa1b0;letter-spacing:0.06px">'
                   "Cornix \u00b7 3\u00d76 + 3 thumb keys per half</text>")
    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------------- png ----
def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        found = shutil.which(c) if not c.startswith("/") else (c if Path(c).exists() else None)
        if found:
            return found
    return None


def write_png(svg: str, out: Path) -> bool:
    chrome = find_chrome()
    if not chrome:
        return False
    m = re.search(r'width="(\d+)" height="(\d+)"', svg)
    w, h = int(m.group(1)), int(m.group(2))
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "page.html"
        page.write_text(
            '<html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;'
            'background:transparent}svg{display:block}</style></head><body>'
            + svg + "</body></html>"
        )
        png = Path(td) / "out.png"
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=2", f"--window-size={w},{h}",
             f"--screenshot={png}", page.as_uri()],
            check=True, capture_output=True,
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(png, out)
    return True


# -------------------------------------------------------------------- main ----
def load_vil_labels(path: Path, layer: int) -> dict[tuple[int, int], tuple[str, str]]:
    data = json.loads(path.read_text())
    rows = data["layout"][layer]
    labels = {}
    for r, row in enumerate(rows):
        for c, code in enumerate(row):
            labels[(r, c)] = format_key(code)
    return labels


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vil", type=Path, help="print this .vil's keys on the keycaps")
    ap.add_argument("--layer", type=int, default=0, help="layer of --vil to print (default 0)")
    ap.add_argument("--out", type=Path, default=Path("images/cornix-board.png"))
    ap.add_argument("--svg", action="store_true", help="also/instead write the SVG next to --out")
    ap.add_argument("--title", action="store_true", help="small caption under the keyboard")
    args = ap.parse_args()

    labels = load_vil_labels(args.vil, args.layer) if args.vil else {}
    svg = render(load_keys(), labels, args.title)

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    svg_path = out.with_suffix(".svg")
    if args.svg or out.suffix.lower() == ".svg":
        svg_path.write_text(svg + "\n")
        print(f"wrote {svg_path}")
        if out.suffix.lower() == ".svg":
            return 0

    if out.suffix.lower() == ".svg":
        return 0
    if write_png(svg, out):
        print(f"wrote {out}")
        if args.svg:
            svg_path.write_text(svg + "\n")
        return 0

    svg_path.write_text(svg + "\n")
    print(f"no Chrome found to rasterise - wrote {svg_path} instead", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
