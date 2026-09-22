# Week-1 Setup Kit — ha-rule-analyzer

Everything here was installed and tested together in a clean sandbox on
2026-09-21, so the versions are known-good. Your part is three copy-paste steps.

## T02 — Python environment
```bash
cd ha-rule-analyzer            # your repo root
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python verify_env.py           # must print "All checks passed ✅"
```
`verify_env.py` doesn't just import the libs — it makes Z3 solve a tiny
conflict, CP-SAT optimize a tiny objective, and PyYAML parse an HA automation,
so a pass means the whole toolchain actually works.

## T03 — Home Assistant in Docker
Needs Docker Desktop (or Docker Engine) installed.
```bash
mkdir -p ha-config
docker compose up -d                       # starts HA at http://localhost:8123
# finish the one-time onboarding in the browser, then:
cp automations/sample_automations.yaml ha-config/automations.yaml
# In HA: Developer Tools → YAML → Reload Automations  (or restart the container)
docker compose logs -f                      # watch it come up
```
`automations/sample_automations.yaml` is seeded with all 5 conflict types plus a
clean negative-control automation. Each block is tagged with its ground-truth
`>>> TYPE:` label, so these double as your first detector test fixtures.

## T06 — Corpus scraper (Week 2, skeleton ready now)
```bash
export GITHUB_TOKEN=ghp_...     # fine-grained PAT, public-repo read is enough
python scrape_corpus.py --source github --max 50
python scrape_corpus.py --source forum  --max 25
```
Output lands in `corpus/raw/` (gitignored) with a `corpus/manifest.csv` that
records each automation's **license** and whether it's redistributable — so you
can build the open benchmark without accidentally shipping GPL/unlicensed rules.
The GitHub path is functional; the forum (Discourse) path is a working pager with
two clearly-marked TODOs for YAML extraction.

## Files
- `requirements.txt` — pinned, verified-compatible versions
- `verify_env.py` — toolchain sanity check
- `docker-compose.yml` — minimal, isolated HA instance
- `automations/sample_automations.yaml` — 10 fixtures (5 conflict types + control)
- `scrape_corpus.py` — license-aware corpus scraper skeleton
