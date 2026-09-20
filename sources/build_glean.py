#!/usr/bin/env python3
"""Glean: Bingham letters the bulk pass left behind, second chance with
today's machinery (better cleaning, editor-voice and fragment rules).

Only bodies bulk skipped for floor/short reasons that now clear the bar.
Dupe-skipped bodies stay out (near-dupes of published records). Bodies
already published in equivalent form stay out. Non-Napoleon senders
(e.g. an enclosed Nelson journal) stay out — see NOT_HIS.

Additive only: published records are never touched. New ids are per-date
nap-YYYYMMDD-8X from 81 upward, skipping used sequences; build_index fails
loudly on any collision.

Run from anywhere:  python3 sources/build_glean.py
"""
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "sources"))
from common import clean, sentences, score_sent, NAP
from narrate_contexts import (strip_leads, trim_clause, VERBISH, FIRST_PERSON,
                              DANGLING_START)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# addressees whose Bingham bodies are not Napoleon's writing
NOT_HIS = {"mrsnelson", "mrs nelson", "nelson", "wellington",
           "horationelson", "dukeofwellington"}

CONT_OPENERS = {"to", "and", "but", "for", "with", "in", "on", "at", "by",
                "of", "from", "as", "that", "which", "who", "whom", "whose",
                "than", "then", "thus", "until", "since", "because",
                "while", "where", "when"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def era(iso):
    y, m = int(iso[:4]), int(iso[5:7])
    if iso < "1796-01-01":
        return ("Army of Italy (Toulon)", "toulon-1793" if iso < "1795-01-01"
                else "youth-1795")
    if iso < "1797-01-01":
        return ("Army of Italy", "italy-1796")
    if iso < "1798-01-01":
        return ("Army of Italy", "campo-1797")
    if iso < "1799-11-01":
        return ("Army of the Orient", "egypt-1798")
    if iso < "1800-01-01":
        return ("Consulate", "brumaire-1799")
    if iso < "1801-01-01":
        return ("Consulate", "marengo-1800")
    if iso < "1803-01-01":
        return ("Consulate", "consulate-1802")
    if iso < "1804-01-01":
        return ("Consulate", "boulogne-1803")
    if iso < "1805-01-01":
        return ("Empire", "empire-1804")
    if iso < "1806-01-01":
        return ("Grande Armée", "austerlitz-1805")
    if iso < "1807-01-01":
        return ("Grande Armée", "jena-1806")
    if iso < "1807-06-01":
        return ("Grande Armée", "eylau-1807")
    if iso < "1808-01-01":
        return ("Grande Armée", "tilsit-1807")
    if iso < "1808-10-01":
        return ("Empire", "spain-1808")
    if iso < "1809-01-01":
        return ("Empire", "erfurt-1808")
    if iso < "1810-01-01":
        return ("Empire", "wagram-1809")
    if iso < "1812-01-01":
        return ("Empire", "marie-louise-1810")
    if iso < "1813-01-01":
        return ("Grande Armée", "russia-1812")
    if iso < "1814-01-01":
        return ("Grande Armée", "leipzig-1813")
    if iso < "1814-04-01":
        return ("Empire", "france-1814")
    if iso < "1814-05-01":
        return ("Empire", "fontainebleau-1814")
    if iso < "1815-01-01":
        return ("Empire", "elba-1814")
    if iso < "1815-03-01":
        return ("Empire", "elba-1814")
    if iso < "1815-08-01":
        return ("Empire", "waterloo-1815")
    return ("Empire", "sthelena-1815")


def pretty_addr(a):
    a = a.strip().rstrip(".")
    if a.lower().startswith("citizen "):
        return "To " + a[8:].strip().title()
    return "To " + a.title()


def viable(s):
    s = strip_leads(s).strip()
    if not (80 <= len(s) <= 320):
        return None
    if not re.match(r'[A-Z0-9À-Þ"]', s):
        return None
    if s.split()[0].lower().rstrip(",;:") in CONT_OPENERS:
        return None
    if DANGLING_START.match(s):
        return None
    if re.search(r"\b(Bonaparte|Napoleon)\b", s) \
            and not FIRST_PERSON.search(s):
        return None
    if score_sent(s) < 2.0:
        return None
    if not VERBISH.search(s[:140]):
        return None
    return trim_clause(s)


BARCH = "Bingham, Selection from the Letters and Despatches (London, 1884) — public domain"
URLS = {"1": "https://archive.org/details/acp7797.0001.001.umich.edu",
        "2": "https://archive.org/details/cu31924024332243",
        "3": "https://archive.org/details/cu31924024332250"}


def main():
    bodies = []
    for vn in ("bingham_vol1.json", "bingham_vol2.json", "bingham_vol3.json"):
        bodies += json.load(open(os.path.join(ROOT, "sources", vn),
                                 encoding="utf-8"))
    pub = []
    for f in sorted(os.listdir(DATA)):
        if not (f.startswith("nap_") and f.endswith(".json")):
            continue
        if f == "nap_glean.json":
            continue  # own previous output
        pub += json.load(open(os.path.join(DATA, f), encoding="utf-8"))
    pub_by_id = {p["id"]: p for p in pub}
    used = {}
    date_texts = {}
    for p in pub:
        m = re.match(r"^nap-(\d{8})-(\d+)$", p.get("id", ""))
        if m and p.get("date", "").replace("-", "") == m.group(1):
            used.setdefault(p["date"], set()).add(int(m.group(2)))
        date_texts.setdefault(p.get("date"), []).append(
            (p.get("displayText") or "")[:150])

    out = []
    for r in sorted([x for x in bodies if x.get("iso")],
                    key=lambda x: x["iso"]):
        if norm(r["addr"]) in NOT_HIS:
            continue
        # already published in equivalent form (same letter, any slice)?
        body_n = norm(clean(r["body"], 10000))
        if any(body_n[:120] in norm(p.get("displayText") or "") or
               norm(p.get("displayText") or "")[:120] in body_n
               for p in pub if p.get("date") == r["iso"]):
            continue
        cands = []
        for s in sentences(clean(r["body"], 10000)):
            v = viable(s)
            if v:
                cands.append(v)
        cands.sort(key=score_sent, reverse=True)
        if not cands:
            continue
        disp = cands[0]
        if any(difflib.SequenceMatcher(
                None, disp[:150], q[:150]).ratio() > 0.55
               for q in date_texts.get(r["iso"], [])):
            continue
        date_texts.setdefault(r["iso"], []).append(disp[:150])
        seqs = used.setdefault(r["iso"], set())
        seq = 81
        while seq in seqs:
            seq += 1
        if seq > 89:
            print("no glean slot left on %s, skipping %s %s"
                  % (r["iso"], r["addr"], seq))
            continue
        seqs.add(seq)
        v = "1" if r["iso"] < "1803" else ("2" if r["iso"] < "1810" else "3")
        cert = "approximate" if r.get("fuzzy_date") else "certain"
        place = (r["place"] or "Headquarters").strip().title()
        fac, eid = era(r["iso"])
        out.append({
            "id": "nap-%s-%02d" % (r["iso"].replace("-", ""), seq),
            "author": NAP["author"], "handle": NAP["handle"],
            "accountType": NAP["accountType"], "faction": fac,
            "date": r["iso"], "timeLabel": "TIME UNCERTAIN",
            "timePrecision": "day", "location": place,
            "originalLanguage": "French",
            "displayText": "“" + disp + "”",
            "sourceTitle": "%s, %s, %s"
                           % (pretty_addr(r["addr"]), r["place"] or place,
                              r["iso"]),
            "archive": BARCH, "sourceUrl": URLS[v], "documentType": "letter",
            "evidenceType": "TRANSLATION", "dateCertainty": cert,
            "eventIds": [eid], "editorialStatus": "verified",
            "context": "Letter to %s from %s, %s. Full text in the "
                       "Bingham selection (public domain)."
                       % (r["addr"].title(), place, r["iso"])})
    out.sort(key=lambda r: (r["date"], r["id"]))
    with open(os.path.join(DATA, "nap_glean.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("glean: %d new letters from %d bodies"
          % (len(out), len([b for b in bodies if b.get("iso")])))


if __name__ == "__main__":
    main()
