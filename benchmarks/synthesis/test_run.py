import json
import os
import re
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

import numpy as np
import pytest
from engines.engine import BASIS_GATES
from qasm_to_unitary import convert
from qiskit import QuantumCircuit, qasm2
from qiskit.quantum_info import Operator

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parents[1]


@pytest.fixture(params=["cz", "h_cx_t"])
def target(tmp_path, request) -> Path:
    for suffix in (".qasm", ".mitms"):
        name = request.param + suffix
        copyfile(HERE / "inputs" / name, tmp_path / name)
    return tmp_path / f"{request.param}.qasm"


def run_engine(engine: str, input_file: Path, *options: str) -> str:
    config = input_file.parent / "quokka.json"
    config.write_text(json.dumps({"TIMEOUT": 10}))
    process = subprocess.run(
        [
            sys.executable,
            str(HERE / "run.py"),
            engine,
            str(input_file),
            *options,
        ],
        env={
            **os.environ,
            "PATH": f"{ROOT / '.solvers/bin'}:{os.environ.get('PATH', '')}",
            "QUOKKA_CONFIG": str(config),
            "OPENBLAS_NUM_THREADS": "1",
        },
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    timing = re.search(r"Synthesis time: ([0-9.]+) s", process.stderr)
    assert timing and float(timing[1]) > 0, process.stderr

    return process.stdout


def assert_circuit(result: QuantumCircuit, target: Path, min_fidelity: float) -> None:
    reference = qasm2.load(target)
    unitary = np.asarray(Operator(reference))
    assert result.num_qubits == reference.num_qubits
    assert set(result.count_ops()) <= set(BASIS_GATES)
    fidelity = (
        abs(np.vdot(unitary, np.asarray(Operator(result)))) ** 2 / len(unitary) ** 2
    )
    assert fidelity >= min_fidelity - 1e-12, f"Fidelity: {fidelity}"


def test_quokka_exact(target):
    output = run_engine("quokka", target)
    assert_circuit(qasm2.loads(output), target, 1.0)


def test_quokka_approximate(target):
    output = run_engine("quokka", target, "--fidelity", ".99")
    assert_circuit(qasm2.loads(output), target, 0.99)


def test_qiskit(target):
    output = run_engine("qiskit", target, "--approximation-degree", ".99")
    assert_circuit(qasm2.loads(output), target, 0.99)


def test_synthetiq(target):
    native = target.with_suffix(".txt")
    convert(target, native)
    output = run_engine("synthetiq", native, "--epsilon", ".01", "--timeout", "10")
    assert_circuit(qasm2.loads(output), target, (1 - 0.01**2) ** 2)


def test_mitms(target):
    output = run_engine("mitms", target.with_suffix(".mitms"), "--timeout", "10")
    # MITMS prints native circuit rows before each "Cost" line, not QASM.
    blocks = output.split("Cost ")[:-1]
    assert blocks, output
    for block in blocks:
        rows = [
            re.findall(r"C\(\d+\)|[IHSTX]\*?", line)
            for line in block.strip().splitlines()[-2:]
        ]
        result = QuantumCircuit(2)
        for column in zip(*rows, strict=True):
            for qubit, gate in enumerate(column):
                if gate.startswith("C("):
                    result.cx(qubit, int(gate[2:-1]) - 1)
                elif gate not in {"I", "X"}:
                    getattr(result, gate.lower().replace("*", "dg"))(qubit)
        assert_circuit(result, target, 1.0)
