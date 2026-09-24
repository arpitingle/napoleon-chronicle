#!/usr/bin/env python3
"""Corr intake, phase B: machine-translate French excerpts + address lines
to English with a local opus-mt model (no network, no API).

Reads sources/corr_intake.json, writes sources/corr_mt.json
{id: {en, addr_en}}. Resumable (skips ids already present) and
incremental (saves every 50). Quality gates live in phase C; here we
translate everything that has text.

Run in background:  nohup python3 sources/build_corr_phaseB.py &
"""
import json
import os
import sys
import time

import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")


def main():
    torch.set_num_threads(max(1, (os.cpu_count() or 4) - 2))
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    tok = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-fr-en")
    model = AutoModelForSeq2SeqLM.from_pretrained("/tmp/opus-fr-en")
    model.eval()

    intake = json.load(open(os.path.join(SRC, "corr_intake.json"),
                            encoding="utf-8"))
    out_path = os.path.join(SRC, "corr_mt.json")
    done = {}
    if os.path.exists(out_path):
        done = json.load(open(out_path, encoding="utf-8"))
    todo = [r for r in intake if r["id"] not in done]
    print("intake: %d, done: %d, todo: %d"
          % (len(intake), len(done), len(todo)), flush=True)
    # bucket by length for efficient batching
    todo.sort(key=lambda r: len(r["excerpt_fr"]))
    BATCH = 16
    t0 = time.time()
    with torch.no_grad():
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            texts = [r["excerpt_fr"] for r in chunk]
            addrs = [r["addr_fr"].lower() for r in chunk]
            inp = tok(texts, return_tensors="pt", padding=True,
                      truncation=True, max_length=512)
            out = model.generate(**inp, max_new_tokens=256)
            ens = [tok.decode(o, skip_special_tokens=True) for o in out]
            inp2 = tok(addrs, return_tensors="pt", padding=True,
                       truncation=True, max_length=64)
            out2 = model.generate(**inp2, max_new_tokens=32)
            aens = [tok.decode(o, skip_special_tokens=True) for o in out2]
            for r, en, ae in zip(chunk, ens, aens):
                done[r["id"]] = {"en": en.strip(), "addr_en": ae.strip()}
            if (i // BATCH) % 4 == 3 or i + BATCH >= len(todo):
                json.dump(done, open(out_path, "w", encoding="utf-8"),
                          ensure_ascii=False)
                el = time.time() - t0
                print("  %d/%d  %.0fs  (%.1f/s)" % (
                    min(i + BATCH, len(todo)), len(todo), el,
                    (i + len(chunk)) / max(el, 0.01)), flush=True)
    json.dump(done, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    print("done: %d translations" % len(done))


if __name__ == "__main__":
    main()
