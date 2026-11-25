#!/usr/bin/env bash
#
# Build the Cornix Miryoku ZMK firmware locally, without GitHub Actions.
#
#   scripts/build-local.sh                 # left + right halves
#   scripts/build-local.sh left            # one target
#   scripts/build-local.sh all             # left right ph_left dongle reset
#   PRISTINE=1 scripts/build-local.sh all  # clean rebuild
#
# It mirrors what .github/workflows does: a west workspace whose manifest is
# this repo's config/west.yml (zmk main + zmk-keyboard-cornix + miryoku_zmk),
# then `west build -s zmk/app ... -DZMK_CONFIG=<workspace>/config`.
#
# Prerequisites (see README.md "Build locally"):
#   - west on PATH (in an activated python venv)
#   - Zephyr host deps: cmake ninja gperf dtc
#   - Zephyr SDK with arm-zephyr-eabi installed and exported
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="${ZMK_WORKSPACE:-$HOME/zmk-cornix-ws}"
TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(left right)
if [ "${TARGETS[0]}" = "all" ]; then TARGETS=(left right ph_left dongle reset); fi

if ! command -v west >/dev/null 2>&1; then
  echo "west not found. Activate the venv that has west: source ~/.venvs/zmk/bin/activate" >&2
  exit 1
fi

# ZMK's CI image is built with Zephyr SDK 0.16.x; 0.17.x ships a picolibc whose
# sys/lock.h collides with Zephyr 4.1's picolibc glue
# ("conflicting types for '__lock___libc_recursive_mutex'"). Use a local 0.16.9
# unless the caller pinned something else.
for d in "$HOME"/zephyr-sdk-0.16.*; do
  if [ -d "$d" ]; then
    if [ -n "${ZEPHYR_SDK_INSTALL_DIR:-}" ] && [ "$ZEPHYR_SDK_INSTALL_DIR" != "$d" ]; then
      echo "overriding ZEPHYR_SDK_INSTALL_DIR=$ZEPHYR_SDK_INSTALL_DIR with $d (0.17+ breaks Zephyr 4.1's picolibc)" >&2
    fi
    export ZEPHYR_SDK_INSTALL_DIR="$d"
    break
  fi
done
if [ -n "${ZEPHYR_SDK_INSTALL_DIR:-}" ]; then
  echo "using Zephyr SDK: $ZEPHYR_SDK_INSTALL_DIR"
fi

mkdir -p "$WS"
cd "$WS"

# The manifest repo has to sit at <workspace>/config (config/west.yml uses
# `self: path: config`) and the keymap includes ../../miryoku_zmk relative to it,
# so copy instead of symlinking - a symlink would make the compiler resolve the
# real path and look for miryoku_zmk inside this repo. Synced on every run, so
# edits here are picked up.
mkdir -p config
rsync -a --delete "$REPO_DIR/config/" config/
echo "synced $REPO_DIR/config -> $WS/config"

if [ ! -d .west ]; then
  echo "== first run: fetching ZMK, Zephyr and modules into $WS (several GB, be patient)"
  west init -l config
  west update --fetch-opt=--filter=tree:0
  west zephyr-export
  west packages pip --install
fi

PRISME_FLAG=""
[ -n "${PRISTINE:-}" ] && PRISME_FLAG="-p"

# board/shield/snippet per artifact, matching build.yaml
build() {
  local name="$1" board="$2" shield="${3:-}" snippets="${4:-}"
  local args=(-s zmk/app -d "build/$name" -b "$board")
  # shellcheck disable=SC2206
  [ -n "$snippets" ] && args+=($snippets)
  args+=(-- -DZMK_CONFIG="$WS/config")
  [ -n "$shield" ] && args+=(-DSHIELD="$shield")
  echo "== building $name ($board ${shield:-no shield})"
  # shellcheck disable=SC2086
  west build $PRISME_FLAG "${args[@]}"
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    left)    build left    cornix_left//zmk  cornix_indicator "-S studio-rpc-usb-uart" ;;
    right)   build right   cornix_right//zmk cornix_indicator "-S studio-rpc-usb-uart" ;;
    ph_left) build ph_left cornix_ph_left//zmk cornix_indicator "-S studio-rpc-usb-uart" ;;
    dongle)  build dongle  nice_nano//zmk cornix_dongle_adapter "-S studio-rpc-usb-uart -S nrf52840-nosd" ;;
    reset)   build reset   cornix_right//zmk settings_reset "-S studio-rpc-usb-uart -S nrf52840-nosd" ;;
    *) echo "unknown target: $t (left|right|ph_left|dongle|reset|all)" >&2; exit 1 ;;
  esac
done

# --- collect the artifacts into the repo -----------------------------------
# The west build trees stay in $WS (hundreds of MB); only the finished UF2s come
# back here, so this repository is the single source of truth for flashing.
artifact_name() {          # bash 3.2 on macOS: no associative arrays
  case "$1" in
    left)    echo left-central.uf2 ;;
    right)   echo right-peripheral.uf2 ;;
    ph_left) echo left-peripheral-dongle.uf2 ;;
    dongle)  echo dongle-central.uf2 ;;
    reset)   echo settings-reset.uf2 ;;
  esac
}
mkdir -p "$REPO_DIR/firmware"
for t in "${TARGETS[@]}"; do
  src="$WS/build/$t/zephyr/zmk.uf2"
  [ -f "$src" ] || continue
  cp "$src" "$REPO_DIR/firmware/$(artifact_name "$t")"
done
( cd "$REPO_DIR/firmware" && shasum -a 256 ./*.uf2 > SHA256SUMS )

echo
echo "== firmware/ (source: $(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo uncommitted))"
ls -1 "$REPO_DIR"/firmware/*.uf2 2>/dev/null || true
echo
echo "flash with: sudo scripts/flash-uf2-raw.sh firmware/<file>.uf2"
