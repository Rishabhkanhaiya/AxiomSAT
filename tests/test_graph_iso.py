"""
Tests for Graph Isomorphism Reduction and SAT Solving.
"""

import networkx as nx
from axiomsat.encoders.graph_isomorphism import encode_graph_isomorphism, decode_isomorphism_solution
from axiomsat.core.solver import CDCLSolver
from axiomsat.core.types import Status


def test_isomorphic_cycle_graphs():
    # G1: 4-cycle (0-1-2-3-0)
    g1 = nx.cycle_graph(4)

    # G2: Isomorphic relabeled 4-cycle
    # Map: 0->A, 1->B, 2->C, 3->D
    mapping_truth = {0: "A", 1: "B", 2: "C", 3: "D"}
    g2 = nx.relabel_nodes(g1, mapping_truth)

    formula, encoder = encode_graph_isomorphism(g1, g2)
    solver = CDCLSolver(formula)
    status, model = solver.solve()

    assert status == Status.SAT
    assert model is not None
    mapping = decode_isomorphism_solution(encoder, model)
    assert len(mapping) == 4
    assert encoder.verify_isomorphism(mapping) is True


def test_non_isomorphic_same_size():
    # G1: 4-cycle (all degrees 2)
    g1 = nx.cycle_graph(4)

    # G2: 4-path (0-1-2-3) has 3 edges, but let's make 4 nodes with degrees: 3, 1, 1, 1 (Star graph)
    # Even if we add an edge, degree sequences or structure will differ
    g2 = nx.star_graph(3)  # 4 nodes: center has deg 3, others deg 1

    formula, encoder = encode_graph_isomorphism(g1, g2)
    solver = CDCLSolver(formula)
    status, model = solver.solve()

    assert status == Status.UNSAT
    assert model is None


def test_petersen_isomorphism():
    # Petersen graph has 10 vertices, 15 edges
    g1 = nx.petersen_graph()
    perm = {i: (i + 3) % 10 for i in range(10)}
    g2 = nx.relabel_nodes(g1, perm)

    formula, encoder = encode_graph_isomorphism(g1, g2)
    solver = CDCLSolver(formula)
    status, model = solver.solve()

    assert status == Status.SAT
    mapping = decode_isomorphism_solution(encoder, model)
    assert encoder.verify_isomorphism(mapping) is True
