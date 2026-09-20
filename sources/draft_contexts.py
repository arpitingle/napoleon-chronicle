#!/usr/bin/env python3
"""Draft editorial summaries for the 641 boilerplate contexts in nap_bulk.json.

Bulk records carry only `Letter to X from Y. Full text in the Bingham
selection` as context, so the feed headline falls back to bare metadata
("To X, Paris, date") with no message. This script drafts a terse headlinese
summary per record — house style like the hand-written ones ("Ultimatum
season.", "Champaubert won.") — using ONLY words/entities extracted from the
letter itself (no paraphrase, no invention):

  VERB head + top content terms, e.g. "Dispatch: Cleves, Prussia, hostilities."

Output: sources/context_drafts.json {id: {draft, date, sourceTitle, excerpt,
flags, auto_ok}}. Nothing is published by this script: an apply step (with
human review of flagged drafts) writes sources/context_overrides.json, which
build_index.py applies at manifest build time.

Run from anywhere:  python3 sources/draft_contexts.py
"""
import json, os, re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STOP = set("""
a an the and or but of to in on for with from by at as is are was were be been
being it its this that these those he him his she her they them their we our
you your i my me mine our ours him himself herself itself themselves himself
not no yes so than then too very can will shall may might must would could
should have has had having do does did doing done will would there here where
when while which who whom whose what how all any both each few more most
other some such only own same over under again once between into through
upon about after before during without within along across per via
le la les de des du un une et est sont dans pour avec par sur au aux ce ces
cette son sa ses leur leurs il ils elle elles nous vous je tu on ne pas plus
tout toute tous toutes comme aussi mais ou donc car ni que qui quoi dont
mon ma mes ton ta tes son sa ses notre votre votre leurs leur y en
his majesty her majesty excellency monsieur citizen general minister emperor
king prince duke marshal count baron lord sir madam lady dear sir yours
faithfully obedient humble servant letter received yours dated instant ultimo
myself himself herself itself ourselves yourselves themselves whether
""".split())

VERB_WORDS = {"order", "orders", "send", "sent", "dispatch", "report", "news",
              "demand", "demands", "refusal", "denial", "funds", "march",
              "warning", "request", "announcement", "instructions", "forwarded",
              "approval", "proposal", "appointment", "attack", "victory",
              "retreat", "surrender", "complaint", "arrest", "assurance",
              "promise", "authorization", "ban", "grant", "resolve", "received",
              "arrival", "arrive", "arrives", "arrived", "seizure", "occupation",
              "crossing", "entry", "recall", "dismissal", "outlook", "hopes",
              "wishes", "urging", "threat", "punishment", "reward", "transfer",
              "embarkation", "siege", "destruction", "abdication", "marriage",
              "coronation", "reply", "brief", "wrote", "written"}

IMPERATIVE_NOISE = {"write", "writes", "let", "have", "make", "take", "give",
                    "send", "tell", "see", "hear", "read", "think", "know",
                    "find", "leave", "hold", "keep", "put", "set", "order",
                    "explain", "state", "observe", "contain", "insert",
                    "remark"}


def load_words():
    for p in ("/usr/share/dict/words", "/usr/dict/words"):
        try:
            return set(w.strip().lower() for w in open(p, encoding="utf-8",
                                                       errors="replace"))
        except OSError:
            continue
    return set()

IRREG = {"paid": "pay", "became": "become", "heard": "hear",
           "held": "hold", "laid": "lay", "said": "say", "done": "do",
           "gone": "go", "known": "know", "grown": "grow", "shown": "show",
           "undertaken": "undertake", "taken": "take", "given": "give",
           "written": "write", "chosen": "choose", "forgotten": "forget",
           "withdrew": "withdraw", "undergone": "undergo"}

PERIOD_WORDS = {"roubles", "sangfroid", "emigres", "emigre", "hors",
                "despatch", "despatches", "despatched", "despatching",
                "inclosed", "inclose", "inclosure", "medin", "medins",
                "revictual", "revictuals", "revictualled", "revictualling",
                "fulfil", "fulfils", "fulfilled", "fulfilling"}


def spell_variants(w):
    out = {w}
    for pre in ("under", "over", "fore", "out", "up", "mis"):
        if w.startswith(pre) and len(w) > len(pre) + 3:
            out.add(w[len(pre):])  # foreseen -> seen, overtook -> took
    if "our" in w:  # British spelling in a London 1884 translation
        out.add(w.replace("our", "or"))
    out.add(w.replace("oe", "e"))  # manoeuvre -> maneuver
    out.add(w.replace("oeu", "eu"))
    out.add(w.replace("gg", "g"))  # waggon -> wagon
    out.add(w.replace("desp", "disp"))  # despatch -> dispatch
    if w.endswith("nce"):  # licence -> license
        out.add(w[:-3] + "nse")
    if w.endswith("ise"):  # authorise -> authorize
        out.add(w[:-3] + "ize")
    # chain once more so combined cases resolve (manoeuvre -> maneuver)
    chained = set(out)
    for v in list(out):
        if v.endswith("re"):
            chained.add(v[:-2] + "er")
        chained.add(v.replace("oe", "e"))
    out |= chained
    return out


def stem_forms(w):
    forms = {w}
    if w.endswith("ies"):
        forms.add(w[:-3] + "y")
    if w.endswith("ied"):
        forms.add(w[:-3] + "y")
    if w.endswith("es"):
        forms.add(w[:-2])
    if w.endswith("s"):
        forms.add(w[:-1])
    if w.endswith("ed"):
        forms.update((w[:-2], w[:-1]))
    if w.endswith("ing"):
        forms.update((w[:-3], w[:-3] + "e"))
    if w.endswith("re"):
        forms.add(w[:-2] + "er")  # theatre -> theater
    if w.endswith("est") and len(w) > 5:
        forms.add(w[:-3])  # greatest -> great
        forms.add(w[:-3] + "e")  # bravest -> brave
    if w.endswith("men") and len(w) > 4:
        forms.add(w[:-3] + "man")  # gentlemen -> gentleman
    m = re.match(r"^(.*)(.)\2(ing|ed)$", w)
    if m:  # quitting -> quit, stopped -> stop
        forms.add(m.group(1) + m.group(2))
    return forms


def known(w):
    if (w in WORDS or w in STOP or w in VERB_WORDS or w in SELF
            or w in PERIOD_WORDS or IRREG.get(w, w) in WORDS):
        return True
    for form in stem_forms(w):
        for v in spell_variants(form):
            if v in WORDS:
                return True
    return False


WORDS = load_words()

# flags that still allow auto-approval: terms-only or body-backed drafts whose
# words are all dictionary-clean are safe headlinese, just headless
SOFT_FLAGS = {"no-verb", "body-term"}

VERB = [
    (r"\border(?:s|ed|ing)?\b", "Orders"),
    (r"\bsen[dt]\b|\bdispatche?[sd]?\b", "Dispatch"),
    (r"\breport(?:s|ed|ing)?\b|\binform(?:s|ed)?\b|\bapprise[sd]?\b", "News"),
    (r"\bdemand(?:s|ed)?\b|\binsist(?:s|ed)?\b", "Demands"),
    (r"\brefus(?:e[sd]?|al)\b|\bdeclin(?:e[sd]?)\b", "Refusal"),
    (r"\bden(?:y|ies|ied)\b", "Denial"),
    (r"\bpa(?:y|id|yment)\b|\bfund(?:s|ed)?\b|\bfrancs?\b", "Funds"),
    (r"\bmarch(?:e[sd]?|ing)?\b|\badvance[sd]?\b", "March"),
    (r"\bwarn(?:s|ed|ing)?\b|\bcaution(?:s|ed)?\b", "Warning"),
    (r"\brequest(?:s|ed)?\b|\bbeg(?:s|ged)?\b|\bpray(?:s|ed)?\b", "Request"),
    (r"\bannounce[sd]?\b|\bproclaim(?:s|ed)?\b|\bdeclare[sd]?\b", "Announcement"),
    (r"\binstruct(?:s|ed|ions?)?\b|\bdirect(?:s|ed|ions?)?\b", "Instructions"),
    (r"\bforward(?:s|ed|ing)?\b|\btransmit(?:s|ted)?\b|\benclos(?:e[sd]?|ure)\b", "Forwarded"),
    (r"\bapprov(?:e[sd]?|al)\b|\bsanction(?:s|ed)?\b", "Approval"),
    (r"\bpropos(?:e[sd]?|al)\b|\bsuggest(?:s|ed)?\b", "Proposal"),
    (r"\bappoint(?:s|ed|ment)?\b|\bnominat(?:e[sd]?|ion)\b", "Appointment"),
    (r"\battack(?:s|ed|ing)?\b|\bassault(?:s|ed)?\b|\bstorm(?:s|ed)?\b", "Attack"),
    (r"\bdefeat(?:s|ed)?\b|\bbeat(?:en)?\b|\brout(?:s|ed)?\b", "Victory"),
    (r"\bretreat(?:s|ed|ing)?\b|\bwithdraw(?:s|n|ing)?\b", "Retreat"),
    (r"\bsurrender(?:s|ed)?\b|\bcapitulat(?:e[sd]?|ion)\b", "Surrender"),
    (r"\bcomplain(?:s|ed|t)?\b", "Complaint"),
    (r"\bcongratulate[sd]?\b", "Congratulations"),
    (r"\barrest(?:s|ed)?\b", "Arrest"),
    (r"\bassur(?:e[sd]?|ance)\b", "Assurance"),
    (r"\bpromis(?:e[sd]?)?\b", "Promise"),
    (r"\bauthoris(?:e[sd]?|ation)\b", "Authorization"),
    (r"\bforbid\b|\bforbade\b|\bforbidden\b", "Ban"),
    (r"\bgrant(?:s|ed)?\b", "Grant"),
    (r"\bresolv(?:e[sd]?)\b", "Resolve"),
    (r"\blearn(?:s|ed|t)?\b|\bhear[sd]?\b", "News"),
    (r"\breceiv(?:e[sd]?)\b", "Received"),
    (r"\barriv(?:e[sd]?|al)\b", "Arrival"),
    (r"\bseiz(?:e[sd]?|ure)\b|\bsequest(?:er|ration)\b", "Seizure"),
    (r"\boccup(?:y|ies|ied|ation)\b", "Occupation"),
    (r"\bcross(?:e[sd]?|ing)?\b", "Crossing"),
    (r"\benter(?:s|ed|ing)?\b", "Entry"),
    (r"\brecall(?:s|ed)?\b", "Recall"),
    (r"\bdismiss(?:s|ed|al)?\b", "Dismissal"),
    (r"\bexpect(?:s|ed)?\b", "Outlook"),
    (r"\bhop(?:e[sd]?)\b", "Hopes"),
    (r"\bwish(?:e[sd]?)\b", "Wishes"),
    (r"\bfear(?:s|ed)?\b", "Fears"),
    (r"\bneed(?:s|ed)?\b", "Needs"),
    (r"\bwrot(?:e|ten)\b|\bwritten\b", "News"),
    (r"\bexamine[sd]?\b", "Review"),
    (r"\bpronounc(?:e[sd]?)\b", "Address"),
    (r"\brepl(?:y|ies|ied)\b|\banswer(?:s|ed)?\b", "Reply"),
    (r"\bspeak(?:s|ing)?\b|\btalk(?:s|ed|ing)?\b|\bmention(?:s|ed)?\b", "Brief"),
    (r"\bcontinu(?:e[sd]?|ation)\b|\bremain(?:s|ed|ing)?\b", "Outlook"),
    (r"\blong(?:s|ed|ing)?\b|\bwish(?:e[sd]?)?\b", "Wishes"),
    (r"\burg(?:e[sd]?)\b|\brecommend(?:s|ed|ation)?\b", "Urging"),
    (r"\bthreaten(?:s|ed|ing)?\b", "Threat"),
    (r"\bpunish(?:e[sd]?|ment)?\b", "Punishment"),
    (r"\breward(?:s|ed)?\b|\bpromot(?:e[sd]?|ion)\b", "Reward"),
    (r"\btransfer(?:s|red)?\b|\bdetach(?:e[sd]?|ment)?\b", "Transfer"),
    (r"\bembark(?:s|ed|ation)?\b|\bsail(?:s|ed|ing)?\b|\blan[dd](?:s|ed|ing)?\b", "Embarkation"),
    (r"\bbesieg(?:e[sd]?)\b|\binvest(?:s|ed|ing)?\b|\bblockad(?:e[sd]?)\b", "Siege"),
    (r"\bburn(?:s|ed|ing|t)?\b|\bdestroy(?:s|ed)?\b|\bruin(?:s|ed)?\b", "Destruction"),
    (r"\babdicate[sd]?\b|\bresign(?:s|ed|ation)?\b", "Abdication"),
    (r"\bmarry|marriage\b|\bdivorce[sd]?\b", "Marriage"),
    (r"\bcrown(?:s|ed|ing)?\b", "Coronation"),
]

SELF = {"napoleon", "bonaparte", "buonaparte"}

COMMON_CAPS = {"instead", "another", "however", "therefore", "meanwhile",
               "indeed", "elsewhere", "hitherto", "hence", "thus", "accordingly",
               "moreover", "furthermore", "nevertheless", "otherwise", "besides",
               "general", "citizen", "minister", "emperor", "king", "prince",
               "duke", "marshal", "count", "sir"}

JUNK = [
    re.compile(r"\b[A-Z]{9,}\b"),                       # leaked running head
    re.compile(r"[A-Za-z]+\d+[A-Za-z]+"),               # OCR digit in word
    re.compile(r"\b[A-Z]{2,}[a-z]{2,}"),                # OCR caps salad
    re.compile(r"\b1[78]\s\d\d\b"),                     # spaced year
    re.compile(r"[a-z][A-Z][a-z]"),                     # mid-word case break
    re.compile(r"\S  \S"),                              # doubled space
]


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def contains(a, b, floor=30):
    """True when a and b share a substantive passage (full strings, not
    truncated windows — a 60-char window misses short shared sentences)."""
    na, nb = norm(a), norm(b)
    if len(na) < floor or len(nb) < floor:
        return False
    return na in nb or nb in na


def match_body(rec, bodies_by_key, bodies_by_date):
    key = (rec["date"], norm(re.sub(r"^To\s+", "", rec["sourceTitle"].split(",")[0])))
    cands = bodies_by_key.get(key, [])
    probe = norm(rec["displayText"])[:40]
    for b in cands:
        if probe and probe in norm(b["body"]):
            return b
    if probe:
        # OCR-mangled addressee (e.g. Fouchjfe/FOUCHE): match by excerpt text
        for b in bodies_by_date.get(rec["date"], []):
            if probe in norm(b["body"]):
                return b
    return cands[0] if cands else None


def draft_for(rec, body):
    text = re.sub(r"[“”\"]", "", rec["displayText"]).replace("[…]", " ").strip()
    text = re.sub(r"\s+", " ", text)
    verb = None
    best_pos = None
    for pat, noun in VERB:
        m = re.search(pat, text, re.I)
        if m and (best_pos is None or m.start() < best_pos):
            verb, best_pos = noun, m.start()
    # entities
    scored = []
    VERB_STEMS = {"inform", "informs", "informed", "instruct", "direct",
                  "command", "order", "demand", "request", "warn", "assure",
                  "advise", "urge", "declare", "announce", "pronounce",
                  "deliver", "inclose", "enclose", "forward", "transmit"}

    for m in re.findall(
            r"\b([A-ZÀ-Þ][a-zà-þ]+(?:\s+[A-ZÀ-Þ][a-zà-þ]+){0,2})\b", text):
        m = re.sub(r"^(The|A|An)\s+", "", m)  # "The Malet" -> "Malet"
        if not m:
            continue
        m = re.sub(r"^(Inform|Order|Send|Instruct|Direct|Demand|Report|Warn|"
                   r"Assure|Advise|Urge|Declare|Announce|Inclose|Enclose|"
                   r"Forward|Transmit|Write|Let|Take|Give|Grant)\s+",
                   "", m)  # "Inform General Miollis" -> "General Miollis"
        if not m:
            continue
        ml = m.lower()
        words = ml.split()
        if all(w in STOP or w in COMMON_CAPS or w in SELF for w in words):
            continue
        if len(words) == 1 and (ml in IMPERATIVE_NOISE or ml in VERB_WORDS
                                or ml in VERB_STEMS):
            continue  # sentence-opening verbs ("Write to Massena…") add no topic
        if verb and ml == verb.lower():
            continue
        if len(m) < 4 or re.search(r"[A-Z]{4,}", m):
            continue
        if m in ("I",):
            continue
        scored.append((m, 3))
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*([a-zà-þ]+)?", text):
        unit = (m.group(2) or "").lower()
        if unit in ("pm", "am") or unit in STOP or (unit and len(unit) < 3):
            unit = ""
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        digits = re.sub(r"\D", "", m.group(1))
        is_year = re.fullmatch(r"1[6789]\d\d", digits or "") is not None
        if val < 1000 and not is_year and "," not in m.group(1):
            continue  # stray OCR digit ("25 repent", "7 himself")
        scored.append((f"{m.group(1)} {unit}".strip(), 4))
    words = re.findall(r"[a-zà-þ]{4,}", text.lower())
    freq = Counter(w for w in words
                   if w not in STOP and w not in VERB_STEMS
                   and w not in VERB_WORDS)
    for w, c in freq.items():
        if c >= 2:
            if w.endswith("ing"):
                scored.append((w, 0.5))  # verb forms ("coming") are weak topics
            else:
                scored.append((w, 1 + min(2, c)))
    if len([1 for _, s in scored if s >= 2]) < 4:
        # thin excerpt: allow single-occurrence long nouns as a last resort
        for w, c in freq.items():
            if c == 1 and len(w) >= 6 and (w, 1) not in scored:
                scored.append((w, 0.5))
    seen, ranked = set(), []
    for term, sc in sorted(scored, key=lambda t: -t[1]):
        k = term.lower()
        if k in seen or k in STOP:
            continue
        seen.add(k)
        ranked.append(term)
        if len(ranked) >= 6:
            break
    flags = []
    if body is None:
        flags.append("no-body-match")
    if verb:
        lead = verb + ": "
    else:
        lead = ""
        flags.append("no-verb")
    picks = []
    budget = 110 - len(lead) - 1
    for t in ranked:
        t = t.strip().rstrip(".,;:")
        if not t or len(t) < 3:
            continue
        if " " not in t and any(re.search(r"\b%s\b" % re.escape(t), p, re.I)
                                for p in picks if " " in p or re.search(r"\d", p)):
            continue  # "crowns" adds nothing after "1,000 crowns"
        add = (", " if picks else "") + t
        if len("".join(picks) + add) + 2 > budget and picks:
            break
        picks.append(t)
        if len(picks) >= 3:
            break
    if len(picks) < 2 and body:
        # back up to the full letter body for one more topic term
        btext = re.sub(r"\s+", " ", body["body"][:2000])
        for m in re.findall(
                r"\b([A-ZÀ-Þ][a-zà-þ]+(?:\s+[A-ZÀ-Þ][a-zà-þ]+){0,2})\b", btext):
            ml = m.lower()
            if ml in STOP or ml in SELF or len(m) < 5 or m in picks:
                continue
            if any(ml == p.lower() for p in picks):
                continue
            picks.append(m)
            flags.append("body-term")
            break
    if len(picks) < 2:
        flags.append("thin-terms")
    draft = (lead + ", ".join(picks)).strip().rstrip(".,;:") + "."
    draft = draft[0].upper() + draft[1:]
    if re.search(r"\bCHAPTER\b", rec["displayText"]):
        flags.append("chapter-head")  # excerpt is a book heading, not letter text
    for rx in JUNK:
        if rx.search(draft):
            flags.append("junk-pattern")
            break
    if not (15 <= len(draft) <= 112):
        flags.append("bad-length")
    if norm(draft) and norm(rec["sourceTitle"]).find(norm(draft)[:30]) > -1:
        flags.append("restates-title")
    if WORDS:
        lowers = [p for p in picks if re.fullmatch(r"[a-zà-þ]+", p)]
        for w in lowers:
            if not known(w):
                flags.append("dict-unknown")
                break  # OCR junk ("coatain") must never reach the feed
    return draft, flags


def main():
    bulk = json.load(open(os.path.join(ROOT, "data", "nap_bulk.json"),
                          encoding="utf-8"))
    bodies = []
    for vn in ("bingham_vol1.json", "bingham_vol2.json", "bingham_vol3.json"):
        bodies += json.load(open(os.path.join(ROOT, "sources", vn),
                                 encoding="utf-8"))
    by_key = {}
    by_date = {}
    for b in bodies:
        by_key.setdefault((b["iso"], norm(b["addr"])), []).append(b)
        by_date.setdefault(b["iso"], []).append(b)
    drafts, matched = {}, 0
    for rec in bulk:
        body = match_body(rec, by_key, by_date)
        if body is not None:
            matched += 1
        draft, flags = draft_for(rec, body)
        drafts[rec["id"]] = {
            "draft": draft,
            "date": rec["date"],
            "sourceTitle": rec["sourceTitle"],
            "excerpt": rec["displayText"][:200],
            "flags": flags,
            "auto_ok": set(flags) <= SOFT_FLAGS,
        }
    out = os.path.join(ROOT, "sources", "context_drafts.json")
    json.dump(drafts, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    ok = sum(1 for d in drafts.values() if d["auto_ok"])
    print(f"bulk records: {len(bulk)}, body-matched: {matched}, "
          f"auto_ok: {ok}, flagged: {len(bulk) - ok}")
    flagc = Counter(f for d in drafts.values() for f in d["flags"])
    print("flags:", dict(flagc))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
