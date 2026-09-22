# ha-rule-analyzer

> Neurosymbolic static analysis for detecting and repairing conflicts in Home
> Assistant automation rules — an LLM front-end over a Z3 (SMT) detection core
> and an OR-Tools CP-SAT cost-optimal repair engine.

**Status:** early development · Bachelor's honours thesis (Ontario Tech, 2026–27) ·
supervisor: Prof. Ken Pu

---

## The problem

Home Assistant lets anyone write automations in YAML, but its core has **no
cross-automation conflict detection** — only single-automation tracing and
debugging. When two automations touch the same device or state, they can fight
each other: one opens a window while another runs the heater, two rules racing on
a shared trigger, a rule that can never fire because an earlier one always wins.
Today these bugs are found the hard way, at runtime, in your actual house.

This project analyzes a whole set of automations *statically* — before they run —
and both **explains** and **repairs** the conflicts it finds.

## What it detects

Five conflict types, all decided by an SMT solver rather than heuristics:

1. **Direct action conflict** — two rules drive a shared device/state to
   incompatible values (heat-on vs window-open).
2. **Redundancy** — a rule whose effect is fully covered by another.
3. **Unreachability** — a rule that can never fire given the others.
4. **Loops** — rule A triggers B triggers A …
5. **Shadowing** — an earlier rule always pre-empts a later one.

## How it works

```
messy HA YAML
    │
    ▼
[ LLM front-end ]  ── autoformalizes rules into a clean Intermediate Representation (IR)
    │
    ▼
[ IR + device-state model ]
    │
    ▼
[ Z3 / SMT detection ]  ── sound, decidable checks for the 5 conflict types → counterexamples
    │
    ▼
[ LLM explainer ]  ── turns each solver counterexample into plain English
    │
    ▼
[ OR-Tools CP-SAT repair ]  ── computes the minimal-disruption fix; Z3 re-verifies it
```

The LLM proposes, the solver disposes: every LLM-suggested formalization or repair
is checked by Z3/CP-SAT, so the sound core keeps the neural front-end honest.

## Contribution

<!-- TODO (T05): lock this after the Stage-1 novelty check (T04) is complete.
     Keep it to ~3 honest sentences. Do NOT claim to be first to "use an LLM
     with a solver for smart-home conflicts" — that's already been done
     (SHACR, AutoIoT, TAPChecker/TAPAssure). The defensible, sharpest
     differentiators are the Z3 + CP-SAT repair pairing and the hand-labeled
     Home Assistant corpus. -->

_A three-sentence contribution statement will go here once the novelty check is
locked. Working differentiators: (i) static analysis of real Home Assistant YAML
into an SMT-checkable IR, (ii) Z3 detection of the five inter-automation conflict
types, (iii) an LLM front-end for autoformalization and plain-English
counterexamples, and (iv) CP-SAT **cost-optimal, minimal-disruption** repair,
evaluated on a purpose-built hand-labeled corpus of real HA automations._

## The corpus

Part of this project is a net-new, hand-labeled benchmark of real Home Assistant
automations with their conflicts annotated — released here as an open benchmark
(the first public conflict-labeled HA corpus, to our knowledge). See
[`corpus/`](corpus/).

> **Data note:** some external datasets used for comparison are access-gated and
> **cannot be redistributed** (e.g. the Ur et al. 2016 IFTTT recipes). Do not
> commit any gated third-party data to this repo — see `.gitignore`.

## Install

```bash
# TODO: fill in once the package skeleton lands (T01–T02)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install z3-solver ortools pyyaml requests
```

## Usage

```bash
# TODO: CLI entry point coming in Phase 1
# ha-rule-analyzer path/to/automations.yaml
```

## Roadmap

Detection core → CP-SAT repair → full neurosymbolic loop → HACS add-on + companion
site (v0.1, target Dec 4 2026). See the project board for live status.

## Related work

A full comparison lives in the thesis. In short: prior systems either detect
without repairing (TapChecker-SMT, iRuler, Soteria), repair via automaton editing
or model checking rather than cost optimization (AutoTap, TAPFixer), or verify at
*generation* time rather than analyzing existing rules (AutoIoT,
TAPChecker/TAPAssure). The closest existing system, SHACR, uses a knowledge graph
rather than an SMT solver and does not do cost-optimal repair.

## Citation

```bibtex
@thesis{ericmarkovic2027ha,
  author = {Eric-Markovic, Amelia},
  title  = {Neurosymbolic Static Analysis for Smart-Home Automation Rule Conflicts},
  school = {Ontario Tech University},
  year   = {2027},
  note   = {Bachelor's honours thesis}
}
```

## License

MIT — see [`LICENSE`](LICENSE).

## Acknowledgements

Supervised by Prof. Ken Pu, Ontario Tech University.
