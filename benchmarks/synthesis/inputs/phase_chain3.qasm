OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
rz(pi/3) q[0];
rz(pi/5) q[1];
cx q[0],q[1];
cx q[1],q[2];
