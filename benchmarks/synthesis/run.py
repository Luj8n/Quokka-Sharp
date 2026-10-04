import argparse
import sys
from math import isfinite
from pathlib import Path

from engines.engine import TOOLS, Engine


def probability(value: str) -> float:
    number = float(value)
    if not 0 <= number <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return number


def positive_seconds(value: str) -> float:
    number = float(value)
    if not isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be positive and finite")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""Run one synthesis engine. Original output goes to stdout, timing goes to stderr."""
    )
    engines = parser.add_subparsers(dest="engine", required=True)
    quokka = engines.add_parser(
        "quokka", aliases=["quokka-upstream"], help="QASM input. Exact or approximate"
    )
    quokka.add_argument("input", type=Path)
    quokka.add_argument(
        "--fidelity",
        type=probability,
        default=1.0,
        help="Minimum Jamiołkowski fidelity (default: 1, i.e. exact)",
    )
    qiskit = engines.add_parser(
        "qiskit", help="QASM input; heuristic unitary synthesis"
    )
    qiskit.add_argument("input", type=Path)
    qiskit.add_argument(
        "--approximation-degree",
        type=probability,
        default=0.99,
        help="Qiskit's heuristic dial, not a fidelity bound (default: .9)",
    )
    qiskit.add_argument("--optimization-level", type=int, choices=range(4), default=3)
    mitms = engines.add_parser("mitms", help="Native searches file input. Exact")
    mitms.add_argument("input", type=Path)
    mitms.add_argument(
        "--label", default="target", help="Circuit label in the input file"
    )
    mitms.add_argument(
        "--max-seq-length",
        type=int,
        default=3,
        help="Native sequence limit",
    )
    mitms.add_argument("--timeout", type=positive_seconds, default=60)
    synthetiq = engines.add_parser(
        "synthetiq", help="Native matrix file input. Approximate, heuristic"
    )
    synthetiq.add_argument("input", type=Path)
    synthetiq.add_argument(
        "--epsilon",
        type=probability,
        default=0.01,
        help="Native distance threshold (default: .01)",
    )
    synthetiq.add_argument("--timeout", type=positive_seconds, default=60)
    args = parser.parse_args(argv)
    if args.engine == "mitms" and args.max_seq_length < 2:
        parser.error("--max-seq-length must be at least 2")
    return args


def main() -> None:
    args = parse_args()
    engine: Engine
    try:
        if args.engine in {"quokka", "quokka-upstream"}:
            source = (
                TOOLS / "quokka-upstream" / "quokka_sharp"
                if args.engine == "quokka-upstream"
                else Path(__file__).resolve().parents[2] / "quokka_sharp"
            )
            if not (source / "quokka_sharp" / "__init__.py").is_file():
                raise FileNotFoundError(
                    f"Quokka source missing: {source}. Run scripts/setup-synthesis-engines.sh."
                )
            sys.path.insert(0, str(source))
            from engines.quokka import QuokkaEngine

            engine = QuokkaEngine(fidelity=args.fidelity)
        elif args.engine == "qiskit":
            from engines.qiskit import QiskitEngine

            engine = QiskitEngine(
                approximation_degree=args.approximation_degree,
                optimization_level=args.optimization_level,
            )
        elif args.engine == "mitms":
            from engines.mitms import MitmsEngine

            engine = MitmsEngine(
                label=args.label,
                max_seq_length=args.max_seq_length,
                timeout=args.timeout,
            )
        else:
            from engines.synthetiq import SynthetiqEngine

            engine = SynthetiqEngine(epsilon=args.epsilon, timeout=args.timeout)
        output = engine.run(args.input)
    except Exception as error:  # noqa: BLE001
        raise SystemExit(f"{args.engine} failed: {error}") from None
    print(output, end="" if output.endswith("\n") else "\n")
    print(f"Synthesis time: {engine.elapsed_seconds:.6f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
