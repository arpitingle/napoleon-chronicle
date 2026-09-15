#!/usr/bin/env python3
"""Bulk: every usable dated letter not already published (Bingham I-III).
Verbatim PD excerpts + concise factual contexts. Similarity-deduped."""
import json, re, sys
import difflib
sys.path.insert(0, "sources")
from common import clean, push, NAP, best_excerpt

B = (json.load(open("sources/bingham_vol1.json")) +
     json.load(open("sources/bingham_vol2.json")) +
     json.load(open("sources/bingham_vol3.json")))

pub = []
for f in ["data/napoleon_seed.json", "data/nap_empire.json", "data/nap_fall.json",
          "data/nap_voices.json", "data/nap_france.json"]:
    try:
        pub += json.load(open(f))
    except FileNotFoundError:
        pass
by_date = {}
for p in pub:
    by_date.setdefault(p["date"], []).append(p["displayText"][:150])

BARCH = "Bingham, Selection from the Letters and Despatches (London, 1884) — public domain"
URLS = {"1": "https://archive.org/details/acp7797.0001.001.umich.edu",
        "2": "https://archive.org/details/cu31924024332243",
        "3": "https://archive.org/details/cu31924024332250"}

def era(iso):
    y, m = int(iso[:4]), int(iso[5:7])
    if iso < "1796-01-01":
        return ("Army of Italy (Toulon)", "toulon-1793" if iso < "1795-01-01" else "youth-1795")
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

out, skipped = [], 0
for r in sorted([x for x in B if x["iso"]], key=lambda x: x["iso"]):
    disp = best_excerpt(clean(r["body"], 10000), floor=2.0)
    if not disp:
        skipped += 1
        continue
    if len(disp) < 80:
        skipped += 1
        continue
    dupe = False
    for q in by_date.get(r["iso"], []):
        if difflib.SequenceMatcher(None, disp[:150], q[:150]).ratio() > 0.55:
            dupe = True
            break
    if dupe:
        skipped += 1
        continue
    v = "1" if r["iso"] < "1803" else ("2" if r["iso"] < "1810" else "3")
    cert = "approximate" if r.get("fuzzy_date") else "certain"
    place = (r["place"] or "Headquarters").strip().title().replace("  ", " ")
    fac, eid = era(r["iso"])
    push(out, NAP, fac, r["iso"], None, place,
         "“" + disp + "”",
         f"{pretty_addr(r['addr'])}, {r['place'] or place}, {r['iso']}",
         BARCH, URLS[v], "letter",
         f"Letter to {r['addr'].title()} from {place}, {r['iso']}. Full text in the Bingham selection (public domain).",
         eid, cert=cert)

print("bulk:", len(out), "skipped:", skipped)
json.dump(out, open("data/nap_bulk.json", "w"), ensure_ascii=False, indent=1)
