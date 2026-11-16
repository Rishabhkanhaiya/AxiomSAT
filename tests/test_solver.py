"""
Tests for AxiomSAT CDCL Solver Engine.
"""

from pathlib import Path
from axiomsat.core.types import Formula, Status
from axiomsat.core.dimacs import parse_dimacs
from axiomsat.core.solver import CDCLSolver


def test_simple_sat():
    # (x1 or x2) and (~x1 or x3) and (~x2 or ~x3)
    f = Formula(num_vars=3)
    f.add_clause([1, 2])
    f.add_clause([-1, 3])
    f.add_clause([-2, -3])

    solver = CDCLSolver(f)
    status, model = solver.solve()
    assert status == Status.SAT
    assert model is not None
    assert solver.verify_model() is True


def test_simple_unsat():
    # x1 and ~x1 (trivial contradiction)
    f = Formula(num_vars=1)
    f.add_clause([1])
    f.add_clause([-1])

    solver = CDCLSolver(f)
    status, model = solver.solve()
    assert status == Status.UNSAT
    assert model is None


def test_pigeonhole_unsat():
    # 3 pigeons into 2 holes -> mathematically proven UNSAT
    p = Path("axiomsat/benchmarks/sample_cnfs/pigeonhole_3_2.cnf")
    f = parse_dimacs(p)
    solver = CDCLSolver(f)
    status, model = solver.solve()
    assert status == Status.UNSAT
    assert model is None
    assert solver.stats.conflicts > 0
    assert solver.stats.learned_clauses > 0
