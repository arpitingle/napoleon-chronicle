#!/usr/bin/env python3
"""Corr re-trim: cut edition debris (signatures, filing refs, running
heads, next-letter headers) off FR excerpts, re-translate the trimmed
French with the local opus-mt model, update corr_intake.json +
corr_mt.json in place. Records left with <80 chars of French are
reported for DROP_IDS instead of being mangled.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CUTS = [
    # next-letter header after a filing number, possibly with a running
    # head in between: "... 499. _ AU GENERAL X ..." / "... 23. 356
    # CORRESPOND ... G. — AU CITOYEN Y ..."
    (re.compile(r"\d{2,5}[A-Z]?\b[^.!?…]{0,60}?[_—\-–]\s*(AU |AUX |A |"
                r"ORDRE|ARRET|DECISION|DECRET|PROCLAMATION|NOTE|MESSAGE|"
                r"INSTRUCTION|LETTRE|RAPPORT|DISCOURS|ADJUDANT|COMMANDANT|"
                r"PIECE).*?$", re.I | re.S), "next-header"),
    # running head mid-text: "... entière. 17. 260 CORRESPOXDAXGE DE
    # XAPOLÉON Je ne vous ..." (page number + head, no sentence end).
    # First word anchored to CORRESPONDANCE-mangled forms so legitimate
    # caps ("ORDRE DE BATAILLE") never match.
    (re.compile(r"\s*(?:\d{1,4}\.\s*)?(?:\d{2,4}\s+)?(?:C[O0][A-ZÉÈ]{0,3}R\w*|"
                r"G[O0]RRESP\w*|COIL\w*)\s+DE\s+[A-ZÉÈÀ-Þ]{3,}[^.!?…]{0,40}"
                r"(?:[.!?]\s*(?:—|-)\s*AN\s+[IVXL0-9]+[^.!?…]{0,30}[.!?])?",
                re.S), "head-mid"),
    # enclosure ref + whatever follows ("Pièce n° 2501. — ...")
    (re.compile(r"\s*\.?\s*1?\s*Pi[eè]ce n°\s*\d{2,5}[A-Z]?\..*$", re.S),
     "piece-ref"),
    # mangled running head with volume tag ("CORRESPOXDANCE DE . — AN IV ...")
    (re.compile(r"\s*CORRESP\w*\s+DE\s*\W{0,6}\s*(—|-)?\s*AN\s+[IVXL]+\b.*$",
                re.S), "head-vol"),
    # running head to end of excerpt
    (re.compile(r"\s*(CORRESPOND\w*\s+DE\s+\w*APOL\w*|CO[IIL]RESPOXDAXCK"
                r"|CORRESPONDANCE DE NAPOL).*$", re.S), "head"),
]

SIG_TAIL = re.compile(
    r"\s*,?\s*((?:[A-ZÉÈA-Z']{5,}|Bonaparte|BOMAPARTH|RONAI'AIITE)"
    r"\.{0,3})(.*)$", re.S)
FILING_WORDS = re.compile(
    r"Archiv|Dépôt|Dépot|Dépùl|Ui.pùl|Comm\.|En minutes|Empire|guerre|"
    r"Pi[eè]ce|Collection|Collcclioii|par M", re.I)
CLOSE_FILING = re.compile(
    r"\s*Par ordre du (?:général en chef|Premier Consul)\.\s*"
    r"(?:Dépôt|Dépot|Dépùl|Ui.pùl|Dépôl|Collcclioii|Collection)?"
    r".*?$", re.I | re.S)


def sig_cut(fr):
    """Cut a signature + filing tail ('... intentions. Bonaparte.
    Archives ... 1981.') but never substantive prose: the tail after
    the name must be short or carry filing words."""
    m = SIG_TAIL.search(fr)
    if not m or m.start() <= 0:
        return fr, None
    name, tail = m.group(1), m.group(2)
    is_bonaparte = bool(re.match(
        r"(Bonaparte|BOMAPARTH|RONAI'AIITE)", name))
    if FILING_WORDS.search(tail) or (is_bonaparte and len(tail) < 45):
        return fr[:m.start()].rstrip(" ."), "signature"
    return fr, None


def trim(fr):
    fr = re.sub(r"\s*\[…\]$|\s*\[\.\.\.\]$", "", fr).strip()
    why = None
    for _ in range(3):  # next-header, then the exposed signature/filing
        changed = False
        for rx, name in CUTS:
            m = rx.search(fr)
            if m and m.start() > 0:
                fr = fr[:m.start()].rstrip(" .")
                why = name if why is None else why + "+" + name
                changed = True
                break
        fr2, w2 = sig_cut(fr)
        if w2:
            fr, why = fr2, (why + "+" + w2 if why else w2)
            changed = True
        m = CLOSE_FILING.search(fr)
        if m and m.start() > 0:
            fr = fr[:m.start()].rstrip(" .")
            why = (why + "+filing" if why else "filing")
            changed = True
        if not changed:
            break
    # dangling tail after a real cut ("... vivres pour"): drop the fragment
    if why is not None:
        m = re.search(r"[.!?…]\s*[^.!?…]{0,29}$", fr)
        if m and re.search(r"[.!?…]", fr[:m.start()]):
            fr = fr[:m.start() + 1].rstrip()
            why = why + "+dangle"
        # ends with a preposition/article: back up to the last boundary
        if re.search(
                r"\b(à|son|sa|ses|le|la|les|un|une|des|du|de|d'|et|en|"
                r"dans|pour|avec|que|qui|sur|par|au|aux|l'|s'|c'|qu'|"
                r"lorsque|comme|car|mais|ou|où|dont|est|sont|était|"
                r"étaient|a|ont|avait|avaient|sera|seront)\s*$", fr, re.I):
            m2 = re.search(r"[,;:.!?…]\s*[^,;:.!?…]*$", fr)
            if m2 and m2.start() > 0:
                fr = fr[:m2.start() + 1].rstrip()
                why = why + "+prep"
    # tail cleanups: OCR debris that survives a cut (only on cut excerpts)
    if why is not None:
        fr = re.sub(r",\s*[a-zA-Z]\s*$", "", fr)      # "...compromettre., i"
        fr = re.sub(r"\s+\d{1,4}[A-Z]?\.?$", "", fr)  # "...change 1"
        fr = re.sub(r"[\s.,;:{■»«\"\-–—/]+$", "", fr)  # punct salad
        # cleanup left a dangling prep ("...d'administration du"):
        # strip trailing prep words; the [...] marks the continuation
        for _ in range(3):
            m = PREP_END.search(fr)
            if not m:
                break
            fr = fr[:m.start()].rstrip()
            why = why + "+tail"
    return fr + " […]", why


PREP_END = re.compile(
    r"\b(à|son|sa|ses|mon|ma|mes|ton|ta|tes|leur|leurs|notre|nos|"
    r"votre|vos|ce|cet|cette|le|la|les|un|une|des|du|de|d'|et|en|"
    r"dans|pour|avec|que|qu'|qui|sur|par|au|aux|l'|s'|c'|"
    r"lorsque|comme|car|mais|ou|où|dont|est|sont|était|"
    r"étaient|a|ont|avait|avaient|sera|seront)\s*(\[…\])?$", re.I)


FR_START = {
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "en",
    "dans", "pour", "avec", "que", "qui", "sur", "par", "au", "aux",
    "ce", "cette", "ces", "son", "sa", "ses", "mon", "ma", "mes",
    "car", "mais", "ou", "où", "donc", "or", "ni", "comme", "lorsque",
    "quand", "si", "tout", "tous", "toute", "ne", "pas", "plus",
    "jamais", "ici", "c", "l", "d", "s", "qu", "j", "m", "t", "y",
}


def ends_dangling(fr):
    t = re.sub(r"\s*\[…\]$", "", fr)
    if PREP_END.search(t):
        return True
    m = re.match(r"([A-Za-zÀ-Þà-þ]+)", t)
    if m and m.group(1)[0].islower():
        w = m.group(1).lower()
        if len(w) < 4 and w not in FR_START:
            return True  # mid-word fragment start ("ir sans délai")
    return False


def main():
    intake = json.load(open(os.path.join(HERE, "corr_intake.json")))
    mt = json.load(open(os.path.join(HERE, "corr_mt.json")))
    by_id = {r["id"]: r for r in intake}
    todo, short = [], []
    for r in intake:
        fr = r["excerpt_fr"]
        new, why = trim(fr)
        if why is None:
            continue
        if len(new) < 60 or ends_dangling(new):
            short.append((r["id"], why, len(new)))
            continue
        todo.append((r["id"], new, why))
    print(f"trimmable: {len(todo)}, too-short-after-trim: {len(short)}")
    for i, why, n in short:
        print(f"  DROP? {i} ({why}, {n} chars): "
              f"{by_id[i]['excerpt_fr'][:80]}")
    if "--dry" in sys.argv:
        for rid, new_fr, why in todo:
            print(f"  TRIM [{why}] {rid}: ...{by_id[rid]['excerpt_fr'][-90:]}")
            print(f"    -> ...{new_fr[-90:]}")
        return
    if not todo:
        return
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    tok = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-fr-en")
    model = AutoModelForSeq2SeqLM.from_pretrained("/tmp/opus-fr-en")
    model.eval()
    BS = 16
    for c in range(0, len(todo), BS):
        chunk = todo[c:c + BS]
        texts = [re.sub(r"\s*\[…\]$|\s*\[\.\.\.\]$", "", t[1]).strip()
                 for t in chunk]
        inp = tok(texts, return_tensors="pt", padding=True,
                  truncation=True, max_length=256)
        with torch.no_grad():
            gen = model.generate(**inp, max_length=256, num_beams=1,
                                 do_sample=False)
        ens = tok.batch_decode(gen, skip_special_tokens=True)
        for (rid, new_fr, why), en in zip(chunk, ens):
            by_id[rid]["excerpt_fr"] = new_fr
            mt[rid]["en"] = en.strip()
        print(f"  retranslated {min(c + BS, len(todo))}/{len(todo)}",
              flush=True)
    json.dump(intake, open(os.path.join(HERE, "corr_intake.json"), "w"),
              ensure_ascii=False, indent=1)
    json.dump(mt, open(os.path.join(HERE, "corr_mt.json"), "w"),
              ensure_ascii=False)
    print("wrote corr_intake.json + corr_mt.json")


if __name__ == "__main__":
    main()
