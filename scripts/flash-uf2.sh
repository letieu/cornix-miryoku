#!/usr/bin/env bash
#
# Flash a UF2 onto the Cornix bootloader from the command line.
#
#   scripts/flash-uf2.sh ~/Downloads/cornix-zmk/0-s140-restore.uf2
#   VOL=/Volumes/cornix scripts/flash-uf2.sh file.uf2
#
# Waits for the bootloader volume (this board labels it "cornix", not
# "NICENANO"), refuses to write if macOS mounted it read-only, then copies the
# file and waits for the volume to vanish (that is the bootloader flashing and
# rebooting).
#
set -euo pipefail

VOL="${VOL:-/Volumes/cornix}"
f="${1:?usage: flash-uf2.sh <file.uf2>}"

[ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
case "$f" in *.uf2) ;; *) echo "not a .uf2: $f" >&2; exit 1 ;; esac

printf 'waiting for %s ' "$VOL"
for _ in $(seq 1 60); do
  [ -d "$VOL" ] && break
  printf '.'
  sleep 1
done
echo
[ -d "$VOL" ] || { echo "$VOL never appeared - double-tap RESET on the half" >&2; exit 1; }

if mount | grep "on $VOL " | grep -q read-only; then
  cat >&2 <<EOF
$VOL is mounted READ-ONLY, so the write would fail.

That is macOS's FAT driver refusing this bootloader's hand-rolled filesystem
(diskutil verifyVolume says it is clean). Fixes, in order:
  1) another computer (Windows/Linux) - always works
  2) eject + double-tap RESET, then retry (clean mount is sometimes writable)
  3) sudo diskutil unmount $VOL && sudo mount -t msdos -o rw /dev/diskX $VOL
EOF
  exit 2
fi

echo "writing $(basename "$f") ($(stat -f%z "$f") bytes) to $VOL"
cp "$f" "$VOL/"
sync

printf 'waiting for the volume to disappear '
for _ in $(seq 1 45); do
  if [ ! -d "$VOL" ]; then
    echo; echo "OK - bootloader took the file and rebooted"
    exit 0
  fi
  printf '.'
  sleep 1
done
echo
echo "volume is still there after 45s - the copy may not have been taken" >&2
exit 3
