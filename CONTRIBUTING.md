# Contributing

Thanks for your interest! This project is a research tool + open benchmark for
detecting and repairing conflicts in Home Assistant automations. Contributions,
bug reports, and — especially — **real-world conflicting automations for the
corpus** are all welcome.

> This is an active thesis project. Until v0.1 the internals move fast; open an
> issue before starting anything large so we don't collide.

## Ways to help

- **Report a conflict from your own setup.** If two of your automations fight,
  open an issue with the (anonymized) YAML and what went wrong. These become
  labeled corpus entries — the single most valuable contribution.
- **Report a bug** in the analyzer (a false positive, a missed conflict, a
  parser crash on valid YAML).
- **Improve detection / repair / the IR.** See open issues tagged
  `good first issue`.

## Development setup

```bash
git clone https://github.com/<your-username>/ha-rule-analyzer.git
cd ha-rule-analyzer
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install z3-solver ortools pyyaml requests
# TODO: pip install -e . once packaging lands
```

## The five conflict types

When filing a conflict, please label it with the type if you can:

| Type | Meaning |
|------|---------|
| **Direct action conflict** | Two rules drive a shared device/state to incompatible values |
| **Redundancy** | A rule fully covered by another |
| **Unreachability** | A rule that can never fire |
| **Loop** | A → B → A trigger chains |
| **Shadowing** | An earlier rule always pre-empts a later one |

## Filing issues

Please use the issue templates (bug report / conflict report / feature request).
Include your Home Assistant version and a **minimal** pair of automations that
reproduces the problem — anonymize entity names and remove any secrets.

## Pull requests

1. Branch off `main` (e.g. `feature/detect-loops`, `fix/yaml-parser`).
2. Keep PRs focused and small.
3. Make sure the test suite passes and add a test for anything you fix.
4. Reference the issue it closes (`Closes #123`).

## Data & privacy

**Never** commit secrets (API keys, tokens) or access-gated third-party datasets.
Only cleaned, licensed, anonymized automations belong in `corpus/`. See
`.gitignore`.

## License

By contributing you agree your contributions are licensed under the project's MIT
License.
