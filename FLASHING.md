# Flashing ZMK + Miryoku onto the Cornix, step by step

From the stock **RMK + Vial** firmware to **ZMK with the Miryoku layout**, both
halves. No compiling needed — the UF2s are already built.

Everything lives in this repo's `firmware/` folder:

| File | Size | Role |
|---|---|---|
| `settings-reset.uf2` | 114 K | wipes stored settings + BLE bonds |
| `left-central.uf2` | 526 K | left half — the BLE/USB central |
| `right-peripheral.uf2` | 375 K | right half — peripheral |
| `left-peripheral-dongle.uf2`, `dongle-central.uf2` | | dongle setup only |

Rollback kit: `scripts/prepare-rollback.sh` fills `firmware/rollback/` with the
stock RMK left/right UF2s, the settings-reset image and the current `.vil`
(git-ignored — vendor binaries, not published).

**No SoftDevice restore needed:** the board module's recovery guide mentions
flashing s140 first, because some published ZMK artifacts are SoftDevice builds
(app at 0x26000). The artifacts here are not: the Cornix devicetree uses
`CONFIG_FLASH_LOAD_OFFSET=0x1000` (no SoftDevice), which is also where the stock
RMK image lives (`cornix-left.uf2` -> 0x1000-0x6A500, checked in the UF2 block
headers). Flashing s140 would only overwrite the app slot with SoftDevice code.

## If macOS mounts the volume read-only

Known on newer macOS: the volume mounts, `fsck` says it is clean, but every write
fails with `Read-only file system` / `mount: invalid file system`. The bootloader's
MSC handler parses **every** 512-byte write as a UF2 block and programs the
address inside that block regardless of the LBA, so the FAT can be bypassed
entirely - raw-write the file at the block device:

```bash
sudo scripts/flash-uf2-raw.sh firmware/settings-reset.uf2
sudo scripts/flash-uf2-raw.sh firmware/left-central.uf2
```

The script validates that the file is a chain of nRF52840 UF2 blocks, unmounts
the read-only volume, `dd`s the file as raw MSC writes and waits for the device
to reboot (a few `dd: Input/output error` lines at the end are the expected
success case). If nothing was programmed it says so and the old firmware is
untouched. `--dry-run` prints the block count and flash range without writing.

---

## Before you start

- USB-C **data** cable (charge-only cables never show the flash drive).
- Do one half at a time; keep the other one unplugged and switched off.
- Reset button = the small button on/near the nice!nano controller.
  **Double-tap = two quick presses** (< 0.5 s apart).
- A volume named **`cornix`** in Finder means you are in the bootloader (this
  board's bootloader uses its own label, not the default `NICENANO`). It contains
  `INFO_UF2.TXT`, `INDEX.HTM` and `CURRENT.UF2`; `INFO_UF2.TXT` should say
  `Board-ID: cornix` and `SoftDevice: not found`. It disappears after each flash;
  you always double-tap again for the next file.
- Drag the file onto `cornix`. Wait for the copy to finish and the drive to
  unmount on its own before touching anything.
- If the volume mounts **read-only** (Finder refuses the drop, "Read-only file
  system" in Terminal), eject it and double-tap RESET again - macOS flags the FAT
  as dirty after an interrupted write and only remounts read-write on a fresh
  bootloader entry. If it still refuses: `sudo mount -t msdos -o rw /dev/diskN
  /Volumes/cornix`, or flash from Windows/Linux, which never do this.

---

## Left half (central)

1. Switch the keyboard on and plug **USB-C into the left half**.
2. **Double-tap RESET.** Finder shows the volume **`cornix`**.
   If not: other cable/port, double-tap faster, or check with `ls /Volumes`.
3. Drag **`settings-reset.uf2`** onto `cornix`. It copies, the drive unmounts
   and the half reboots into a minimal firmware that erases stored settings and
   old BLE bonds.
4. **Double-tap RESET** again → `cornix` → drag **`left-central.uf2`**: ZMK +
   Miryoku (layers generated from the `.vil`). The half reboots into the
   keyboard.
5. Unplug the left half.

## Right half (peripheral)

7. Plug **USB-C into the right half**.
8. **Double-tap RESET** → `cornix` → drag **`settings-reset.uf2`**.
9. **Double-tap RESET** → `cornix` → drag **`right-peripheral.uf2`**.
11. Unplug, then **power-cycle both halves together** (switch off both, switch
    on both) so the two sides re-establish the split link.

⚠️ Never put `left-central` on the right half: two centrals = no working split.

## Remapping later, like Vial

This firmware has ZMK Studio enabled. Plug the left half in over USB, open
<https://zmk.studio/> in Chrome/Edge, connect to `Cornix` and edit keys/layers
live. Studio talks over a USB serial endpoint, so the board must show up as
`/dev/cu.usbmodem*` (`ls /dev/cu.usbmodem*`); if that is missing the flashed
image was built without the `studio-rpc-usb-uart` snippet - rebuild with
`PRISTINE=1 ./scripts/build-local.sh left` and reflash. Studio stores changes in NVS; the compiled keymap only comes back after
"Restore Stock Settings" in Studio. Timing/mouse/combo settings are not editable
there - those live in `config/` and need a rebuild.

## First run

12. Plug USB into the **left half** (the central). Typing should work over USB
    within a second or two.
13. Bluetooth: on the Mac, **delete the old keyboard entry** (the RMK one) under
    System Settings → Bluetooth, unplug USB, then pair the new **`Cornix`**.
    Stale bonds are the usual cause of "it connects but nothing types".
14. Quick functional check:
    - Base: `Q W E R T / Y U I O P`, home-row mods, `LT` thumbs (Esc/Spc/Tab |
      Ent/Bspc/Del).
    - Hold **Tab-thumb** → MOUSE layer: `h/j/k/l` moves the pointer and reaches
      full speed in ~0.3 s (no second key needed), scroll keys on the row below,
      clicks on the right thumbs.
    - Hold **Space-thumb** → NAV layer with `h/j/k/l` arrows.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| No `cornix` volume | data cable, other port, double-tap faster; check `ls /Volumes` |
| Volume is read-only, Finder refuses the drop | eject + double-tap RESET for a clean mount; else `sudo mount -t msdos -o rw /dev/diskN /Volumes/cornix`; else flash from Windows/Linux |
| Drag does nothing | re-drag; keep the Finder window open until it unmounts |
| Nothing types after flashing | wrong half got the wrong file, or the halves need a joint power-cycle → re-flash with correct files, cycle both |
| Types on USB, dead on BLE | delete host pairing, re-pair; confirm both halves were re-flashed |
| Half is completely dead (no USB, no BLE) | double-tap RESET still works — the bootloader is write-protected. Re-flash step 0, 1, 2/3 again |
| Want to go back to Vial | `firmware/rollback/`: double-tap RESET → `0-settings-reset.uf2` → `1-cornix-rmk-left.uf2` / `2-cornix-rmk-right.uf2`, re-pair, then Vial → *File → Load saved layout* → `cornix-miryoku-qwerty.vil` |

Recovery rule of thumb: **the bootloader never goes away.** No matter how bad
the firmware is, double-tap RESET gives you `cornix` and you can flash again.

## Rebuilding after changing the keymap

```bash
source ~/.venvs/zmk/bin/activate
cd ~/code/personal/cornix-miryoku
./scripts/build-local.sh left right      # or: all
```

Then repeat steps 4–5 / 9–10 (settings-reset is optional on a re-flash of the
same firmware family — just flash `left-central` / `right-peripheral`).
