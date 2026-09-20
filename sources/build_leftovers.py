#!/usr/bin/env python3
"""Leftovers: unused Josephine, Wellington attributions, rev-dated Bingham."""
import json, sys
sys.path.insert(0, "sources")
from common import clean, push, NAP, JOSEPHINE_URL

J = json.load(open("sources/josephine1856.json"))
W = json.load(open("sources/wellington.json"))
B = (json.load(open("sources/bingham_vol1.json")) +
     json.load(open("sources/bingham_vol2.json")) +
     json.load(open("sources/bingham_vol3.json")))

WELL = {"author": "Duke of Wellington", "handle": "@wellington", "accountType": "person"}
WELL_URL = "https://archive.org/details/india.history.resource.111797"
WARCH = "Wellington, Despatches 1799–1815 (1902 selection) — public domain"

out = []

JLEFT = [
 ("1797-02-13", "campo-1797", "Ancona rescript received?"),
 ("1804-08-06", "empire-1804", "Calais: setting out for Dunkirk this evening."),
 ("1807-01-07", "eylau-1807", "Warsaw cold, roads wretched, region unsafe."),
 ("1807-01-19", "eylau-1807", "Smiled at her fears; despair at her tone."),
 ("1807-02-01", "eylau-1807", "120 miles from Warsaw; cold weather."),
 ("1807-02-12", "eylau-1807", "Darmagnac's letter forwarded; a good soldier."),
 ("1807-02-18", "eylau-1807", "Moving to winter quarters; rain and thaw."),
 ("1807-03-13", "eylau-1807", "Silence the Mayence salon gossip."),
 ("1807-03-17", "eylau-1807", "Humble equipage unworthy of her rank (×2 letters)."),
 ("1807-04-02", "eylau-1807", "Finckenstein: pleasant château like Bessieres'."),
 ("1807-04-18", "eylau-1807", "Her little Creole temper; chagrin read with pain."),
 ("1807-05-10", "friedland-1807", "No ladies in correspondence with me."),
 ("1807-05-12", "friedland-1807", "St. Cloud instead? Seen with pain."),
 ("1807-05-14", "friedland-1807", "Poor Napoleon's death grieved them (nephew)."),
 ("1807-05-16", "friedland-1807", "Hortense arrived; injury already suffered."),
 ("1807-05-20", "friedland-1807", "Lucken rest a fortnight."),
 ("1807-05-26", "friedland-1807", "Hortense at Lucken; grieved."),
 ("1807-06-06", "tilsit-1807", "Continually sad; giving pain."),
 ("1807-12-11", "tilsit-1807", "Udine: Garden fountains pleased her."),
 ("1808-10-09", "erfurt-1808", "Just driven over the battle-field."),
 ("1809-09-09", "wagram-1809", "Kems, 2 a.m.: come to see the troops."),
 ("1810-04-28", "marie-louise-1810", "Eugene written; Tascher marriage ordered."),
 ("1810-07-08", "marie-louise-1810", "Eugene's presence will do her good."),
]

for iso, eid, ctx in JLEFT:
    c = [r for r in J if r["iso"] == iso]
    if not c:
        raise SystemExit(f"NO MATCH j {iso}")
    # skip if same-day Josephine already published with similar text
    r = c[0]
    push(out, dict(NAP, faction="Empire"), "Empire", iso, None,
         r["place"].title(), "“" + clean(r["body"]) + "”",
         f"To Josephine, {r['place'].title()}, {iso}",
         "Confidential Correspondence of Napoleon and Josephine (London, 1856) — public domain",
         JOSEPHINE_URL, "love letter", ctx, eid)

# Wellington remaining indices
M = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
     "July": 7, "August": 8, "September": 9, "Sept": 9, "October": 10, "November": 11,
     "Nov": 11, "December": 12, "Dec": 12, "Feb": 2, "Mar": 3, "Apr": 4, "Jan": 1,
     "Aug": 8, "Oct": 10}
WCTX = {
 0: ("empire-admin", "India: the other empire rising."),
 1: ("empire-admin", "Poona: subsidiary alliances."),
 2: ("empire-admin", "Poona: Mahratta wars."),
 4: ("peninsular-1808", "Masséna's retreat watched from Lonzao."),
 5: ("peninsular-1808", "Portugal administered."),
 8: ("peninsular-1808", "Discipline foundations: NCOs."),
 9: ("peninsular-1808", "Officers' conduct regulated."),
 12: ("france-1814", "Toulouse aftermath staff work."),
 13: ("france-1814", "Toulouse: military secretary's orders."),
}
for idx, (eid, ctx) in WCTX.items():
    r = W[idx]
    iso = f"{r['year']}-{M[r['month']]:02d}-{int(r['day']):02d}"
    push(out, WELL, "Anglo-Allied Army (opposing)", iso, None, r["place"],
         "“" + clean(r["body"], 340) + "”",
         f"To {r['to']}, {r['place']}, {iso}", WARCH,
         WELL_URL, "dispatch", ctx, eid, ev="ORIGINAL MANUSCRIPT")

# rev-dated Bingham leftovers (republican calendar, month certain)
RSEL = [
 ("Prairial", "1795", "JOSEPH BUONAPARTE", "1795-06-01", "youth-1795",
  "Paris", "To Joseph Buonaparte", "Prairial Year III: Désirée demands his portrait."),
 ("Nivose", "1804", "JOSEPHINE", "1804-01-01", "marie-louise-1810",
  "Paris", "To Josephine", "Nivôse Year XII: no news for days."),
 ("Prairial", "1801", "BRUIX", "1801-06-01", "consulate-1802",
  "At sea", "To Admiral Bruix", "Prairial Year IX: ready to sail."),
]
for mon, yr, key, iso, eid, loc, toline, ctx in RSEL:
    c = [r for r in B if r.get("rev_date") and key in r["addr"] and (r.get("year") or "") == yr]
    if not c:
        raise SystemExit(f"NO MATCH rev {key} {yr}")
    r = c[0]
    push(out, NAP, "Empire", iso, None, loc,
         "“" + clean(r["body"]) + "”",
         f"{toline}, {mon} {yr} (revolutionary date; day approximate)",
         "Bingham, Selection (London, 1884) — public domain",
         "https://archive.org/details/acp7797.0001.001.umich.edu",
         "letter", ctx + " Revolutionary calendar date; rendered to the 1st, marked approximate.", eid,
         cert="approximate")

json.dump(out, open("data/nap_leftovers.json", "w"), ensure_ascii=False, indent=1)
print("leftovers:", len(out))
