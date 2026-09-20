# Chronicle — Napoleon

Napoleon's real letters, orders and proclamations (1791–1821) as a
Twitter-style timeline. Each post shows a first-person paraphrase in his
voice; the verbatim quote and its source sit underneath. Static site, no
build step: `index.html` + `app.js` + a JSON archive.

## Run it

The app fetches JSON, so serve it over HTTP (not `file://`):

```bash
python3 -m http.server 8000
# open http://localhost:8000/
```

## Check it

```bash
python3 sources/build_index.py   # rebuild manifest + era shards
python3 sources/verify.py        # integrity + content checks (0 errors = ship)
node tests/smoke_app.mjs         # headless app test (55 checks)
```

## Data pipeline

Public-domain books (`sources/*.txt`, OCR) → `parse_*.py` →
`build_*.py` → `data/nap_*.json` → `build_index.py` → `index.json` +
`shard_<era>.json` → `app.js`. Shared helpers live in
`sources/common.py`; hand-written tweets, contexts and voices in
`sources/tweet_paraphrases.json` and `sources/context_overrides.json`.
Generated files are committed so the site serves as-is; rebuilds are
deterministic.

## Notes

- Only Napoleon-authored records are published (1292 posts); nothing is
  invented beyond the letter — paraphrase policy in [EDITORIAL.md](EDITORIAL.md).
- Keyboard: `←`/`→` move a day, `r` replays it, `Esc` closes the profile.
- Known gaps are tracked in [EDITORIAL.md](EDITORIAL.md).
