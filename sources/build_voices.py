#!/usr/bin/env python3
"""Voices: Wellington, Las Cases, Northumberland, youth, Directory-incoming, Josephine leftovers."""
import json, re, sys
sys.path.insert(0, "sources")
from common import (clean, push, NAP, BINGHAM_URL, JOSEPHINE_URL)

W = json.load(open("sources/wellington.json"))
J = json.load(open("sources/josephine1856.json"))
B1 = json.load(open("sources/bingham_vol1.json"))

WELL = {"author": "Duke of Wellington", "handle": "@wellington", "accountType": "person"}
WARDEN = {"author": "W. Warden", "handle": "@warden_northumberland", "accountType": "person"}
LASCASES_URL = "https://archive.org/details/mmorialdesaint0301lascuoft"
NORTH_URL = "https://archive.org/details/letters00writtenonwardrich"
WELL_URL = "https://archive.org/details/india.history.resource.111797"

out = []

WSEL = [
 (3, "Busaco eve resolve: no mercy expected, none asked.", "peninsular-1808"),
 (6, "Fuentes d'Oñoro aftermath: details win battles.", "peninsular-1808"),
 (7, "Badajoz stormed: gallantry beyond expression.", "peninsular-1808"),
 (10, "Contractors and traducers: the army's parasites.", "peninsular-1808"),
 (11, "Portuguese paid, Portuguese fight: regularity wins.", "peninsular-1808"),
 (14, "Toulouse taken; Buonaparte overturned.", "france-1814"),
 (15, "Intelligence charlatans in Brussels.", "waterloo-1815"),
 (16, "French army dissolving after Waterloo.", "waterloo-1815"),
 (17, "No laying down arms: abdication insufficient security.", "waterloo-1815"),
]

for idx, ctx, eid in WSEL:
    r = W[idx]
    M = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
         "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
    iso = f"{r['year']}-{M[r['month']]:02d}-{int(r['day']):02d}"
    push(out, WELL, "Anglo-Allied Army (opposing)", iso, None, r["place"],
         "“" + clean(r["body"], 340) + "”",
         f"To {r['to']}, {r['place']}, {iso}",
         "Wellington, Despatches 1799–1815 (1902 selection) — public domain",
         WELL_URL, "dispatch", ctx, eid, ev="ORIGINAL MANUSCRIPT")

# ---------- Las Cases (Fifth Part conversations, undated in print) ----------
L = open("sources/lascases1823.txt", encoding="utf-8", errors="replace").read()
L = re.sub(r"(\w)-\s+(\w)", r"\1\2", L)
L = re.sub(r"\s+", " ", L)

def lasc(probe, length=1400):
    pat = r"\s+".join(re.escape(w) for w in probe.split())
    m = re.search(pat, L)
    if not m:
        raise SystemExit(f"NO LASCASES {probe}")
    seg = L[m.start():m.start()+length]
    seg = re.split(r"\d{1,3}\s+(NAPOLEON.?S|THE EMPEROR)", seg)[0]
    return seg.strip()

LSEL = [
 ("Abolit ten o'clock, the Emperor entered my apartment", "1816-07-10", "certain",
  "Longwood", "sthelena-1815", "Walk, calash, Beaumarchais read."),
 ("Rostopchin baving been pronounced", "1816-01-01", "approximate",
  "Longwood", "sthelena-1815", "On Moscow's burning and Rostopchin; undated conversation."),
 ("Blucher and the Duke of Wellington were surprized", "1816-01-01", "approximate",
  "Longwood", "waterloo-1815", "Dictated Waterloo narrative: the surprise opening."),
 ("Quatre-Bras", "1816-01-01", "approximate",
  "Longwood", "waterloo-1815", "Dictated Waterloo narrative continues."),
 ("position at SaintJ", "1816-01-01", "approximate",
  "Longwood", "sthelena-1815", "Egypt remembered: romance as episode."),
]

for probe, iso, cert, loc, eid, ctx in LSEL:
    seg = lasc(probe)
    push(out, dict(NAP, faction="St Helena (reported)"), "St Helena (reported)", iso, None, loc,
         "“" + clean(seg, 340) + "”",
         "Las Cases, Mémorial (English ed., 1823), Fifth Part conversations",
         "Las Cases, Journal of Napoleon's St Helena conversations (London, 1823) — public domain",
         LASCASES_URL, "reported conversation",
         ctx + " Reported speech via Las Cases' journal; undated in print except where stated.",
         eid, cert=cert, ev="EYEWITNESS ACCOUNT")

# ---------- Northumberland voyage ----------
N = open("sources/northumberland1816.txt", encoding="utf-8", errors="replace").read()
N = re.sub(r"(\w)-\s+(\w)", r"\1\2", N)
N = re.sub(r"\s+", " ", N)

def north(probe, length=900):
    pat = r"\s+".join(re.escape(w) for w in probe.split())
    m = re.search(pat, N)
    if not m:
        raise SystemExit(f"NO NORTH {probe}")
    return N[m.start():m.start()+length].strip()

NSEL = [
 ("3d of August, 1815", "1815-08-04", "approximate", "At sea", "sthelena-1815",
  "Transfer Bellerophon to Northumberland; date from narrative."),
 ("14th of October, 1815", "1815-10-14", "certain", "Off St Helena", "sthelena-1815",
  "Landfall eve: the Peak sighted at sunset; narrative date explicit."),
 ("voluntary surrender", "1815-08-01", "approximate", "At sea", "sthelena-1815",
  "The surrender that surprised Maitland."),
]

for probe, iso, cert, loc, eid, ctx in NSEL:
    seg = north(probe)
    push(out, WARDEN, "Royal Navy (eyewitness)", iso, None, loc,
         "“" + clean(seg, 340) + "”",
         f"Warden's letter, {iso}",
         "Warden, Letters from the Northumberland and St Helena (London, 1816) — public domain",
         NORTH_URL, "eyewitness letter", ctx, eid, cert=cert, ev="ORIGINAL MANUSCRIPT")

# ---------- Youth 1795 ----------
def find_b1(iso, key, place=None):
    import re as _re
    norm = lambda s: _re.sub(r"\s+", " ", (s or "").lower())
    c = [r for r in B1 if r["iso"] == iso and key in r["addr"]
         and (place is None or norm(place) in norm(r["place"]))]
    if not c:
        raise SystemExit(f"NO MATCH youth {iso} {key}")
    return c[0]

YSEL = [
 ("1795-07-12", "JOSEPH", None, "Paris", "To Joseph Buonaparte", "youth-1795",
  "Quiberon landings; Pichegru about to cross the Rhine."),
 ("1795-07-01", "JOSEPH", "Paris", "Paris", "To Joseph Buonaparte", "youth-1795",
  "Unemployed general, sick in Paris, awaiting fate."),
 ("1795-08-17", "SUCY", None, "Paris", "To Commissary Sucy", "youth-1795",
  "Fortune varies: angling for employment."),
 ("1795-09-06", "JOSEPH", None, "Paris", "To Joseph Buonaparte", "youth-1795",
  "Convention renewed; Vendémiaire brewing."),
]

for iso, key, placekey, loc, toline, eid, ctx in YSEL:
    r = find_b1(iso, key, placekey)
    cert = "approximate" if r.get("fuzzy_date") else "certain"
    push(out, NAP, "Army (unemployed)", iso, None, loc,
         "“" + clean(r["body"]) + "”",
         f"{toline}, {iso}",
         "Bingham, Selection (London, 1884), Vol. I — public domain",
         BINGHAM_URL, "letter", ctx, eid, cert=cert)

# ---------- Directory incoming (secret1846, hand) ----------
S = open("sources/secret1846.txt", encoding="utf-8", errors="replace").read()
S = re.sub(r"(\w)-\s+(\w)", r"\1\2", S)
S = re.sub(r"\s+", " ", S)

DIRARCH = "Secret letters from Napoleon's cabinet (London, 1846), Vol. I — public domain"
DIRURL = "https://archive.org/details/10421011bsb"
DSEL = [
 ("16 Ventose", "1796-03-06", "Paris", "italy-1796",
  "The Directory's Italy instructions: seize Savona if useful; spare Genoa.",
  "To Gen. Bonaparte: campaign instructions"),
 ("29 Messidor", "1796-07-17", "Paris", "italy-1796",
  "Paris answers Roverbella: Mantua's supplies will decide.",
  "To the General-in-Chief: reply on Mantua"),
]
for probe, iso, loc, eid, ctx, title in DSEL:
    pat = r"\s+".join(re.escape(w) for w in probe.split())
    m = re.search(pat, S)
    if not m:
        raise SystemExit(f"NO SECRET {probe}")
    seg = S[m.start():m.start()+900]
    push(out, {"author": "The Executive Directory", "handle": "@directoire",
               "accountType": "institution"}, "French Government (orders)", iso, None, loc,
         "“" + clean(seg, 340) + "”", title + f", {iso}", DIRARCH, DIRURL,
         "instructions", ctx + " Incoming voice: Paris orders to its general.", eid)

# ---------- Josephine leftovers ----------
JJ = json.load(open("sources/josephine1856.json"))

def ev_label_hour(h):
    if not h:
        return None
    if "AM" in h:
        n = int(h.split()[0])
        return "MORNING" if n != 12 else None
    if "PM" in h:
        n = int(h.split()[0])
        return "EVENING" if (n >= 5 and n != 12) else "AFTERNOON"
    return None

JSEL = [
 ("1803-06-23", "1803-06-23", "certain", None, "consulate-1802", "Malmaison summer: health anxieties."),
 ("1803-07-01", "1803-07-01", "certain", None, "consulate-1802", "Her letter answered; health unwritten."),
 ("1801-07-18", "1807-07-18", "approximate", None, "tilsit-1807", "Misprinted year; Dresden stay on the Tilsit return."),
]

for find_iso, iso, cert, tlab, eid, ctx in JSEL:
    c = [r for r in JJ if r["iso"] == find_iso]
    if not c:
        raise SystemExit(f"NO MATCH j {find_iso}")
    r = c[0]
    lab = tlab or ev_label_hour(r.get("hour")) or "TIME UNCERTAIN"
    push(out, dict(NAP, faction="Empire"), "Empire", iso, lab,
         r["place"].title(), "“" + clean(r["body"]) + "”",
         f"To Josephine, {r['place'].title()}, {find_iso} (printed date)",
         "Confidential Correspondence of Napoleon and Josephine (London, 1856) — public domain",
         JOSEPHINE_URL, "love letter", ctx, eid, cert=cert)

json.dump(out, open("data/nap_voices.json", "w"), ensure_ascii=False, indent=1)
print("voices:", len(out))
