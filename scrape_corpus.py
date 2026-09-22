#!/usr/bin/env python3
"""
scrape_corpus.py  —  corpus scraper skeleton for ha-rule-analyzer (T06)

Pulls real Home Assistant automations from two sources:
  1. GitHub  — public `automations.yaml` files via the code-search API.
  2. HA forum — Blueprints from the Home Assistant community (Discourse) forum.

Design goals (why it's built this way):
  * LICENSE-AWARE. For every GitHub hit it records the repo's license, because
    you can only *redistribute* automations under a permissive license in your
    open benchmark. Nothing is filtered out for you — it's recorded so you can
    decide. GPL/AGPL/unlicensed items are flagged, not silently included.
  * DEDUP by content hash, so forks and copy-paste don't inflate the corpus.
  * POLITE. Honors GitHub's rate-limit headers and sleeps rather than hammering.
  * RESUMABLE. Writes one JSON record per automation to corpus/raw/ plus a
    manifest.csv; re-running skips hashes already seen.

Raw output lands in corpus/raw/ which is .gitignored (see repo .gitignore):
commit only the cleaned, license-cleared, hand-labeled subset.

Setup:
    export GITHUB_TOKEN=ghp_...        # a fine-grained PAT, public-repo read is enough
    python scrape_corpus.py --source github --max 200
    python scrape_corpus.py --source forum  --max 100

This is a SKELETON: the GitHub path is functional; the forum path gives you a
working Discourse pager to point at the Blueprints Exchange category and adapt.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

GITHUB_API = "https://api.github.com"
FORUM_BASE = "https://community.home-assistant.io"
# Blueprints Exchange category on the HA Discourse forum:
FORUM_BLUEPRINTS_CATEGORY = "blueprints-exchange/53"

OUT_DIR = Path("corpus/raw")
MANIFEST = Path("corpus/manifest.csv")

PERMISSIVE = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "cc0-1.0", "unlicense"}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _session(token: str | None) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json",
                      "User-Agent": "ha-rule-analyzer-corpus/0.1"})
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


def _respect_rate_limit(resp: requests.Response) -> None:
    """Sleep if we're about to run out of GitHub search quota."""
    remaining = resp.headers.get("X-RateLimit-Remaining")
    reset = resp.headers.get("X-RateLimit-Reset")
    if remaining is not None and int(remaining) <= 1 and reset:
        wait = max(0, int(reset) - int(time.time())) + 2
        print(f"  rate limit hit — sleeping {wait}s", file=sys.stderr)
        time.sleep(wait)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def _seen_hashes() -> set[str]:
    if not MANIFEST.exists():
        return set()
    with MANIFEST.open() as f:
        return {row["hash"] for row in csv.DictReader(f)}


def _record(rec: dict, seen: set[str]) -> bool:
    """Write one automation record + append to manifest. Returns True if new."""
    h = rec["hash"]
    if h in seen:
        return False
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{rec['source']}_{h}.json").write_text(json.dumps(rec, indent=2))
    new_file = not MANIFEST.exists()
    with MANIFEST.open("a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["hash", "source", "repo_or_topic", "url", "license", "redistributable"])
        w.writerow([h, rec["source"], rec.get("repo", ""), rec["url"],
                    rec.get("license", ""), rec.get("redistributable", "")])
    seen.add(h)
    return True


# --------------------------------------------------------------------------- #
# GitHub
# --------------------------------------------------------------------------- #
def scrape_github(session: requests.Session, max_items: int, seen: set[str]) -> int:
    """Find public automations.yaml files via code search."""
    added = 0
    # GitHub code search: filename + likely-HA content anchor to cut noise.
    query = 'filename:automations.yaml "platform:" "service:"'
    page = 1
    while added < max_items:
        resp = session.get(f"{GITHUB_API}/search/code",
                           params={"q": query, "per_page": 30, "page": page})
        if resp.status_code == 401:
            print("  GitHub code search needs auth — set GITHUB_TOKEN.", file=sys.stderr)
            break
        if resp.status_code == 403:
            _respect_rate_limit(resp)
            continue
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            break
        for it in items:
            if added >= max_items:
                break
            repo = it["repository"]["full_name"]
            raw = _fetch_github_file(session, it["url"])
            if raw is None:
                continue
            lic = _fetch_github_license(session, repo)
            rec = {
                "source": "github",
                "repo": repo,
                "url": it["html_url"],
                "license": lic,
                "redistributable": lic in PERMISSIVE,
                "hash": _content_hash(raw),
                "content": raw,
            }
            if _record(rec, seen):
                added += 1
                print(f"  + [{added}] {repo}  ({lic or 'no-license'})")
        _respect_rate_limit(resp)
        page += 1
        time.sleep(1)  # be polite
    return added


def _fetch_github_file(session: requests.Session, api_url: str) -> str | None:
    r = session.get(api_url)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("encoding") == "base64":
        try:
            return base64.b64decode(data["content"]).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return None
    return data.get("content")


def _fetch_github_license(session: requests.Session, repo: str) -> str:
    r = session.get(f"{GITHUB_API}/repos/{repo}/license")
    if r.status_code == 200:
        return (r.json().get("license") or {}).get("spdx_id", "").lower()
    return ""  # no detectable license == treat as NOT redistributable


# --------------------------------------------------------------------------- #
# HA community forum (Discourse) — Blueprints Exchange
# --------------------------------------------------------------------------- #
def scrape_forum(session: requests.Session, max_items: int, seen: set[str]) -> int:
    """Page the Blueprints Exchange category via Discourse's JSON API.

    Discourse exposes JSON by appending .json to any URL. Blueprint posts embed
    YAML in fenced code blocks; extract those as candidate automations/blueprints.
    NOTE: respect the forum's Terms of Service and be gentle with rate.
    """
    added = 0
    page = 0
    while added < max_items:
        url = f"{FORUM_BASE}/c/{FORUM_BLUEPRINTS_CATEGORY}.json?page={page}"
        resp = session.get(url, headers={"Accept": "application/json"})
        if resp.status_code != 200:
            print(f"  forum returned {resp.status_code}; stopping.", file=sys.stderr)
            break
        topics = resp.json().get("topic_list", {}).get("topics", [])
        if not topics:
            break
        for t in topics:
            if added >= max_items:
                break
            topic_url = f"{FORUM_BASE}/t/{t['slug']}/{t['id']}"
            rec = {
                "source": "forum",
                "repo": f"topic/{t['id']}",
                "url": topic_url,
                "license": "forum-post",       # clarify reuse terms before redistributing
                "redistributable": False,       # default conservative
                "hash": _content_hash(topic_url),  # TODO: hash extracted YAML, not URL
                "title": t.get("title", ""),
            }
            # TODO: GET f"{topic_url}.json", pull cooked HTML/first post, extract
            #       fenced ```yaml blocks, hash + store each block separately.
            if _record(rec, seen):
                added += 1
                print(f"  + [{added}] {t.get('title','')[:60]}")
        page += 1
        time.sleep(1.5)  # gentle
    return added


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Corpus scraper for ha-rule-analyzer")
    ap.add_argument("--source", choices=["github", "forum"], required=True)
    ap.add_argument("--max", type=int, default=100, help="max new items to pull")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if args.source == "github" and not token:
        print("WARNING: no GITHUB_TOKEN set — code search will 401. "
              "Create a fine-grained PAT (public-repo read) and export it.", file=sys.stderr)

    session = _session(token)
    seen = _seen_hashes()
    print(f"{len(seen)} automations already in corpus; pulling up to {args.max} more "
          f"from {args.source}…")

    if args.source == "github":
        n = scrape_github(session, args.max, seen)
    else:
        n = scrape_forum(session, args.max, seen)

    print(f"Done. Added {n} new automations. Corpus now in {OUT_DIR}/ (manifest: {MANIFEST}).")
    print("Reminder: only the license-cleared, hand-labeled subset should be committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
