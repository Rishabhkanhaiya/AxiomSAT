"""
Implication Graph and 1-UIP Conflict Analysis for AxiomSAT.

The Implication Graph is a Directed Acyclic Graph (DAG) tracking variable assignments,
their decision levels, and the antecedent clauses that caused unit propagations.
When a conflict is reached, 1-UIP (First Unique Implication Point) cut analysis
derives the learned conflict clause via backward binary resolution.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from .types import Literal, Variable, Clause, lit_var, lit_neg


@dataclass
class AssignmentNode:
    """
    A node in the Implication Graph representing an assigned variable.
    """
    var: Variable
    val: bool
    level: int
    antecedent: Optional[Clause] = None  # None if this was a decision variable
    index: int = 0  # Global chronological order index


class ImplicationGraph:
    """
    Manages the Implication Graph and computes 1-UIP learned clauses.
    """
    def __init__(self):
        # nodes[var] = AssignmentNode
        self.nodes: Dict[Variable, AssignmentNode] = {}
        # Chronological assignment trail: list of literals in order of assignment
        self.trail: List[Literal] = []
        # trail_levels[level] = start index in trail for that level
        self.level_markers: List[int] = [0]
        self.current_index: int = 0

    def add_assignment(self, var: Variable, val: bool, level: int, antecedent: Optional[Clause] = None) -> None:
        """Record a variable assignment into the implication graph and trail."""
        node = AssignmentNode(var=var, val=val, level=level, antecedent=antecedent, index=self.current_index)
        self.nodes[var] = node
        lit = var if val else -var
        self.trail.append(lit)
        self.current_index += 1

    def new_decision_level(self) -> int:
        """Mark the beginning of a new decision level."""
        self.level_markers.append(len(self.trail))
        return len(self.level_markers) - 1

    def current_level(self) -> int:
        return len(self.level_markers) - 1

    def is_assigned(self, var: Variable) -> bool:
        return var in self.nodes

    def get_value(self, var: Variable) -> Optional[bool]:
        node = self.nodes.get(var)
        return node.val if node else None

    def get_lit_value(self, lit: Literal) -> Optional[bool]:
        val = self.get_value(lit_var(lit))
        if val is None:
            return None
        return val if lit > 0 else (not val)

    def backtrack_to_level(self, target_level: int) -> List[Variable]:
        """
        Backtracks trail and nodes to target_level.
        Returns the list of unassigned variables.
        """
        if target_level >= len(self.level_markers):
            return []

        cutoff = self.level_markers[target_level + 1] if target_level + 1 < len(self.level_markers) else len(self.trail)
        unassigned_vars = []

        while len(self.trail) > cutoff:
            lit = self.trail.pop()
            v = lit_var(lit)
            if v in self.nodes:
                del self.nodes[v]
                unassigned_vars.append(v)

        del self.level_markers[target_level + 1:]
        return unassigned_vars

    def analyze_conflict(self, conflict_clause: Clause) -> Tuple[List[Literal], int]:
        """
        1-UIP (First Unique Implication Point) Conflict Analysis Algorithm:
        Performs backward resolution from the conflict clause along the implication graph
        until exactly one literal from the current decision level remains.

        Returns:
            (learned_clause_literals, backjump_level)
        """
        d_level = self.current_level()
        if d_level == 0:
            # Unresolvable conflict at root level -> UNSAT
            return [], -1

        learned_lits: Set[Literal] = set(conflict_clause.literals)
        trail_pos = len(self.trail) - 1

        while True:
            # Count literals from current decision level
            current_level_lits = [
                lit for lit in learned_lits
                if self.nodes[lit_var(lit)].level == d_level
            ]

            if len(current_level_lits) <= 1:
                # 1-UIP reached! Exactly one literal at the current decision level.
                break

            # Find the most recently assigned literal from current decision level
            while trail_pos >= 0:
                trail_lit = self.trail[trail_pos]
                trail_pos -= 1
                if trail_lit in learned_lits or lit_neg(trail_lit) in learned_lits:
                    res_var = lit_var(trail_lit)
                    break

            antecedent = self.nodes[res_var].antecedent
            if antecedent is None:
                break

            # Resolution step: Resolve current learned set with antecedent clause
            # Remove the resolved literal (and its negation)
            learned_lits.discard(res_var)
            learned_lits.discard(-res_var)

            for lit in antecedent.literals:
                if lit_var(lit) != res_var:
                    learned_lits.add(lit)

        learned_clause = list(learned_lits)

        # Determine backjump level (2nd highest decision level in learned clause)
        backjump_level = 0
        uip_lit = None
        for lit in learned_clause:
            lvl = self.nodes[lit_var(lit)].level
            if lvl == d_level:
                uip_lit = lit
            elif lvl > backjump_level:
                backjump_level = lvl

        # Ensure 1-UIP literal is at index 0 for 2WL efficiency
        if uip_lit is not None:
            learned_clause.remove(uip_lit)
            learned_clause.insert(0, uip_lit)

        return learned_clause, backjump_level
