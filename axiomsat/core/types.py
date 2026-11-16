"""
Core data types and structures for AxiomSAT.
"""

from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field


class Status(Enum):
    SAT = "SATISFIABLE"
    UNSAT = "UNSATISFIABLE"
    UNKNOWN = "UNKNOWN"


class Value(Enum):
    UNDEF = 0
    FALSE = -1
    TRUE = 1

    @classmethod
    def from_bool(cls, b: bool) -> "Value":
        return cls.TRUE if b else cls.FALSE

    def to_bool(self) -> Optional[bool]:
        if self == Value.TRUE:
            return True
        if self == Value.FALSE:
            return False
        return None


# In DIMACS convention:
# Variable: integer 1, 2, 3, ...
# Literal: x (positive) or -x (negative)
Literal = int
Variable = int
Assignment = Dict[Variable, bool]


def lit_var(lit: Literal) -> Variable:
    """Return the underlying variable of a literal."""
    return abs(lit)


def lit_sign(lit: Literal) -> bool:
    """Return True if positive literal, False if negative."""
    return lit > 0


def lit_neg(lit: Literal) -> Literal:
    """Return the negated literal."""
    return -lit


@dataclass
class Clause:
    """
    Represents a disjunction of literals: (l1 OR l2 OR ... OR lk).
    """
    literals: List[Literal]
    is_learned: bool = False
    activity: float = 0.0

    def __len__(self) -> int:
        return len(self.literals)

    def __iter__(self):
        return iter(self.literals)

    def __repr__(self) -> str:
        tag = " [Learned]" if self.is_learned else ""
        lits_str = " v ".join(f"x{l}" if l > 0 else f"~x{-l}" for l in self.literals)
        return f"({lits_str}){tag}"


@dataclass
class Formula:
    """
    Represents a CNF formula: conjunction of clauses.
    """
    num_vars: int
    clauses: List[Clause] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)

    def add_clause(self, literals: List[Literal], is_learned: bool = False) -> Clause:
        # Eliminate duplicates within a clause
        unique_lits = list(dict.fromkeys(literals))
        c = Clause(literals=unique_lits, is_learned=is_learned)
        self.clauses.append(c)
        for lit in unique_lits:
            v = lit_var(lit)
            if v > self.num_vars:
                self.num_vars = v
        return c

    def __len__(self) -> int:
        return len(self.clauses)

    def __repr__(self) -> str:
        return f"Formula(vars={self.num_vars}, clauses={len(self.clauses)})"
