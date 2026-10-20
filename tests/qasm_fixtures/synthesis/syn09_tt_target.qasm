// syn09_tt_target.qasm
// TARGET: S gate
// gate_set={h, cx, t, s, cz}: TT = S.
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
t q[0];
t q[0];
