#!/usr/bin/env python3
"""Run the Lodi letter-to-tweet publishing pipeline.

Hand-edited paraphrases live in tweet_paraphrases.json. This runner applies
them to the editorial overrides, rebuilds the published archive, and verifies
tweet coverage and archive integrity in sequence.

Run from anywhere: python3 sources/lodi.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable


def main():
    for script in ("apply_contexts.py", "build_index.py", "verify.py"):
        print("\n== Lodi: %s ==" % script, flush=True)
        subprocess.run([PYTHON, os.path.join(ROOT, "sources", script)],
                       cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
