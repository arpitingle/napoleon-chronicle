#!/usr/bin/env python3
"""Shared helpers for Napoleon builders. Quotes verbatim from PD sources;
light cleanup only (running heads, spacing, footnote junk). No words altered."""
import json, re

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}

RUNHEAD_NUM = re.compile(r"[A-Z][A-Z \.]{8,55}\. \d{1,3}")
GOCORR = re.compile(r"\bgo (THE CORRESPONDENCE OF NAPOLEON|NAPOLEONS? +ADDRESSES)\.?")

def clean(s, limit=300):
    s = s.replace(" ", " ")
    s = re.sub(r"\^", "", s)
    s = RUNHEAD_NUM.sub(" ", s)
    s = GOCORR.sub(" ", s)
    s = re.sub(r"\bVOL\. II\.?[^.]{0,40}THE CORRESPONDENCE OF NAPOLEON\b", " ", s)
    s = re.sub(r"\b[0-9a-z]{1,4}( \d{1,3})? THE CORRESPONDENCE OF NAPOLEON\b", " ", s)
    s = re.sub(r"\bVOL\. II[^.]{0,25}", " ", s)
    s = re.sub(r"\b\d{1,3} NAPOLEON.?S\s+ADDRESSES\.?", " ", s)
    s = re.sub(r"\s*\d{1,4}[\*o]?\s+(CONFIDENTIAL LETTERS|NAPOLEON.?S)\.?\s*", " ", s)
    # leading dateline/signature echoes ("St. Cloud, 22nd June, 1806. " / '" Napoleon." to X.')
    s = re.sub(r"^.{0,90}?\b(1[78]\d\d)\.\s*(?=[A-Z“\"'])", "", s) if re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December|St\. Cloud|Paris|Napoleon|DECISION|DECREE|CHAPTER)", s[:90]) else s
    s = re.sub(r'^["“”\s]*" Napoleon\."\s*to [^.]+\.\s*', "", s)
    s = re.sub(r"^[^.]{0,70}?\b(17\d\d|18\d\d)\.\s*", " ", s)
    s = re.sub(r"\b[A-Z][A-Z \.]{6,40}\. [a-z0-9]{1,4}\b", " ", s)
    s = re.sub(r"\.\s+\.", ".", s)
    s = re.sub(r"^[\s.\"'*^~]+", "", s)
    s = re.sub(r"\s+", " ", s).strip(" \"'*^~")
    # trailing page-signature codes and detached signatures
    s = re.sub(r'\s*" Napoleon\."\s*[A-Z]? ?\d*\.?\s*$', "", s)
    s = re.sub(r'\s*" Napoleon\."\s*(?=[A-Z“\"]|$)', " ", s)
    s = re.sub(r"\s+[A-Z]( [A-Z]){0,2} \d\.?\s*$", "", s)
    s = re.sub(r"\s+[A-Z]( [A-Z]){1,2} \d\.?(?=[\s\[“\"—])", " ", s)
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"\.{3,}", ".", s)
    s = re.sub(r"(?<!\.)\.\.(?!\.)", ".", s)
    s = re.sub(r"([A-Za-z])\d(?=[\s.,;:\]])", r"\1", s)
    s = re.sub(r"\b[Ff] \d\b", "", s)
    s = re.sub(r"\s+''", "", s)
    s = re.sub(r"\^", "", s)
    s = re.sub(r"^M\. ", "", s)
    s = re.sub(r"\s+", " ", s).strip(" \"'")
    if len(s) <= limit:
        return s
    cut = s[:limit]
    for p in (". ", "! ", "? ", "; ", " — ", ", "):
        k = cut.rfind(p)
        if k > limit * 0.45:
            return cut[:k+1].strip() + " […]"
    return cut.strip() + " […]"

VIVID = re.compile(r"\b(gloire|victoire|sang|mort|honneur|liberté|patrie|courage|peur|terrible|immense|désastre|triomphe|vengeance|trahison|complot|famine|pillage|incendie|glory|victory|blood|death|honour|honor|liberty|courage|fear|terrible|disaster|triumph|revenge|treason|famine|courageux|brave|audace|péril|danger)\b", re.I)
BOILER = re.compile(r"^(vous trouverez ci-joint|j'ai reçu votre|je vous prie de me faire|il est ordonné|citoyen|li est ordonné|you will find (in|en)closed|i have received your|i beg you will|it is (hereby )?ordered|the general-in-chief orders|article 1)", re.I)

def sentences(s):
    parts = re.split(r"(?<=[.!?;:])\s+", s)
    out = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # glue tiny fragments (datelines, page heads) to neighbours
        if len(p) < 40 and out is False:
            pass
        if len(p) < 40:
            buf = (buf + " " + p).strip()
            continue
        if buf:
            p = (buf + " " + p).strip()
            buf = ""
        out.append(p)
    if buf and (not out or len(buf) > 40):
        out.append(buf)
    return [x for x in out if len(x) >= 40]

def score_sent(s):
    sc = 0.0
    n = len(s)
    if 60 <= n <= 220:
        sc += 2.0
    elif n > 320:
        sc -= 1.5
    sc += min(3.0, len(re.findall(r"\d[\d,\.]*", s)) * 1.0)
    sc += min(2.0, len(VIVID.findall(s)) * 1.0)
    if re.search(r"\b(je|j'|nous|moi|i\b|we\b|my\b)", s, re.I):
        sc += 0.5
    if BOILER.match(s):
        sc -= 4.0
    # never pick datelines, signatures, chapter heads, decree/proclamation labels
    if re.match(r'^["“”\s]*([A-Z][\w\-\. ]{1,40}?,\s*)?\d{1,2}(st|nd|rd|th)?,?\s+[A-Z][a-z]+\s*,?\s*1[78]\d\d\.?\s*["“”\s]*$', s):
        sc -= 10.0
    if re.match(r'^["“”\s]*(Napoleon\.|DECREE\.?|DECISION\.?|PROCLAMATION[^a-z]*|CHAPTER[^a-z]*|ORDER[^a-z]*)\s*["“”\s]*$', s):
        sc -= 10.0
    if re.match(r'["“”\s]*\d+\s+(DECISION|DECREE)\b', s):
        sc -= 6.0
    if re.match(r'["“”\s]*\d+(st|nd|rd|th)\b', s):
        sc -= 2.0
    # penalize OCR garbage: digit-letter mixes, stray backslashes, lone fragments
    sc -= min(4.0, len(re.findall(r"[A-Za-z]+\d+[A-Za-z0-9]*|\d+[A-Za-z]+", s)) * 2.0)
    sc -= min(2.0, s.count("\\") * 2.0 + s.count("^") * 2.0)
    sc -= min(2.0, len(re.findall(r"\b[A-Za-z]\b", s)) * 0.4)
    if re.search(r"^[\"'“”\s]*\.{2,}", s):
        sc -= 2.0
    return sc

def best_excerpt(body, limit=300, floor=1.0):
    """Pick the highest-scoring 1-2 sentences instead of the opening lines.
    Returns None if nothing scores above floor (letter sits out)."""
    sents = sentences(body)
    if not sents:
        return clean(body, limit)
    ranked = sorted(range(len(sents)), key=lambda i: -score_sent(sents[i]))
    if score_sent(sents[ranked[0]]) < floor:
        return None
    first = ranked[0]
    picks = [first]
    # add a neighbour for context if it fits and scores decently
    for j in (first + 1, first - 1):
        if 0 <= j < len(sents) and j not in picks:
            cur = " ".join(sents[k] for k in sorted(picks + [j]))
            if len(cur) <= limit and score_sent(sents[j]) > 0:
                picks.append(j)
            break
    picks.sort()
    txt = " ".join(sents[k] for k in picks)
    # strip leading dateline/signature/dec decree-label fragments from excerpt
    txt = re.sub(r'^["“”\s]*" Napoleon\."\s*to [^.]+\.\s*', "", txt)
    m = re.match(r'^.{0,100}?\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b.{0,45}?1[78][\s\dOolI]{2,5}\.\s*', txt)
    if m:
        txt = txt[m.end():].strip()
    txt = re.sub(r'^(CHAPTER|DECREE|DECISION|PROCLAMATION|ORDER)[^.]{0,60}?\.\s*', "", txt)
    txt = txt.strip()
    if len(txt) > limit:
        cut = txt[:limit]
        for p in (". ", "! ", "? ", "; ", ", "):
            k = cut.rfind(p)
            if k > limit * 0.45:
                txt = cut[:k+1].strip()
                break
        else:
            txt = cut.strip()
    return txt + " […]"

_seq = [0]

def push(out, author_d, faction, date, tlabel, loc, disp, src_title,
         archive, url, dtype, ctx, eid, cert="certain", lang=None, ev="TRANSLATION"):
    _seq[0] += 1
    out.append({
        "id": f"nap-{date.replace('-','')}-{_seq[0]:02d}",
        "author": author_d["author"], "handle": author_d["handle"],
        "accountType": author_d["accountType"], "faction": faction,
        "date": date, "timeLabel": tlabel or "TIME UNCERTAIN", "timePrecision": "day",
        "location": loc,
        "originalLanguage": lang or ("French" if author_d["author"] == "Napoleon Bonaparte" else "English"),
        "displayText": disp, "sourceTitle": src_title, "archive": archive,
        "sourceUrl": url, "documentType": dtype, "evidenceType": ev,
        "dateCertainty": cert, "eventIds": [eid], "editorialStatus": "verified",
        "context": ctx})

BINGHAM_URL = "https://archive.org/details/acp7797.0001.001.umich.edu"
JOSEPHINE_URL = "https://archive.org/details/confidentialcorr00napoiala"
TARBELL_URL = "https://archive.org/details/napoleonsaddress00napo"
