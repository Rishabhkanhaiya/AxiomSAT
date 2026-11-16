"""
Formal Methods & Verification: Combinational Equivalence Checking (CEC) via Miter Circuit.

Constructs a Miter circuit comparing two digital logic circuits C1 and C2 sharing
identical inputs. Translates gate logic into CNF via Tseitin Transformation and
asserts that the outputs differ.
- UNSAT -> Circuits are formally proven identical across all 2^n inputs.
- SAT   -> Counterexample input vector is found exposing a design bug or discrepancy.
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from axiomsat.core.types import Formula, Clause, Literal, Assignment


class GateType(Enum):
    INPUT = "INPUT"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"
    NAND = "NAND"
    NOR = "NOR"
    XNOR = "XNOR"


@dataclass
class Gate:
    name: str
    gate_type: GateType
    inputs: List[str] = field(default_factory=list)


class Circuit:
    """
    Represents a digital logic circuit DAG.
    """
    def __init__(self, name: str = "Circuit"):
        self.name = name
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.gates: Dict[str, Gate] = {}

    def add_input(self, name: str) -> None:
        if name not in self.inputs:
            self.inputs.append(name)
            self.gates[name] = Gate(name=name, gate_type=GateType.INPUT)

    def add_gate(self, name: str, gate_type: GateType, in_nodes: List[str]) -> None:
        self.gates[name] = Gate(name=name, gate_type=gate_type, inputs=in_nodes)

    def set_output(self, name: str) -> None:
        if name not in self.outputs:
            self.outputs.append(name)

    def evaluate(self, input_vals: Dict[str, bool]) -> Dict[str, bool]:
        """Simulates circuit on an input vector."""
        values: Dict[str, bool] = dict(input_vals)

        def eval_node(node: str) -> bool:
            if node in values:
                return values[node]
            g = self.gates[node]
            in_vals = [eval_node(inp) for inp in g.inputs]

            if g.gate_type == GateType.INPUT:
                res = values.get(node, False)
            elif g.gate_type == GateType.NOT:
                res = not in_vals[0]
            elif g.gate_type == GateType.AND:
                res = all(in_vals)
            elif g.gate_type == GateType.OR:
                res = any(in_vals)
            elif g.gate_type == GateType.XOR:
                res = in_vals[0] ^ in_vals[1]
            elif g.gate_type == GateType.NAND:
                res = not all(in_vals)
            elif g.gate_type == GateType.NOR:
                res = not any(in_vals)
            elif g.gate_type == GateType.XNOR:
                res = not (in_vals[0] ^ in_vals[1])
            else:
                raise ValueError(f"Unknown gate {g.gate_type}")

            values[node] = res
            return res

        return {out: eval_node(out) for out in self.outputs}


class Miter:
    """
    Constructs a Miter circuit between Circuit C1 and Circuit C2.
    Asserts Miter Output = XOR(Out1, Out2) == 1.
    """
    def __init__(self, c1: Circuit, c2: Circuit):
        if c1.inputs != c2.inputs:
            raise ValueError(f"Circuits must share identical inputs. C1: {c1.inputs}, C2: {c2.inputs}")
        if len(c1.outputs) != len(c2.outputs):
            raise ValueError(f"Output count mismatch: C1={len(c1.outputs)}, C2={len(c2.outputs)}")

        self.c1 = c1
        self.c2 = c2
        self.var_map: Dict[str, int] = {}
        self.rev_var_map: Dict[int, str] = {}
        self.var_counter = 0

    def _get_var(self, name: str) -> int:
        if name not in self.var_map:
            self.var_counter += 1
            self.var_map[name] = self.var_counter
            self.rev_var_map[self.var_counter] = name
        return self.var_map[name]

    def _add_gate_cnf(self, formula: Formula, out_var: int, gate_type: GateType, in_vars: List[int]) -> None:
        """Tseitin transformation rules for elementary logic gates."""
        if gate_type == GateType.NOT:
            a = in_vars[0]
            formula.add_clause([out_var, a])
            formula.add_clause([-out_var, -a])

        elif gate_type == GateType.AND:
            a, b = in_vars[0], in_vars[1]
            formula.add_clause([-a, -b, out_var])
            formula.add_clause([a, -out_var])
            formula.add_clause([b, -out_var])

        elif gate_type == GateType.OR:
            a, b = in_vars[0], in_vars[1]
            formula.add_clause([a, b, -out_var])
            formula.add_clause([-a, out_var])
            formula.add_clause([-b, out_var])

        elif gate_type == GateType.XOR:
            a, b = in_vars[0], in_vars[1]
            formula.add_clause([-a, -b, -out_var])
            formula.add_clause([a, b, -out_var])
            formula.add_clause([a, -b, out_var])
            formula.add_clause([-a, b, out_var])

        elif gate_type == GateType.NAND:
            a, b = in_vars[0], in_vars[1]
            formula.add_clause([-a, -b, -out_var])
            formula.add_clause([a, out_var])
            formula.add_clause([b, out_var])

        elif gate_type == GateType.NOR:
            a, b = in_vars[0], in_vars[1]
            formula.add_clause([a, b, out_var])
            formula.add_clause([-a, -out_var])
            formula.add_clause([-b, -out_var])

        elif gate_type == GateType.XNOR:
            a, b = in_vars[0], in_vars[1]
            formula.add_clause([-a, -b, out_var])
            formula.add_clause([a, b, out_var])
            formula.add_clause([a, -b, -out_var])
            formula.add_clause([-a, b, -out_var])

    def encode(self) -> Formula:
        """Encodes full miter circuit into CNF."""
        formula = Formula(num_vars=0)
        formula.comments.append(f"Formal Verification Miter: {self.c1.name} vs {self.c2.name}")

        # 1. Primary Inputs (shared between C1 and C2)
        for inp in self.c1.inputs:
            self._get_var(f"IN_{inp}")

        # 2. Tseitin translation for Circuit 1
        for g_name, gate in self.c1.gates.items():
            if gate.gate_type == GateType.INPUT:
                continue
            out_v = self._get_var(f"C1_{g_name}")
            in_vs = [
                self._get_var(f"IN_{i}") if i in self.c1.inputs else self._get_var(f"C1_{i}")
                for i in gate.inputs
            ]
            self._add_gate_cnf(formula, out_v, gate.gate_type, in_vs)

        # 3. Tseitin translation for Circuit 2
        for g_name, gate in self.c2.gates.items():
            if gate.gate_type == GateType.INPUT:
                continue
            out_v = self._get_var(f"C2_{g_name}")
            in_vs = [
                self._get_var(f"IN_{i}") if i in self.c2.inputs else self._get_var(f"C2_{i}")
                for i in gate.inputs
            ]
            self._add_gate_cnf(formula, out_v, gate.gate_type, in_vs)

        # 4. Miter XOR gates comparing corresponding outputs
        diff_vars: List[int] = []
        for i, (out1, out2) in enumerate(zip(self.c1.outputs, self.c2.outputs)):
            out1_v = self._get_var(f"IN_{out1}") if out1 in self.c1.inputs else self._get_var(f"C1_{out1}")
            out2_v = self._get_var(f"IN_{out2}") if out2 in self.c2.inputs else self._get_var(f"C2_{out2}")
            diff_v = self._get_var(f"MITER_DIFF_{i}")
            self._add_gate_cnf(formula, diff_v, GateType.XOR, [out1_v, out2_v])
            diff_vars.append(diff_v)

        # 5. Final assertion: At least one output differs
        # (diff_0 OR diff_1 OR ... OR diff_k) = TRUE
        formula.add_clause(diff_vars)

        formula.num_vars = self.var_counter
        return formula

    def extract_counterexample(self, model: Assignment) -> Dict[str, bool]:
        """Extracts primary input values that trigger difference between circuits."""
        counterexample: Dict[str, bool] = {}
        for inp in self.c1.inputs:
            var_name = f"IN_{inp}"
            var_id = self.var_map.get(var_name)
            if var_id and var_id in model:
                counterexample[inp] = bool(model[var_id])
        return counterexample


def encode_miter_to_cnf(c1: Circuit, c2: Circuit) -> Tuple[Formula, Miter]:
    miter = Miter(c1, c2)
    formula = miter.encode()
    return formula, miter
