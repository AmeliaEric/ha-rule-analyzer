#!/usr/bin/env python3
"""
verify_env.py  —  T02 sanity check for the ha-rule-analyzer stack.

Run this right after `pip install -r requirements.txt`. It confirms that
z3, OR-Tools CP-SAT, PyYAML, and requests all import AND actually solve a
tiny problem — so you know the toolchain works before you build on it.

    python verify_env.py

Exits 0 if everything passes, 1 otherwise.
"""
import sys

def check_versions():
    import z3, ortools, yaml, requests
    print(f"  z3-solver : {z3.get_version_string()}")
    print(f"  ortools   : {ortools.__version__}")
    print(f"  PyYAML    : {yaml.__version__}")
    print(f"  requests  : {requests.__version__}")

def check_z3():
    """Prove Z3 can find a model — the heart of the detection layer."""
    from z3 import Ints, Solver, sat
    heat, window = Ints('heat window')  # 1 = on/open, 0 = off/closed
    s = Solver()
    # A toy 'direct action conflict': heater on while window open.
    s.add(heat == 1, window == 1)
    assert s.check() == sat, "Z3 failed to solve a trivial SAT instance"
    m = s.model()
    print(f"  Z3 counterexample found: heat={m[heat]}, window={m[window]}  (SAT ✓)")

def check_cpsat():
    """Prove OR-Tools CP-SAT can optimize — the heart of the repair layer."""
    from ortools.sat.python import cp_model
    model = cp_model.CpModel()
    x = model.NewIntVar(0, 10, 'x')
    y = model.NewIntVar(0, 10, 'y')
    model.Add(x + y == 10)
    model.Minimize(x)               # minimal-edit style objective
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), "CP-SAT failed"
    print(f"  CP-SAT optimum found: x={solver.Value(x)}, y={solver.Value(y)}  (OPTIMAL ✓)")

def check_yaml():
    """Prove PyYAML parses a Home Assistant automation."""
    import yaml
    doc = yaml.safe_load(
        "- alias: test\n"
        "  trigger:\n"
        "    - platform: numeric_state\n"
        "      entity_id: sensor.temp\n"
        "      below: 18\n"
        "  action:\n"
        "    - service: climate.turn_on\n"
        "      target: {entity_id: climate.living_room}\n"
    )
    assert doc[0]["alias"] == "test", "PyYAML parsed HA automation incorrectly"
    print(f"  PyYAML parsed automation: alias={doc[0]['alias']!r}  (✓)")

def main():
    print("ha-rule-analyzer environment check")
    print("-" * 40)
    ok = True
    for name, fn in [
        ("versions", check_versions),
        ("z3 solve", check_z3),
        ("cp-sat optimize", check_cpsat),
        ("yaml parse", check_yaml),
    ]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {name} FAILED: {e}")
            ok = False
    print("-" * 40)
    if ok:
        print("All checks passed — you're ready to build. ✅")
        return 0
    print("Some checks failed — fix the above before continuing.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
