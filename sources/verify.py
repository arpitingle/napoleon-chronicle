#!/usr/bin/env python3
"""Validate the generated archive before it ships.

  errors   manifest integrity (sha256/count per shard), schema, duplicate ids,
           id/date agreement, referential integrity against events.json, and
           label/sort values app.js cannot render
  warnings content smells: leaked running heads, OCR digit-for-letter, spaced
           years, duplicate bodies, translations with no French original

Each check is pinned to a defect observed in this archive, so this is a
regression net: it fails if a rebuild reintroduces one.

Run from anywhere:
  python3 sources/verify.py                # errors fail the run
  python3 sources/verify.py --strict       # warnings fail too (use in CI)
  python3 sources/verify.py --check-urls   # also HEAD every archive.org link
"""
import argparse, hashlib, json, os, re
from collections import Counter
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
APP_JS = os.path.join(ROOT, "app.js")
INDEX_HTML = os.path.join(ROOT, "index.html")

REQ_IDX = ["meta", "counts", "authors", "events", "shards", "shardByYear",
           "byYear", "dateCount", "appRange", "contentSpan"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^nap-(\d{4})(\d{2})(\d{2})-\d+$")

errors, warnings = [], []


def err(m):
    errors.append(m)


def warn(m):
    warnings.append(m)


def js_labels(name):
    """Keys of a `const NAME={...}` literal in app.js — the display contract."""
    if not os.path.exists(APP_JS):
        return None
    m = re.search(re.escape(name) + r"\s*=\s*\{(.*?)\}",
                  open(APP_JS, encoding="utf-8").read(), re.S)
    return set(re.findall(r"['\"]([^'\"]+)['\"]\s*:", m.group(1))) if m else None


def load_index():
    p = os.path.join(DATA, "index.json")
    if not os.path.exists(p):
        err("data/index.json missing - run: python3 sources/build_index.py")
        return None
    try:
        idx = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        err("data/index.json is not valid JSON: %s" % e)
        return None
    for k in REQ_IDX:
        if k not in idx:
            err("index.json missing key: %s" % k)
    if not idx.get("shards"):
        err("index.json lists no shards")
    return idx

def check_shards(idx):
    """sha256, count, schema and era range for every shard; catch orphans."""
    listed = {s["file"] for s in idx.get("shards", [])}
    on_disk = {"data/" + f for f in os.listdir(DATA)
               if f.startswith("shard_") and f.endswith(".json")}
    for orphan in sorted(on_disk - listed):
        err("orphan shard %s is not listed in index.json" % orphan)
    for missing in sorted(listed - on_disk):
        err("shard %s is listed in index.json but not on disk" % missing)

    required = idx.get("meta", {}).get("schema", {}).get("required", [])
    posts = []
    for s in idx.get("shards", []):
        p = os.path.join(ROOT, s["file"])
        if not os.path.exists(p):
            continue
        raw = open(p, "rb").read()
        if hashlib.sha256(raw).hexdigest() != s.get("sha256"):
            err("%s sha256 mismatch - index.json is stale, rebuild it" % s["file"])
        try:
            recs = json.loads(raw.decode("utf-8"))
        except Exception as e:
            err("%s is not valid JSON: %s" % (s["file"], e))
            continue
        if len(recs) != s.get("count"):
            err("%s holds %d records, manifest says %s"
                % (s["file"], len(recs), s.get("count")))
        for r in recs:
            rid = r.get("id")
            for k in required:
                if k not in r:
                    err("%s: %s missing required field %s" % (s["file"], rid, k))
            if r.get("editorialStatus") != "verified":
                err("%s: %s is published but not editorialStatus=verified"
                    % (s["file"], rid))
            if not DATE_RE.match(str(r.get("date", ""))):
                err("%s: %s has malformed date %r" % (s["file"], rid, r.get("date")))
            else:
                m = ID_RE.match(str(rid))
                if not m:
                    err("%s: id %r is not nap-YYYYMMDD-NN" % (s["file"], rid))
                elif "%s-%s-%s" % m.groups() != r["date"]:
                    err("%s: id %s does not encode its date %s" % (s["file"], rid, r["date"]))
                lo, hi = s.get("from"), s.get("to")
                if isinstance(lo, int) and isinstance(hi, int) \
                        and not (lo <= int(r["date"][:4]) <= hi):
                    err("%s holds %s dated %s, outside its %d..%d era"
                        % (s["file"], rid, r["date"], lo, hi))
            if not (r.get("displayText") or "").strip():
                err("%s: %s has empty displayText" % (s["file"], rid))
            posts.append(r)
    return posts


def check_referential(posts, idx):
    ids = Counter(p["id"] for p in posts)
    dup = [i for i, c in ids.items() if c > 1]
    if dup:
        err("duplicate ids across shards: %s" % dup[:5])

    ev_ids = {e["id"] for e in idx.get("events", [])}
    bad = sorted({e for p in posts for e in p.get("eventIds", []) if e not in ev_ids})
    if bad:
        err("eventIds with no entry in events.json: %s" % bad)
    if any(not p.get("eventIds") for p in posts):
        warn("%d posts carry no eventIds"
             % sum(1 for p in posts if not p.get("eventIds")))

    ev_labels = js_labels("EV_SHORT")
    if ev_labels is None:
        warn("could not read EV_SHORT from app.js - badge check skipped")
    else:
        for val, n in Counter(p["evidenceType"] for p in posts
                              if p["evidenceType"] not in ev_labels).items():
            err("evidenceType %r (%d posts) has no EV_SHORT label in app.js" % (val, n))
    order = js_labels("ORDER")
    if order is None:
        warn("could not read ORDER from app.js - sort check skipped")
    else:
        for val, n in Counter(p["timeLabel"] for p in posts
                              if p["timeLabel"] not in order).items():
            err("timeLabel %r (%d posts) is not in ORDER - sort yields NaN" % (val, n))
    for val, n in Counter(p.get("dateCertainty") for p in posts
                          if p.get("dateCertainty") not in ("certain", "approximate")).items():
        err("dateCertainty %r (%d posts) is not certain|approximate" % (val, n))


def check_coverage(posts, idx):
    by_year = Counter(p["date"][:4] for p in posts)
    date_count = Counter(p["date"] for p in posts)
    if idx.get("counts", {}).get("posts") != len(posts):
        err("counts.posts=%s but shards hold %d posts"
            % (idx.get("counts", {}).get("posts"), len(posts)))
    if idx.get("byYear") != {k: by_year[k] for k in sorted(by_year)}:
        err("index.json byYear disagrees with the shards - rebuild the index")
    if idx.get("dateCount") != {k: date_count[k] for k in sorted(date_count)}:
        err("index.json dateCount disagrees with the shards - rebuild the index")

    rng = idx.get("appRange", {})
    try:
        start, end = date.fromisoformat(rng["from"]), date.fromisoformat(rng["to"])
    except Exception:
        err("appRange is missing or malformed: %r" % rng)
        return
    sby = idx.get("shardByYear", {})
    unmapped = [y for y in range(start.year, end.year + 1) if str(y) not in sby]
    if unmapped:
        err("years with no shard (those dates would load nothing): %s" % unmapped)
    days, d = 0, start
    while d <= end:
        days += 1
        d += timedelta(days=1)
    if rng.get("days") != days:
        err("appRange.days=%s but the range spans %d days" % (rng.get("days"), days))
    if rng.get("daysWithPosts") != len(date_count):
        err("appRange.daysWithPosts=%s but %d dates carry documents"
            % (rng.get("daysWithPosts"), len(date_count)))
    for s in idx.get("shards", []):
        if not (isinstance(s.get("from"), int) and isinstance(s.get("to"), int)):
            err("shard %s has no from/to year range" % s.get("file"))
        elif s["from"] > s["to"]:
            err("shard %s has from > to" % s.get("file"))


def check_content(posts, idx):
    """Smells observed in this archive - a rebuild must not reintroduce them."""
    LQ, DQ, DOT = chr(8220), chr(34), chr(46)
    STRAY = "".join(re.escape(c) for c in (DQ, chr(39), DOT, "*", chr(8212), chr(171), chr(8226), chr(60)))
    pats = [("leaked running head (9+ capitals)", r"\b[A-Z]{9,}\b"),
            ("OCR digit inside a word", r"[A-Za-z]+\d+[A-Za-z]+"),
            ("spaced year (e.g. '18 12')", r"\b1[78]\s\d\d\b"),
            ("HTML or scrape boilerplate", r"<[a-z/]|style-scope|Internet Archive"),
            ("replacement character", "[\ufffd]"),
            ("doubled space", r"\S  \S"),
            ("mid-word case break (OCR)", r"[a-z][A-Z][a-z]"),
            ("stray punctuation after the opening quote",
             "^[" + LQ + DQ + "]*[ ]*[" + STRAY + "]"),
            ("leading dateline (Month, year)",
             "^[" + LQ + DQ + r"\"]*\s*\b(January|February|March|April|May|June|July|"
             r"August|September|October|November|December),\s*1[78]\d\d")]
    for label, pat in pats:
        rx = re.compile(pat)
        hits = [p["id"] for p in posts if rx.search(p.get("displayText") or "")]
        if hits:
            warn("%-34s %3d posts  e.g. %s" % (label, len(hits), hits[0]))

    bodies = Counter(re.sub(r"\W+", " ", (p.get("displayText") or "").lower()).strip()[:120]
                     for p in posts)
    dups = [k for k, c in bodies.items() if c > 1 and k]
    if dups:
        warn("%-34s %3d pairs  e.g. %r" % ("duplicate body text", len(dups), dups[0][:50]))

    modern = [p for p in posts if "Translated for Chronicle" in (p.get("context") or "")]
    missing = [p for p in posts if p.get("evidenceType") == "TRANSLATION"
               and not p.get("originalText")]
    warn("%-34s %3d posts (%d marked 'Translated for Chronicle')"
         % ("translation, no French original", len(missing), len(modern)))
    if not any(p.get("reactions") for p in posts):
        warn("%-34s no post uses the field - UI affordance is dead" % "reactions")
    tlab = Counter(p["timeLabel"] for p in posts)
    warn("%-34s %d of %d posts are TIME UNCERTAIN"
         % ("time resolution", tlab.get("TIME UNCERTAIN", 0), len(posts)))
    for a in idx.get("authors", []):
        if not a.get("avatar"):
            warn("%-34s %s (%d posts) falls back to an initial"
                 % ("author without portrait", a["author"], a["count"]))


def check_app_refs():
    """Every DOM id app.js touches must exist in index.html or be built by it."""
    if not (os.path.exists(APP_JS) and os.path.exists(INDEX_HTML)):
        warn("app.js/index.html not found - DOM reference check skipped")
        return
    src = open(APP_JS, encoding="utf-8").read()
    html = open(INDEX_HTML, encoding="utf-8").read()
    referenced = set(re.findall(r"\$\(\s*['\"]#([\w-]+)['\"]\s*\)", src))
    referenced |= set(re.findall(r"getElementById\(\s*['\"]([\w-]+)['\"]", src))
    referenced |= set(re.findall(r"querySelector(?:All)?\(\s*['\"]#([\w-]+)", src))
    in_html = set(re.findall(r'id="([\w-]+)"', html))
    built = set(re.findall(r'id="([\w-]+)"', src))
    broken = sorted(referenced - in_html - built)
    if broken:
        err("app.js references DOM ids that do not exist: %s" % broken)
    STRUCTURAL = {"landing", "app", "layout", "leftCol", "feedCol", "topbar",
                  "timelineHead"}          # layout hooks, addressed by CSS only
    unused = sorted(in_html - referenced - built - STRUCTURAL)
    if unused:
        warn("index.html ids never referenced by app.js: %s" % unused)
    for f in ("data/index.json", "data/events.json"):
        if not os.path.exists(os.path.join(ROOT, f)):
            err("archive input is absent: %s" % f)
    if "DATA_FILES" in src:
        warn("app.js still hardcodes DATA_FILES - the manifest should own that")


def check_urls(posts):
    import urllib.request
    urls = sorted({p["sourceUrl"] for p in posts if p.get("sourceUrl")})
    for u in urls:
        try:
            req = urllib.request.Request(u, method="HEAD",
                                         headers={"User-Agent": "Chronicle-verify/1.0"})
            code = urllib.request.urlopen(req, timeout=15).status
        except Exception as e:
            warn("source link unreachable: %s (%s)" % (u, str(e)[:60]))
            continue
        if code >= 400 and code != 403:
            warn("source link HTTP %s: %s" % (code, u))
    print("checked %d distinct source link(s)" % len(urls))


def main():
    ap = argparse.ArgumentParser(description="Validate the Chronicle archive.")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as failures (CI)")
    ap.add_argument("--check-urls", action="store_true",
                    help="HEAD every distinct source link")
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    a = ap.parse_args()

    idx = load_index()
    posts = []
    if idx:
        posts = check_shards(idx)
        check_referential(posts, idx)
        check_coverage(posts, idx)
        check_content(posts, idx)
        check_app_refs()
        if a.check_urls:
            check_urls(posts)

    if not a.quiet:
        print("Archive: %d posts in %d shards" % (len(posts), len(idx.get("shards", [])) if idx else 0))
    for w in warnings:
        if not a.quiet:
            print("  warn  " + w)
    for e in errors:
        print("  ERROR " + e)
    print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    if errors or (a.strict and warnings):
        print("FAIL")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
