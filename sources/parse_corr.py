#!/usr/bin/env python3
"""Parse Second Empire Correspondance (French, PD) OCR into dated pieces.

Anchors on editor-computed Gregorian dates in parentheses.
Output: {no, addr, place, iso, body}.
"""
import re, json, sys

def parse(path, year_fix=None):
    raw = open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw)
    t = re.sub(r"\s+", " ", t)
    dates = list(re.finditer(r"\((\d{1,2}) ([A-Za-zéûè]+) (1[789]\d\d|170\d)\)", t))
    recs = []
    for n, m in enumerate(dates):
        day, mon, yr = m.group(1), m.group(2), m.group(3)
        if yr.startswith("170") and year_fix:
            yr = year_fix
        back = t[max(0, m.start()-400):m.start()]
        hm = re.search(r"(\d{1,5})\.\s*[—–-]\s*(.+)$", back)
        if not hm:
            continue
        no, rest = hm.group(1), hm.group(2).strip()
        # place: capitalized chunk right before revolutionary day-month
        pm = re.search(r"([A-ZÀÂÉÈÊÎÔÙÜÇ][A-Za-zàâéèêîôùüç\-\.' ]{1,30}?),?\s*\d{1,2}\s+[a-zéûè]+\s+an\b", rest)
        if pm:
            place = pm.group(1).strip(" .'")
            addr = rest[:pm.start()].strip(" .—–-")
        else:
            place, addr = None, rest[:120]
        end = dates[n+1].start() if n+1 < len(dates) else m.end() + 3000
        # cut body at next header number
        seg = t[m.end():min(end, m.end()+3000)]
        nm = re.search(r"\d{1,5}\.\s*[—–-]\s*[A-ZÀÂ]", seg)
        if nm:
            seg = seg[:nm.start()]
        # strip page headers
        seg = re.sub(r"CORRESPONDANCE DE NAPOLÉON[^\.]{0,40}\.?\s*\d{0,4}", " ", seg)
        seg = re.sub(r"\s+", " ", seg).strip()
        recs.append({"no": no, "addr": addr[:140], "place": place,
                     "day": day, "month": mon, "year": yr,
                     "iso": f"{yr}-{day.zfill(2)}-01"[:7] + f"-{day.zfill(2)}",
                     "body": seg[:2600]})
    # fix iso properly
    MFR = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
           "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10,
           "novembre": 11, "décembre": 12, "decembre": 12}
    for r in recs:
        mm = MFR.get(r["month"].lower().strip("."), 0)
        r["iso"] = f"{r['year']}-{mm:02d}-{int(r['day']):02d}" if mm else None
    recs = [r for r in recs if r["iso"]]
    return recs

if __name__ == "__main__":
    yf = sys.argv[3] if len(sys.argv) > 3 else None
    recs = parse(sys.argv[1], yf)
    json.dump(recs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print("pieces:", len(recs))
    from collections import Counter
    print(sorted(Counter(r["iso"][:4] for r in recs).items()))
