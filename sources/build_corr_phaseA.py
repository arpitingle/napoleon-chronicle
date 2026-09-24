#!/usr/bin/env python3
"""Corr intake, phase A: select new Napoleon letters from the parsed
Correspondance (French OCR), repair OCR years, dedupe against the published
archive, and cut French excerpts. No translation here (phase B).

Writes (untracked work files):
  sources/corr_intake.json  — candidate new records with FR excerpts
  sources/corr_enrich.json  — {published id: FR excerpt} for records that
                              lack a French originalText

Selection rules (strict by design; dup posts were a past pain):
  - year repair, single-digit OCR fixes only, always dateCertainty
    "approximate": 1706->1796, 1707->1797, 1708->1798, 1709->1799;
    vol2/vol3 1790-12->1796-12 else 1790/1791->1797; vol5 1790->1799;
    1903->1803. Anything else outside 1789-1821 is dropped.
  - enrichment (attach FR original): exact date + surname overlap, and only
    where the published record has no originalText.
  - intake skip: same, plus +-1 day (avoids cross-edition dup posts).
  - within-intake dupes: same date + same addressee surname -> keep first.
  - excerpt floor 80 chars; empty addressee -> skip (no reliable title).
"""
import glob
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import best_excerpt, clean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = {'citoyen', 'citoyenne', 'general', 'marechal', 'marshal', 'prince',
        'king', 'queen', 'emperor', 'empereur', 'ministre', 'minister',
        'monsieur', 'madame', 'comte', 'count', 'duc', 'duke', 'the', 'des',
        'les', 'aux', 'paris', 'france', 'armee', 'army', 'mon', 'ma', 'son',
        'sa', 'notre', 'votre', 'milan', 'nice', 'citizen', 'talleyrand'}

# address must open like one (else the parser swept body text into addr)
ADDR_OK = re.compile(
    r'^(au[x]?|à|a|ordre|arr[eê]t[ée]?|d[eé]cision|d[eé]cret'
    r'|m\.|monsieur|madame|citoyen|citoyenne|g[eé]n[eé]ral|pour|instruction'
    r'|note|message|proclamation|discours|allocution|lettre|memes|au)',
    re.I)
# editor page furniture that best_excerpt must never quote
PAGE_PATTS = [
    r'\b\d{2,4}\s*[—–-]\s*AN?\s+[IVXL]+(?:\s*\(\d{4}\))?',
    r'[—–-]\s*A[NMX]\s+[IVXL]+\s*\(\d{3,4}\)\.?\s*\d*',
    r'\bCORRESPONDANCE DE [A-ZÀ-Þ ]+',
    r'\bCollection [A-Za-zéèê]+',
    r'\bTome [IVXL\d]+\b\.?',
    r'\b\d{1,3}\s+l?[ÉE]ON\s+I{1,3}\b[^\n.]{0,60}',
    r'\bNAPOL[ÉE]ON\s+I{1,3}\b[^\n.]{0,60}',
]
DAYNOISE = re.compile(r'^-?[0-9iIzZTSstQq]{1,2}[Mm]?(?:th|TH|\)th)?$')
EXONYMS = {'caire': 'Cairo', 'londres': 'London', 'vienne': 'Vienna',
           'moscou': 'Moscow', 'varsovie': 'Warsaw',
           'alexandrie': 'Alexandria', 'damiette': 'Damietta',
           'genes': 'Genoa', 'genova': 'Genoa', 'venise': 'Venice',
           'turin': 'Turin', 'naples': 'Naples', 'rome': 'Rome',
           'lisbonne': 'Lisbon', 'copenhague': 'Copenhagen',
           'madrid': 'Madrid', 'berlin': 'Berlin', 'milan': 'Milan',
           'tortone': 'Tortona', 'tortoue': 'Tortona', 'brescia': 'Brescia',
           'plaisance': 'Piacenza', 'mantoue': 'Mantua', 'verone': 'Verona',
           'gorizia': 'Gorizia', 'goritz': 'Gorizia', 'trieste': 'Trieste',
           'ancone': 'Ancona', 'jerusalem': 'Jerusalem',
           'suez': 'Suez', 'jaffa': 'Jaffa'}


def build_place_gazetteer(shards):
    """Established shard locations double as the spelling authority for
    OCR-mangled corr datelines (Tortoue->Tortona)."""
    import difflib  # noqa: F401 (used by callers via returned data)
    from collections import Counter
    c = Counter((r.get('location') or '').strip()
                for r in shards.values())
    gaz = sorted({loc for loc, n in c.items()
                  if n >= 3 and len(loc) >= 3
                  and not re.search(r'\d', loc)
                  and re.fullmatch(r"[A-Za-zÀ-ÿ' \-\.]+", loc)})
    gaz += ['Gorizia', 'Roverbella', 'Pavia', 'Lodi', 'Arcole', 'Rivoli',
            'Bassano', 'Trent', 'Castiglione', 'Marengo', 'Brescia',
            'Tortona', 'Piacenza', 'Parma', 'Modena', 'Bologna', 'Ferrara',
            'Livorno', 'Trieste', 'Ancona', 'Jerusalem', 'Suez', 'Jaffa']
    return gaz


def norm_place(raw, gazetteer):
    import difflib
    t = clean_place_corr(raw)
    if not t:
        return ''
    low = fold(t).lower().strip()
    low = re.sub(r"^(le|la|les|l|de|du|des|d|au|aux|en)\s+", "", low).strip()
    if low in EXONYMS:
        return EXONYMS[low]
    if t in gazetteer:
        return t
    hit = difflib.get_close_matches(t, gazetteer, n=1, cutoff=0.82)
    return hit[0] if hit else ''


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode(
        'ascii', 'ignore').decode()


def clean_addr(raw):
    """Keep the addressee segment; drop dateline tails and body bleed.
    Abbreviated addresses (A. S. A. R. ...) survive period-splitting by
    extending short first segments."""
    t = re.sub(r'\s+', ' ', (raw or '').strip())
    segs = re.split(r'\.\s*', t)
    out = segs[0].strip()
    i = 1
    # extend past abbreviations, initials and cut-off fragments — but
    # never into the dateline (months, Quartier, leading digits)
    DATELINE_BIT = re.compile(
        r'(?i)(janvier|février|fevrier|mars|avril|mai|juin|juillet|aout|août|'
        r'septembre|octobre|novembre|decembre|décembre|vendemiaire|'
        r'vendémiaire|brumaire|frimaire|nivose|nivôse|pluviose|pluviôse|'
        r'ventose|ventôse|germinal|floreal|floréal|prairial|messidor|'
        r'thermidor|fructidor|quartier|^\s*\d)')
    while i < len(segs) and (
            len(out) < 15
            or re.search(r'\b[A-ZÀ-Þ]\.?$', out)
            or re.search(r'\b[A-Za-zÀ-ÿ]{1,2}$', out)) \
            and not DATELINE_BIT.search(segs[i]):
        out = (out + '. ' + segs[i]).strip()
        i += 1
    out = re.sub(r'\s+[A-ZÀ-Þ]\.?$', '', out).strip()
    out = re.sub(r'\d+$', '', out).strip().strip(' ,;:-')
    if not out or not ADDR_OK.match(fold(out)):
        return None
    return out


def clean_body_corr(body):
    t = clean(body or '', 10000)
    for pat in PAGE_PATTS:
        t = re.sub(pat, ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def good_excerpt(ex):
    # French excerpts legitimately open lowercase (l'on, il, je): only
    # length and leading debris disqualify.
    if not ex or len(ex) < 80:
        return False
    if re.search(r'^\W*\d', ex):
        return False
    if re.search(r'CORRESPONDANCE|CORRESPOXDAXCE|l[ÉE]ON\s+I\b|'
                 r'NAPOL[ÉE]ON\s+I\b|\bA[NMX]\s+[IVXL]+\s*\(\d|'
                 r'Dépôt de la guerre|Depot de la guerre', ex):
        return False
    if re.search(r'[\[\(]\s*$', ex.rstrip(' ….…')):
        return False
    return True


FR_MONTHS = ('janvier|fevrier|février|mars|avril|mai|juin|juillet|aout|août|'
             'septembre|octobre|novembre|decembre|décembre|vendemiaire|'
             'vendémiaire|brumaire|frimaire|nivose|nivôse|pluviose|pluviôse|'
             'ventose|ventôse|germinal|floreal|floréal|prairial|messidor|'
             'thermidor|fructidor')
FR_ELIDE = re.compile(r"\b[lLdDsScCjJmMtTyYnNquQU ’'](?=[A-Za-zÀ-Þ])")


def score_sent_fr(s):
    """best_excerpt's scorer tuned for French: elisions (l', d', s')
    and regimental markers (1er, 5e, 22\") are ordinary French, not OCR
    junk. Mirrors common.score_sent otherwise; shared code untouched."""
    sc = 0.0
    n = len(s)
    if 60 <= n <= 220:
        sc += 2.0
    elif n > 320:
        sc -= 1.5
    sc += min(3.0, len(re.findall(r"\d[\d,\.]*", s)) * 1.0)
    if re.search(r"\b(je|j'|nous|moi|mon\b|ma\b|mes\b|notre\b|nos\b|vous\b)",
                 s, re.I):
        sc += 0.5
    if re.match(r'^["“”\s]*([A-Z][\w\-\. ]{1,40}?,\s*)?\d{1,2}\s+('
                + FR_MONTHS + r')\b', s):
        sc -= 10.0
    if re.match(r'^["“”\s]*(BONAPARTE\.?|NAPOLEON\.?|ORDRE\.?|ARRETE\.?|'
                r'DECISION\.?|DECRET\.?|PROCLAMATION[^a-z]*|'
                r'CHAPITRE[^a-z]*)["“”\s]*$', s):
        sc -= 10.0
    # editor running heads and footnote markers are never letter text
    if re.search(r'CORRESPONDANCE|CORRESPOXDAXCE|l[ÉE]ON\s+I\b|'
                 r'NAPOL[ÉE]ON\s+I\b|\bAN\s+[IVXL]+\s*\(\d', s):
        sc -= 10.0
    if re.match(r'^\W*\d+\s+\S', s):
        sc -= 6.0
    # OCR case-breaks inside words (rKguillette, jVapoléon)
    sc -= min(3.0, len(re.findall(r'[a-zà-ÿ][A-ZÀ-Þ][a-zà-ÿ]', s)) * 1.5)
    # digit-letter mixes, but NOT French ordinals (1er/1re/2e/22e) or
    # unit marks (1"/5*), and NOT elided single letters (l'/d'/s')
    t = re.sub(r"\b\d+(?:er|re|e|°)\b", "N", s)
    t = re.sub(r"\b\d+[\"'*°]", "N", t)
    sc -= min(4.0, len(re.findall(r"[A-Za-z]+\d+[A-Za-z0-9]*|\d+[A-Za-z]{2,}",
                                  t)) * 2.0)
    sc -= min(2.0, t.count("\\") * 2.0 + t.count("^") * 2.0)
    t2 = FR_ELIDE.sub("", t)
    sc -= min(2.0, len(re.findall(r"\b[A-Za-z]\b", t2)) * 0.4)
    return sc


def best_excerpt_fr(body, limit=300, floor=1.0, excerpt_floor=60):
    """best_excerpt for French bodies. Returns None below standard."""
    from common import sentences
    sents = sentences(body)
    if not sents:
        return None
    ranked = sorted(range(len(sents)), key=lambda i: -score_sent_fr(sents[i]))
    if score_sent_fr(sents[ranked[0]]) < floor:
        return None
    first = ranked[0]
    picks = [first]
    for j in (first + 1, first - 1):
        if 0 <= j < len(sents) and j not in picks:
            cur = " ".join(sents[k] for k in sorted(picks + [j]))
            if len(cur) <= limit and score_sent_fr(sents[j]) > 0:
                picks.append(j)
            break
    picks.sort()
    txt = " ".join(sents[k] for k in picks)
    txt = re.sub(r'^["“”\s]*" Napoleon\."\s*to [^.]+\.\s*', "", txt)
    txt = re.sub(r'^["“”\s]*BONAPARTE\.?\s*', "", txt)
    txt = re.sub(r'^.{0,100}?\b\d{1,2}\s+(' + FR_MONTHS +
                 r')\b.{0,45}?(1[78][\s\dOolI]{2,5}|an\s+[IVXL]+)\.?\s*', "",
                 txt)
    txt = re.sub(r'^(CHAPITRE|ARRETE|ORDRE|DECISION|DECRET|PROCLAMATION)'
                 r'[^.]{0,60}?\.\s*', "", txt)
    txt = txt.strip()
    if len(txt) > limit:
        cut = txt[:limit]
        for p in (". ", "! ", "? ", "; ", ", "):
            k = cut.rfind(p)
            if k > limit * 0.45:
                txt = cut[:k + 1].strip()
                break
        else:
            txt = cut.strip()
    if len(txt) < excerpt_floor:
        return None
    return txt + " […]"


ADDR_TITLES = {'general', 'generaux', 'ministre', 'ministres', 'citoyen',
               'citoyenne', 'marechal', 'prince', 'roi', 'reine', 'empereur',
               'directeur', 'directoire', 'senat', 'corps', 'armee',
               'division', 'brigade', 'etat', 'major', 'consul', 'consuls',
               'troupes', 'armee', 'marine'}
ADDR_DOCS = {'ordre', 'ordres', 'arrete', 'arret', 'decision', 'decret',
             'proclamation', 'discours', 'allocution', 'message', 'note',
             'instruction', 'instructions', 'lettre', 'rapport', 'ordredujour'}


def addr_ok(addr):
    """An addressee must name someone/something, not trail off mid-word."""
    words = [w.lower() for w in re.findall(r'[A-Za-zÀ-ÿ]{4,}', fold(addr))]
    if not words:
        return False
    if all(w in ADDR_TITLES for w in words):
        core = fold(addr).lower().replace(' ', '')
        return core in ADDR_DOCS
    return True


def clean_place_corr(loc):
    t = (loc or '').strip()
    if not t or len(t) < 3 or re.search(r'\d', t):
        return ''
    if DAYNOISE.fullmatch(t):
        return ''
    return t


def surnames(s):
    s = unicodedata.normalize('NFKD', s or '').encode(
        'ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z]{3,}', s) if w not in STOP}


def shift(iso, d):
    import datetime
    try:
        t = datetime.date.fromisoformat(iso) + datetime.timedelta(days=d)
        return t.isoformat()
    except Exception:
        return None


def repair_year(iso, vol):
    """Single-digit OCR year fixes with volume + content consistency.
    Returns (iso, repaired_bool) or (None, False) if unrepairable."""
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', iso or '')
    if not m:
        return None, False
    y, mo, d = m.groups()
    if '1789' <= y <= '1821':
        return iso, False
    if y in ('1706', '1707', '1708', '1709'):
        return '179' + y[3] + '-' + mo + '-' + d, True
    if y in ('1790', '1791'):
        if vol in ('corr_vol2.json', 'corr_vol3.json'):
            return ('1796-' + mo + '-' + d, True) if mo == '12' \
                else ('1797-' + mo + '-' + d, True)
        if vol == 'corr_vol5.json':
            return '1799-' + mo + '-' + d, True
        return None, False
    if y == '1903' and vol == 'corr_vol8.json':
        return '1803-' + mo + '-' + d, True
    return None, False


def main():
    shards = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'shard_*.json')):
        for r in json.load(open(f, encoding='utf-8')):
            if r.get('author') == 'Napoleon Bonaparte':
                shards[r['id']] = r
    bydate = {}
    for sid, r in shards.items():
        bydate.setdefault(r['date'], []).append((sid, surnames(
            r.get('sourceTitle', ''))))
    used_ids = set(shards)
    for f in glob.glob(os.path.join(ROOT, 'data', 'nap_*.json')):
        for r in json.load(open(f, encoding='utf-8')):
            used_ids.add(r.get('id'))

    per_date_n = {}
    intake, enrich = [], {}
    gazetteer = build_place_gazetteer(shards)
    stats = {'seen': 0, 'bad_year': 0, 'empty_addr': 0, 'thin': 0,
             'enriched': 0, 'dup_skip': 0, 'in_dup': 0, 'kept': 0,
             'bad_excerpt': 0}
    seen_keys = set()
    for path in sorted(glob.glob(os.path.join(ROOT, 'sources',
                                              'corr_vol*.json'))):
        vol = os.path.basename(path)
        for b in json.load(open(path, encoding='utf-8')):
            stats['seen'] += 1
            iso, repaired = repair_year(b.get('iso'), vol)
            if iso is None:
                stats['bad_year'] += 1
                continue
            addr = clean_addr(b.get('addr'))
            if not addr or not addr_ok(addr):
                stats['empty_addr'] += 1
                continue
            place = norm_place(b.get('place'), gazetteer)
            if not place:
                # dateline remainder sometimes holds the town
                m = re.search(r'[Qq]uartier [gj][ée]n[eé]ral\s*,([^,.]+)',
                              b.get('addr') or '')
                if m:
                    place = norm_place(m.group(1), gazetteer)
            bs = surnames(addr)
            # exact-date match -> enrichment candidate
            exact = [sid for sid, ss in bydate.get(iso, []) if bs & ss]
            if exact:
                sid = exact[0]
                if shards[sid].get('originalText'):
                    stats['dup_skip'] += 1
                    continue
                ex = best_excerpt_fr(clean_body_corr(b.get('body')))
                if ex and good_excerpt(ex):
                    enrich[sid] = ex
                    stats['enriched'] += 1
                else:
                    stats['thin'] += 1
                continue
            # +-1 day match -> skip (cross-edition dup avoidance)
            fuzzy = False
            for dd in (-1, 1):
                for sid, ss in bydate.get(shift(iso, dd) or '', []):
                    if bs & ss:
                        fuzzy = True
                        break
                if fuzzy:
                    break
            if fuzzy:
                stats['dup_skip'] += 1
                continue
            ex = best_excerpt_fr(clean_body_corr(b.get('body')))
            if not good_excerpt(ex):
                stats['bad_excerpt'] += 1
                continue
            # within-intake dupes: same date + near-identical excerpt means
            # the same letter filed twice (orders often repeat); distinct
            # same-day letters to one addressee are kept.
            import difflib
            dup = False
            for prev in intake:
                if prev['iso'] != iso:
                    continue
                ea, eb = prev['excerpt_fr'][:150], ex[:150]
                if ea and eb and difflib.SequenceMatcher(None, ea, eb).ratio() > 0.8:
                    dup = True
                    break
            if dup:
                stats['in_dup'] += 1
                continue
            n = per_date_n.get(iso, 700)
            rid = 'nap-%s-%d' % (iso.replace('-', ''), n)
            while rid in used_ids:
                n += 1
                rid = 'nap-%s-%d' % (iso.replace('-', ''), n)
            per_date_n[iso] = n + 1
            used_ids.add(rid)
            intake.append({
                'id': rid,
                'iso': iso,
                'date': iso,
                'addr_fr': addr,
                'place': place,
                'body_fr': b.get('body') or '',
                'excerpt_fr': ex,
                'vol': vol,
                'corr_no': b.get('no'),
                'repaired_date': repaired,
            })
            stats['kept'] += 1
    json.dump(intake, open(os.path.join(ROOT, 'sources', 'corr_intake.json'),
                           'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump(enrich, open(os.path.join(ROOT, 'sources', 'corr_enrich.json'),
                           'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('stats:', stats)
    print('intake: %d, enrich: %d' % (len(intake), len(enrich)))


if __name__ == '__main__':
    main()
