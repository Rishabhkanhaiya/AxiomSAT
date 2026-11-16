"""
Decision heuristics and data structures for CDCL SAT Solving:
1. VSIDS (Variable State Independent Decaying Sum)
2. Two-Watched Literals (2WL) Index
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from .types import Literal, Variable, Clause, lit_var, lit_sign, lit_neg


class VSIDS:
    """
    Variable State Independent Decaying Sum (VSIDS) decision heuristic.
    Pioneered by the Chaff solver, standard in modern CDCL engines.
    """
    def __init__(self, num_vars: int, decay: float = 0.95):
        self.num_vars = num_vars
        self.decay = decay
        self.increment = 1.0
        self.scores: Dict[Variable, float] = {v: 0.0 for v in range(1, num_vars + 1)}
        self.phase_cache: Dict[Variable, bool] = {v: True for v in range(1, num_vars + 1)}

    def bump(self, var: Variable) -> None:
        """Bump activity score for a variable involved in a conflict."""
        if var in self.scores:
            self.scores[var] += self.increment
            if self.scores[var] > 1e100:
                self.rescale()

    def bump_clause(self, clause: Clause) -> None:
        """Bump activity for all variables in a learned or conflict clause."""
        for lit in clause.literals:
            self.bump(lit_var(lit))

    def decay_scores(self) -> None:
        """Decay all scores by scaling the increment."""
        self.increment /= self.decay

    def rescale(self) -> None:
        """Rescale all scores to prevent numeric overflow."""
        for v in self.scores:
            self.scores[v] *= 1e-100
        self.increment *= 1e-100

    def set_phase(self, var: Variable, val: bool) -> None:
        """Save preferred truth value (phase saving)."""
        self.phase_cache[var] = val

    def pick_variable(self, unassigned: Set[Variable]) -> Tuple[Variable, bool]:
        """
        Pick the unassigned variable with the highest activity score.
        Returns (variable, preferred_boolean_value).
        """
        best_var = max(unassigned, key=lambda v: self.scores.get(v, 0.0))
        preferred_phase = self.phase_cache.get(best_var, True)
        return best_var, preferred_phase


class TwoWatchedLiterals:
    """
    Two-Watched Literals (2WL) data structure for ultra-fast Boolean Constraint Propagation.
    """
    def __init__(self, num_vars: int):
        self.num_vars = num_vars
        self.watches: Dict[Literal, List[Clause]] = defaultdict(list)
        # clause_watches[id(clause)] = [w1, w2]
        self.clause_watches: Dict[int, List[Literal]] = {}

    def register_clause(self, clause: Clause) -> Optional[Literal]:
        cid = id(clause)
        lits = clause.literals
        if len(lits) == 0:
            self.clause_watches[cid] = []
            return None
        if len(lits) == 1:
            self.watches[lits[0]].append(clause)
            self.clause_watches[cid] = [lits[0]]
            return lits[0]  # Unit clause immediately

        w1 = lits[0]
        w2 = lits[1]
        self.watches[w1].append(clause)
        self.watches[w2].append(clause)
        self.clause_watches[cid] = [w1, w2]
        return None

    def update_watch(self, cid: int, old_lit: Literal, new_lit: Literal, clause: Clause) -> None:
        """Replaces old_lit with new_lit in the watched list for a clause."""
        if clause in self.watches[old_lit]:
            self.watches[old_lit].remove(clause)
        self.watches[new_lit].append(clause)

        cur = self.clause_watches.get(cid, [])
        if len(cur) >= 2:
            if cur[0] == old_lit:
                cur[0] = new_lit
            elif cur[1] == old_lit:
                cur[1] = new_lit
        self.clause_watches[cid] = cur
