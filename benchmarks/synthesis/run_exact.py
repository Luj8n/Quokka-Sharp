import sys

from batch import run_batch

INPUTS = ["csx"]
RUNS = [
    ("quokka-exact", "quokka", ".qasm", []),
    ("quokka-upstream-exact", "quokka-upstream", ".qasm", []),
    ("mitms", "mitms", ".mitms", ["--max-seq-length", "6", "--timeout", "3600"]),
]


if __name__ == "__main__":
    sys.exit(run_batch(INPUTS, RUNS))
