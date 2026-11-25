#!/usr/bin/env bash
#
# Flash a UF2 onto the Cornix bootloader when macOS refuses to mount the volume
# read-write ("Read-only file system" / "invalid file system").
#
# It does not use the FAT filesystem at all: the bootloader's MSC handler parses
# every 512-byte WRITE10 as a UF2 block and programs the address carried inside
# that block (see Adafruit_nRF52_Bootloader src/usb/ghostfat.c: write_block() is
# called for every write regardless of LBA). So writing the .uf2 file straight
# at the raw block device flashes it exactly like a drag-and-drop would.
#
#   sudo scripts/flash-uf2-raw.sh <file.uf2> [--dry-run]
#
# Requirements: the half must be in bootloader mode (the `cornix` volume exists,
# double-tap RESET), and sudo.
#
set -euo pipefail

f="${1:?usage: flash-uf2-raw.sh <file.uf2> [--dry-run]}"
dry="${2:-}"
VOL=/Volumes/cornix

[ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }

# --- validate: must be a chain of 512-byte nRF52840 UF2 blocks -------------
python3 - "$f" <<'PY'
import struct, sys
path = sys.argv[1]
data = open(path, 'rb').read()
if len(data) % 512:
    sys.exit("file is not a multiple of 512 bytes -- not a UF2 file")
blocks = len(data) // 512
lo = hi = None
for i in range(blocks):
    b = data[i * 512:(i + 1) * 512]
    m0, m1, flags, addr, psz, bno, nb, famid = struct.unpack('<IIIIIIII', b[:32])
    if m0 != 0x0A324655 or m1 != 0x9E5D5157:
        sys.exit(f"block {i}: not a UF2 block (bad magic)")
    if famid != 0xADA52840:
        sys.exit(f"block {i}: family 0x{famid:08X}, this bootloader only takes nRF52840 0xADA52840")
    lo = addr if lo is None else min(lo, addr)
    hi = addr + psz if hi is None else max(hi, addr + psz)
print(f"  {blocks} blocks, flash range 0x{lo:06X}-0x{hi:06X}")
PY

# --- find the bootloader's disk -------------------------------------------
# The volume is hand-rolled FAT that macOS may mount read-only or not at all,
# so look for it in the disk list rather than in /Volumes.
dev="$(diskutil list 2>/dev/null | grep -i 'cornix' | awk '{print $NF}' | tail -1 || true)"
[ -n "${dev:-}" ] || {
  echo "no 'cornix' disk found. Is the half in bootloader mode?" >&2
  echo "  - plug USB-C into the half, double-tap RESET, then retry" >&2
  exit 1
}
echo "  device /dev/r$dev"

[ "$dry" = "--dry-run" ] && { echo "  dry run: not writing"; exit 0; }

[ "$(id -u)" -eq 0 ] || { echo "needs root for raw writes: sudo $0 $f" >&2; exit 1; }

# --- unmount any read-only mount, then raw-write the file -----------------
diskutil unmount "$VOL" >/dev/null 2>&1 || true
echo "  writing $(stat -f%z "$f") bytes as raw MSC writes (FAT ignored)"
# dd stops with an I/O error when the bootloader resets at the end of the last
# block; that is the success case, so don't let it abort the script.
set +e
dd if="$f" of="/dev/r$dev" bs=512 conv=notrunc 2>&1 | tail -3
sync
set -e

# --- did it take it? -------------------------------------------------------
printf '  waiting for the device to reset '
for _ in $(seq 1 20); do
  if ! diskutil list 2>/dev/null | grep -qi 'cornix'; then
    echo; echo "  OK - bootloader finished and rebooted"
    exit 0
  fi
  printf '.'
  sleep 1
done
echo
cat >&2 <<EOF
  still there after 20 s -- most likely nothing was programmed.

  That happens when the bootloader's app window starts above the target range
  (it silently skips writes below USER_FLASH_START). Nothing is damaged: the
  old firmware is still in place. Use a Windows/Linux host and drag-and-drop.
EOF
exit 3
