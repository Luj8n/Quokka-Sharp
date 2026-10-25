import sys

from batch import run_batch

INPUTS_2Q = ["ct_cy"]
INPUTS_3Q = ["phase_chain3"]
RUNS_PER_CIRCUIT = 5

RUNS_2Q = [
    (
        "quokka-approximate",
        "quokka",
        ".qasm",
        ["--fidelity", "0.89", "--timeout", "15"],
    ),
    (
        "quokka-upstream-approximate",
        "quokka-upstream",
        ".qasm",
        ["--fidelity", "0.89", "--timeout", "15"],
    ),
    ("qiskit", "qiskit", ".qasm", ["--approximation-degree", "0.89"]),
    (
        "synthetiq",
        "synthetiq",
        ".txt",
        ["--epsilon", "0.23791151042843564", "--timeout", "15"],
    ),
    (
        "mitms-approximate",
        "mitms",
        ".mitms",
        ["--approximate", "--max-depth", "4", "--timeout", "15"],
    ),
]

RUNS_3Q = [
    (
        "quokka-approximate",
        "quokka",
        ".qasm",
        ["--fidelity", "0.95", "--timeout", "60"],
    ),
    (
        "quokka-upstream-approximate",
        "quokka-upstream",
        ".qasm",
        ["--fidelity", "0.95", "--timeout", "60"],
    ),
    ("qiskit", "qiskit", ".qasm", ["--approximation-degree", "0.99"]),
    (
        "synthetiq",
        "synthetiq",
        ".txt",
        ["--epsilon", "0.15912437122924844", "--timeout", "60"],
    ),
]


if __name__ == "__main__":
    status = 0
    for inputs, runs in [(INPUTS_2Q, RUNS_2Q), (INPUTS_3Q, RUNS_3Q)]:
        status |= run_batch(
            inputs,
            runs,
            runs_per_circuit=RUNS_PER_CIRCUIT,
            measure_fidelity=True,
        )
    sys.exit(status)
