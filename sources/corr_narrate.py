#!/usr/bin/env python3
"""Phase D: draft narratives + voices for data/nap_corr.json.

Mirrors narrate_contexts.main() but with body=None (displayText-only).
Doc-type records ("Ordre, ...") get scene+clause with no "To X:" frame,
matching the shipped precedent ("Decisions, 1800-01-02" has no frame).
Non-auto_ok records are REMOVED from nap_corr.json; drafts merge into
sources/context_drafts.json and sources/voice_drafts.json.
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from narrate_contexts import (  # noqa: E402
    narrate, voice_for, scene_for, clause_from, trim_clause,
    JUNK, XREF, DATE_PAT, WORDS, STOP)
from draft_contexts import known  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "sources")


def narrate_doc(rec, blurb):
    """Scene + clause, no frame. Same gates as narrate()."""
    flags = []
    clause = clause_from(rec["displayText"])
    if clause is None:
        return None, ["no-clause"]
    draft = " ".join(p for p in (blurb, clause) if p)
    if not draft.endswith((".", "\u2026", "?", "!")):
        draft += "."
    if len(draft) > 300:
        clause = trim_clause(clause, 170 - (len(draft) - 300))
        draft = " ".join(p for p in (blurb, clause) if p)
        if not draft.endswith((".", "\u2026")):
            draft += "."
    for rx in JUNK:
        if rx.search(draft):
            flags.append("clause-junk")
            break
    if XREF.search(draft):
        flags.append("xref")
    if DATE_PAT.search(draft):
        flags.append("has-date")
    if not (60 <= len(draft) <= 305):
        flags.append("bad-length")
    if WORDS:
        for w in re.findall(r"(?<![A-Za-z\u00c0-\u00de])[a-z\u00e0-\u00fe]{4,}",
                            clause):
            if w not in STOP and not known(w):
                flags.append("dict-unknown")
                break
    return draft, flags


def main():
    path = os.path.join(ROOT, "data", "nap_corr.json")
    recs = json.load(open(path, encoding="utf-8"))
    events = {e["id"]: e for e in
              json.load(open(os.path.join(ROOT, "data", "events.json"),
                             encoding="utf-8"))["events"]}
    drafts, voices, kept = {}, {}, []
    for rec in recs:
        eid = (rec.get("eventIds") or [""])[0]
        blurb = events.get(eid, {}).get("blurb") or ""
        scene = scene_for(rec, blurb)
        is_doc = not re.match(r"^To\s", rec.get("sourceTitle") or "", re.I)
        if is_doc:
            draft, flags = narrate_doc(rec, scene)
        else:
            draft, flags = narrate(rec, None, scene)
        voice, vflags = voice_for(rec, None)
        if voice is not None:
            # OCR-mangled addressee ("Ixt", "Uxt") yields a junk @mention:
            # keep the sentence, drop the handle
            m = re.match(r"@([a-z]+)\s", voice)
            if m and len(m.group(1)) < 4:
                voice = voice[m.end():]
        ok = draft is not None and set(flags) <= {"body-clause"}
        if not ok:
            continue
        kept.append(rec)
        if voice is not None:
            voices[rec["id"]] = voice
        drafts[rec["id"]] = {
            "draft": draft, "date": rec["date"],
            "sourceTitle": rec["sourceTitle"],
            "excerpt": rec["displayText"][:200], "flags": flags,
            "auto_ok": True,
        }
    print(f"corr narrate: {len(recs)} in, {len(kept)} auto_ok, "
          f"{len(recs) - len(kept)} dropped, voices {len(voices)}")
    json.dump(kept, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for name, new in (("context_drafts.json", drafts),
                      ("voice_drafts.json", voices)):
        p = os.path.join(SRC, name)
        old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        old.update(new)
        json.dump(old, open(p, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"merged {len(new)} into {name} (total {len(old)})")


if __name__ == "__main__":
    main()
