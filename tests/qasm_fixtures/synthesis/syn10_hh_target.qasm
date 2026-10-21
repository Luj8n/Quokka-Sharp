// syn10_hh_target.qasm
// TARGET: Identity gate (H H = I).
// gate_set={h, cx, s}: H H = I (empty circuit).

OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];

h q[0];
h q[0];