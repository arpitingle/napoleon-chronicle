# Editorial policy

## What may be published

Only Napoleon Bonaparte's own letters, orders, proclamations and
despatches — and only records carrying `editorialStatus: "verified"`.
Wellington despatches, Directory orders, Nelson letters and St Helena
eyewitness accounts (Warden and company) are collected in the slices as raw
material but never published; `build_index.py` skips them loudly and
`verify.py` fails the build if one slips through. Nothing else is published.

## Sourcing rule

Quotes are **verbatim** from public-domain editions. The pipeline's `clean()`
removes running heads and OCR debris; it does not paraphrase, modernise or
re-order words. Where a passage is shortened, it is cut at a sentence boundary
and marked `[…]`.

Principal sources (all pre-1930, public domain):

| Source | Used for |
|---|---|
| Bingham, *Selection from the Letters and Despatches* (London, 1884), Vols. I–III | Napoleon's letters and orders, Egypt, Italy, the Empire |
| *Correspondance de Napoléon Ier* (Second Empire, French) | French originals, dates |
| *Confidential Correspondence of Napoleon and Josephine* (London, 1856) | the Josephine letters |
| Tarbell, *Napoleon's Addresses* (1897) | proclamations and addresses |
| Wellington, *Despatches* (1902) | the opposing voice |
| Las Cases 1823, O'Meara 1822, Antommarchi 1825, Lowe 1853, Warden 1816 | St Helena |
| Masson & Schütz (1908) | the Corsican youth fragments |

## Selection, not padding

`common.py` scores every sentence and publishes the highest-scoring one or two:
vivid or consequential language is rewarded, bureaucratic boilerplate
("you will find enclosed…", "article 1") and OCR garbage are penalised. If
nothing clears the floor the document **sits out**. Coverage is therefore
uneven by design — honest gaps, not filler.

## The Lodi pipeline

Lodi is the letter-to-tweet pipeline. `sources/tweet_paraphrases.json` holds
one editor-written paraphrase per published letter record. Run
`python3 sources/lodi.py` to apply the paraphrases, rebuild the shards, and
verify coverage and archive integrity. The verifier fails if a published
letter record has no tweet, a tweet points to no published record, or a tweet
fails the voice, length, date-token, or formatting checks.

The unit is the **archive record**, not a proven unique historical letter.
Separate records can quote overlapping or duplicate source passages, and
identical tweet wording can occur where the source text genuinely repeats.
The pipeline flags repeated paraphrase text for editorial review; it does not
silently merge records.

## Summaries

The tweet uses Napoleon's first-person voice. A Lodi paraphrase is a modern
paraphrase of the published record, not a quotation. It is limited to what
the surviving source text supports: when only an excerpt survives, it must
not imply knowledge of the whole letter, and uncertain or damaged passages
must be identified as such. No invented facts, people, or numbers. The
verbatim excerpt remains available under **Verbatim**, with source and context
available beside it.

Where no paraphrase exists yet, the tweet falls back to an extractive
first-person voice line (picked, never composed), then to the editorial
narrative. Iron rule, enforced by `verify.py`: **an extractive tweet is
always contained in its own verbatim quote** (minus the @mention).

Under a voice tweet sits the context line: scene (the record's event moment)
plus frame (the addressee with a rostered factual role). Behind Verbatim
sits the full quote, unaltered.

Hand-written contexts set the house style ("Ultimatum season."). The 641
bulk records once carried only boilerplate ("Letter to X from Y. Full
text…"); their narratives are drafted extractively (`narrate_contexts.py`:
event scene + roster frame + letter clause, date-gated so no future blurb
leaks into a past letter, with junk/dictionary/chapter-head gates) plus
editor review of every flagged draft (`hand_contexts.json`). Voice lines
come from the same script (first-person, self-contained, @mention only for
a resolvable addressee). Published via `context_overrides.json`, applied by
`build_index.py`; `verify.py` fails if boilerplate returns. Machine drafts
stay out of `sources/*.txt` corpora and `data/nap_*.json` slices — they live
only in the overrides file and the shards built from it.

## Threads

The archive does not publish multi-post letter threads. The interface must
not group separate records just because they share an author and date; every
record renders independently. A future thread feature would need explicit
source-linked relationship metadata and editorial review.

## Labels

The UI must label what it cannot verify:

* `dateCertainty: "approximate"` → `~ approx date` badge.
* non-English original → `🌐 translation` badge, with `originalText` shown
side by side where the record carries it.
* `evidenceType` (`TRANSLATION`, `ORIGINAL MANUSCRIPT`, `EYEWITNESS ACCOUNT`, …).
* Later memoirs and reported speech are labelled as such and never presented as
the live voice of the day.

`verify.py` fails if a record carries an `evidenceType` or `timeLabel` that
`app.js` has no label/order for — the UI must never render an unlabelled value.

## Open item: who translated this?

The stated policy is that English comes from pre-1930 published translations.
That is true for the great majority, but **271 records are modern renderings made
by this project**, flagged in their `context` as "Translated for Chronicle from
the public-domain French".

This is a real discrepancy between policy and practice, and it is
*disclosed in the record* rather than hidden — but the UI does not yet surface
the distinction, so a reader cannot tell a Bingham 1884 translation from a modern
one at a glance. Two acceptable resolutions:

1. label it in the feed (a distinct evidence badge plus a translator credit), or
2. retire those records in favour of published translations.

Until one is chosen, `verify.py` keeps printing the count so the number cannot
quietly grow.

## Known defects ledger

The current baseline, printed by `verify.py` (keep these numbers falling):

| Defect | Count |
|---|---|
| translation with no French original in the record | 1,059 |
| modern "Translated for Chronicle" renderings | 271 |
| dated days vs the 12,052-day advertised range | 833 of 12,052 |
| leaked all-caps running heads | 12 |
| spaced years (`18 12` for 1812) | 14 |
| OCR digit inside a word (`i8o.`) | 6 |
| duplicate body text | 4 pairs |

Fixes belong in `sources/common.py` (or the builder that emitted the record)
and must be accompanied by a check in `verify.py` so the defect cannot return.
