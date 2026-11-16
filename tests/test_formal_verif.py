"""
Tests for Formal Verification and Circuit Miter Equivalence Checking.
"""

from axiomsat.encoders.formal_verification import Circuit, GateType, encode_miter_to_cnf
from axiomsat.core.solver import CDCLSolver
from axiomsat.core.types import Status


def test_demorgan_equivalence():
    # C1: ~(A and B) using NAND gate
    c1 = Circuit("DeMorgan_NAND")
    c1.add_input("A")
    c1.add_input("B")
    c1.add_gate("out", GateType.NAND, ["A", "B"])
    c1.set_output("out")

    # C2: ~A or ~B
    c2 = Circuit("DeMorgan_OR")
    c2.add_input("A")
    c2.add_input("B")
    c2.add_gate("notA", GateType.NOT, ["A"])
    c2.add_gate("notB", GateType.NOT, ["B"])
    c2.add_gate("out", GateType.OR, ["notA", "notB"])
    c2.set_output("out")

    formula, miter = encode_miter_to_cnf(c1, c2)
    solver = CDCLSolver(formula)
    status, model = solver.solve()

    # Formally verified equivalent -> UNSAT!
    assert status == Status.UNSAT
    assert model is None


def test_buggy_circuit_counterexample():
    # C1: Correct AND gate
    c1 = Circuit("Correct_AND")
    c1.add_input("A")
    c1.add_input("B")
    c1.add_gate("out", GateType.AND, ["A", "B"])
    c1.set_output("out")

    # C2: Faulty circuit (designer accidentally used OR gate)
    c2 = Circuit("Buggy_OR")
    c2.add_input("A")
    c2.add_input("B")
    c2.add_gate("out", GateType.OR, ["A", "B"])
    c2.set_output("out")

    formula, miter = encode_miter_to_cnf(c1, c2)
    solver = CDCLSolver(formula)
    status, model = solver.solve()

    # Discrepancy detected -> SAT!
    assert status == Status.SAT
    assert model is not None

    cex = miter.extract_counterexample(model)
    # Verify counterexample actually produces different outputs
    out1 = c1.evaluate(cex)
    out2 = c2.evaluate(cex)
    assert out1 != out2


def test_full_adder_equivalence():
    # 1-bit Full Adder Implementation 1
    c1 = Circuit("Adder_Impl1")
    c1.add_input("A")
    c1.add_input("B")
    c1.add_input("Cin")
    c1.add_gate("xor1", GateType.XOR, ["A", "B"])
    c1.add_gate("Sum", GateType.XOR, ["xor1", "Cin"])
    c1.add_gate("and1", GateType.AND, ["A", "B"])
    c1.add_gate("and2", GateType.AND, ["xor1", "Cin"])
    c1.add_gate("Cout", GateType.OR, ["and1", "and2"])
    c1.set_output("Sum")
    c1.set_output("Cout")

    # 1-bit Full Adder Implementation 2 (using majority function for Cout: (A&B) | (B&Cin) | (A&Cin))
    c2 = Circuit("Adder_Impl2")
    c2.add_input("A")
    c2.add_input("B")
    c2.add_input("Cin")
    c2.add_gate("xor_ab", GateType.XOR, ["A", "B"])
    c2.add_gate("Sum", GateType.XOR, ["xor_ab", "Cin"])
    c2.add_gate("ab", GateType.AND, ["A", "B"])
    c2.add_gate("bcin", GateType.AND, ["B", "Cin"])
    c2.add_gate("acin", GateType.AND, ["A", "Cin"])
    c2.add_gate("t1", GateType.OR, ["ab", "bcin"])
    c2.add_gate("Cout", GateType.OR, ["t1", "acin"])
    c2.set_output("Sum")
    c2.set_output("Cout")

    formula, miter = encode_miter_to_cnf(c1, c2)
    solver = CDCLSolver(formula)
    status, model = solver.solve()

    # Formally verified equivalent -> UNSAT!
    assert status == Status.UNSAT
