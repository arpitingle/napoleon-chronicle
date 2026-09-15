#!/usr/bin/env python3
"""Build data/index.json plus one shard per campaign era.

The 15 build_*.py scripts each emit their own slice (data/nap_*.json). This step
is the single runtime entry point for the web app: it collects every slice, keeps
only editorialStatus=verified, partitions the records by era and writes

  data/index.json           manifest — counts, coverage, authors, events, shard map
  data/shard_<era>.json     the post records themselves

Replaces the hardcoded DATA_FILES list that used to live in app.js, so a new
builder's output needs no front-end edit: any data/nap_*.json is picked up.

Run from anywhere:  python3 sources/build_index.py
"""
import glob, hashlib, json, os, re
from collections import Counter, defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
AVATARS = os.path.join(ROOT, "images", "avatars")

APP_RANGE = ("1789-01-01", "1821-12-31")
VERSION = "0.3.0"

# Campaign eras, in order. A shard is one lazy-loaded payload for the feed.
ERAS = [
    ("revolution", "Revolution & youth", 1789, 1795),
    ("italy", "Italy 1796-97", 1796, 1797),
    ("egypt", "Egypt & Brumaire", 1798, 1799),
    ("consulate", "Consulate & peace", 1800, 1804),
    ("empire", "Empire at its height", 1805, 1811),
    ("crisis", "Russia to the Hundred Days", 1812, 1815),
    ("sthelena", "St Helena", 1816, 1821),
]

# Portrait lookup: images/avatars/<slug>.jpg. Add a file, get an avatar.
AVATAR_ALIASES = {
    "napoleon bonaparte": "napoleon",
    "duke of wellington": "wellington",
    "horatio nelson": "nelson",
}

# Fields every published record must carry. Shared with app.js and verify.py.
REQUIRED = [
    "id", "author", "handle", "accountType", "faction", "date", "timeLabel",
    "location", "originalLanguage", "displayText", "sourceTitle", "archive",
    "sourceUrl", "evidenceType", "dateCertainty", "eventIds", "editorialStatus",
]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def avatar_for(author):
    for cand in (AVATAR_ALIASES.get(author.lower()), slug(author),
                 slug(author.split()[-1]) if author.split() else None):
        if not cand:
            continue
        if os.path.exists(os.path.join(AVATARS, cand + ".jpg")):
            return "images/avatars/%s.jpg" % cand
    return None


def load_verified():
    """Every slice, deduped by id, in deterministic order."""
    files = [os.path.join(DATA, "napoleon_seed.json")]
    files += sorted(glob.glob(os.path.join(DATA, "nap_*.json")))
    posts, seen, per_file = [], {}, {}
    for f in files:
        if not os.path.exists(f):
            raise SystemExit("missing slice: %s" % f)
        raw = json.load(open(f, encoding="utf-8"))
        if not isinstance(raw, list):
            raise SystemExit("%s is not a list of records" % f)
        kept = 0
        for r in raw:
            if r.get("editorialStatus") != "verified":
                continue
            rid = r.get("id")
            if not rid:
                raise SystemExit("%s has a record with no id" % f)
            if rid in seen:
                raise SystemExit("duplicate id %s in %s (already in %s)"
                                 % (rid, os.path.basename(f), seen[rid]))
            missing = [k for k in REQUIRED if k not in r]
            if missing:
                raise SystemExit("%s: %s missing %s"
                                 % (os.path.basename(f), rid, missing))
            seen[rid] = os.path.basename(f)
            posts.append(r)
            kept += 1
        per_file[os.path.basename(f)] = kept
    posts.sort(key=lambda r: (r["date"], r["id"]))
    return posts, per_file


def era_of(year):
    for eid, _label, lo, hi in ERAS:
        if lo <= year <= hi:
            return eid
    return None


def main():
    posts, per_file = load_verified()

    buckets = defaultdict(list)
    unmapped = Counter()
    for r in posts:
        eid = era_of(int(r["date"][:4]))
        if eid is None:
            unmapped[r["date"][:4]] += 1
        else:
            buckets[eid].append(r)
    if unmapped:
        raise SystemExit("years outside every era: %s — extend ERAS" % dict(unmapped))

    shards, shard_by_year = [], {}
    for eid, label, lo, hi in ERAS:
        recs = buckets.get(eid, [])
        name = "shard_%s.json" % eid
        blob = json.dumps(recs, ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as fh:
            fh.write(blob)
        for y in range(lo, hi + 1):
            shard_by_year[str(y)] = eid
        shards.append({"id": eid, "label": label, "file": "data/" + name,
                       "from": lo, "to": hi, "count": len(recs),
                       "bytes": len(blob.encode("utf-8")),
                       "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest()})

    by_year = Counter(r["date"][:4] for r in posts)
    date_count = Counter(r["date"] for r in posts)

    authors = []
    for name in sorted({r["author"] for r in posts},
                       key=lambda a: -sum(1 for r in posts if r["author"] == a)):
        recs = [r for r in posts if r["author"] == name]
        authors.append({
            "author": name,
            "handle": recs[0]["handle"],
            "accountType": recs[0]["accountType"],
            "avatar": avatar_for(name),
            "count": len(recs),
            "factions": sorted({r["faction"] for r in recs}),
            "years": sorted({int(r["date"][:4]) for r in recs}),
            "firstDate": min(r["date"] for r in recs),
            "lastDate": max(r["date"] for r in recs),
            "documentTypes": sorted({r.get("documentType", "letter") for r in recs}),
        })

    ev = json.load(open(os.path.join(DATA, "events.json"), encoding="utf-8"))
    start, end = APP_RANGE
    span, gap = 0, 0
    have = set(date_count)
    d, e = date.fromisoformat(start), date.fromisoformat(end)
    while d <= e:
        span += 1
        if d.isoformat() not in have:
            gap += 1
        d += timedelta(days=1)

    index = {
        "meta": {
            "app": "Chronicle: Napoleon",
            "version": VERSION,
            "generated": date.today().isoformat(),
            "schema": {"required": REQUIRED},
            "editorialPolicy": ev["meta"]["editorialPolicy"],
            "coverageNote": ("%d verified documents, %s to %s, across %d dated days; "
                             "%d of the %d days in %s..%s carry nothing. Generated by "
                             "sources/build_index.py.")
                            % (len(posts), posts[0]["date"], posts[-1]["date"],
                               len(date_count), gap, span, start, end),
            "builtFrom": per_file,
        },
        "counts": {"posts": len(posts), "dates": len(date_count),
                   "authors": len(authors), "events": len(ev["events"]),
                   "shards": len(shards), "slices": len(per_file)},
        "appRange": {"from": start, "to": end, "days": span,
                     "daysWithPosts": span - gap, "emptyDays": gap},
        "contentSpan": {"from": posts[0]["date"], "to": posts[-1]["date"]},
        "byYear": {k: by_year[k] for k in sorted(by_year)},
        "dateCount": {k: date_count[k] for k in sorted(date_count)},
        "authors": authors,
        "events": ev["events"],
        "eventMeta": ev["meta"],
        "shards": shards,
        "shardByYear": shard_by_year,
    }
    with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("index.json: %d posts / %d dates / %d authors / %d shards"
          % (len(posts), len(date_count), len(authors), len(shards)))
    for s in shards:
        print("   %-11s %-28s %4d posts %6.1f KB"
              % (s["id"], s["label"], s["count"], s["bytes"] / 1024))
    print("   coverage: %d of %d days in %s..%s carry a document (%d empty)"
          % (span - gap, span, start, end, gap))


if __name__ == "__main__":
    main()
