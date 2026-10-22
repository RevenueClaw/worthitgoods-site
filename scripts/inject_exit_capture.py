#!/usr/bin/env python3
"""Inject the exit-intent capture script tag into every built HTML page.

Idempotent: skips pages that already reference the script.
Run after generation (build.sh) so all 300+ pages get the capture.

Usage: python3 scripts/inject_exit_capture.py
"""
import re
import sys
from pathlib import Path

TAG = '<script src="/assets/exit-capture.js" defer></script>'
MARKER = 'exit-capture.js'
ROOT = Path(__file__).resolve().parent.parent / '_site'


def inject(path: Path) -> bool:
    try:
        s = path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return False
    if MARKER in s:
        return False
    m = list(re.finditer(r'</body>', s, re.I))
    if not m:
        return False
    i = m[-1].start()
    path.write_text(s[:i] + TAG + '\n' + s[i:], encoding='utf-8')
    return True


def main() -> int:
    if not ROOT.is_dir():
        print(f"no _site dir at {ROOT}", file=sys.stderr)
        return 1
    changed = total = 0
    for p in ROOT.rglob('*.html'):
        total += 1
        if inject(p):
            changed += 1
    print(f"exit-capture: injected into {changed}/{total} pages")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
