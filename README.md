# Chronicle — Napoleon

Napoleon's letters, orders and proclamations (1790–1821) as a Twitter-style
timeline. Posts pair a first-person paraphrase or selected extract with the
verbatim source text and citation. The static site is served directly from
`index.html`, `app.js`, and the generated JSON archive; no frontend build is
required.

## Run it

The app fetches JSON, so serve it over HTTP (not `file://`):

```bash
python3 -m http.server 8000
# open http://localhost:8000/
```

## Check it

```bash
python3 sources/build_index.py   # rebuild manifest + era shards from slices
python3 sources/verify.py        # archive integrity + editorial lint
node tests/smoke_app.mjs         # headless app smoke test
```

For a static host, publish the project root as-is. Keep `index.html`,
`app.js`, `styles.css`, `data/`, and `images/` at the same relative paths;
the site has no build step. The map view uses Leaflet and OpenStreetMap tiles
when opened, while the archive and timeline work without them.

## Data pipeline

Public-domain books and correspondence (`sources/*.txt`, OCR) → parsers and
builders → `data/nap_*.json` slices → `sources/build_index.py` →
`data/index.json` and `data/shard_<era>.json` → `app.js`. Shared helpers live
in `sources/common.py`; editorial paraphrases, contexts, and voices live in
`sources/tweet_paraphrases.json` and `sources/context_overrides.json`.
Generated archive files are committed so the site serves as-is.

The letter-to-tweet workflow is the **Lodi pipeline**. Add or edit one
record-keyed paraphrase in `sources/tweet_paraphrases.json`, then run
`python3 sources/lodi.py` to apply overrides, rebuild the published shards,
and validate that every published letter record has exactly one mapped tweet.
Paraphrases stay within the surviving source text; see [EDITORIAL.md](EDITORIAL.md)
for the policy on excerpts, damaged text, and duplicate records.

## Notes

- Only verified Napoleon-authored records are published. Counts are generated
  in `data/index.json` (currently 2,726 posts); see [EDITORIAL.md](EDITORIAL.md)
  for sourcing and paraphrase policy.
- The feed includes modern paraphrases and selected verbatim extracts; open
  **Source & context** and **Verbatim** on a post to inspect its evidence.
- Keyboard: `←`/`→` move a day, `r` replays it, `Esc` closes the profile.
- Known gaps are tracked in [EDITORIAL.md](EDITORIAL.md).
