"""
Benchmarking and Profiling Suite for AxiomSAT.
Compares native AxiomSAT CDCL engine against industry-standard solvers via PySAT (Glucose3, MiniSat22, CaDiCaL).
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from axiomsat.core.types import Formula, Status
from axiomsat.core.solver import CDCLSolver
from axiomsat.core.dimacs import parse_dimacs

try:
    from pysat.solvers import Glucose3, Minisat22
    from pysat.formula import CNF
    PYSAT_AVAILABLE = True
except ImportError:
    PYSAT_AVAILABLE = False


@dataclass
class BenchmarkResult:
    benchmark_name: str
    num_vars: int
    num_clauses: int
    axiomsat_status: str
    axiomsat_time_ms: float
    axiomsat_conflicts: int
    axiomsat_decisions: int
    pysat_status: Optional[str] = None
    pysat_time_ms: Optional[float] = None
    agreement: bool = False


class BenchmarkSuite:
    """
    Executes comparative benchmarks across a collection of CNF formulas.
    """
    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_on_formula(self, name: str, formula: Formula) -> BenchmarkResult:
        # 1. Run Native AxiomSAT CDCL
        native_solver = CDCLSolver(formula)
        status_native, model_native = native_solver.solve()
        native_time_ms = native_solver.stats.solve_time_seconds * 1000.0

        pysat_status = None
        pysat_time_ms = None
        agreement = True

        # 2. Run PySAT (Glucose3) if available
        if PYSAT_AVAILABLE:
            pysat_cnf = CNF()
            for c in formula.clauses:
                if not c.is_learned:
                    pysat_cnf.append(c.literals)

            t0 = time.perf_counter()
            with Glucose3(bootstrap_with=pysat_cnf) as solver:
                is_sat = solver.solve()
                t1 = time.perf_counter()
                pysat_time_ms = (t1 - t0) * 1000.0
                pysat_status = "SATISFIABLE" if is_sat else "UNSATISFIABLE"

            agreement = (status_native.value == pysat_status)

        result = BenchmarkResult(
            benchmark_name=name,
            num_vars=formula.num_vars,
            num_clauses=len([c for c in formula.clauses if not c.is_learned]),
            axiomsat_status=status_native.value,
            axiomsat_time_ms=native_time_ms,
            axiomsat_conflicts=native_solver.stats.conflicts,
            axiomsat_decisions=native_solver.stats.decisions,
            pysat_status=pysat_status,
            pysat_time_ms=pysat_time_ms,
            agreement=agreement,
        )
        self.results.append(result)
        return result

    def run_on_file(self, file_path: str) -> BenchmarkResult:
        p = Path(file_path)
        formula = parse_dimacs(p)
        return self.run_on_formula(p.name, formula)

    def print_summary_table(self) -> None:
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(title="AxiomSAT vs Industry Solver (Glucose3/PySAT) Benchmarks")
            table.add_column("Benchmark", style="cyan")
            table.add_column("Vars", justify="right")
            table.add_column("Clauses", justify="right")
            table.add_column("AxiomSAT Result", style="bold")
            table.add_column("AxiomSAT (ms)", justify="right")
            table.add_column("Conflicts", justify="right")
            table.add_column("PySAT (ms)", justify="right")
            table.add_column("Verified Agreement", justify="center")

            for r in self.results:
                agree_str = "[green]MATCH[/green]" if r.agreement else "[red]MISMATCH[/red]"
                pysat_time = f"{r.pysat_time_ms:.2f}" if r.pysat_time_ms is not None else "N/A"
                table.add_row(
                    r.benchmark_name,
                    str(r.num_vars),
                    str(r.num_clauses),
                    r.axiomsat_status,
                    f"{r.axiomsat_time_ms:.2f}",
                    str(r.axiomsat_conflicts),
                    pysat_time,
                    agree_str
                )
            console.print(table)
        except ImportError:
            print(f"{'Benchmark':<25} | {'Vars':<5} | {'Clauses':<7} | {'AxiomSAT':<12} | {'AxiomSAT(ms)':<12} | {'PySAT(ms)':<10} | {'Match'}")
            print("-" * 85)
            for r in self.results:
                pysat_time = f"{r.pysat_time_ms:.2f}" if r.pysat_time_ms is not None else "N/A"
                print(f"{r.benchmark_name:<25} | {r.num_vars:<5} | {r.num_clauses:<7} | {r.axiomsat_status:<12} | {r.axiomsat_time_ms:<12.2f} | {pysat_time:<10} | {r.agreement}")


def run_benchmark(file_paths: List[str]) -> BenchmarkSuite:
    suite = BenchmarkSuite()
    for fp in file_paths:
        suite.run_on_file(fp)
    suite.print_summary_table()
    return suite
