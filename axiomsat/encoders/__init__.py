"""
Encoders for Discrete Mathematics Reductions to SAT:
1. Graph Isomorphism -> CNF
2. Formal Verification / Circuit Miter Equivalence -> CNF
"""

from .graph_isomorphism import (
    GraphIsomorphismEncoder,
    encode_graph_isomorphism,
    decode_isomorphism_solution,
)
from .formal_verification import (
    Circuit,
    Gate,
    GateType,
    Miter,
    encode_miter_to_cnf,
)

__all__ = [
    "GraphIsomorphismEncoder",
    "encode_graph_isomorphism",
    "decode_isomorphism_solution",
    "Circuit",
    "Gate",
    "GateType",
    "Miter",
    "encode_miter_to_cnf",
]
