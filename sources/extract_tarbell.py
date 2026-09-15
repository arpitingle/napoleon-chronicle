#!/usr/bin/env python3
"""Deterministic Tarbell extraction: locate each wanted piece by distinctive
probes, slice body, assign explicit iso. No heading regex."""
import json, re

T = open("sources/tarbell1897.txt", encoding="utf-8", errors="replace").read()

def dehyphen(t):
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
    return re.sub(r"\s+", " ", t)

# (key, start-probe, end-probe-or-None, iso, cert, title, event, context)
WANT = [
 ("milan", "You  have  rushed", "fri", "1796-05-15", "certain", "Proclamation on Entering Milan", "italy-1796", "Milan entered: the torrent proclamation."),
 ("brescia", "Brescia", None, "1796-05-28", "certain", "Proclamation on Entering Brescia", "italy-1796", "Brescia entered."),
 ("mantua", "Mantua", None, "1796-11-06", "certain", "Address During the Siege of Mantua", "italy-1796", "Mantua besieged."),
 ("cisalpine", "Cisalpine", None, "1797-11-17", "certain", "Proclamation to the Cisalpine Republic", "campo-1797", "A sister republic proclaimed."),
 ("egypt-embark", "Embarking", None, "1798-06-01", "approximate", "Proclamation on Embarking for Egypt", "egypt-1798", "Embarkation address."),
 ("egyptians", "Egyptians", None, "1798-07-01", "approximate", "Proclamation to the Egyptians", "egypt-1798", "Liberation proclaimed."),
 ("egypt-govt", "Government of Egypt", None, "1798-07-27", "certain", "Order on the Government of Egypt", "egypt-1798", "Occupation organised."),
 ("tippoo", "Tippoo", None, "1799-01-25", "certain", "Letter to Tippoo Sahib", "egypt-1798", "To Mysore against England."),
 ("acre-abandon", "Abandoning", None, "1799-05-01", "approximate", "Proclamation on Abandoning Acre", "egypt-1798", "Acre abandoned."),
 ("departure-fr", "Departure for France", None, "1799-08-01", "approximate", "Proclamation on Departure for France", "egypt-1798", "Farewell to Egypt."),
 ("army-east", "Army of the East", None, "1799-11-01", "approximate", "Proclamation to the Army of the East", "brumaire-1799", "Consulate address."),
 ("marengo-eve", "Marengo,  June", None, "1800-06-01", "approximate", "Proclamation before Marengo", "marengo-1800", "Marengo eve."),
 ("marengo-austria", "Field of Marengo", None, "1800-06-01", "approximate", "Letter to Austria from Marengo", "marengo-1800", "To the Emperor, on the field."),
 ("colors", "Behold your colors", None, "1804-12-03", "certain", "Address on Presenting the Colors", "empire-1804", "Eagles presented."),
 ("england-king", "my b?'other", None, "1805-01-02", "certain", "Letter to the King of England", "austerlitz-1805", "Peace offered."),
 ("jerome", "Jerome Bonaparte", None, "1805-05-06", "certain", "Letter to Jérôme Bonaparte", "austerlitz-1805", "American marriage forbidden."),
 ("third-coalition", "Third Coalition", None, "1805-09-01", "approximate", "Proclamation on the Third Coalition", "austerlitz-1805", "War proclaimed."),
 ("ulm", "Fall of Ulm", None, "1805-10-01", "approximate", "Address after Ulm", "austerlitz-1805", "Ulm fallen."),
 ("austerlitz-after", "I am satisfied with you", None, "1805-12-03", "certain", "Proclamation after Austerlitz", "austerlitz-1805", "The bulletin-proclamation."),
 ("pressburg", "Peace with Austria", None, "1805-12-26", "certain", "Address on Peace with Austria", "austerlitz-1805", "Pressburg announced."),
 ("feb1806", "February, 1806", None, "1806-02-01", "approximate", "Proclamation to the Soldiers", "jena-1806", "1806 address."),
 ("captive", "Captive Officers", None, "1806-10-15", "certain", "Address to the Captive Officers", "jena-1806", "Magnanimity after Jena."),
 ("warsaw", "Entering Warsaw", None, "1807-01-01", "approximate", "Proclamation before Entering Warsaw", "eylau-1807", "Warsaw proclamation."),
 ("prussia-eylau", "period to the misfortunes", None, "1807-02-01", "approximate", "Letter to the King of Prussia", "eylau-1807", "Peace offered after Eylau; month certain."),
 ("friedland", "Friedland", None, "1807-06-24", "certain", "Proclamation after Friedland", "tilsit-1807", "Friedland proclaimed."),
 ("champagny07", "Champagny, Nov", None, "1807-11-15", "certain", "Letter to Champagny", "tilsit-1807", "Settlement administered."),
 ("spaniards", "second  self", None, "1808-06-02", "certain", "Proclamation to the Spaniards", "spain-1808", "Joseph's crown announced."),
 ("austria08", "Empei'or of Austria", None, "1808-10-01", "approximate", "Letter to the Emperor of Austria", "erfurt-1808", "Erfurt letter."),
 ("spanish-people", "Spanish People, December", None, "1808-12-01", "approximate", "Proclamation to the Spanish People", "spain-1808", "Madrid taken."),
 ("morla", "vain you employ", None, "1808-12-03", "certain", "Summons to Morla", "spain-1808", "Surrender by 6 a.m."),
 ("eckmuhl", "Eckmuhl", None, "1809-04-01", "approximate", "Proclamation before Eckmühl", "wagram-1809", "Eckmühl."),
 ("ratisbon", "Ratisbon", None, "1809-04-01", "approximate", "Proclamation at Ratisbon", "wagram-1809", "Ratisbon."),
 ("vienna09", "Entering Vienna", None, "1809-05-01", "approximate", "Address on Entering Vienna", "wagram-1809", "Vienna entered."),
 ("hungarians", "Hungarians", None, "1809-05-01", "approximate", "Proclamation to the Hungarians", "wagram-1809", "Hungarians summoned."),
 ("borodino", "Borodino", None, "1812-09-07", "certain", "Address before Borodino", "russia-1812", "Borodino eve."),
 ("alexander12", "Alexander I", None, "1812-09-20", "certain", "Letter to Alexander I", "russia-1812", "From burning Moscow."),
 ("legis13f", "Legislative Body, Feb", None, "1813-02-14", "certain", "Discourse to the Legislative Body", "leipzig-1813", "1813 opening."),
 ("legis13d", "Legislative Body, December", None, "1813-12-01", "approximate", "Address to the Legislative Body", "leipzig-1813", "December 1813."),
 ("abdication-speech", "only obstacle", None, "1814-04-04", "certain", "Declaration of Abdication", "fontainebleau-1814", "Fontainebleau declaration; Tarbell misdates April 2."),
 ("old-guard", "Old Guard", None, "1814-04-20", "certain", "Farewell to the Old Guard", "fontainebleau-1814", "The courtyard farewell."),
 ("anniversary15", "Marengo and Friedland", None, "1815-06-14", "certain", "Proclamation of June 14, 1815", "waterloo-1815", "Are we not still the same men?"),
 ("belgians", "Belgians", None, "1815-06-17", "certain", "Proclamation to the Belgians", "waterloo-1815", "Ligny announced."),
 ("bellerophon", "Bellerophon", None, "1815-08-04", "certain", "Bellerophon Protest", "sthelena-1815", "Guest, not prisoner."),
]

found, missing = [], []
for key, probe, endp, iso, cert, title, eid, ctx in WANT:
    import re as _re
    pat = r"\s+".join(_re.escape(w) for w in probe.split())
    idxs = [m.start() for m in _re.finditer(pat, T)]
    if not idxs:
        missing.append(key)
        continue
    # prefer occurrence in body region (after TOC ~25000), latest sensible
    cands = [i for i in idxs if i > 25000] or idxs
    i = cands[0]
    seg = T[i:i+2500]
    # cut at next page footer
    seg = re.split(r"\d{1,3}\s+NAPOLEON.?S\s+ADDRESSES\.?", seg)[0]
    found.append((key, iso, cert, title, eid, ctx, seg.strip()[:2200]))
print("found:", len(found), "missing:", missing)
json.dump([{"key": k, "iso": i, "cert": c, "title": t, "event": e, "ctx": x, "body": b}
           for k, i, c, t, e, x, b in found],
          open("sources/tarbell_picked.json", "w"), ensure_ascii=False, indent=1)
