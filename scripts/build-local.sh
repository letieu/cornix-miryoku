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
if [ -z "${ZEPHYR_SDK_INSTALL_DIR:-}" ]; then
  for d in "$HOME"/zephyr-sdk-0.16.*; do
    [ -d "$d" ] && export ZEPHYR_SDK_INSTALL_DIR="$d" && break
  done
fi
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

PRISTINE=""
[ -n "${PRISTINE:-}" ] && PRISTINE="-p"

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
  west build $PRISTINE "${args[@]}"
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    left)    build left    cornix_left//zmk ;;
    right)   build right   cornix_right//zmk ;;
    ph_left) build ph_left cornix_ph_left//zmk ;;
    dongle)  build dongle  nice_nano//zmk cornix_dongle_adapter "-S studio-rpc-usb-uart -S nrf52840-nosd" ;;
    reset)   build reset   cornix_right//zmk settings_reset "-S studio-rpc-usb-uart -S nrf52840-nosd" ;;
    *) echo "unknown target: $t (left|right|ph_left|dongle|reset|all)" >&2; exit 1 ;;
  esac
done

echo
echo "== UF2 files (double-tap RESET, drag onto the \`cornix\` volume, or use scripts/flash-uf2-raw.sh):"
ls -1 "$WS"/build/*/zephyr/zmk.uf2 2>/dev/null || true
