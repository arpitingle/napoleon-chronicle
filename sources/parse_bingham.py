#!/usr/bin/env python3
"""Parse Bingham (1884) 'Selection from the letters and despatches of the
first Napoleon' OCR text into structured letter records.

Reusable for all three volumes. Output: JSON list of
{addr, place, day, month, year, iso, body, head_line}.
Only records with a confident Gregorian date get `iso`.
"""
import re, json, sys

MONTHS = {m: i+1 for i, m in enumerate(
    ["January","February","March","April","May","June","July",
     "August","September","October","November","December"])}
# revolutionary months -> approximate Gregorian mapping not applied; flagged
REV = ["Vendemiaire","Vendémiaire","Brumaire","Frimaire","Nivose","Nivôse",
       "Pluviose","Pluviôse","Ventose","Ventôse","Germinal","Floreal","Floréal",
       "Prairial","Messidor","Thermidor","Fructidor"]

HEAD = re.compile(r'^(To|TO)\s+([A-Z][A-Za-z \.\-]{2,60}?)\.?\s*$')
DATE = re.compile(
    r'"?\s*([A-Z][A-Za-z\-\. ]{0,35}?),?\s+(\d{1,2})(?:st|nd|rd|th|d|\^)?\s+'
    r'([A-Za-z\^]+?)(?:s)?,?\s+(17\d{2}|18\d{2})\s*\.?')
FOOT = re.compile(r'^\d{1,3} THE CORRESPONDENCE OF NAPOLEON\.?\s*$')
SIG = re.compile(r'"{0,2}\s*(Bonaparte|BUONAPARTE|Buonaparte)\s*\.\s*"{0,2}\s*$')

import difflib
MONTHS_FUZZ = list(MONTHS) + REV

def fuzz_month(raw):
    w = re.sub(r'[^A-Za-z]', '', raw)
    if not w:
        return None, 0.0
    best, score = None, 0.0
    import difflib
    for m in MONTHS_FUZZ:
        r = difflib.SequenceMatcher(None, w.lower(), m.lower()).ratio()
        if r > score:
            best, score = m, r
    if score < 0.38:
        return None, score
    return best, score

def fuzz_year_post(post, chapter=None):
    """Year rescue on post-month substring."""
    base = re.sub(r'[^0-9iljoOySJt\^]', '', post)[:8]
    base = re.sub(r'^[ilJ\^]', '1', base)
    cands = []
    for omap in ("0", "9"):
        t = base.replace("^", "9").replace("o", omap).replace("O", omap).replace(
            "S", "8").replace("i", "1").replace("I", "1").replace("l", "1").replace(
            "t", "1").replace("J", "1")
        m = re.match(r'(17\d\d|18\d\d)', t)
        if m and 1784 <= int(m.group(1)) <= 1821:
            cands.append(m.group(1))
    for c in cands:
        if chapter and c == str(chapter):
            return c
    if cands:
        return cands[0]
    tok = re.sub(r'[^0-9iljoOyS\^]', '', post)
    m = re.match(r'(17\d\d|18\d\d)', tok)
    if m and 1784 <= int(m.group(1)) <= 1821:
        return m.group(1)
    tok = re.sub(r'[^0-9iljoOyS\^]', '', post)
    tok = tok.replace("i", "1").replace("l", "1").replace("^", "9").replace("o", "9").replace("O", "9").replace("S", "8")
    if re.fullmatch(r'[179][79]?[79]?7', tok) and 2 <= len(tok) <= 4 and chapter and str(chapter).endswith("7"):
        return str(chapter)
    if re.fullmatch(r'1[789]\d', tok) and chapter and tok[:2] == str(chapter)[:2]:
        return str(chapter)
    return None

def fuzz_year(raw, chapter=None):
    r2 = raw.replace("S", "8")
    m = re.search(r'17(\d)\W{0,3}(\d)', r2)
    if m:
        y = int("17" + m.group(1) + m.group(2))
        if 1784 <= y <= 1821:
            return str(y)
    m = re.search(r'\b(17\d{2}|18\d{2})\b', r2)
    if m:
        return m.group(1)
    # chapter-aware rescue for mangled years
    if chapter:
        tok = re.sub(r'[^0-9iljoOyS\^]', '', raw)
        tok = tok.replace("i", "1").replace("l", "1").replace("^", "9").replace("o", "9").replace("O", "9").replace("S", "8")
        if re.fullmatch(r'[179][79]?[79]?7', tok) and len(tok) >= 2 and str(chapter).startswith(tok[0]) and str(chapter).endswith(tok[-1]):
            return str(chapter)
    return None

def preen_line(line):
    line = re.sub(r'\bZth\b', '7th', line)
    line = re.sub(r'\blot/', '1st/', line)
    line = re.sub(r'2o//i', '20th', line)
    line = re.sub(r'\\oth', '10th', line)
    line = re.sub(r'\bJime\b', 'June', line)
    line = re.sub(r'\bJattuary\b', 'January', line)
    return line

def find_date(win_lines, chapter=None):
    """win_lines: list of (idx, text). Return (place, day, month, year, idx, fuzzy) or Nones."""
    for idx, raw in win_lines:
        line = preen_line(raw.strip())
        if not line or FOOT.match(line) or len(line) > 120:
            continue
        yr = fuzz_year(line, chapter)
        words = re.findall(r"[A-Za-z\^]{3,12}", line)
        mo = None
        mi = -1
        mscore = 0.0
        for k, w in enumerate(words):
            hit, score = fuzz_month(w)
            if hit and score > mscore:
                mo, mi, mscore = hit, k, score
        if not mo:
            continue
        mpos = line.find(words[mi])
        if not yr:
            yr = fuzz_year_post(line[mpos+len(words[mi]):], chapter)
            if not yr:
                continue
        # mask multi-digit years so day search can't eat them
        masked = re.sub(r"\b\d{3,4}\b", "  ", line)
        best, bestd = None, 1e9
        for m in re.finditer(r"(?:(?P<b>[il])(?P<c>[oO\^])|(?P<d>\d)(?P<e>[il])|(?P<a>[il1]?\d\d?))", masked):
            if m.group("b") is not None:
                v = int("1" + ("4" if m.group("c") == "^" else "0"))
            elif m.group("d") is not None and m.group("e") is not None:
                v = int(m.group("d") + "1")
            else:
                a = m.group("a")
                a = ("1" + a[1:]) if a[:1] in ("i", "l") else a
                v = int(a)
            if 1 <= v <= 31:
                d = abs(m.start() - mpos)
                if d < bestd:
                    best, bestd = v, d
        day = best
        day_fuzzy = False
        if day is None:
            day, day_fuzzy = "01", True
        # place = text before month word, last comma chunk
        pre = line[:mpos].strip(' "\',;:')
        place = None
        if pre:
            chunk = [c.strip(' "\'') for c in pre.split(",") if c.strip(' "\'')]
            for c in reversed(chunk):
                if re.search(r"[A-Z]", c) and len(c) <= 30 and len(c) >= 2:
                    place = c
                    break
        return place, str(day), mo, yr, idx, ((mscore < 0.6) or day_fuzzy)
    return None, None, None, None, None, False

def clean_body(raw):
    lines = []
    for ln in raw.split("\n"):
        s = ln.strip()
        if not s or FOOT.match(s):
            continue
        lines.append(s)
    text = " ".join(lines)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)   # de-hyphenate line breaks
    text = re.sub(r"\s+", " ", text)
    return text.strip(' "\'')

def norm_month(m):
    m = m.strip().strip("^").rstrip("s") if m.strip("^").lower() not in ("paris",) else m
    m = m.strip().strip("^")
    if m.endswith("s") and m[:-1] in MONTHS:
        m = m[:-1]
    return m

def parse(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    lines = t.split("\n")
    heads = [(i, l.strip()) for i, l in enumerate(lines)
             if HEAD.match(l.strip()) and len(l.strip()) < 70]
    recs = []
    chapter = None
    for n, (i, h) in enumerate(heads):
        m = HEAD.match(h)
        addr = re.sub(r"\s+", " ", m.group(2)).strip()
        end = heads[n+1][0] if n+1 < len(heads) else min(i+120, len(lines))
        block = lines[i+1:end]
        # chapter year context: look back for "The Year XXXX"
        for back in range(i, max(0, i-60), -1):
            cm = re.search(r"The Year (17\d\d|18\d\d|1[78]\d\d)", lines[back])
            if cm:
                chapter = cm.group(1)
                break
        # find date: search 8 lines after header, then 3 lines before
        win = [(i+1+k, block[k]) for k in range(min(8, len(block)))]
        win += [(i-b, lines[i-b]) for b in (1, 2, 3) if i-b >= 0]
        place, day, month, year, date_idx, fuzzy = find_date(win, chapter)
        if date_idx is not None and date_idx > i:
            date_pos = date_idx - (i+1)
        else:
            date_pos = -1
        body_lines = block[(date_pos+1) if date_pos >= 0 else 0:]
        # cut at signature
        cut = len(body_lines)
        for k, ln in enumerate(body_lines):
            if SIG.search(ln.strip()):
                cut = k
                break
            if re.match(r'^CHAPTER [IVX]+\.?$', ln.strip()) or ln.strip() in ("CONTENTS.",):
                cut = k
                break
        body = clean_body("\n".join(body_lines[:cut]))
        iso = None
        if month in MONTHS and year:
            try:
                iso = f"{year}-{MONTHS[month]:02d}-{int(day):02d}"
            except ValueError:
                iso = None
        rev = month in REV or (month or "") in REV
        recs.append({"addr": addr, "place": place, "day": day, "month": month,
                     "year": year, "iso": iso, "rev_date": bool(rev),
                     "fuzzy_date": bool(fuzzy),
                     "chars": len(body), "body": body[:3000]})
    return recs

if __name__ == "__main__":
    recs = parse(sys.argv[1])
    dated = [r for r in recs if r["iso"]]
    print(f"headers={len(recs)} dated={len(dated)} rev-only={sum(1 for r in recs if r['rev_date'] and not r['iso'])}")
    yrs = sorted(r["iso"][:4] for r in dated)
    print("range:", yrs[0], "->", yrs[-1])
    json.dump(recs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print("wrote", sys.argv[2])
