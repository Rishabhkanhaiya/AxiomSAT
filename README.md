# AxiomSAT ⚡
> **A CDCL-Based Boolean Satisfiability (SAT) Engine with Graph Isomorphism and Formal Verification Benchmarking**

---

## 📌 Project Overview
**AxiomSAT** is a high-performance modern Boolean Satisfiability (SAT) solver built from first principles for Discrete Mathematics and Theoretical Computer Science. It implements the industrial-grade **Conflict-Driven Clause Learning (CDCL)** algorithm, featuring Two-Watched Literals (2WL), Boolean Constraint Propagation (BCP), Dynamic Implication Graph construction, 1-UIP (Unique Implication Point) conflict analysis, non-chronological backjumping, and VSIDS (Variable State Independent Decaying Sum) decision heuristics.

Beyond solving raw propositional formulas in DIMACS CNF format, AxiomSAT bridges **Propositional Logic**, **Algorithmic Graph Theory**, and **Formal Methods** through:
1. **Graph Isomorphism Reduction**: Encoding the classic graph isomorphism problem into CNF to decide topological equivalence of graph pairs.
2. **Formal Verification Benchmarking**: Equivalence checking of combinational logic circuits via Miter formulation to guarantee hardware correctness.
3. **Interactive Visualizer**: A visual learning platform showing live implication graphs, conflict cuts, and step-by-step CDCL search trees.

---

## 📐 Theoretical Foundations (Discrete Mathematics)

```
                            ┌────────────────────────────────────────┐
                            │        Discrete Mathematics Core       │
                            └───────────────────┬────────────────────┘
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
┌──────────────────┐                  ┌──────────────────┐                  ┌──────────────────┐
│  Propositional   │                  │   Algorithmic    │                  │  Formal Methods  │
│      Logic       │                  │   Graph Theory   │                  │  & Verification  │
├──────────────────┤                  ├──────────────────┤                  ├──────────────────┤
│ • CNF Formulas   │                  │ • Implication DAG│                  │ • Circuit Miters │
│ • Resolution Rule│                  │ • Graph Isomorph.│                  │ • Equivalence    │
│ • Boolean Satisf.│                  │ • Graph Coloring │                  │ • Counterexamples│
│ • NP-Complete    │                  │ • 1-UIP Cuts     │                  │ • Model Checking │
└──────────────────┘                  └──────────────────┘                  └──────────────────┘
```

1. **Propositional Logic & CNF**:
   Any propositional formula can be expressed in Conjunctive Normal Form (CNF):
   $$\Phi = \bigwedge_{i=1}^{m} \left( \bigvee_{j=1}^{k_i} l_{i,j} \right)$$
   where $l_{i,j}$ are literals (variables $x$ or their negations $\neg x$).

2. **Conflict-Driven Clause Learning (CDCL)**:
   Unlike naive DPLL which does chronological backtracking, CDCL:
   - Tracks variable assignments in an **Implication Graph**.
   - Identifies the root cause of contradictions using **1-UIP (First Unique Implication Point)** graph cut.
   - Derives and learns new clauses using the **Resolution Rule**:
     $$\frac{A \lor x \quad B \lor \neg x}{A \lor B}$$
   - Executes **non-chronological backjumping**, bypassing exponentially many invalid assignments.

3. **Graph Isomorphism via SAT Reduction**:
   Given two graphs $G_1 = (V_1, E_1)$ and $G_2 = (V_2, E_2)$ with $|V_1| = |V_2| = n$:
   - Let boolean variable $x_{u, v}$ be `TRUE` iff vertex $u \in V_1$ is mapped to $v \in V_2$.
   - **Bijection Constraints**:
     - At least one mapping: $\forall u \in V_1, \bigvee_{v \in V_2} x_{u, v}$
     - At most one mapping: $\forall u \in V_1, \forall v \neq w, (\neg x_{u, v} \lor \neg x_{u, w})$
     - Injective mapping: $\forall v \in V_2, \forall u \neq w, (\neg x_{u, v} \lor \neg x_{w, v})$
   - **Adjacency / Edge Preservation Constraints**:
     $$\forall (u_1, u_2) \in E_1 \text{ and } (v_1, v_2) \notin E_2 \implies (\neg x_{u_1, v_1} \lor \neg x_{u_2, v_2})$$
     $$\forall (u_1, u_2) \notin E_1 \text{ and } (v_1, v_2) \in E_2 \implies (\neg x_{u_1, v_1} \lor \neg x_{u_2, v_2})$$

4. **Formal Circuit Equivalence (Miter Formulation)**:
   Given two circuits $C_1(\vec{x})$ and $C_2(\vec{x})$, construct miter output:
   $$M(\vec{x}) = C_1(\vec{x}) \oplus C_2(\vec{x})$$
   AxiomSAT tests the satisfiability of $M(\vec{x}) = 1$:
   - **UNSAT** $\implies$ $C_1 \equiv C_2$ (Mathematically proven identical).
   - **SAT** $\implies$ Assignment represents a counterexample where $C_1(\vec{x}) \neq C_2(\vec{x})$.

---

## 📂 Repository Structure

```
dm-course [project]/
├── README.md                          # Project documentation & math foundations
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Package configuration
│
├── axiomsat/                          # Main Python Package
│   ├── __init__.py
│   ├── core/                          # CDCL Core Engine
│   │   ├── __init__.py
│   │   ├── types.py                   # Literals, Clauses, Status definitions
│   │   ├── dimacs.py                  # DIMACS CNF Parser and Writer
│   │   ├── implication_graph.py       # DAG representation & 1-UIP Cut Algorithm
│   │   ├── heuristics.py              # 2-Watched Literals & VSIDS
│   │   └── solver.py                  # Complete CDCL Solver implementation
│   │
│   ├── encoders/                      # Reductions from Discrete Math to CNF
│   │   ├── __init__.py
│   │   ├── graph_isomorphism.py       # Graph Isomorphism to CNF encoder
│   │   ├── graph_coloring.py          # Vertex k-Coloring to CNF encoder
│   │   └── formal_verification.py     # Circuit Miter Equivalence encoder
│   │
│   └── benchmarks/                    # Benchmark suite & data
│       ├── __init__.py
│       ├── runner.py                  # Profiler & benchmark executor
│       ├── sample_cnfs/               # Standard SAT/UNSAT test cases
│       └── sample_graphs/             # Benchmark graph pairs
│
├── web/                               # Interactive Web Application
│   ├── app.py                         # Streamlit Interactive Dashboard
│   └── visualizer.py                  # Graphviz & NetworkX graph renderer
│
└── tests/                             # Unit & Integration Tests
    ├── test_solver.py                 # Core CDCL tests
    ├── test_graph_iso.py              # Isomorphism reduction tests
    └── test_formal_verif.py           # Circuit equivalence tests
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Virtual environment recommended

### 2. Setup
```bash
pip install -r requirements.txt
```

### 3. Run AxiomSAT CLI
```bash
# Solve a DIMACS CNF formula
python -m axiomsat.core.solver benchmarks/sample_cnfs/pigeonhole_3_2.cnf

# Check Graph Isomorphism
python -m axiomsat.encoders.graph_isomorphism --graph1 g1.json --graph2 g2.json
```

### 4. Launch Interactive Visualizer
```bash
streamlit run web/app.py
```
