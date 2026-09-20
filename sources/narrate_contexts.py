#!/usr/bin/env python3
"""Narrative contexts for the 641 boilerplate bulk records.

A tweet needs a narrative voice, not keyword tags. Each narrative is built
from three grounded parts — nothing invented:

  scene  the record's event moment blurb (hand-written, events.json)
  frame  the addressee with a factual role (ROSTER below; plain name fallback)
  clause one coherent clause from the letter itself (its point, verbatim
         words, trimmed to fit — the full quote stays behind Verbatim)

e.g. "Moscow entered, Moscow burned, the wreck retreats. To Marshal Davout:
hold the Hamburg fortress."

Output: sources/context_drafts.json (same schema as draft_contexts.py, plus
"parts"), consumed by apply_contexts.py + hand_contexts.json as before.

Run from anywhere:  python3 sources/narrate_contexts.py
"""
import json, os, re, sys, unicodedata
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "sources"))
from draft_contexts import (match_body, norm, contains, known, JUNK, WORDS,
                            VERB, STOP)
from common import clean_place

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# normalized-address -> "role + name" frame. Date-sensitive entries are
# functions of (name, date). Keep to well-established identities only.
def eugene(name, date):
    return ("his stepson Eugène, viceroy of Italy" if date >= "1805-06"
            else "his stepson Eugène")


def joseph(name, date):
    if "spain" in name or ("joseph" in name and date >= "1808-06"):
        return "his brother Joseph, king of Spain"
    if "naples" in name or "joseph" in name:
        return "his brother Joseph, king of Naples"
    return "his brother Joseph"


def spain_king(name, date):
    if date >= "1808-06":
        return "his brother Joseph, king of Spain"
    return "the Spanish king"


ROSTER = {
    "thedirectory": "the Directory",
    "clarke": "his war minister Clarke",
    "genclarke": "his war minister Clarke",
    "talleyrand": "his foreign minister Talleyrand",
    "mde": None,  # prefix fragment, never a full key
    "mdetalleyrand": "his foreign minister Talleyrand",
    "mtalleyrand": "his foreign minister Talleyrand",
    "champagny": "his minister Champagny",
    "mdechampagny": "his minister Champagny",
    "berthier": "his chief of staff Berthier",
    "marshalberthier": "his chief of staff Berthier",
    "generalberthier": "his chief of staff Berthier",
    "princeofneufchatel": "his chief of staff Berthier",
    "princeofneuchatel": "his chief of staff Berthier",
    "eugene": eugene,
    "princeeugene": eugene,
    "eugenenapoleon": eugene,
    "empress": "Josephine",
    "theempress": "Josephine",
    "josephine": "Josephine",
    "theempressjosephine": "Josephine",
    "maret": "his secretary of state Maret",
    "bassano": "his secretary of state Maret",
    "dukeofbassano": "his secretary of state Maret",
    "davoust": "Marshal Davout",
    "davout": "Marshal Davout",
    "marshaldavoust": "Marshal Davout",
    "marshaldavout": "Marshal Davout",
    "emperorofrussia": "Tsar Alexander",
    "fouche": "his police minister Fouché",
    "mfouche": "his police minister Fouché",
    "fouchjfe": "his police minister Fouché",
    "emperorofaustria": "the Austrian emperor",
    "cambaceres": "his arch-chancellor Cambacérès",
    "princecambaceres": "his arch-chancellor Cambacérès",
    "decres": "his navy minister Decrès",
    "admiraldecres": "his navy minister Decrès",
    "viceadmiraldecrfes": "his navy minister Decrès",  # OCR for Decrès
    "carnot": "Carnot",
    "fesch": "his uncle Cardinal Fesch",
    "cardinalfesch": "his uncle Cardinal Fesch",
    "caulaincourt": "Caulaincourt",
    "generalcaulaincourt": "Caulaincourt",
    "dukeofvicence": "Caulaincourt",
    "dukeofvicenza": "Caulaincourt",
    "savary": "Savary",
    "gensavary": "Savary",
    "dukeofrovigo": "Savary",
    "chaptal": "his interior minister Chaptal",
    "murat": "his brother-in-law Murat",
    "generalmurat": "his brother-in-law Murat",
    "lucienbonaparte": "his brother Lucien",
    "lucienbuonaparte": "his brother Lucien",
    "josephbonaparte": "his brother Joseph",
    "josephbuonaparte": "his brother Joseph",
    "moreau": "his rival Moreau",
    "generalmoreau": "his rival Moreau",
    "kleber": "Kléber in Egypt",
    "marmont": "Marmont",
    "genmarmont": "Marmont",
    "kinglouisofholland": "his brother Louis, king of Holland",
    "kingofholland": "his brother Louis, king of Holland",
    "pope": "Pope Pius VII",
    "hhthepope": "Pope Pius VII",
    "holyfather": "Pope Pius VII",
    "junot": "Junot",
    "genjunot": "Junot",
    "massena": "Masséna",
    "soult": "Marshal Soult",
    "marshalsoult": "Marshal Soult",
    "dukeofdalmatia": "Marshal Soult",
    "ney": "Marshal Ney",
    "marshalney": "Marshal Ney",
    "lannes": "Lannes",
    "augereau": "Augereau",
    "marshalaugereau": "Augereau",
    "bernadotte": "Bernadotte",
    "marshalbernadotte": "Bernadotte",
    "lefebvre": "Lefebvre",
    "marshallefebvre": "Lefebvre",
    "macdonald": "Marshal Macdonald",
    "gaudin": "his finance minister Gaudin",
    "lebrun": "Lebrun in Paris",
    "portalis": "Portalis",
    "bigot": "Bigot",
    "duroc": "his palace marshal Duroc",
    "genduroc": "his palace marshal Duroc",
    "jerome": "his brother Jérôme, king of Westphalia",
    "kingjerome": "his brother Jérôme, king of Westphalia",
    "kingofwestphalia": "his brother Jérôme, king of Westphalia",
    "queenofprussia": "Queen Louise of Prussia",
    "kingofprussia": "the Prussian king",
    "kingofnaples": joseph,
    "kingjoseph": joseph,
    "princejoseph": joseph,
    "kingofspain": spain_king,
    "rearadmiraldecres": "his navy minister Decrès",
    "regnier": "his grand-judge Régnier",
    "brune": "Marshal Brune",
    "generalbrune": "Marshal Brune",
    "bertrand": "Bertrand",
    "generalbertrand": "Bertrand",
    "laplace": "the savant Laplace",
    "sultan": "Sultan Selim",
    "sultanselim": "Sultan Selim",
    "princeregentofportugal": "the Prince Regent of Portugal",
    "tippoo": "Tipu Sultan",
    "princeofthepeace": "Godoy, Prince of the Peace",
    "theelectorofvvirtemberg": "the Elector of Württemberg",
    "thecardinalarchbishopofparis": "his uncle Cardinal Fesch",
    "marshaldavoust": "Marshal Davout",
    "davoust": "Marshal Davout",
    "emperorofturkey": "the Ottoman sultan",
    "angereau": "Augereau",
    "marshalangereau": "Augereau",
    "marineminister": "his navy minister",
    "warminister": "his war minister",
    "foreignminister": "his foreign minister",
    "ministerofforeignaffairs": "his foreign minister",
}

AUX = (r"\bam\b|\bis\b|\bare\b|\bwas\b|\bwere\b|\bhave\b|\bhas\b|\bhad\b"
       r"|\bwill\b|\bshall\b|\bmust\b|\bdo\b|\bdoes\b|\bdid\b|\blet\b"
       r"|\btak(?:e|es|ing|ook|en)\b|\bmak(?:e|es|ing)\b|\bmad(?:e|e)\b"
       r"|\bgiv(?:e|es|ing|en)\b|\bgav(?:e|e)\b|\bsen[dt]\b|\bcom(?:e|es|ing)"
       r"\b|\bcam(?:e|e)\b|\bgo\b|\bgoes\b|\bwent\b|\bse(?:e|es|en)\b|\bwrot\b"
       r"|\bwrit(?:e|ten)\b"
       r"|\bsaw\b|\bknow(?:s|n)?\b|\bknew\b|\bthink\b|\bthought\b"
       r"|\bfin[dd](?:s|ing)?\b|\bfound\b|\bleav(?:e|es|ing)\b|\bleft\b"
       r"|\bhol[dd](?:s|ing)?\b|\bhel[dd]\b|\bkeep(?:s|ing)?\b|\bkept\b"
       r"|\bput\b|\bset\b|\bseem(?:s|ed|ing)?\b|\bbecom(?:e|es|ing)\b"
       r"|\bbecam(?:e|e)\b|\bgrow(?:s|ing|n)?\b|\bgrew\b|\bliv(?:e|es|ing|ed)"
       r"\b|\bfall?(?:s|en|ing)?\b|\bfell\b|\bris(?:e|es|ing|en)\b"
       r"|\bfigh[tt](?:s|ing)?\b|\bfought\b|\bwin\b|\bwins\b|\bwon\b"
       r"|\blos(?:e|es|ing|t)\b|\bow(?:e|es|ed|ing)\b|\bwant(?:s|ed|ing)?\b"
       r"|\bbeliev(?:e|es|ed|ing)\b|\bdesir(?:e|es|ed|ing)\b"
       r"|\bseek(?:s|ing)?\b|\bsough[tt]\b|\bgain(?:s|ed|ing)?\b"
       r"|\bsav(?:e|es|ed|ing)\b|\bspar(?:e|es|ed|ing)\b|\bjoin(?:s|ed|ing)?\b"
       r"|\bquit(?:s|ting)?\b|\bstay(?:s|ed|ing)?\b|\bserv(?:e|es|ed|ing)\b"
       r"|\bdeserv(?:e|es|ed|ing)\b|\bcontain(?:s|ed|ing)?\b"
       r"|\bexplain(?:s|ed|ing)?\b|\bstat(?:e|es|ed|ing)\b"
       r"|\bobserv(?:e|es|ed|ing)\b|\bremark(?:s|ed|ing)?\b"
       r"|\brequir(?:e|es|ed|ing)\b|\bsuppos(?:e|es|ed|ing)\b"
       r"|\bimagin(?:e|es|ed|ing)\b|\bwish(?:e[sd]?|ing)?\b"
       r"|\bfear(?:s|ed|ing)?\b|\bneed(?:s|ed|ing)?\b|\bhop(?:e[sd]?|ing)?\b"
       r"|\bpress(?:e[sd]?|ing|ure)?\b")

VERBISH = re.compile("|".join([p for p, _ in VERB] + [AUX]), re.I)


# earliest month the event blurb is true of. A record dated before its
# event's gate gets a neutral "Place, Month Year." scene instead — the old
# code printed "Prussia annihilated in seven days" on February 1806 letters.
EVENT_DATES = {
    "toulon-1793": "1793-09", "youth-1795": "1795-09",
    "italy-1796": "1796-05", "campo-1797": "1797-04",
    "egypt-1798": "1798-07", "brumaire-1799": "1799-10",
    "marengo-1800": "1800-06", "consulate-1802": "1802-03",
    "boulogne-1803": "1803-05", "empire-1804": "1804-05",
    "austerlitz-1805": "1805-12", "jena-1806": "1806-10",
    "eylau-1807": "1807-02", "tilsit-1807": "1807-06",
    "spain-1808": "1808-05", "erfurt-1808": "1808-09",
    "wagram-1809": "1809-07", "marie-louise-1810": "1810-03",
    "russia-1812": "1812-09", "leipzig-1813": "1813-10",
    "france-1814": "1814-01", "fontainebleau-1814": "1814-04",
    "elba-1814": "1814-05", "waterloo-1815": "1815-06",
    "sthelena-1815": "1815-10",
}

MONTHS = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May",
          6: "June", 7: "July", 8: "August", 9: "September", 10: "October",
          11: "November", 12: "December"}

MONTH_WORDS = {"january", "february", "march", "april", "may", "june",
               "july", "august", "september", "october", "november",
               "december", "janvier", "février", "fevrier", "mars", "avril",
               "mai", "juin", "juillet", "aout", "août", "septembre",
               "octobre", "novembre", "decembre", "décembre"}


def defootnote(t):
    """"Russia 1 Tell" — a bare digit between sentences is a footnote ref,
    not prose. Month-guarded so "June 12 The army" survives."""
    def fix(m):
        if m.group(1).lower() in MONTH_WORDS:
            return m.group(0)
        return m.group(1) + ". " + m.group(2)
    return re.sub(r"([A-Za-zÀ-Þ]{3,})\s+\d{1,3}\s+([A-ZÀ-Þ])", fix, t)


def scene_for(rec, blurb):
    """Event blurb, or a neutral place scene when the event hasn't happened.
    Never a date: the UI already shows the date on every card."""
    eid = (rec.get("eventIds") or [""])[0]
    gate = EVENT_DATES.get(eid)
    if blurb and (not gate or rec["date"][:7] >= gate):
        return blurb
    loc = clean_place(rec.get("location"))
    if not loc:
        return ""  # OCR-mangled filing ("27M", "I'^th"): no scene at all
    return loc + "."


DATE_PAT = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\b|\b1[789]\d\d\b|\b1[78]\s\d\d\b|"
    r"\b\d{1,2}(st|nd|rd|th)\b", re.I)

LEAD_JUNK = [
    re.compile(r"^“", ),
    re.compile(r"^(To\s+[A-Z][^.!?]{5,80}?\.\s*)", ),          # address block
    re.compile(r"^(\"[A-Z][A-Za-z \-']{3,40}?,\s*)", ),          # "Bayonne,
    re.compile(r"^([A-Z][a-z]+\s*,?\s*(th|st|nd|rd)?\s*[A-Za-z]*\s*"
               r"1[78]\d\d\.?\s*\*?\s*)", ),                     # dateline
    re.compile(r"^((O|«)\s*)?CHAPTER[^.!?]*[.!?]\s*", re.I),     # chapter head
    re.compile(r"^((O|«)\s*)?THE YEAR 1[78]\d\d[^.!?]*[.!?]\s*", re.I),
    re.compile(r"^\([^)]*omitted\)\.?\s*", re.I),                # (words omitted)
    re.compile(r"^(My\s+)?(Sir|Madame|Monsieur|Lord|Cousin|Son|Daughter"
               r"|Sister|Brother)[^:—–-]*[:—–-]\s*"),              # vocative
    re.compile(r"^u\s+BONAPARTE\.?\s*", re.I),                  # signature echo
    re.compile(r"^\"?\s*Napoleon\.\"?\s*", ),
    # OCR/editorial crust: stray quotes and stars (never bare digits — "2
    # Artillery" is content, not crust), signature leaks, footnote tags,
    # caps heads. A bare small number is crust only before a non-unit word:
    # "32 I" and "3 The effect" go, "2 Artillery" and "10,000 men" stay.
    re.compile(r"^[\s\"'«»<>*'\.,;:—–\-]+"),
    re.compile(r"^\d{1,3}\s+(?!(?:men|francs|guns|ships|soldiers|crowns"
               r"|troops|artillery|cavalry|horses|waggons|miles|leagues"
               r"|days|months|years|prisoners|o'clock)\b)", re.I),
    re.compile(r"^.\s+\d{1,3}\s+"),  # "I 17 On the…" — stray OCR folio
    re.compile(r"^On\s+the\s+(?:1\s+)?\d{1,2}\w*\s+[A-Za-z]+,?\s*"),
    re.compile(r"^BONAPARTE\.?\s*", ),
    re.compile(r"^\d+\s+Bonaparte\s+(added|writes|observes|says)[^:]*:"
               r"\s*\**\s*"),
    re.compile(r"^Bonaparte\.?\*{0,3}\s*"),
    re.compile(r"^[A-Z][A-Z \-/']{4,40}?\.\s*"),
]

# a signature with text after it means the excerpt ran past the letter's end
# into an editor bridge or the next letter — the clause stops at the signature
# (period form only: "Napoleon said" attributions without one are kept)
MID_SIG = re.compile(
    r"""\s*"?\s*\**\s*BONAPARTE\.?"?\s*(?=\s*\S)""")
MID_SIG_N = re.compile(r"\s*\"Napoleon\.\"\s*(?=\s*\S)")

TRAIL_SIG = re.compile(
    r"\s*(“?\s*\"?\s*NAPOLEON\.?\"?\s*”?|u\s+BONAPARTE\.?\s*|BONAPARTE\.?\s*"
    r"|NAPOLEON LOUIS\.?\s*)$", re.I)


def strip_leads(t):
    for _ in range(6):
        for rx in LEAD_JUNK:
            t = rx.sub("", t, count=1).strip()
        t = _strip_ocr_dateline(t)
        # leading lowercase debris with a stray digit ("de Caulaincourt 1 "
        # before the real sentence): drop it, unless it carries a verb
        m = re.match(r"^([a-zà-þ][^.?!;]{1,60}?\d[^.?!;]{0,10}?)\s+(?=[A-ZÀ-Þ])", t)
        if m and not VERBISH.search(m.group(1)):
            t = t[m.end():].strip()
    return t


DATE_WORDS = ("january|february|march|april|may|june|july|august|september|"
              "october|november|december|vendemiaire|vendémiaire|brumaire|"
              "frimaire|nivose|nivôse|pluviose|pluviôse|ventose|ventôse|"
              "germinal|floreal|floréal|prairial|messidor|thermidor|fructidor")


def _strip_ocr_dateline(t):
    """A mangled dateline like "i^th April ^ 1802. ''" — anything up to the
    first year-number, provided the prefix smells of dates, not prose."""
    m = re.match(r"^(.{1,60}?1[78]\d\d\.?)\s*[\*'\"\s]*", t)
    if m and re.search(DATE_WORDS + r"|\bth\b|\bst\b|\bnd\b|\brd\b|\^|\*",
                       m.group(1), re.I):
        return t[m.end():].strip()
    return t


ABBR = ("marshal", "general", "gen", "st", "m", "no", "art", "mr",
        "dr", "col", "maj", "lt", "etc", "pp", "vol", "ch")

KEEP_FRAG = {"No", "Yes", "Sir", "Madame", "Monsieur", "Well", "Ah", "Oh",
             "My", "Your", "And", "But", "For", "Yet"}


def split_sents(t, glue_min=35):
    guarded = t
    for a in ABBR:
        guarded = re.sub(r"\b(%s)\. " % a, r"\1<prd> ", guarded,
                         flags=re.I)
    parts = re.split(r"(?<=[.!?;:])\s+", guarded)
    out, buf = [], ""
    for p in parts:
        p = p.replace("<prd>", ".").strip()
        if not p:
            continue
        if len(p) < glue_min:
            if re.fullmatch(r"[A-ZÀ-Þ][a-zà-þ]+", p) and p not in KEEP_FRAG:
                continue  # stray name fragment ("Michel"), not a sentence
            if re.search(r"(?<![\d,])\b\d{1,3}\b(?![\d,])", p) \
                    and not VERBISH.search(p):
                continue  # footnote debris ("De Caulaincourt 1"): drop it,
                          # never glue it onto the next sentence
            buf = (buf + " " + p).strip()
            continue
        if buf:
            p, buf = (buf + " " + p).strip(), ""
        out.append(p)
    if buf and (not out or len(buf) > glue_min):
        out.append(buf)
    return out


def score_clause(s):
    sc = 0.0
    if VERBISH.search(s[:120]):
        sc += 3.0
    sc += min(2.0, len(re.findall(r"\d[\d,]*", s)) * 1.0)
    sc += min(2.0, len(re.findall(
        r"[A-ZÀ-Þ][a-zà-þ]+(?:\s+[A-ZÀ-Þ][a-zà-þ]+){0,2}", s)) * 0.5)
    if re.match(r"^(And|But|For|Or|Nor|So|Yet)\b", s):
        sc -= 1.0
    if "?" in s:
        sc -= 2.0
    if DATE_PAT.search(s):
        sc -= 4.0  # the UI shows the date; the tweet must not
    if len(s) > 220:
        sc -= 1.0
    return sc


def clean_end(s):
    s = re.sub(r"[;:,.\s…/\\*\"]+$", "", s).strip()
    return s


def trim_clause(s, limit=170):
    s = re.sub(r"[\r\n\t]+", " ", s)  # stray CRs surface as ^M in JSON
    s = re.sub(r"\.{2,}", "…", s)  # source ellipses first, so cuts never double
    s = TRAIL_SIG.sub("", s.strip()).strip()
    s = re.sub(r"([A-Za-z-]+)\s+-\s*([A-Za-z])", r"\1-\2", s)  # in -chief
    # footnote ref after a word ("Belliard,2 that"); thousands ("40,000")
    # are safe because the comma there follows a digit, not a letter
    s = re.sub(r"(?<=[A-Za-z]),\d+\s+(?=[a-zà-þ])", ", ", s)
    s = re.sub(r"(\w)'-?d\s+'(\w)", r"\1 d'\2", s)  # charge'-d 'affaires
    s = re.sub(r"(\w)'-?d\s+'(\w)", r"\1 d'\2", s)  # charge'-d 'affaires
    s = re.sub(r"\([^)]*\/[^)]*\)$", "", s).strip()  # (400,000/.) debris
    s = s.rstrip(";:,").strip()
    # OCR footnote tail ("...disposal.1 The Sax"): cut from ".digit + Capital"
    s = re.sub(r"\.\d+\s+[A-Z][A-Za-zÀ-Þ ,;'\-()]*$", ".", s).strip()
    if len(s) <= limit:
        return clean_end(s)
    cut = s[:limit]
    for sep in ("; ", ": ", " — ", ", ", " "):
        k = cut.rfind(sep)
        if k > limit * 0.5:
            return cut[:k].rstrip(" ,;:—-/\\*\"") + "…"
    return cut.rstrip() + "…"


def is_editor_voice(s):
    # Bingham narrates between letters ("orders were despatched by Bonaparte",
    # "a note informs us that ... Napoleon threw himself on his bed"):
    # third person about him, never his voice — and never the tweet
    if re.search(r"\b(Bonaparte|Napoleon)\b", s) \
            and not FIRST_PERSON.search(s):
        return True
    if re.search(r"as above|see above|following letter|preceding|see below"
                 r"|above-mentioned", s, re.I):
        return True
    return False


def third_person(s):
    """Narrative clauses must carry his voice, address someone, or open with
    his own command. Bare third-person reportage about himself ("He was
    Emperor…") reads as someone else describing Napoleon under his
    checkmark — reject it and let a better sentence (or hand review) win."""
    if FIRST_PERSON.search(s):
        return False
    if re.search(r"\byou\b|\byour\b", s, re.I):
        return False
    if re.match(r"^(Let|See|Take|Send|Tell|Reply|Be|Write|Make|Give|Order"
                r"|Inform|Show|Keep|Hold|Put|Set|Disarm|Burn|Shoot|March"
                r"|Summon|Explain|Reply)\b", s):
        return False
    if re.match(r"^(He|She|It|They)\b", s):
        return True
    if re.search(r"Emperor himself|His Majesty himself", s):
        return True
    return False


XREF = re.compile(r"as above|see above|noted above|same .* note|following "
                  r"letter|preceding|see below|above-mentioned", re.I)


def clause_from(text):
    t = re.sub(r"\s+", " ", text).strip()
    t = (t.replace("“", '"').replace("”", '"').replace("«", '"')
           .replace("»", '"'))
    t = defootnote(t)
    t = MID_SIG.sub(". ", t)
    t = MID_SIG_N.sub(". ", t)
    t = re.sub(r'"', "", t).replace("[…]", " ").strip()
    t = re.sub(r"\s+", " ", t)
    t = strip_leads(t).strip()
    sents = [strip_leads(s).strip()
             for s in split_sents(t) if len(s) >= 30]
    sents = [s for s in sents
             if len(s) >= 30 and not is_editor_voice(s)
             and not third_person(s)]
    if not sents:
        return None
    best = max(sents, key=score_clause)
    if score_clause(best) < 3.0:
        return None
    c = trim_clause(best)
    c = re.sub(r"^(And|But|For|Yet)\s+", "", c)
    return c[0].upper() + c[1:] if c else None


TITLE_STRIP = ("the", "general", "marshal", "admiral", "cardinal",
               "prince", "princess", "count", "comte", "vice", "m")

# words that are never the surname, for handle picking
NAME_SKIP = {"his", "her", "my", "the", "a", "general", "marshal", "admiral",
             "cardinal", "prince", "princess", "count", "comte", "duke",
             "king", "queen", "emperor", "minister", "secretary", "chief",
             "staff", "grand", "judge", "arch", "chancellor", "foreign",
             "war", "interior", "police", "navy", "finance", "state", "law",
             "tsar", "sultan", "elector", "stepson", "son", "brother",
             "uncle", "cousin", "nephew", "rival", "savant", "palace",
             "archduke", "of", "de", "m"}

HANDLE_SPECIAL = {"pope": "pope", "holyfather": "pope",
                  "hhthepope": "pope",
                  "kleber": "kleber", "lebrun": "lebrun",
                  "peace": "godoy", "princeofthepeace": "godoy",
                  "vvirtemberg": "wurttemberg",
                  "theelectorofvvirtemberg": "wurttemberg",
                  "directory": "directory", "senate": "senate",
                  "russia": "alexander", "emperorofrussia": "alexander",
                  "austria": "austria", "emperorofaustria": "austria",
                  "prussia": "prussia", "kingofprussia": "prussia",
                  "spain": "spain", "england": "england"}


def resolve_role(rec):
    """Roster role for the addressee, or None. Shared by frame and handle so
    an OCR-mangled filing ("CAMBACFIRIS") still yields a clean name."""
    m = re.match(r"^To\s+(.+?)(?:,|$)", rec["sourceTitle"] or "", re.I)
    raw = (m.group(1).strip() if m else "").rstrip(".")
    key = norm(raw)
    cands = [key]
    for t in TITLE_STRIP:
        if key.startswith(t) and len(key) > len(t) + 2:
            cands.append(key[len(t):])
    for c in cands:
        if c in ROSTER:
            role = ROSTER[c]
            return role(raw, rec["date"]) if callable(role) else role
    return None


def handle_for(rec):
    """@mention handle for the addressee, or None when unresolvable."""
    m = re.match(r"^To\s+(.+?)(?:,|$)", rec["sourceTitle"] or "", re.I)
    if not m:
        return None
    raw = m.group(1).strip().rstrip(".")
    key = norm(raw)
    if key in HANDLE_SPECIAL:
        return HANDLE_SPECIAL[key]
    for t in TITLE_STRIP:
        if key.startswith(t) and len(key) > len(t) + 2:
            cand = key[len(t):]
            if cand in HANDLE_SPECIAL:
                return HANDLE_SPECIAL[cand]
    role = resolve_role(rec)
    if role:
        # first real name in the role ("his stepson Eugène, viceroy of
        # Italy" -> eugene, not italy)
        for w in re.findall(r"[A-Za-zÀ-Þà-þ]+", role):
            if len(w) > 2 and w.lower() not in NAME_SKIP \
                    and not re.fullmatch(r"VII?I?|IV|IX|XII?|V", w):
                return unicodedata.normalize(
                    "NFD", w.lower()).encode("ascii", "ignore").decode()
        return None
    if re.search(r"[A-Z]{5,}|\d", raw):
        return None  # OCR-mangled: bare clause rather than a junk handle
    if re.search(r"[A-Z]{5,}|\d", raw):
        return None  # OCR-mangled: bare clause rather than a junk handle
    words = re.findall(r"[A-Za-zÀ-Þ]+", raw)
    titles = {"general", "marshal", "admiral", "cardinal", "prince",
              "princess", "count", "comte", "duke", "king", "queen",
              "emperor", "minister", "secretary", "chief", "staff",
              "grand", "judge", "arch", "chancellor", "foreign", "war",
              "interior", "police", "navy", "the", "of", "de", "m"}
    names = [w.lower() for w in words
             if w.lower() not in titles and len(w) > 2]
    if not names:
        return None
    return names[-1]


FIRST_PERSON = re.compile(
    r"\b(I|We|My|Our|Me|we|my|our|me|myself|ourselves|You|you|Your|your"
    r"|Yours|yours|moi|je|nous|mon|ma|mes|notre|nos|Moi|Je|Nous|Mon|Ma"
    r"|Mes|Notre|Nos|mienne|nôtre)\b")

DANGLING_START = re.compile(
    r"^(He|She|It|They|This|That|These|Those|There|Then|Thus|Such|Which|Who"
    r"|What|Where|When|While|Without|With|For|From|On|At|By|If|Though"
    r"|Although|However|Meanwhile|Instead|Besides|Yet|Nor|Or|Until|Since"
    r"|Because|So|Then|No|Yes|Second|Third|Fourth|Art"
    r"|As\s+(you|I|we|he|she|it|they|my|your|his|her|our|their|this|that)"
    r"|Your\s+(Majesty|Lordship|Highness|Excellency))\b", re.I)

BARE_PRONOUN = re.compile(r"\b(her|him|them)\b", re.I)


def score_voice(s):
    sc = 0.0
    if re.match(r"^(I|We|My|Our|You|Your|Let|Soldiers|Citizens|Frenchmen"
                r"|Officers|Generals|Brave)\b", s):
        sc += 3.0
    if FIRST_PERSON.search(s):
        sc += 2.0
    if VERBISH.search(s[:120]):
        sc += 2.0
    if DATE_PAT.search(s):
        sc -= 4.0  # the UI shows the date; the tweet must not
    if BARE_PRONOUN.search(s) and not re.search(
            r"[A-ZÀ-Þ][a-zà-þ]+(?:\s+[A-ZÀ-Þ][a-zà-þ]+){0,2}", s):
        sc -= 4.0
    if re.search(r"\?", s):
        sc -= 3.0
    sc += min(1.5, len(re.findall(r"\d[\d,]*", s)) * 0.75)
    return sc


def voice_from(pool):
    """Best first-person self-contained sentence, or None. No fragment
    gluing here: a glued "It will be paid easily. You have…" would tweet
    with a dangling antecedent."""
    cands = []
    for s in split_sents(pool, glue_min=0):
        s = strip_leads(s).strip()
        if not (35 <= len(s) <= 220):
            continue
        if not re.match(r'[A-Z0-9À-Þ"]', s):
            continue  # fragment tail ("de Nerciat.", "more than 1,500…")
        if DANGLING_START.match(s):
            continue
        if not FIRST_PERSON.search(s):
            continue
        if not VERBISH.search(s[:140]):
            continue
        cands.append(s)
    if not cands:
        return None
    best = max(cands, key=score_voice)
    if score_voice(best) < 4.0:
        return None
    return trim_clause(best, 200)


def voice_for(rec, body_text=None):
    """@handle + first-person clause from the record's OWN excerpt, else
    None (the app then tweets the narrative instead).

    Deliberately never falls back to the letter body: the tweet must always
    be contained in its verbatim, or readers rightly cry fake. verify.py
    enforces tweet-subset-of-quote on every shipped record."""
    t = re.sub(r"[“”\"]", "", rec["displayText"]).replace("[…]", " ").strip()
    t = re.sub(r"\s+", " ", t)
    t = defootnote(t)
    t = MID_SIG.sub(". ", t)
    t = MID_SIG_N.sub(". ", t)
    v = voice_from(t)
    if v is None:
        return None, ["no-voice"]
    flags = []
    if DATE_PAT.search(v):
        flags.append("voice-date")
        return None, flags
    if len(re.findall(r"\b[A-Z]{3,}\b", v)) >= 3:
        flags.append("voice-junk")  # shouting OCR ("THE AULIC COUNCIL")
        return None, flags
    if re.search(r"(?<![\d,])\b\d{1,3}\s+[a-zà-þ]", v) \
            and "o'clock" not in v.lower():
        flags.append("voice-junk")  # stray OCR digit ("I 29 march")
        return None, flags
    if re.search(r"(?<![\d,])\b\d{1,3}\s+[A-ZÀ-Þ]", v):
        flags.append("voice-junk")  # footnote debris ("English 1 Government")
        return None, flags
    if re.search(r"(?<=[A-Za-z]{4})\.\s+(?=[A-Z][a-z])", v):
        flags.append("voice-junk")  # defootnote scar, not a sentence break
        return None, flags
    if re.search(r"\bthe\s+I\s+\d", v):
        flags.append("voice-junk")  # "repay ourselves the I 40,000"
        return None, flags
    for rx in JUNK:
        if rx.search(v):
            flags.append("voice-junk")
            return None, flags
    if WORDS:
        for w in re.findall(r"(?<![A-Za-zÀ-Þ])[a-zà-þ]{4,}", v):
            if w not in STOP and not known(w):
                flags.append("voice-dict")
                return None, flags
    handle = handle_for(rec)
    if handle and re.search(r"\byou\b|\byour\b", v, re.I):
        v = "@" + handle + " " + v
    return v, flags


def frame_for(rec):
    role = resolve_role(rec)
    if role:
        return "To " + role + ":"
    m = re.match(r"^To\s+(.+?)(?:,|$)", rec["sourceTitle"] or "", re.I)
    raw = (m.group(1).strip() if m else "").rstrip(".")
    # plain name fallback — title-cased, never invented
    name = re.sub(r"\s+", " ", raw).strip()
    if not name or len(name) < 3 or re.search(r"[A-Z]{5,}|\d", name):
        return None  # OCR-mangled addressee: no frame rather than garbage
    return "To " + name.title() + ":"


def narrate(rec, body_text, blurb):
    flags = []
    clause = clause_from(rec["displayText"])
    if clause is None and body_text:
        btext = re.sub(r"\s+", " ", body_text[:3000])
        btext = (btext.replace("“", '"').replace("”", '"')
                 .replace("«", '"').replace("»", '"'))
        btext = MID_SIG.sub(". ", btext)
        btext = MID_SIG_N.sub(". ", btext)
        for s in split_sents(btext):
            if len(s) < 40 or re.search(r"\bCHAPTER\b", s):
                continue
            if is_editor_voice(s):
                continue
            c = trim_clause(strip_leads(s))
            if c and score_clause(c) >= 3.0 and len(c) >= 30 \
                    and not third_person(c):
                clause = c[0].upper() + c[1:]
                flags.append("body-clause")
                break
    if clause is None:
        flags.append("no-clause")
        return None, flags
    frame = frame_for(rec)
    if frame is None:
        flags.append("no-frame")
        return None, flags
    draft = " ".join(p for p in (blurb, frame, clause) if p)
    if not draft.endswith((".", "…", "?", "!")):
        draft += "."
    if len(draft) > 300:
        clause = trim_clause(clause, 170 - (len(draft) - 300))
        draft = " ".join(p for p in (blurb, frame, clause) if p)
        if not draft.endswith((".", "…")):
            draft += "."
    for rx in JUNK:
        if rx.search(draft):
            flags.append("clause-junk")
            break
    if XREF.search(draft):
        flags.append("xref")  # cross-record pointer: hand-write, never ship
    if DATE_PAT.search(draft):
        flags.append("has-date")  # dates live in the UI, never the tweet
    if not (60 <= len(draft) <= 305):
        flags.append("bad-length")
    if WORDS:
        # only words lowercase in the clause itself: names are Capitalized
        # and skipped, so OCR junk ("coatain", "anluse") is what trips this
        for w in re.findall(r"(?<![A-Za-zÀ-Þ])[a-zà-þ]{4,}", clause):
            if w not in STOP and not known(w):
                flags.append("dict-unknown")
                break
    return draft, flags


def main():
    bulk = json.load(open(os.path.join(ROOT, "data", "nap_bulk.json"),
                          encoding="utf-8"))
    recs = list(bulk)
    for extra in ("nap_threads.json", "nap_glean.json"):
        extra_path = os.path.join(ROOT, "data", extra)
        if os.path.exists(extra_path):
            recs += json.load(open(extra_path, encoding="utf-8"))
    bodies = []
    for vn in ("bingham_vol1.json", "bingham_vol2.json", "bingham_vol3.json"):
        bodies += json.load(open(os.path.join(ROOT, "sources", vn),
                                 encoding="utf-8"))
    by_key, by_date = {}, {}
    for b in bodies:
        by_key.setdefault((b["iso"], norm(b["addr"])), []).append(b)
        by_date.setdefault(b["iso"], []).append(b)
    events = {e["id"]: e for e in
              json.load(open(os.path.join(ROOT, "data", "events.json"),
                             encoding="utf-8"))["events"]}
    drafts, matched = {}, 0
    voices = {}
    for rec in recs:
        body = match_body(rec, by_key, by_date)
        if body is not None:
            matched += 1
        eid = (rec.get("eventIds") or [""])[0]
        blurb = events.get(eid, {}).get("blurb") or ""
        draft, flags = narrate(
            rec, body["body"] if body else None, scene_for(rec, blurb))
        voice, vflags = voice_for(rec, body["body"] if body else None)
        # voice gates live inside voice_for (None = fall back to narrative);
        # they never sink the narrative itself
        if voice is not None:
            voices[rec["id"]] = voice
        drafts[rec["id"]] = {
            "draft": draft,
            "date": rec["date"],
            "sourceTitle": rec["sourceTitle"],
            "excerpt": rec["displayText"][:200],
            "flags": flags,
            "auto_ok": draft is not None and set(flags) <= {"body-clause"},
        }
    out = os.path.join(ROOT, "sources", "context_drafts.json")
    thread_path = os.path.join(ROOT, "data", "nap_threads.json")
    thread_ids = set()
    if os.path.exists(thread_path):
        thread_ids = {r["id"] for r in
                      json.load(open(thread_path, encoding="utf-8"))}
    by_date = {}
    for i, d in drafts.items():
        if i in thread_ids:
            continue
        by_date.setdefault(d["date"], []).append(d["draft"] or "")
        if i in voices:
            by_date[d["date"]].append(voices[i])
    for i, v in list(voices.items()):
        if i in thread_ids and any(
                contains(v, t) for t in by_date.get(drafts[i]["date"], [])):
            del voices[i]  # twin would retweet its parent: narrative instead
    json.dump({k: v for k, v in drafts.items()},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for v in drafts.values() if v["auto_ok"])
    print(f"records: {len(recs)} (bulk {len(bulk)}), body-matched: {matched}, "
          f"auto_ok: {ok}, flagged: {len(recs) - ok}, voices: {len(voices)}")
    print("flags:", dict(Counter(f for v in drafts.values()
                                 for f in v["flags"])))
    print(f"wrote {out}")
    vout = os.path.join(ROOT, "sources", "voice_drafts.json")
    json.dump(voices, open(vout, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote {vout} ({len(voices)} voice tweets)")


if __name__ == "__main__":
    main()
