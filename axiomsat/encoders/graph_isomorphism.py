"""
Algorithmic Graph Theory: Graph Isomorphism to SAT Reduction.

Reduces the problem of checking whether two graphs G1 and G2 are isomorphic
into a Conjunctive Normal Form (CNF) formula.
If the CNF is SATISFIABLE, the graphs are isomorphic, and the satisfying
assignment yields the exact vertex bijection f: V1 -> V2.
If UNSATISFIABLE, the graphs are non-isomorphic.
"""

from typing import Dict, List, Tuple, Optional, Any, Set
import networkx as nx
from axiomsat.core.types import Formula, Assignment


class GraphIsomorphismEncoder:
    """
    Encodes Graph Isomorphism between two graphs G1, G2 into CNF.
    """
    def __init__(self, g1: nx.Graph, g2: nx.Graph, use_degree_pruning: bool = True):
        self.g1 = g1
        self.g2 = g2
        self.use_degree_pruning = use_degree_pruning

        self.nodes1 = sorted(list(g1.nodes()))
        self.nodes2 = sorted(list(g2.nodes()))
        self.n1 = len(self.nodes1)
        self.n2 = len(self.nodes2)

        # Mapping: (u, v) -> variable ID (1-indexed)
        self.var_map: Dict[Tuple[Any, Any], int] = {}
        self.rev_var_map: Dict[int, Tuple[Any, Any]] = {}
        self.num_vars = 0

    def quick_invariant_check(self) -> Tuple[bool, str]:
        """
        Runs fast discrete math invariant checks (vertex count, edge count, degree sequences).
        If any mismatch occurs, graphs are guaranteed non-isomorphic without SAT solving.
        """
        if self.n1 != self.n2:
            return False, f"Vertex count mismatch: |V1|={self.n1} != |V2|={self.n2}"

        e1 = self.g1.number_of_edges()
        e2 = self.g2.number_of_edges()
        if e1 != e2:
            return False, f"Edge count mismatch: |E1|={e1} != |E2|={e2}"

        deg1 = sorted([d for _, d in self.g1.degree()])
        deg2 = sorted([d for _, d in self.g2.degree()])
        if deg1 != deg2:
            return False, f"Degree sequence mismatch: {deg1} != {deg2}"

        return True, "Passed fast graph invariant checks"

    def encode(self) -> Tuple[Formula, bool]:
        """
        Generates the CNF formula for Graph Isomorphism.
        Returns (Formula, is_trivially_unsat).
        """
        passed, reason = self.quick_invariant_check()
        if not passed:
            # Generate trivial UNSAT formula (1 and -1)
            f = Formula(num_vars=1)
            f.comments.append(f"Invariants failed: {reason}")
            f.add_clause([1])
            f.add_clause([-1])
            return f, True

        # Assign boolean variables x_{u, v} for each node u in G1 and v in G2
        var_id = 1
        for u in self.nodes1:
            u_deg = self.g1.degree[u]
            for v in self.nodes2:
                v_deg = self.g2.degree[v]
                if self.use_degree_pruning and u_deg != v_deg:
                    # Incompatible degrees cannot map to each other
                    continue
                self.var_map[(u, v)] = var_id
                self.rev_var_map[var_id] = (u, v)
                var_id += 1

        self.num_vars = var_id - 1
        formula = Formula(num_vars=self.num_vars)
        formula.comments.append(f"Graph Isomorphism: |V|={self.n1}, |E|={self.g1.number_of_edges()}")

        # 1. Bijection Constraint: Each u in G1 must map to AT LEAST ONE v in G2
        for u in self.nodes1:
            lits = [self.var_map[(u, v)] for v in self.nodes2 if (u, v) in self.var_map]
            if not lits:
                # No compatible node for u
                formula.add_clause([1])
                formula.add_clause([-1])
                return formula, True
            formula.add_clause(lits)

        # 2. Bijection Constraint: Each u in G1 maps to AT MOST ONE v in G2 (Function property)
        for u in self.nodes1:
            compat_v = [v for v in self.nodes2 if (u, v) in self.var_map]
            for i in range(len(compat_v)):
                for j in range(i + 1, len(compat_v)):
                    v1 = compat_v[i]
                    v2 = compat_v[j]
                    formula.add_clause([-self.var_map[(u, v1)], -self.var_map[(u, v2)]])

        # 3. Bijection Constraint: Each v in G2 has AT MOST ONE preimage u in G1 (Injective property)
        for v in self.nodes2:
            compat_u = [u for u in self.nodes1 if (u, v) in self.var_map]
            for i in range(len(compat_u)):
                for j in range(i + 1, len(compat_u)):
                    u1 = compat_u[i]
                    u2 = compat_u[j]
                    formula.add_clause([-self.var_map[(u1, v)], -self.var_map[(u2, v)]])

        # 4. Adjacency / Edge Preservation Constraints:
        # If (u1, u2) in E1 and (v1, v2) NOT in E2, cannot map u1->v1 and u2->v2
        for i in range(self.n1):
            for j in range(i + 1, self.n1):
                u1 = self.nodes1[i]
                u2 = self.nodes2[j]
                edge1 = self.g1.has_edge(u1, u2)

                for v1 in self.nodes2:
                    if (u1, v1) not in self.var_map:
                        continue
                    for v2 in self.nodes2:
                        if v1 == v2 or (u2, v2) not in self.var_map:
                            continue
                        edge2 = self.g2.has_edge(v1, v2)

                        # Structural mismatch: edge in one graph but not the other
                        if edge1 != edge2:
                            formula.add_clause([-self.var_map[(u1, v1)], -self.var_map[(u2, v2)]])

        return formula, False

    def decode_solution(self, model: Assignment) -> Dict[Any, Any]:
        """
        Decodes a satisfying assignment model into a node bijection f: V1 -> V2.
        """
        mapping: Dict[Any, Any] = {}
        for var, val in model.items():
            if val and var in self.rev_var_map:
                u, v = self.rev_var_map[var]
                mapping[u] = v
        return mapping

    def verify_isomorphism(self, mapping: Dict[Any, Any]) -> bool:
        """
        Independently checks that mapping is a valid isomorphism between G1 and G2.
        """
        if len(mapping) != self.n1:
            return False
        if len(set(mapping.values())) != self.n2:
            return False

        for u1, u2 in self.g1.edges():
            v1, v2 = mapping[u1], mapping[u2]
            if not self.g2.has_edge(v1, v2):
                return False

        for v1, v2 in self.g2.edges():
            # Invert check
            rev_map = {v: u for u, v in mapping.items()}
            u1, u2 = rev_map[v1], rev_map[v2]
            if not self.g1.has_edge(u1, u2):
                return False

        return True


def encode_graph_isomorphism(g1: nx.Graph, g2: nx.Graph) -> Tuple[Formula, GraphIsomorphismEncoder]:
    encoder = GraphIsomorphismEncoder(g1, g2)
    formula, _ = encoder.encode()
    return formula, encoder


def decode_isomorphism_solution(encoder: GraphIsomorphismEncoder, model: Assignment) -> Dict[Any, Any]:
    return encoder.decode_solution(model)
