#!/usr/bin/env bash
#
# Collect everything needed to get back to the stock RMK + Vial firmware into one
# folder, so a bad ZMK flash is a two-drag recovery.
#
#   scripts/prepare-rollback.sh              # -> firmware/rollback/ (git-ignored)
#   OUT=~/Desktop/rollback scripts/prepare-rollback.sh
#   ZIP=/path/to/V1.6.zip scripts/prepare-rollback.sh
#
# The stock firmware UF2s ship inside the board module
# (zmk-keyboard-cornix/rmkfw/*.zip); they are the only way back, because the
# nice_nano bootloader cannot read the installed firmware out of the chip.
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$REPO_DIR/firmware/rollback}"
MODULE="${CORNIX_MODULE:-$REPO_DIR/../zmk-keyboard-cornix}"
ZMK_WS="${ZMK_WORKSPACE:-$HOME/zmk-cornix-ws}"

if [ -z "${ZIP:-}" ]; then
  ZIP="$(ls -t "$MODULE"/rmkfw/*.zip 2>/dev/null | head -1 || true)"
fi
if [ -z "$ZIP" ] || [ ! -f "$ZIP" ]; then
  echo "stock RMK firmware zip not found. Set ZIP=<path to V1.6.zip>," >&2
  echo "or clone https://github.com/hitsmaxft/zmk-keyboard-cornix next to this repo." >&2
  exit 1
fi

mkdir -p "$OUT"
echo "stock firmware: $ZIP"
rm -rf "$OUT/_unzip"
mkdir -p "$OUT/_unzip"
unzip -o -q "$ZIP" -x "__MACOSX/*" -d "$OUT/_unzip"

# left half = central in a standard split, right half = peripheral
cp "$OUT/_unzip"/cornix-left.uf2 "$OUT/1-cornix-rmk-left.uf2"
cp "$OUT/_unzip"/cornix-right.uf2 "$OUT/2-cornix-rmk-right.uf2"
rm -rf "$OUT/_unzip"

# ZMK settings_reset: clears ZMK's NVS + BLE bonds; harmless on RMK too, and it
# is the first thing to try if the keyboard boots but behaves oddly.
if [ -f "$ZMK_WS/build/reset/zephyr/zmk.uf2" ]; then
  cp "$ZMK_WS/build/reset/zephyr/zmk.uf2" "$OUT/0-settings-reset.uf2"
fi
cp "$REPO_DIR/vial/cornix-miryoku-qwerty.vil" "$OUT/cornix-miryoku-qwerty.vil"

cat > "$OUT/ROLLBACK.txt" <<EOF
Back to the stock RMK + Vial firmware
=====================================
Source: $ZIP

0-settings-reset.uf2   clears stored settings / BLE bonds (ZMK build; optional
                       but recommended when coming from ZMK)
1-cornix-rmk-left.uf2   stock RMK: left half (central in a standard split)
2-cornix-rmk-right.uf2  stock RMK: right half (peripheral)

For each half, in this order:
  1. Plug the half in with USB-C.
  2. Double-tap its RESET button -> a NICENANO volume appears in Finder.
     (This always works: the bootloader lives in a protected part of the chip
     and none of these UF2s touch it, no matter how broken the firmware is.)
  3. Drag the UF2 onto NICENANO. The drive unmounts and the half reboots.
  4. Left half: any order is fine, but flash the reset first if you were on ZMK.

Then:
  5. On the host, remove the old Bluetooth entry for the keyboard and pair again
     (stale bonds from the previous firmware are the usual reason "it connects
     but types nothing").
  6. Open Vial over USB, File -> Load saved layout, pick
     cornix-miryoku-qwerty.vil from this folder (it is the repo's current
     layout, including the faster mouse settings and your hand edits).

Checksums:
EOF
( cd "$OUT" && md5 -q 0-settings-reset.uf2 1-cornix-rmk-left.uf2 2-cornix-rmk-right.uf2 2>/dev/null \
  | paste -d' ' - <(printf '%s\n' 0-settings-reset.uf2 1-cornix-rmk-left.uf2 2-cornix-rmk-right.uf2) \
  >> ROLLBACK.txt ) || true

echo
ls -lh "$OUT"
echo
echo "read $OUT/ROLLBACK.txt for the two-drag recovery steps"
