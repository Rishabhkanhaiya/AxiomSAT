"""
AxiomSAT CDCL Solver Engine.
Implements Two-Watched Literals (2WL), Boolean Constraint Propagation (BCP),
1-UIP Conflict Analysis, Non-chronological Backjumping, VSIDS, and Restarts.
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .types import Status, Value, Literal, Variable, Clause, Formula, Assignment, lit_var, lit_neg
from .heuristics import VSIDS, TwoWatchedLiterals
from .implication_graph import ImplicationGraph


@dataclass
class SolverStats:
    decisions: int = 0
    propagations: int = 0
    conflicts: int = 0
    learned_clauses: int = 0
    restarts: int = 0
    solve_time_seconds: float = 0.0

    def summary(self) -> str:
        return (
            f"Decisions: {self.decisions} | "
            f"Propagations: {self.propagations} | "
            f"Conflicts: {self.conflicts} | "
            f"Learned: {self.learned_clauses} | "
            f"Restarts: {self.restarts} | "
            f"Time: {self.solve_time_seconds * 1000:.2f} ms"
        )


class CDCLSolver:
    """
    State-of-the-art CDCL Boolean Satisfiability Solver.
    """
    def __init__(self, formula: Formula, vsids_decay: float = 0.95):
        self.formula = formula
        self.num_vars = formula.num_vars
        self.ig = ImplicationGraph()
        self.vsids = VSIDS(self.num_vars, decay=vsids_decay)
        self.twl = TwoWatchedLiterals(self.num_vars)
        self.stats = SolverStats()
        self.model: Optional[Assignment] = None
        self.status = Status.UNKNOWN

        # Pre-seed VSIDS scores with literal occurrence frequencies
        for clause in formula.clauses:
            for lit in clause.literals:
                self.vsids.scores[lit_var(lit)] += 1.0

        # Register all initial clauses with 2WL
        self.unassigned_vars: Set[Variable] = set(range(1, self.num_vars + 1))
        self.pending_units: List[Tuple[Literal, Optional[Clause]]] = []

        for c in formula.clauses:
            unit = self.twl.register_clause(c)
            if unit is not None:
                self.pending_units.append((unit, c))

    def _assign(self, lit: Literal, level: int, antecedent: Optional[Clause] = None) -> None:
        """Assign variable corresponding to literal to satisfy the literal."""
        var = lit_var(lit)
        val = (lit > 0)
        self.ig.add_assignment(var, val, level, antecedent)
        if var in self.unassigned_vars:
            self.unassigned_vars.remove(var)
        self.vsids.set_phase(var, val)
        self.stats.propagations += 1

    def _bcp(self) -> Optional[Clause]:
        """
        Boolean Constraint Propagation (BCP) using Two-Watched Literals.
        Returns the conflicting clause if a contradiction is encountered, otherwise None.
        """
        # Process any pending unit clauses at level 0 first
        while self.pending_units:
            unit_lit, reason = self.pending_units.pop(0)
            cur_val = self.ig.get_lit_value(unit_lit)
            if cur_val is False:
                return reason  # Root contradiction
            if cur_val is None:
                self._assign(unit_lit, self.ig.current_level(), reason)

        # Propagate through the trail
        trail_idx = 0
        while trail_idx < len(self.ig.trail):
            assigned_lit = self.ig.trail[trail_idx]
            trail_idx += 1

            # A literal assigned_lit is TRUE -> lit_neg(assigned_lit) is FALSE
            falsified_lit = lit_neg(assigned_lit)
            watching_clauses = list(self.twl.watches[falsified_lit])

            for clause in watching_clauses:
                cid = id(clause)
                w_lits = self.twl.clause_watches.get(cid, [])
                if not w_lits:
                    continue

                if len(w_lits) == 1:
                    # Single literal clause
                    if self.ig.get_lit_value(w_lits[0]) is False:
                        return clause
                    continue

                w1, w2 = w_lits[0], w_lits[1]
                other_watched = w2 if w1 == falsified_lit else w1

                # If the other watched literal is TRUE, the clause is already satisfied
                if self.ig.get_lit_value(other_watched) is True:
                    continue

                # Look for a replacement non-falsified literal
                replacement: Optional[Literal] = None
                for candidate in clause.literals:
                    if candidate != w1 and candidate != w2:
                        val = self.ig.get_lit_value(candidate)
                        if val is not False:  # either True or Undefined
                            replacement = candidate
                            break

                if replacement is not None:
                    # Found replacement: update watch
                    self.twl.update_watch(cid, falsified_lit, replacement, clause)
                else:
                    # No replacement found. The other watched literal must be satisfied!
                    other_val = self.ig.get_lit_value(other_watched)
                    if other_val is False:
                        # Conflict! Both watched literals are false and no replacements exist.
                        return clause
                    elif other_val is None:
                        # Unit propagation!
                        self._assign(other_watched, self.ig.current_level(), antecedent=clause)

        return None

    def solve(self, max_conflicts: Optional[int] = None) -> Tuple[Status, Optional[Assignment]]:
        """
        Main CDCL Solving Loop.
        """
        start_time = time.perf_counter()

        # Step 1: Initial BCP at decision level 0
        conflict = self._bcp()
        if conflict is not None:
            self.stats.solve_time_seconds = time.perf_counter() - start_time
            self.status = Status.UNSAT
            return Status.UNSAT, None

        restart_interval = 100
        conflicts_since_restart = 0

        while self.unassigned_vars:
            if max_conflicts and self.stats.conflicts >= max_conflicts:
                self.status = Status.UNKNOWN
                return Status.UNKNOWN, None

            # Pick next decision variable using VSIDS
            var, preferred_phase = self.vsids.pick_variable(self.unassigned_vars)
            self.stats.decisions += 1
            decision_lit = var if preferred_phase else -var

            # Branch: Advance decision level and assign
            new_level = self.ig.new_decision_level()
            self._assign(decision_lit, new_level, antecedent=None)

            # Inner propagation and conflict-resolution loop
            while True:
                conflict = self._bcp()
                if conflict is None:
                    break  # Propagation completed with no contradiction

                # Contradiction detected!
                self.stats.conflicts += 1
                conflicts_since_restart += 1

                if self.ig.current_level() == 0:
                    # Conflict at root level -> UNSAT mathematically proven
                    self.stats.solve_time_seconds = time.perf_counter() - start_time
                    self.status = Status.UNSAT
                    return Status.UNSAT, None

                # 1-UIP Conflict Analysis
                learned_lits, backjump_level = self.ig.analyze_conflict(conflict)
                if backjump_level < 0:
                    self.stats.solve_time_seconds = time.perf_counter() - start_time
                    self.status = Status.UNSAT
                    return Status.UNSAT, None

                # Bump VSIDS activities
                for lit in learned_lits:
                    self.vsids.bump(lit_var(lit))
                self.vsids.decay_scores()

                # Learn the new clause
                learned_clause = self.formula.add_clause(learned_lits, is_learned=True)
                self.stats.learned_clauses += 1
                self.twl.register_clause(learned_clause)

                # Non-chronological Backjumping
                unassigned = self.ig.backtrack_to_level(backjump_level)
                for u in unassigned:
                    self.unassigned_vars.add(u)

                # Unit propagation of the 1-UIP literal at backjump level
                if learned_lits:
                    uip_lit = learned_lits[0]
                    self._assign(uip_lit, backjump_level, antecedent=learned_clause)

            # Luby / Geometric restart check
            if conflicts_since_restart >= restart_interval:
                self.stats.restarts += 1
                conflicts_since_restart = 0
                restart_interval = int(restart_interval * 1.5)
                unassigned = self.ig.backtrack_to_level(0)
                for u in unassigned:
                    self.unassigned_vars.add(u)

        # All variables assigned without conflicts -> SATISFIABLE!
        self.stats.solve_time_seconds = time.perf_counter() - start_time
        self.model = {v: self.ig.get_value(v) for v in range(1, self.num_vars + 1)}
        self.status = Status.SAT
        return Status.SAT, self.model

    def verify_model(self) -> bool:
        """
        Independently checks that every original clause in the formula evaluates to TRUE under self.model.
        """
        if self.model is None:
            return False
        for clause in self.formula.clauses:
            if clause.is_learned:
                continue
            clause_sat = False
            for lit in clause.literals:
                val = self.model.get(lit_var(lit))
                if val is not None and ((lit > 0 and val) or (lit < 0 and not val)):
                    clause_sat = True
                    break
            if not clause_sat:
                return False
        return True
