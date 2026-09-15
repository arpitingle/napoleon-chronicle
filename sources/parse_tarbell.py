#!/usr/bin/env python3
"""Parse Tarbell (1897) Napoleon's Addresses OCR into {title, iso, approx, body}.

Headings look like:  Proclamation after the Battle of Austerlitz, Dec. 3, 1805.
plus a few 'To X ... date' headings after page footers.
"""
import re, json, sys

MONTHS = {m: i+1 for i, m in enumerate(
    ["January","February","March","April","May","June","July",
     "August","September","October","November","December"])}
ABBR3 = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
         "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
         "Oct": "October", "Nov": "November", "Dec": "December"}

KINDS = ("Proclamation|Address|Letter|Order|Speech|Farewell|Summons|Discourse|"
         "Conversation|Protest|Will|Extract|Answer|Note")

def normalize(t):
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
    t = re.sub(r"1S(\d\d)", r"18\1", t)
    t = re.sub(r"iS(?=\d)", "18", t)
    t = re.sub(r"l8l(\d)", r"181\1", t)
    t = re.sub(r"\b18 ([45])\b", r"18\1", t)
    t = re.sub(r"Dec\. i,", "Dec. 1,", t)
    t = re.sub(r"\blo, (?=1799)", "10, ", t)
    t = re.sub(r"\bi8oy\b", "1807", t)
    t = re.sub(r"\biSoy\b", "1807", t)
    t = re.sub(r"Febj'uary", "February", t)
    return re.sub(r"\s+", " ", t)

MRE = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*)"
DRE = r"([A-Za-z0-9]{1,5})?(?:st|nd|rd|th)?,?\s*(1[78]\d\d)\.?"

def split_day(tok):
    if not tok:
        return 1, True
    raw = tok.strip()
    cl = raw.replace("i", "1").replace("l", "1").replace("Z", "1").replace(
        "o", "0").replace("O", "0").replace("^", "").replace("/", "").replace("'", "")
    m = re.match(r"(\d{1,2})", cl)
    if not m:
        return 1, True
    v = int(m.group(1))
    if not 1 <= v <= 31:
        return 1, True
    return v, (cl != raw or len(cl) > 2)

def split_month_day(src):
    m = re.search(MRE + r"\.?,?\s*" + DRE, src)
    if not m:
        return None, None, None
    mon = m.group(1)
    for full in MONTHS:
        if full.lower().startswith(mon[:3].lower()):
            mon = full
            break
    return mon, m.group(2), m.group(3)

def parse(path):
    t = normalize(open(path, encoding="utf-8", errors="replace").read())
    hp = re.compile(r"((?:" + KINDS + r")s?\b[^\"\n]{0,120}?)"
                    r",?\s+" + MRE + r"\.?,?\s*" + DRE)
    spans = [(m.group(0).strip(), m.start(), m.end()) for m in hp.finditer(t)]
    # drop spans that swallowed two headings
    kl = [k.lower() for k in KINDS.split("|")]
    kept = []
    for h, s, e in spans:
        pre = h[:max(0, h.find("18"))]
        if sum(pre.lower().count(k) for k in kl) >= 2:
            continue
        kept.append((h, s, e))
    spans = kept
    # To-start headings right after page footers
    foot = re.compile(r"(?:napoleon's addresses\.?\s*\d{1,3}|\d{1,3}\s*napoleon's addresses\.?|NAPOLEON,\s+[A-Z][A-Z ]{0,40}?\.?\s*\d{0,3})")
    for fm in foot.finditer(t):
        seg = t[fm.end():fm.end()+450]
        tm = re.match(r"\s*((?:To|For)\b[^\"\n]{2,140}?),?\s+" + MRE + r"\.?,?\s*" + DRE, seg)
        if tm:
            s = fm.end() + tm.start(1)
            spans.append((tm.group(0).strip(), s, s + tm.end()))
    spans.sort(key=lambda x: x[1])
    out = []
    for n, (h, s, e) in enumerate(spans):
        end = spans[n+1][1] if n+1 < len(spans) else e + 6000
        body = t[e:min(end, e+6000)]
        body = re.split(r"\d{1,3}\s+NAPOLEON.?S\s+ADDRESSES\.?", body)[0]
        body = body.strip(' "\'“”')
        mon, day, yr = split_month_day(h)
        if not (mon and yr):
            continue
        daynum, approx = split_day(day)
        out.append({"title": re.sub(r"\s+", " ", h).strip(),
                    "iso": f"{yr}-{MONTHS.get(mon,1):02d}-{daynum:02d}",
                    "approx": approx, "body": body.strip()[:2500]})
    return out

if __name__ == "__main__":
    recs = parse(sys.argv[1])
    json.dump(recs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print("raw:", len(recs))
