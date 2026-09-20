#!/usr/bin/env python3
"""Merge machine-drafted + hand-written contexts into overrides.

Reads sources/context_drafts.json (auto_ok drafts only),
sources/hand_contexts.json (editor prose for flagged drafts),
sources/voice_drafts.json (first-person tweet lines, already gated) and
sources/tweet_paraphrases.json (hand LLM paraphrases, one tweet per
letter) and writes sources/context_overrides.json {"_meta": {...},
"contexts": {...}, "voices": {...}, "tweets": {...}}. build_index.py
applies all three at manifest build time, so a slice rebuild cannot
silently restore the boilerplate.

Refusing to run if any draft is neither auto_ok nor covered by hand prose:
every published record must have a reviewed summary.

Run from anywhere:  python3 sources/apply_contexts.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
sys.path.insert(0, SRC)
from common import DROP_IDS


def main():
    drafts = json.load(open(os.path.join(SRC, "context_drafts.json"),
                            encoding="utf-8"))
    hand = json.load(open(os.path.join(SRC, "hand_contexts.json"),
                          encoding="utf-8"))
    voices = json.load(open(os.path.join(SRC, "voice_drafts.json"),
                            encoding="utf-8"))
    tweets = json.load(open(os.path.join(SRC, "tweet_paraphrases.json"),
                            encoding="utf-8"))
    uncovered = [i for i, d in drafts.items()
                 if not d["auto_ok"] and i not in hand]
    if uncovered:
        raise SystemExit("unreviewed drafts (add to hand_contexts.json): %s"
                         % uncovered[:10])
    contexts = {}
    for i, d in drafts.items():
        if i in DROP_IDS:
            continue
        contexts[i] = hand.get(i, d["draft"])
    stray = [i for i in hand if i not in drafts and i not in DROP_IDS]
    if stray:
        raise SystemExit("hand entries matching no draft: %s" % stray[:10])
    bulk_ids = set(drafts)
    stray_v = [i for i in voices if i not in bulk_ids]
    if stray_v:
        raise SystemExit("voice entries matching no draft: %s" % stray_v[:10])
    FP = re.compile(r"\b(I|we|my|our|me|us|you|your)\b", re.I)
    NODATE = re.compile(
        r"\b(?:January|February|April|June|July|August|September|October|"
        r"November|December)\b|\bMay\b|\bMarch\b|\b1[789]\d\d\b|"
        r"\b1[78]\s\d\d\b|\b\d{1,2}(st|nd|rd|th)\b")
    for i, t in tweets.items():
        if not t or len(t) > 280 or not FP.search(t) or NODATE.search(t):
            raise SystemExit("bad paraphrase %s (%d chars)" % (i, len(t or "")))
    tvoices = {i: v for i, v in voices.items() if i not in DROP_IDS}
    out = {"_meta": {"records": len(contexts),
                     "machine": sum(1 for i in contexts if i not in hand),
                     "hand": len(hand),
                     "voices": len(tvoices),
                     "tweets": len(tweets),
                     "method": "narrative scene+frame+clause "
                               "(narrate_contexts.py) + editor review for "
                               "contexts; first-person extractive tweet "
                               "lines for voices; hand LLM paraphrases for "
                               "tweets; never invention beyond the letter"},
           "contexts": contexts,
           "voices": tvoices,
           "tweets": tweets}
    json.dump(out, open(os.path.join(SRC, "context_overrides.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print("overrides: %d (%d machine, %d hand), voices: %d, tweets: %d"
          % (len(contexts), out["_meta"]["machine"], len(hand),
             len(tvoices), len(tweets)))


if __name__ == "__main__":
    main()
