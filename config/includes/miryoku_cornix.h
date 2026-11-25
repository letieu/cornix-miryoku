// Miryoku physical layout mapping for the Cornix
// (ZMK module: hitsmaxft/zmk-keyboard-cornix, boards jzf/cornix_*)
//
// Binding order is the ZMK transform order from
// boards/jzf/cornix/cornix-layouts.dtsi (layout_50, 50 positions):
//
//    0..5   left  row0   outer -> inner      6..11  right row0  inner -> outer
//   12..17  left  row1   outer -> inner     18..23  right row1  inner -> outer
//   24..29  left  row2   outer -> inner     30,31   inner column keys (LH3/RH3)
//   32..37  right row2   inner -> outer
//   38..40  left  palm keys (unused)        41..43  left  thumb fan
//   44..46  right thumb fan                 47..49  right palm keys (unused)
//
// Miryoku uses 5 columns per hand, so one main column per half is left empty
// with &none. Shipped choice: the **outermost** column (positions 0, 5, 6, 11,
// 24 and 37) - the same as the Vial layout, so the hole is at the outside of the
// board and the centre stays fully usable. This matches the Kyria mapping
// upstream (`XXX` at the start of every left row, at the end of every right row).
// Move the XXX placeholders to the inner ends instead for upstream Miryoku's
// "pinkies usable, hole next to the centre" variant.

#pragma once

#if !defined (MIRYOKU_LAYOUTMAPPING_CORNIX)

#define XXX &none

// Beyond Miryoku's 36 keys the board has 14 more cells (outer columns, the two
// inner keys and the 3+3 palm keys). They are passed as A00..A13 so hand-placed
// keys from the .vil survive: A00 is the far top-left, A08 the outer left palm,
// etc. Empty cells are &none, exactly like the Vial layout.
#define MIRYOKU_LAYOUTMAPPING_CORNIX( \
     K00, K01, K02, K03, K04,      K05, K06, K07, K08, K09, \
     K10, K11, K12, K13, K14,      K15, K16, K17, K18, K19, \
     K20, K21, K22, K23, K24,      K25, K26, K27, K28, K29, \
     N30, N31, K32, K33, K34,      K35, K36, K37, N38, N39, \
     A00, A01, A02, A03, A04,      A05, A06, A07, A08, A09, \
     A10, A11, A12, A13 \
) \
A00 K00 K01 K02 K03 K04    K05 K06 K07 K08 K09 A01 \
A02 K10 K11 K12 K13 K14    K15 K16 K17 K18 K19 A03 \
A04 K20 K21 K22 K23 K24    A06 A07    K25 K26 K27 K28 K29 A05 \
A08 A09 A10    K32 K33 K34    K35 K36 K37    A11 A12 A13

#endif

#define MIRYOKU_MAPPING MIRYOKU_LAYOUTMAPPING_CORNIX
