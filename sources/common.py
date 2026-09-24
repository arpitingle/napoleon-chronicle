#!/usr/bin/env python3
"""Shared helpers for Napoleon builders. Quotes verbatim from PD sources;
light cleanup only (running heads, spacing, footnote junk). No words altered."""
import json, re

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}

# Records that must never publish, even though their slices carry them:
# exact duplicates filed twice, or non-letter material (contents pages,
# chapter prefaces) parsed as letters. Skipped loudly by build_index.
DROP_IDS = {
    "nap-18150226-77",   # dup of nap-18150226-641 (same Elba farewell body)
    "nap-18080217-127",  # dup of nap-18080217-412 (same Caulaincourt letter)
    "nap-18060201-187",  # Tarbell contents page, not the proclamation
    "nap-18051201-292",  # chapter preface; the letter ships as nap-18051201-48
    "nap-17960501-16",   # dup of nap-17960501-09 (same Directory letter)
    "nap-18070201-371",  # dup of nap-18070201-95 (same Prussia letter)
    "nap-18070301-377",  # dup of nap-18070301-98 (same Porte letter)
    "nap-18070301-378",  # dup of nap-18070301-99 (same Naples letter)
    "nap-18050810-274",  # dup of nap-18050810-35 (same Daru letter)
    "nap-18050810-275",  # dup of nap-18050810-37 (same Hanover letter)
    "nap-17960501-81",   # dup of nap-17960501-08 (same Faypoult letter)
    "nap-17960501-82",   # dup of nap-17960501-11 (same Finances letter)
    "nap-17961002-18",   # dup of nap-17961002-13 (same Directory letter)
    "nap-17961002-19",   # dup of nap-17961002-14 (same Emperor letter)
    "nap-18060910-341",  # dup of nap-18060910-72 (same Berthier letter)
    "nap-18060910-343",  # dup of nap-18060910-74 (same Holland letter)
    "nap-18070101-360",  # dup of nap-18070101-89 (same Berthier letter)
    "nap-17960802-29",   # Nelson journal filed as Napoleon; not his writing
    "nap-17990307-114",  # British writer (Troubridge/Nile) filed as Napoleon
    "nap-17990314-116",  # Bey of Tunis letter filed as Napoleon; not his
    "nap-18030710-207",  # editorial mashup, no attributable letter text
    "nap-18030710-208",  # hostile British writer filed as Napoleon; not his
    "nap-18030810-213",  # Nelson message to prisoners filed as Napoleon
    "nap-17960528-167",  # contents page (list of addresses), not a letter
    "nap-17980727-172",  # contents page (list of proclamations), not a letter
    "nap-18051001-183",  # contents page (list of addresses), not a letter
    "nap-18051226-186",  # contents page (list of proclamations), not a letter
    "nap-18081001-194",  # contents page (list of proclamations), not a letter
    "nap-18081201-195",  # contents page (list of proclamations), not a letter
    "nap-18130214-93",   # contents page (list of addresses), not a letter
    "nap-18131201-94",   # contents page (list of addresses), not a letter
    "nap-18101104-498",  # index fragment, not a letter
    "nap-18101226-502",  # chapter intro, not a letter
    "nap-18140901-640",  # chapter intro, not a letter
    "nap-18140301-625",  # editorial note (no letter exists), not a letter
    "nap-17960429-81",   # dup fragment of nap-17960429-07 (same Coni letter)
    "nap-17961004-20",   # dup of nap-17961004-17 (same Modena letter)
    "nap-17970201-20",   # dup of nap-17970201-163 (same Savants letter)
    "nap-17970416-81",   # dup of nap-17970416-21 (same Leclerc letter)
    "nap-17970714-81",   # dup fragment of nap-17970714-23 (same address)
    "nap-17980702-57",   # dup fragment of nap-17980702-54 (same Alexandria text)
    "nap-17990102-81",   # dup of nap-17990102-32 (same Tippoo letter)
    "nap-18000601-177",  # dup of nap-18000601-176 (same Marengo text)
    "nap-18070622-112",  # dup of nap-18070622-111 (same St Denis text)
    "nap-18130830-597",  # dup of nap-18130830-53 (same Wurtemberg letter)
    "nap-18070701-394",  # dup fragment of nap-18070701-81 (same Portugal letter)
    "nap-18120307-534",  # dup of nap-18120307-21 (same Lauriston letter)
    "nap-18120406-537",  # dup of nap-18120406-22 (same Berthier letter)
    "nap-18120701-539",  # dup of nap-18120701-25 (same Berthier letter)
    "nap-18120807-542",  # dup of nap-18120807-27 (same Maret letter)
    "nap-18121001-547",  # dup of nap-18121001-30 (same Berthier letter)
    "nap-18121201-552",  # dup of nap-18121201-34 (same Narbonne letter)
    "nap-18121210-553",  # dup of nap-18121210-33 (same Maret compilation)
    "nap-18100620-478",  # dup of nap-18100620-04 (same Russia letter)
    "nap-18100701-479",  # dup of nap-18100701-05 (same Gaudin letter)
    "nap-18100802-485",  # dup of nap-18100802-07 (same Russia letter)
    "nap-18100917-488",  # dup of nap-18100917-08 (same Berthier letter)
    "nap-18110607-510",  # dup of nap-18110607-12 (same Berthier letter)
    "nap-18110802-517",  # dup of nap-18110802-13 (same Maret letter)
    "nap-18110901-520",  # dup of nap-18110901-18 (same Davout letter)
    "nap-18111231-526",  # dup of nap-18111231-20 (same Champagny letter)
    "nap-18140102-608",  # dup of nap-18140102-59 (same St Dizier letter)
    "nap-17960527-701",  # corr: excerpt is filing close + next header only
    "nap-18000112-703",  # corr: excerpt is signature + next header only
    "nap-17960600-700",  # corr: edition dates it "June 1796" only; no day
    "nap-18000427-701",  # corr: excerpt opens with filing debris ("', <")
    "nap-17960504-19",   # Bingham narrator's account of a letter, not Napoleon's writing
    "nap-17940104-700",  # corr: excerpt is a filing header, no letter text
    "nap-17960530-700",  # corr: excerpt is filing close + next header only
    "nap-17960622-700",  # corr: excerpt is signature + next header only
    "nap-17960713-700",  # corr: excerpt ends mid-sentence, incomplete
    "nap-17960728-702",  # corr: excerpt is filing close + next header only
    "nap-17961119-703",  # corr: excerpt starts and ends mid-word, incomplete
    "nap-17980803-700",  # corr: 42-char fragment, too thin for a record
    "nap-17981006-701",  # corr: pay-table fragment + running head
    "nap-17981116-701",  # corr: 50-char fragment, too thin for a record
    "nap-18000118-702",  # corr: excerpt is a question fragment + signature
    "nap-18000216-700",  # corr: excerpt is filing close + next header only
    "nap-18000510-702",  # corr: excerpt is signature + next header only
    "nap-18000715-703",  # corr: excerpt is signature + next header only
    "nap-18001120-700",  # corr: excerpt is head debris, no letter text
    "nap-18001222-700",  # corr: excerpt is signature + next header only
    "nap-18010306-700",  # corr: excerpt is signature + next header only
    "nap-18010413-702",  # corr: excerpt is signature + next header only
    "nap-18010720-700",  # corr: excerpt is OCR salad, no readable text
    "nap-18010723-700",  # corr: excerpt is signature + annex header only
    "nap-18011115-700",  # corr: excerpt is filing close + next header only
    "nap-18020210-704",  # corr: excerpt is signature + next header only
    "nap-18021218-700",  # corr: excerpt is signature + next header only
    "nap-18030923-700",  # corr: end-of-volume matter, not a letter
    "nap-18020720-700",  # corr: excerpt is OCR salad, no readable text
}

# OCR-mangled datelines, lowercased: each maps to the real place.
# Only confident readings live here; anything doubtful stays raw and is
# hidden by the display layers instead.
PLACE_FIX = {
    "kcenigsberg": "Königsberg",
    "schcenbrunn": "Schönbrunn",
    "schoenbrunn": "Schönbrunn",
    "brtjnn": "Brünn",
    "auserlitz": "Austerlitz",
    "compeigne": "Compiègne",
    "coiipeigxe": "Compiègne",
    "finckbnsteix": "Finckenstein",
    "finckensteix": "Finckenstein",
    "finckexstein": "Finckenstein",
    "fixckensteix": "Finckenstein",
    "flnkensteln": "Finckenstein",
    "pinkenstein": "Finckenstein",
    "plnckenstein": "Finckenstein",
    "finkenstein": "Finckenstein",
    "fontainebleait": "Fontainebleau",
    "fontainebleatt": "Fontainebleau",
    "erfurth": "Erfurt",
    "donauwoerth": "Donauwörth",
    "dusseldorf": "Düsseldorf",
    "chalon-sur-saone": "Chalon-sur-Saône",
    "aix la chapelle": "Aix-la-Chapelle",
    "st cloud": "St. Cloud",
    "st. clovd": "St. Cloud",
    "st; cloud": "St. Cloud",
    "marmieolo": "Marmirolo",
    "golimin": "Golymin",
    "goritz": "Gorizia",
    "bayon-ne": "Bayonne",
    "porto ferrajo": "Portoferraio",
    "berg-op-zoom": "Bergen-op-Zoom",
    "rastadt": "Rastatt",
    "strasburg": "Strasbourg",
    "veroni": "Verona",
    "gyzeh": "Giza",
    "ghjatsh": "Giza",
    "mojaisk": "Mozhaysk",
    "dorogsbouje": "Dorogobuzh",
    "viazma": "Vyazma",
    "wittemberg": "Wittenberg",
    "llebstadt": "Liebstadt",
    "varis": "Paris",
    "wurchen": "Wurzen",
    "forli": "Forlì",
    "frankfort": "Frankfurt",
    "frejus": "Fréjus",
    "nymphenberg": "Nymphenburg",
    "tretes": "Trèves",
    "lesaca": "Lesaka",
    "captain at sea.": "At sea",
    "camp or boulogne": "Camp Of Boulogne",
    "pont de briques": "Pont-de-Briques",
    "piacenza": "Piacenza",
    "placentia": "Piacenza",
}

#unrecoverable filings: blanked everywhere (sourceTitle keeps them).
UNMAPPABLE_PLACES = {
    "uh", "wi", "iwi", "gta", "luh", "haynan", "rosnig", "istk", "freueda",
    "blechenkovitchi", "biechenkovitchi", "tth", "stk", "gth", "a",
    "z'^st", "zzth", "t-7th",
}

PLACE_JUNK = re.compile(r"\d|[^\w\s\.\-'/À-Þà-þ]|^[^A-Za-zÀ-Þ]")


def clean_place(loc):
    """Normalize an OCR-mangled dateline, or "" when unrecoverable."""
    t = (loc or "").strip()
    if not t:
        return ""
    if t.lower() in PLACE_FIX:
        return PLACE_FIX[t.lower()]
    t = re.sub(r"^[\s*^•■\-\"'<>\\/]+", "", t).strip()
    t = re.sub(r"[\s*^•■\-\"'<>\\/]+$", "", t).strip()
    m = re.match(r"^Cloud\.\s+(.+)$", t, re.I)
    if m:
        t = m.group(1).strip()
    if t.lower() in PLACE_FIX:
        return PLACE_FIX[t.lower()]
    if t.lower() in UNMAPPABLE_PLACES:
        return ""
    if len(t) < 3 or PLACE_JUNK.search(t):
        return ""
    return t

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
