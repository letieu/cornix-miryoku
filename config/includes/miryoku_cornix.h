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
// Miryoku uses 5 columns per hand, so the innermost main column of each half
// (positions 5 and 6, plus its bottom-row keys 29 and 32) is left empty with
// &none. Everything the physical keymap does not need is &none as well.
// If you would rather drop the outermost pinkie column instead, move the
// XXX placeholders to the start of each left row and the end of each right row.

#pragma once

#if !defined (MIRYOKU_LAYOUTMAPPING_CORNIX)

#define XXX &none

#define MIRYOKU_LAYOUTMAPPING_CORNIX( \
     K00, K01, K02, K03, K04,      K05, K06, K07, K08, K09, \
     K10, K11, K12, K13, K14,      K15, K16, K17, K18, K19, \
     K20, K21, K22, K23, K24,      K25, K26, K27, K28, K29, \
     N30, N31, K32, K33, K34,      K35, K36, K37, N38, N39 \
) \
K00 K01 K02 K03 K04 XXX    XXX K05 K06 K07 K08 K09 \
K10 K11 K12 K13 K14 XXX    XXX K15 K16 K17 K18 K19 \
K20 K21 K22 K23 K24 XXX    XXX XXX    XXX K25 K26 K27 K28 K29 \
XXX XXX XXX    K32 K33 K34    K35 K36 K37    XXX XXX XXX

#endif

#define MIRYOKU_MAPPING MIRYOKU_LAYOUTMAPPING_CORNIX
