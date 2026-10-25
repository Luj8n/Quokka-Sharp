import sys

from batch import run_batch

INPUTS = ["qft2_no_swap", "ghz3", "cluster3"]
# Example: {"num_qubits": 2, "depth": 1, "num_circuits": 10, "seed": 1}
RANDOM_CIRCUIT: dict[str, int] | None = {
    "num_qubits": 2,
    "depth": 10,
    "num_circuits": 2,
    "seed": 2,
}
RUNS_PER_CIRCUIT = 5
RUNS = [
    ("quokka-exact", "quokka", ".qasm", ["--timeout", "15"]),
    ("quokka-upstream-exact", "quokka-upstream", ".qasm", ["--timeout", "15"]),
    ("mitms", "mitms", ".mitms", ["--max-depth", "10", "--timeout", "15"]),
]


if __name__ == "__main__":
    sys.exit(run_batch(INPUTS, RUNS, RANDOM_CIRCUIT, runs_per_circuit=RUNS_PER_CIRCUIT))
