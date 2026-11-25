# Flashing ZMK + Miryoku onto the Cornix, step by step

From the stock **RMK + Vial** firmware to **ZMK with the Miryoku layout**, both
halves. No compiling needed — the UF2s are already built.

Everything lives in `~/Downloads/cornix-zmk/`:

| # | File | Size | Role |
|---|---|---|---|
| 0 | `0-s140-restore.uf2` | 304 K | SoftDevice s140 (RMK ships without one) |
| 1 | `1-settings-reset.uf2` | 114 K | wipes stored settings + BLE bonds |
| 2 | `2-LEFT-central.uf2` | 526 K | left half — the BLE/USB central |
| 3 | `3-RIGHT-peripheral.uf2` | 375 K | right half — peripheral |
| – | `optional-LEFT-for-dongle.uf2`, `optional-DONGLE-central.uf2` | | dongle setup only |

Rollback kit (already prepared): `~/Downloads/cornix-rollback/` with the stock
RMK left/right UF2s, a settings-reset image and the current `.vil`.

**Why step 0 exists:** the stock RMK firmware was built without a SoftDevice.
The ZMK halves are SoftDevice-based builds, so without step 0 they would boot
into nothing (still recoverable via the bootloader, but pointless). The board's
own recovery guide (`zmk-keyboard-cornix/bootloader/README.md`) says exactly
this: restore s140 first, then flash ZMK.

---

## Before you start

- USB-C **data** cable (charge-only cables never show the flash drive).
- Do one half at a time; keep the other one unplugged and switched off.
- Reset button = the small button on/near the nice!nano controller.
  **Double-tap = two quick presses** (< 0.5 s apart).
- A `NICENANO` volume in Finder means you are in the bootloader. It disappears
  after each flash; you always double-tap again for the next file.
- Drag the file onto `NICENANO`. Wait for the copy to finish and the drive to
  unmount on its own before touching anything.

---

## Left half (central) — files 0, 1, 2

1. Switch the keyboard on and plug **USB-C into the left half**.
2. **Double-tap RESET.** Finder shows **`NICENANO`**.
   If not: other cable/port, double-tap faster, or check with `ls /Volumes`.
3. Drag **`0-s140-restore.uf2`** onto `NICENANO`. It copies, the drive unmounts,
   the half reboots (it does nothing visible — that is expected).
4. **Double-tap RESET** again → `NICENANO` → drag **`1-settings-reset.uf2`**.
   This erases stored settings and old BLE bonds.
5. **Double-tap RESET** again → `NICENANO` → drag **`2-LEFT-central.uf2`**.
   This is the real firmware: ZMK + Miryoku (QWERTY base, vim nav/mouse layers).
6. Unplug the left half.

## Right half (peripheral) — files 0, 1, 3

7. Plug **USB-C into the right half**.
8. **Double-tap RESET** → `NICENANO` → drag **`0-s140-restore.uf2`**.
9. **Double-tap RESET** → `NICENANO` → drag **`1-settings-reset.uf2`**.
10. **Double-tap RESET** → `NICENANO` → drag **`3-RIGHT-peripheral.uf2`**.
11. Unplug, then **power-cycle both halves together** (switch off both, switch
    on both) so the two sides re-establish the split link.

⚠️ Never put `2-LEFT` on the right half: two centrals = no working split.

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
| No `NICENANO` volume | data cable, other port, double-tap faster; check `ls /Volumes` |
| Drag does nothing | re-drag; keep the Finder window open until it unmounts |
| Nothing types after flashing | wrong half got the wrong file, or the halves need a joint power-cycle → re-flash with correct files, cycle both |
| Types on USB, dead on BLE | delete host pairing, re-pair; confirm both halves were re-flashed |
| Half is completely dead (no USB, no BLE) | double-tap RESET still works — the bootloader is write-protected. Re-flash step 0, 1, 2/3 again |
| Want to go back to Vial | `~/Downloads/cornix-rollback/`: double-tap RESET → `0-settings-reset.uf2` → `1-cornix-rmk-left.uf2` / `2-cornix-rmk-right.uf2`, re-pair, then Vial → *File → Load saved layout* → `cornix-miryoku-qwerty.vil` |

Recovery rule of thumb: **the bootloader never goes away.** No matter how bad
the firmware is, double-tap RESET gives you `NICENANO` and you can flash again.

## Rebuilding after changing the keymap

```bash
source ~/.venvs/zmk/bin/activate
cd ~/code/personal/cornix-miryoku
./scripts/build-local.sh left right      # or: all
```

Then repeat steps 4–5 / 9–10 (settings-reset is optional on a re-flash of the
same firmware family — just flash `2-LEFT` / `3-RIGHT`).
