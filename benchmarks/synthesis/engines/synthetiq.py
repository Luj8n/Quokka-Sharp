from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from .engine import BASIS_GATES, TOOLS, Engine, run_external


@dataclass
class SynthetiqEngine(Engine):
    root: Path = TOOLS / "synthetiq"
    epsilon: float = 0.01
    timeout: float = 60

    def run(self, target: Path) -> str:
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            start = perf_counter()
            output = run_external(
                [
                    str(self.root / "bin/rust"),
                    str(target.resolve()),
                    "--absolute-input",
                    "--output",
                    "output",
                    "--absolute-output",
                    "--gate-set",
                    str(self.root / "data/gates/CliffordT"),
                    "--absolute-gates",
                    "--threads",
                    "1",
                    "--time",
                    str(self.timeout),
                    "--circuits",
                    "1",
                    "--epsilon",
                    str(self.epsilon),
                    "--depth-gates",
                    ",".join(BASIS_GATES),
                    "--qubit_independence",
                ],
                directory,
                self.timeout + 5,
            )
            self.elapsed_seconds = perf_counter() - start
            result = next((directory / "output").glob("*.qasm"), None)
            if result is None:
                raise RuntimeError(
                    f"Synthetiq found no circuit. Original output:\n{output}"
                )
            return result.read_text()
