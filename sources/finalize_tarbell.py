#!/usr/bin/env python3
"""Finalize tarbell.json: dedupe TOC/body pairs, drop junk, fix known year OCR."""
import json, re
from collections import Counter

recs = json.load(open("sources/tarbell_raw.json"))
seen = {}
for r in recs:
    k = (r["iso"], re.sub(r"\W+", "", r["title"].lower())[:36])
    if k in seen:
        if len(r["body"]) > len(seen[k]["body"]):
            seen[k] = r
        continue
    seen[k] = r
out = list(seen.values())
print("dedup:", len(out))
out = [r for r in out if not re.search(r"75|/e/ia|Beg\.mn\.uig|Ricssiaii", r["title"])]
print("junk:", len(out))
out = [r for r in out if len(r["body"]) > 60]
print("bodylen:", len(out))
out = [r for r in out if r["iso"][:4] != "1769"]
for r in out:
    if r["iso"] == "1787-12-10":
        r["iso"] = "1797-12-10"
        r["approx"] = False
json.dump(out, open("sources/tarbell.json", "w"), ensure_ascii=False, indent=1)
print("final:", len(out), sorted(Counter(r["iso"][:4] for r in out).items()))
mk = [(r["iso"], len(r["body"])) for r in out if "Milan" in r["title"]]
print("milan:", mk)
