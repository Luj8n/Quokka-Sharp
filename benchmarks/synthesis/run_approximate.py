import sys

from batch import run_batch

INPUTS = ["cz"]
RUNS = [
    ("quokka-approximate", "quokka", ".qasm", ["--fidelity", "0.99"]),
    (
        "quokka-upstream-approximate",
        "quokka-upstream",
        ".qasm",
        ["--fidelity", "0.99"],
    ),
    ("qiskit", "qiskit", ".qasm", ["--approximation-degree", "0.99"]),
    ("synthetiq", "synthetiq", ".txt", ["--epsilon", "0.07079945545962932"]),
]


if __name__ == "__main__":
    sys.exit(run_batch(INPUTS, RUNS))
