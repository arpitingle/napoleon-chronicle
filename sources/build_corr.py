#!/usr/bin/env python3
"""Phase C: assemble data/nap_corr.json from corr_intake.json + corr_mt.json.

Joins on the preassigned record id (sources/corr_mt.json is keyed by it).
Cleans MT English (French-month capitalization, bracket-debris strip),
QA-gates every EN field, builds titles (person "To X,..." / doc-type
French label per shipped precedent), writes records with their
preassigned nap-YYYYMMDD-7xx ids, applies enrichment (originalText) to
existing nap_*.json files. Idempotent; safe to re-run.
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_contexts import known  # noqa: E402
from narrate_contexts import WORDS, STOP  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = HERE
DATA = os.path.join(os.path.dirname(HERE), "data")

ARCH = ("Correspondance de Napol\u00e9on Ier, Second Empire ed. (Paris, 1858), "
        "Vols. VI\u2013VII \u2014 public domain (French)")
TR = " Translated for Chronicle from the public-domain French; original below."

FR_MARK = re.compile(
    r"\b(les|des|cette|dans|pour|avec|vous|nous|ils|elles|dont|o\u00f9|"
    r"quand|comme|entre|\u00eatre|avoir|fait|plus|tout|tous|toute|toutes|"
    r"ces|sont|leur|leurs|mais|donc|car|ni)\b", re.I)

FR_MONTH = re.compile(
    r"\b(vendemiaire|vendemiary|vend\u00e9miaire|brumaire|"
    r"frimaire|nivose|niv\u00f4se|pluviose|pluvi\u00f4se|ventose|vent\u00f4se|"
    r"germinal|floreal|flor\u00e9al|prairial|messidor|"
    r"th?(?:ermidor|ormidor)|fructidor|complementaires?)\b", re.I)


def era(iso):  # exact copy of sources/build_bulk.py era()
    y, m = int(iso[:4]), int(iso[5:7])
    if iso < "1796-01-01":
        return ("Army of Italy (Toulon)",
                "toulon-1793" if iso < "1795-01-01" else "youth-1795")
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
        return ("Grande Arm\u00e9e", "austerlitz-1805")
    if iso < "1807-01-01":
        return ("Grande Arm\u00e9e", "jena-1806")
    if iso < "1807-06-01":
        return ("Grande Arm\u00e9e", "eylau-1807")
    if iso < "1808-01-01":
        return ("Grande Arm\u00e9e", "tilsit-1807")
    if iso < "1808-10-01":
        return ("Empire", "spain-1808")
    if iso < "1809-01-01":
        return ("Empire", "erfurt-1808")
    if iso < "1810-01-01":
        return ("Empire", "wagram-1809")
    if iso < "1812-01-01":
        return ("Empire", "marie-louise-1810")
    if iso < "1813-01-01":
        return ("Grande Arm\u00e9e", "russia-1812")
    if iso < "1814-01-01":
        return ("Grande Arm\u00e9e", "leipzig-1813")
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


DOC_LABEL = {  # folded first-word of addr_fr -> (French title label, documentType)
    "ordre": ("Ordre", "Order"), "ordres": ("Ordre", "Order"),
    "arrete": ("Arr\u00eat\u00e9", "Decree"), "arretes": ("Arr\u00eat\u00e9", "Decree"),
    "decision": ("D\u00e9cision", "Decision"), "decisions": ("D\u00e9cision", "Decision"),
    "decret": ("D\u00e9cret", "Decree"), "decrets": ("D\u00e9cret", "Decree"),
    "proclamation": ("Proclamation", "Proclamation"),
    "proclamations": ("Proclamation", "Proclamation"),
    "instruction": ("Instruction", "Instruction"),
    "instructions": ("Instruction", "Instruction"),
    "note": ("Note", "Note"), "notes": ("Note", "Note"),
    "message": ("Message", "Message"), "messages": ("Message", "Message"),
    "lettre": ("Lettre", "Letter"),
    "rapport": ("Rapport", "Report"), "rapports": ("Rapport", "Report"),
    "discours": ("Discours", "Speech"),
    "allocution": ("Allocution", "Speech"),
}


def fold(s):
    return (s.lower().replace("\u00e9", "e").replace("\u00e8", "e")
            .replace("\u00ea", "e").replace("\u00e0", "a").replace("\u00e7", "c"))


def clean_en(txt):
    txt = FR_MONTH.sub(lambda m: m.group(0).capitalize(), txt)
    txt = re.sub(r"\s*\[[^\]]{0,40}\]\s*", " ", txt)
    txt = re.sub(r"\s*\([^)]{0,30}$", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def trim_en(txt, cap=420):
    if len(txt) <= cap:
        return txt
    cut = txt[:cap]
    m = re.search(r"\s\S{0,12}$", cut)
    if m:
        cut = cut[:m.start()]
    if not cut.rstrip().endswith(("\u2026", "[...]")):
        cut = cut.rstrip() + " [\u2026]"
    return cut


def title_for(addr_en, addr_fr, place, iso):
    # The French address line is often more reliable than the machine-
    # translated addressee. Repair a few OCR/translation failures against
    # the address and body in the source edition.
    addr_key = re.sub(r"[^a-z]+", " ", fold(addr_fr)).strip()
    aliases = {
        "au general auge": "General Augereau",
        "au general m assena": "General Massena",
        "au general en chef de l armee du roi de sardaicae":
            "King of Sardinia's Commander-in-Chief",
    }
    if addr_key in aliases:
        person = aliases[addr_key]
        t = f"To {person}, {place}, {iso}" if place else f"To {person}, {iso}"
        return t, "Letter"
    fw = fold(addr_fr).split()[0] if fold(addr_fr).split() else ""
    if fw in DOC_LABEL:
        label, dtype = DOC_LABEL[fw]
        t = f"{label}, {place}, {iso}" if place else f"{label}, {iso}"
        return t, dtype
    seg = addr_en.split(",")[0].strip()
    seg = re.sub(r"^(to|al|a|au|aux|the)\s+", "", seg, flags=re.I).strip()
    seg = re.sub(r"^(to|al|a|au|aux|the)\s+", "", seg, flags=re.I).strip()
    person = seg.title().strip(" .") if seg else ""
    words = person.split()
    if len(words) > 4:
        # committee-style addressee: head noun is last
        # ("Commission ... Mediterranean Coasts" -> "Mediterranean Coasts")
        person = re.sub(r"^(The|Of|De|Des|Du|La|Le|Les)\s+", "",
                        " ".join(words[-3:]), flags=re.I)
    if len(person) > 70:
        cut = person[:70]
        person = cut[:cut.rfind(" ")] if " " in cut else cut
    t = f"To {person}, {place}, {iso}" if place else f"To {person}, {iso}"
    return t, "Letter"


def fr_residue(txt):
    return len(set(m.group(0).lower() for m in FR_MARK.finditer(txt)))


def qa_en(txt, fr_txt):
    if not (60 <= len(txt) <= 420):
        return False, f"len={len(txt)}"
    if txt.strip().lower() == fr_txt.strip().lower():
        return False, "echo"
    if "[" in txt or "]" in txt:
        return False, "brackets"
    non = re.sub(r"[A-Za-z0-9\s\"…\[\].,;:!?()\-–—']", "", txt)
    if len(non) / max(1, len(txt)) > 0.08:
        return False, "salad"
    if re.search(r"(.\,.)(\1){2,}", txt):
        return False, "salad"
    toks = txt.split()
    if toks and len(re.findall(r"\b[A-Za-z]\b", txt)) > len(toks) * 0.4:
        return False, "salad"
    if fr_residue(txt) >= 4:
        return False, "fr-residue"
    if WORDS:  # empty on machines without /usr/share/dict/words;
        # narrate_contexts.py gates the same way (never invent a bar
        # the shipped 1292 records didn't clear)
        toks = re.findall(r"(?<![A-Za-zÀ-Þ])[a-zà-þ]{4,}", txt)
        unk = [t for t in toks if t not in STOP and not known(t)]
        if unk:
            return False, f"dict:{unk[:4]}"
    return True, ""


def main():
    intake = json.load(open(os.path.join(SRC, "corr_intake.json")))
    mt = json.load(open(os.path.join(SRC, "corr_mt.json")))

    out, drops = [], Counter()
    for r in intake:
        m = mt.get(r["id"])
        if not m:
            drops["no-mt"] += 1
            continue
        iso = r["date"]
        ex_en = trim_en(clean_en(m["en"].strip()))
        ok, why = qa_en(ex_en, r["excerpt_fr"])
        if not ok:
            drops[f"excerpt:{why.split(':')[0]}"] += 1
            continue
        addr_en = clean_en(m["addr_en"].strip().strip(" ."))
        if (not addr_en or len(addr_en) > 160 or fr_residue(addr_en) >= 2
                or re.search(r"[A-Z]{5,}|\d", addr_en)):
            drops["addr"] += 1
            continue
        title, dtype = title_for(addr_en, r["addr_fr"], r["place"], iso)
        vm = re.search(r"corr_vol(\d+)", r.get("vol", ""))
        v = int(vm.group(1)) if vm else 0
        era_name, eid = era(iso)
        _ = era_name
        out.append({
            "id": r["id"],
            "author": "Napoleon Bonaparte", "handle": "@bonaparte",
            "accountType": "person", "faction": "French",
            "date": iso, "timeLabel": "TIME UNCERTAIN", "timePrecision": "day",
            "location": r["place"] or "",
            "originalLanguage": "French",
            "displayText": f'"{ex_en}"', "sourceTitle": title,
            "archive": ARCH,
            "sourceUrl": ("https://archive.org/details/"
                          f"correspondancede{v:02d}napouoft") if v else "",
            "documentType": dtype, "evidenceType": "TRANSLATION",
            "dateCertainty": ("approximate" if r.get("repaired_date")
                              else "certain"),
            "eventIds": [eid], "editorialStatus": "verified",
            "context": "", "originalText": "",
        })

    json.dump(out, open(os.path.join(DATA, "nap_corr.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"corr records: {len(out)} kept, drops={dict(drops)}")

    enrich = json.load(open(os.path.join(SRC, "corr_enrich.json")))
    files = {}
    for fn in sorted(os.listdir(DATA)):
        if re.match(r"nap_.*\.json$", fn) and fn != "nap_corr.json":
            for rec in json.load(open(os.path.join(DATA, fn))):
                files[rec["id"]] = fn
    applied, cache = 0, {}
    for target, excerpt in enrich.items():
        fn = files.get(target)
        if not fn:
            continue
        p = os.path.join(DATA, fn)
        if p not in cache:
            cache[p] = json.load(open(p))
        for rec in cache[p]:
            if rec["id"] == target and not rec.get("originalText"):
                rec["originalText"] = excerpt
                applied += 1
    for p, recs in cache.items():
        json.dump(recs, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"enrichment applied: {applied}/{len(enrich)}")


if __name__ == "__main__":
    main()
