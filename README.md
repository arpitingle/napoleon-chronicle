# Chronicle — Napoleon

Napoleon's real correspondence presented as a Twitter-style timeline. Every
"Tweet" is a verbatim letter, order, proclamation or dispatch from a
public-domain edition, dated 1791–1821. No framework, no build step, no
dependencies: static HTML/CSS/JS plus a JSON archive and a Python pipeline that
turns OCR'd books into feed records.

## Run it

The app fetches JSON, so it needs a web server (not `file://`):

```bash
python3 -m http.server 8000
# open http://localhost:8000/
```

## Validate and test

```bash
python3 sources/build_index.py        # rebuild the manifest + era shards
python3 sources/verify.py             # data integrity + content smells (errors fail)
python3 sources/verify.py --strict    # warnings fail too — use this in CI
python3 sources/verify.py --check-urls  # also HEAD every archive.org source link
node tests/smoke_app.mjs              # headless test of app.js itself (25 checks)
```

`verify.py` is a regression net: every check is pinned to a defect observed in
this archive, so a rebuild cannot quietly reintroduce one.

Integrity problems (schema, hashes, bad ids, unknown labels) **always** fail the
run. Content smells are warnings: run with `--strict` to make them fail too. That
gate is not yet green — the known-defect baseline in
[EDITORIAL.md](EDITORIAL.md) is still open — so CI should run plain
`verify.py` today and switch to `--strict` once the ledger is cleared.

## How the data reaches the page

```
sources/*.txt  ──parse_*.py──> sources/*.json   (dated records, French + English)
                              │
                              ├── build_*.py ──> data/nap_*.json   (15 slices, by campaign)
                              │                        │
                              │                   build_index.py
                              │                        ▼
                              └──────────────> data/index.json  (manifest)
                                               data/shard_<era>.json (7 payloads)
                                                        │
                                                    app.js (browser)
```

The app fetches **`data/index.json` alone** to boot (counts, coverage, authors,
events, shard map, schema), then lazily fetches only the era shard it needs:

| shard | era | years |
|---|---|---|
| `revolution` | Revolution & youth | 1789–1795 |
| `italy` | Italy 1796-97 | 1796–1797 |
| `egypt` | Egypt & Brumaire | 1798–1799 |
| `consulate` | Consulate & peace | 1800–1804 |
| `empire` | Empire at its height | 1805–1811 |
| `crisis` | Russia to the Hundred Days | 1812–1815 |
| `sthelena` | St Helena | 1816–1821 |

Adding a new `sources/build_*.py` slice needs **no front-end change**: any
`data/nap_*.json` is picked up by `build_index.py` on the next rebuild.

## Failure is loud

A missing or malformed archive file used to be swallowed (`catch(()=>[])`),
which silently deleted posts. Now:

* `data/index.json` failing → the Enter button is disabled and the reason is shown.
* a shard failing or holding records the schema rejects → a red `#archiveError`
banner names the file, says how many records were rejected and offers **Retry**;
whatever did load still renders.
* the manifest carries a `sha256` and record count per shard, so `verify.py`
catches hand-edits and stale indexes.

## Data model

One record per document. Required fields are declared once, in
`index.json meta.schema.required`, and enforced by both `verify.py` and the app:

`id` (`nap-YYYYMMDD-NN`, the date is inside the id), `author`, `handle`,
`accountType`, `faction`, `date`, `timeLabel`, `timePrecision`, `location`,
`originalLanguage`, `displayText`, `sourceTitle`, `archive`, `sourceUrl`,
`documentType`, `evidenceType`, `dateCertainty`, `eventIds`,
`editorialStatus`, `context`, and optionally `originalText`,
`reactions`.

Only `editorialStatus === "verified"` is published. Policy and open provenance
questions live in [EDITORIAL.md](EDITORIAL.md).

## The 15 slices

Each `sources/build_*.py` script writes one `data/nap_*.json` slice and needs no
arguments; run them from the project root, e.g.

```bash
python3 sources/build_seed.py         # data/napoleon_seed.json
python3 sources/build_bulk.py         # data/nap_bulk.json
python3 sources/build_index.py        # then regenerate the manifest
python3 sources/verify.py
```

All slices share `sources/common.py`: `clean()` strips running heads and OCR
debris, `score_sent()`/`best_excerpt()` pick the most vivid sentence instead of
the opening line, and records scoring below a floor are dropped rather than
padded. Quotes are verbatim; no words are altered.

## Repository layout

```
index.html styles.css app.js     the app (no build step)
images/                          hero artwork, portraits
images/avatars/<slug>.jpg        any file here becomes an account's avatar
data/events.json                 hand-written "moments" (32) + policy text
data/index.json                  GENERATED manifest
data/shard_*.json                GENERATED era payloads
data/nap_*.json                  GENERATED slices (pipeline output)
sources/*.py                     pipeline + verify
tests/smoke_app.mjs              headless app test (node, zero deps)
sources/*.txt sources/*.json     raw OCR corpora and dated indexes (~36 MB)
```

GENERATED files are committed so the site can be served as-is; `build_index.py`
is the only thing that writes `index.json` and `shard_*.json` (they are
deterministic — rebuild and the `sha256` values are unchanged).

## Keyboard

With the timeline open: `←`/`→` move a day, `r` toggles Replay day, `s` toggles
Spoiler-free, `Esc` closes the profile modal.

## Known gaps

* 92% of the advertised range (1789–1821) has no document on any given day; the
empty state now routes you to the nearest document rather than dead-ending.
* 1,059 of 1,357 records are translations with no French original in the record
(though the French is often already parsed in `sources/corr_vol*.json`).
* 271 records are modern translations by this project, not by a published
editor — see EDITORIAL.md.
* `corr_vol{09,10,11,20,26}.txt` are Internet Archive HTML pages, not OCR text,
and `corr_vol13.txt` is an "item not available" page — ~700 KB of dead corpus
that overlaps the thinnest years.
* Only 5 accounts exist (Napoleon 1,330; Wellington 18; the Directory 4;
Warden 3; Nelson 2); `reactions` is unused, so that affordance no longer renders.
