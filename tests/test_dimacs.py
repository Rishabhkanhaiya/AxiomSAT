"""
Tests for DIMACS CNF Parser and Writer.
"""

from pathlib import Path
from axiomsat.core.dimacs import parse_dimacs, write_dimacs
from axiomsat.core.types import Formula


def test_parse_simple_cnf():
    cnf_text = """
    c Sample test formula
    p cnf 3 2
    1 -2 0
    2 3 0
    """
    formula = parse_dimacs(cnf_text)
    assert formula.num_vars == 3
    assert len(formula.clauses) == 2
    assert formula.clauses[0].literals == [1, -2]
    assert formula.clauses[1].literals == [2, 3]


def test_write_and_reparse():
    f = Formula(num_vars=4)
    f.add_clause([1, 2, -3])
    f.add_clause([-1, 4])
    serialized = write_dimacs(f)
    f_restored = parse_dimacs(serialized)
    assert f_restored.num_vars == 4
    assert len(f_restored.clauses) == 2
    assert f_restored.clauses[0].literals == [1, 2, -3]
    assert f_restored.clauses[1].literals == [-1, 4]


def test_parse_sample_file():
    sample_path = Path("axiomsat/benchmarks/sample_cnfs/pigeonhole_3_2.cnf")
    if sample_path.exists():
        formula = parse_dimacs(sample_path)
        assert formula.num_vars == 6
        assert len(formula.clauses) == 9
