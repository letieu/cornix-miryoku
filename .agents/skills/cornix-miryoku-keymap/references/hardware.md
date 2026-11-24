# Cornix hardware ↔ Vial grid

50 keys: per half 3 main rows × 6 columns (36), a bottom row of 3 "palm" keys +
3 thumb keys (12), plus 2 inner keys, and 2 encoders (4 rotation slots).

## Vial grid (8 rows × 7 columns)

The firmware's `vial.json` declares `matrix: {rows: 8, cols: 7}`. Rows 0–3 are
the **left** half, rows 4–7 the **right** half. Only these cells exist; every
other cell is `-1` in a `.vil`:

```
left  (cols 0..5, outer -> inner)                 right (cols 0..5, outer -> inner)
r0  (0,0) (0,1) (0,2) (0,3) (0,4) (0,5)     r4  (4,0) (4,1) (4,2) (4,3) (4,4) (4,5)
r1  (1,0) … (1,5)        home row           r5  (5,0) … (5,5)  +  (5,6) inner key
r2  (2,0) … (2,5)  + (2,6) inner key        r6  (6,0) … (6,5)
r3  palm palm palm | thumb thumb thumb      r7  palm palm palm | thumb thumb thumb
```

- Column 6 exists **only** at `(2,6)` and `(5,6)`; in the shipped layout those
  are the two **encoder push buttons** (`KC_MUTE`, `KC_BTN3`).
- Thumbs are always columns 3,4,5 of rows 3 and 7 (row 3: columns 3→5 run
  inner-ward, outer key first; row 7: column 5 is the innermost).
- `(3,0)(3,1)(3,2)` and `(7,0)(7,1)(7,2)` are the palm keys — free real estate.

## Fingers

Left: col0 pinkie, 1 ring, 2 middle, 3 index, 4 inner-index, 5 inner-middle.
Right is mirrored: col0 pinkie (outermost), 1 ring, 2 middle, 3 index,
4 inner-index, 5 inner-middle.

Miryoku needs 5 columns per hand, so one is left empty. **Shipped choice: the
outermost column (col 0 of each half) is empty**, i.e. `--drop outer`, so the
middle of the board stays fully used. Upstream Miryoku instead empties the
innermost columns (`--drop inner`); the user rejected that variant.

## Physical sanity check with the user

```
    ·  Q  W  E  R  T     Y  U  I  O  P  ·
    · ⌃A ⌥S ⌘D ⇧F G     H ⇧J ⌘K ⌥L ⌃' ·
    · LT3(Z) ⌥X C V B    N M , ⌥(.) LT3(/) ·
       · · · Esc SPC TAB   ENT BSP ⌫ · · ·
```

If the user says a column "in the middle" is dead, they are looking at a
`--drop inner` file by mistake.
