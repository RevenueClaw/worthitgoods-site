#!/usr/bin/env python3
"""Moltbook API helper for WorthItGoods scripts (deal_of_the_day.py imports this
as `from moltbook import post_moltbook`).

Created 2026-11-16 — the deal-of-day moltbook leg previously died on
ModuleNotFoundError because this module never existed.

Auth: ~/.config/moltbook/credentials.json -> {"api_key": "***", "agent_name": "rockclaw"}
API base: https://www.moltbook.com/api/v1  (always www — bare domain strips auth)
Scheme: Bearer tried first, X-API-Key fallback (live spec 2026-11 uses Bearer).

Flow per live spec:
  POST /posts {"submolt_name","title","content"} -> may return a pending state
  with an obfuscated math challenge; solve it and POST /verify with the
  verification_code, answer "NN.NN". Content is invisible until verified;
  unsolved challenges expire in ~5 minutes.

Returns True only for a published/verified post. Never raises — callers treat
False + printed reason as "leg failed this run".
"""

import json
import os
import re
import urllib.error
import urllib.request

CREDS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")
BASE = "https://www.moltbook.com/api/v1"
STATE_PATH = os.path.expanduser("~/.openclaw/workspace/memory/moltbook-state.json")

WORD_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}


def _load_key():
    try:
        with open(CREDS_PATH) as f:
            return json.load(f).get("api_key", "").strip()
    except Exception:
        return ""


def _post(path, key, body):
    last = (0, {"error": "no attempt"})
    data = json.dumps(body).encode()
    for hdr in ({"Authorization": f"Bearer {key}"}, {"X-API-Key": key}):
        req = urllib.request.Request(
            BASE + path, data=data,
            headers={**hdr, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode())
            except Exception:
                payload = {"error": str(e)}
            if e.code != 401:
                return e.code, payload
            last = (e.code, payload)
        except Exception as e:
            return 0, {"error": str(e)}
    return last


def _subseq_pos(hay, needle):
    """Start index of the first subsequence occurrence of needle in hay, else -1."""
    hi = 0
    start = -1
    for i, c in enumerate(hay):
        if c == needle[hi]:
            if hi == 0:
                start = i
            hi += 1
            if hi == len(needle):
                return start
    return -1


def _extract_numbers(text):
    """Pull up to two operand values from an obfuscated word problem.
    Real generator (probed 2026-11-16) shatters words ACROSS whitespace
    ("FiV e]" = five, "tWeN tY" = twenty), so we scan sliding windows of
    1-3 joined tokens: contiguous match always; subsequence fallback only
    for long words (>=5) to avoid short words matching everywhere.
    Tens+units in directly adjacent ranges merge ("thirty five" -> 35)."""
    vals = [int(float(t)) for t in re.findall(r"\d+(?:\.\d+)?", text)]
    if len(vals) >= 2:
        return vals[:2]
    toks = [re.sub(r"[^A-Za-z]", "", t).lower() for t in text.split()]
    toks = [t for t in toks if t]
    n = len(toks)
    cands = []
    for i in range(n):
        for w in (1, 2, 3):
            if i + w > n:
                break
            joined = "".join(toks[i:i + w])
            for word, v in WORD_NUM.items():
                if word in joined or (len(word) >= 5 and _subseq_pos(joined, word) >= 0):
                    cands.append((i, i + w, len(word), word, v))
    cands.sort(key=lambda c: (c[0], -c[2]))
    picked, end = [], -1
    for s, e, _l, word, v in cands:
        if s < end:
            continue
        picked.append((s, e, word, v))
        end = e
    tens = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
    out = []
    i = 0
    while i < len(picked):
        s, e, word, v = picked[i]
        if word in tens and i + 1 < len(picked) and picked[i + 1][0] == e and 1 <= picked[i + 1][3] <= 9:
            out.append(v + picked[i + 1][3])
            i += 2
        elif word == "hundred" and out and 1 <= out[-1] <= 9:
            out[-1] = out[-1] * 100
            i += 1
        else:
            out.append(v)
            i += 1
        if len(out) >= 2:
            break
    return out


def _solve(challenge):
    """Best-effort: two operands + one operation keyword -> 'NN.NN'."""
    nums = _extract_numbers(challenge)
    if len(nums) != 2:
        return None
    a, b = nums
    joined = re.sub(r"[^A-Za-z]", "", challenge).lower()
    OPS = [
        ("minus", ("slow", "decreas", "less", "fewer", "minus", "drop", "reduce",
                   "remain", "left", "spent", "give", "lost")),
        ("plus", ("sum", "total", "more", "increase", "plus", "altogether", "join",
                  "grow", "gain", "add")),
        ("times", ("times", "multipl", "each")),
        ("divide", ("divi", "split", "quotient")),
    ]
    best_op, best_idx = None, 1 << 30
    for op, kws in OPS:
        for kw in kws:
            i = joined.find(kw)
            if i >= 0 and i < best_idx:
                best_op, best_idx = op, i
    if best_op == "minus":
        ans = a - b
    elif best_op == "times":
        ans = a * b
    elif best_op == "divide":
        ans = a / b if b else 0
    else:
        ans = a + b
    return f"{ans:.2f}"


def _note(post_id, extra=""):
    """Record post ids so the engagement sweep can see them (skill rule)."""
    try:
        st = json.load(open(STATE_PATH))
    except Exception:
        st = {}
    tp = st.setdefault("tracked_posts", [])
    if post_id and post_id not in tp:
        tp.append(post_id)
    st["last_deal_post"] = {"id": post_id, "note": extra}
    try:
        tmp = STATE_PATH + ".tmp"
        json.dump(st, open(tmp, "w"), indent=1)
        os.replace(tmp, STATE_PATH)
    except Exception:
        pass


def post_moltbook(text, hook_name=None, submolt="general"):
    """Post `text` to Moltbook. Returns bool. Never raises."""
    key = _load_key()
    if not key:
        print("  🦜 Moltbook: no api_key in credentials.json — leg inactive")
        return False
    lines = [l for l in text.strip().splitlines() if l.strip()]
    title = (lines[0] if lines else "WorthItGoods update")[:120]
    status, body = _post("/posts", key, {
        "submolt_name": submolt,
        "title": title,
        "content": text[:2000],
    })
    if status in (401, 403):
        msg = str(body.get("message") or body.get("error") or "")[:120]
        print(f"  🦜 Moltbook: key rejected ({status}: {msg}) — owner must re-claim/re-register")
        return False
    if status not in (200, 201):
        print(f"  🦜 Moltbook: HTTP {status} {str(body)[:140]}")
        return False

    post = body.get("post") or {}
    pid = post.get("id") or body.get("id") or ""
    pending = bool(body.get("verification_required")) or post.get("verification_status") == "pending"
    if not pending:
        _note(pid, hook_name or "direct")
        print(f"  🦜 Moltbook: published {pid[:8]}")
        return True

    v = post.get("verification") or body.get("verification") or {}
    code, chall = v.get("verification_code", ""), v.get("challenge_text", "")
    ans = _solve(chall) if chall else None
    if not (code and ans):
        _note(pid, "pending-unverified")
        print(f"  🦜 Moltbook: challenge unsolved (parsed {ans}) — post left pending, expires in ~5m")
        return False
    vs, vb = _post("/verify", key, {"verification_code": code, "answer": ans})
    ok = vs in (200, 201) and not vb.get("error")
    _note(pid, "verified" if ok else "verify-rejected")
    print(f"  🦜 Moltbook: {'published' if ok else 'verification rejected'} {pid[:8]} (answer {ans})")
    return ok
