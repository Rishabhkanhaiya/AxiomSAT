"""
AxiomSAT Quick Launcher Script.
Run this script to launch the interactive Streamlit Web Visualizer or CLI benchmarks.

Usage:
    python run_demo.py web         # Launches interactive Streamlit dashboard
    python run_demo.py benchmark   # Runs comparative benchmarks vs PySAT (Glucose3)
    python run_demo.py test        # Runs full pytest test suite
"""

import sys
import subprocess
from pathlib import Path

PYTHON_EXE = sys.executable

def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "web"

    if arg == "web":
        print("🚀 Launching AxiomSAT Interactive Web Visualizer...")
        subprocess.run([PYTHON_EXE, "-m", "streamlit", "run", "web/app.py"])

    elif arg == "benchmark":
        print("📊 Running AxiomSAT Benchmarks vs PySAT (Glucose3)...")
        from axiomsat.benchmarks.runner import run_benchmark
        run_benchmark([
            "axiomsat/benchmarks/sample_cnfs/simple_sat.cnf",
            "axiomsat/benchmarks/sample_cnfs/pigeonhole_3_2.cnf"
        ])

    elif arg == "test":
        print("🧪 Running pytest test suite...")
        subprocess.run([PYTHON_EXE, "-m", "pytest", "tests"])

    else:
        print(f"Unknown command: {arg}")
        print("Usage: python run_demo.py [web | benchmark | test]")

if __name__ == "__main__":
    main()
