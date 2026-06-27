"""LLM-judge the MA review-board verdicts where the stored label and the
canonical keyword parser DISAGREE (P0, MA workstream).

The MA Review-Board `decision` vocabulary is open and context-dependent
("accept", "accept with mitigation", "confirmed ... resolved", "approved"),
so neither the stored keyword parser nor the canonical keyword parser can
reliably resolve polarity. For the subset where they disagree, we ask an
independent LLM judge to READ the full board verdict (decision + reason +
recommended_action) and the moderator context, and report whether the
Review Board concluded the code is vulnerable.

This corrects HOW the existing board output is read; it does NOT re-run
inference, so it stays a single experimental condition and leaves cost/
CodeCarbon untouched.

The judge is NOT shown the ground-truth label (no leakage) — it reads the
board's stated conclusion only.

Output (sidecar, raw JSONLs untouched):
    results/rq3_baseline/rq2_ma_disagreement_judged.csv

Usage:
    python scripts/rq2_ma_judge_disagreements.py --dry-run   # build queue, no API
    python scripts/rq2_ma_judge_disagreements.py --claude --judge-model claude-opus-4-6
"""

import argparse
import ast
import csv
import json
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from vuln_parser import classify, strip_markdown_fences, strip_think_block  # noqa: E402

csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDATED_CSV = os.path.join(PROJECT_ROOT, "results", "consolidated_performance.csv")
OUT_CSV = os.path.join(PROJECT_ROOT, "results", "rq3_baseline", "rq2_ma_disagreement_judged.csv")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REQUEST_DELAY = 0.5

SYSTEM_PROMPT = """You are an expert security-analysis adjudicator. You will be \
shown the final output of a "Review Board" agent that concluded a multi-agent \
code security review, optionally with the preceding moderator summary for \
context.

Your ONLY task is to determine what verdict the Review Board reached: did the \
Review Board conclude that the code CONTAINS a vulnerability, or NOT?

Read the board's actual conclusion carefully. Note these conventions:
- "confirmed", "valid", "accept", "accepted", "approved", "accept with \
mitigation/remediation/fixes", "fix required" => the board AFFIRMS that a \
vulnerability exists (VULNERABLE), even when it also proposes a fix.
- "rejected", "invalid", "no vulnerability", "not exploitable", "safe", or a \
verdict that the issue was already fully mitigated/resolved in the code as \
written and no real vulnerability remains => NOT VULNERABLE.

Judge only what the board concluded — do NOT independently re-analyze the code, \
and you are NOT told the ground-truth label.

Respond with a single JSON object and nothing else:
{"verdict": 1 or 0, "rationale": "<one sentence>"}
where 1 = board concluded VULNERABLE, 0 = board concluded NOT vulnerable."""


def as_dict(val):
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        for loader in (json.loads, ast.literal_eval):
            try:
                o = loader(val)
                if isinstance(o, dict):
                    return o
            except (ValueError, SyntaxError, TypeError):
                continue
    return {}


def ma_board_and_context(rec):
    fd = as_dict(rec.get("full_discussion"))
    board = fd.get("review_board") or fd.get("board") or rec.get("reasoning", "")
    moderator = fd.get("moderator", "")
    return str(board), str(moderator)


def _entry_class(stored, canon, determined):
    """Classify an MA entry for stratification."""
    if canon != stored:
        return "disagree"
    if canon == 1:
        return "agree1"
    return "agree0_det" if determined else "agree0_undet"


def build_full_queue():
    """Build the FULL MA entry list, each tagged with its class. The LLM judge
    will become the authoritative MA parser, so every verdict-bearing board is
    a candidate (not just parser disagreements) — both keyword parsers share a
    polarity blind spot on 'accepted and mitigated/resolved', so errors hide
    inside the agreement set too."""
    configs = [r for r in csv.DictReader(open(CONSOLIDATED_CSV))
               if r["dataset"] == "VulTrial-870" and r["design"] == "MA"]
    queue = []
    for cfg in configs:
        seen = set()
        for path in [p.strip() for p in cfg["source_file"].split(";") if p.strip()]:
            for line in open(path):
                if not line.strip():
                    continue
                rec = json.loads(line)
                idx = rec.get("idx")
                if idx is None or int(idx) in seen:
                    continue
                seen.add(int(idx))
                stored = rec.get("vuln")
                try:
                    stored = int(stored)
                except (TypeError, ValueError):
                    stored = 0
                if stored == -1:
                    stored = 1
                board, moderator = ma_board_and_context(rec)
                canon, determined = classify("MA", board)
                queue.append({
                    "model": cfg["model"], "mode": cfg["mode"], "prompting": cfg["prompting"],
                    "idx": int(idx),
                    "ground_truth": int(rec.get("ground_truth", rec.get("target", -1))),
                    "stored": stored, "canon": canon,
                    "cls": _entry_class(stored, canon, determined),
                    "board": board, "moderator": moderator,
                })
    return queue


def stratified_sample(queue, n, seed=42):
    """Even-ish allocation across the four classes; deterministic."""
    import random
    rng = random.Random(seed)
    by_cls = {}
    for q in queue:
        by_cls.setdefault(q["cls"], []).append(q)
    classes = sorted(by_cls)
    per = max(1, n // len(classes))
    out = []
    for c in classes:
        pool = by_cls[c]
        rng.shuffle(pool)
        out.extend(pool[:min(per, len(pool))])
    return out


def parse_judge(text):
    if not text:
        return None, ""
    t = strip_markdown_fences(strip_think_block(text))
    try:
        import re
        m = re.search(r"\{[\s\S]*\}", t)
        obj = json.loads(m.group(0)) if m else json.loads(t)
        v = int(obj.get("verdict"))
        return (v if v in (0, 1) else None), str(obj.get("rationale", ""))[:300]
    except (ValueError, AttributeError, TypeError):
        return None, ""


# One Anthropic client shared across threads (the SDK client is thread-safe).
_CLIENT = None
_CLIENT_LOCK = threading.Lock()


def _client():
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                from anthropic import Anthropic
                _CLIENT = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _CLIENT


def call_claude(system, user, model, retries=5):
    """Call the judge with exponential backoff. Returns text or None on
    exhausted retries. Rate-limit/transient errors get longer backoff."""
    client = _client()
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=model, max_tokens=400, temperature=0.0,
                system=system, messages=[{"role": "user", "content": user}])
            return "".join(b.text for b in resp.content if b.type == "text")
        except Exception as e:  # noqa: BLE001
            msg = str(e).lower()
            transient = any(k in msg for k in (
                "rate", "429", "overloaded", "529", "timeout", "connection",
                "503", "502", "500"))
            if attempt < retries - 1:
                # longer waits for rate/overload; capped exponential
                base = 5 if transient else 2
                wait = min(base ** (attempt + 1), 60)
                time.sleep(wait)
            else:
                # final failure: surface briefly (thread-safe via GIL on print)
                print(f"  give-up after {retries} tries: {str(e)[:120]}")
    return None


FIELDS = ["model", "mode", "prompting", "idx", "ground_truth",
          "stored", "canon", "cls", "judge", "rationale"]

_WRITE_LOCK = threading.Lock()


def _append_row(out_path, row):
    """Durable per-row append (open/write/flush/fsync/close under a lock) so an
    interrupt at any moment leaves a complete, resumable CSV."""
    with _WRITE_LOCK:
        with open(out_path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
            f.flush()
            os.fsync(f.fileno())


def _judge_one(q, model, retries):
    """Worker: judge a single entry. Returns (q, verdict_or_None, rationale)."""
    board = (q["board"] or "").strip()
    if not board:
        return q, None, "empty/truncated board"
    ctx = ""
    if q["moderator"].strip():
        ctx = f"Moderator summary (context):\n{q['moderator'][:2500]}\n\n"
    user = (f"{ctx}Review Board final output:\n{board[:4000]}\n\n"
            f"What verdict did the Review Board reach? Respond with the JSON object.")
    out = call_claude(SYSTEM_PROMPT, user, model, retries)
    v, rat = parse_judge(out)
    return q, v, rat


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--claude", action="store_true")
    ap.add_argument("--judge-model", default="claude-opus-4-6")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, judge a stratified sample of this size (step c). "
                         "0 = full set (step a).")
    ap.add_argument("--skip-classes", default="",
                    help="Comma-separated entry classes to skip (e.g. 'agree1'). "
                         "agree1 validated 100%% judge=stored, so it can be trusted "
                         "without re-judging.")
    ap.add_argument("--workers", type=int, default=8,
                    help="Concurrent API workers (default 8).")
    ap.add_argument("--retries", type=int, default=5,
                    help="Per-call retry attempts with backoff (default 5).")
    ap.add_argument("--out", default=OUT_CSV, help="Output CSV path.")
    args = ap.parse_args()

    queue = build_full_queue()
    print(f"Full MA queue: {len(queue)} entries")
    print(f"  class breakdown: {dict(Counter(q['cls'] for q in queue))}")

    skip = {c.strip() for c in args.skip_classes.split(",") if c.strip()}
    if skip:
        before = len(queue)
        queue = [q for q in queue if q["cls"] not in skip]
        print(f"  skipping classes {sorted(skip)}: {before} -> {len(queue)} entries")

    if args.sample > 0:
        queue = stratified_sample(queue, args.sample)
        print(f"Stratified sample: {len(queue)} entries "
              f"({dict(Counter(q['cls'] for q in queue))})")

    out_path = args.out
    if args.dry_run:
        print(f"\n[dry-run] would judge {len(queue)} entries "
              f"with {args.workers} workers -> {out_path}")
        return

    if not args.claude:
        sys.exit("Specify --claude to run the judge.")
    if not ANTHROPIC_API_KEY:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    # Resume: skip rows already present in the output CSV.
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            for row in csv.DictReader(f):
                done.add((row["model"], row["mode"], row["prompting"], int(row["idx"])))
        print(f"Resuming: {len(done)} already judged")
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    remaining = [q for q in queue
                 if (q["model"], q["mode"], q["prompting"], q["idx"]) not in done]
    print(f"Remaining to judge: {len(remaining)} "
          f"(workers={args.workers}, retries={args.retries})\n")
    if not remaining:
        print("Nothing to do — all entries already judged.")
        return

    ok = fail = 0
    t0 = time.time()
    interrupted = False
    ex = ThreadPoolExecutor(max_workers=args.workers)
    try:
        futures = {ex.submit(_judge_one, q, args.judge_model, args.retries): q
                   for q in remaining}
        for n, fut in enumerate(as_completed(futures), 1):
            q, v, rat = fut.result()
            if v is None:
                fail += 1  # not written -> retried on next resume
            else:
                _append_row(out_path, {
                    "model": q["model"], "mode": q["mode"], "prompting": q["prompting"],
                    "idx": q["idx"], "ground_truth": q["ground_truth"],
                    "stored": q["stored"], "canon": q["canon"], "cls": q["cls"],
                    "judge": v, "rationale": rat})
                ok += 1
            if n % 50 == 0 or n == len(remaining):
                rate = n / max(time.time() - t0, 1e-9)
                eta = (len(remaining) - n) / max(rate, 1e-9)
                print(f"  [{n}/{len(remaining)}] ok={ok} fail={fail} "
                      f"{rate:.1f}/s  ETA {eta/60:.1f} min")
    except KeyboardInterrupt:
        interrupted = True
        print("\n[interrupt] cancelling pending work; written rows are durable. "
              "Re-run the same command to resume.")
        ex.shutdown(wait=False, cancel_futures=True)
    else:
        ex.shutdown(wait=True)

    print(f"\n{'Interrupted' if interrupted else 'Done'}: "
          f"{ok} judged, {fail} failed this session -> {out_path}")
    if fail:
        print(f"  {fail} failures were NOT written; re-run to retry just those.")


if __name__ == "__main__":
    main()
