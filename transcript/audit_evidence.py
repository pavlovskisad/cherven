"""Check that every confident timing rests on evidence anyone can reproduce.

    python3 transcript/audit_evidence.py [extra_pass.json ...]

Each entry of timing.json quotes the recognised speech it was matched to,
as «words»@seconds. Reviewers sometimes ran their own decodes, a few of them
*prompted* with the expected words — and a prompted decode can echo its
prompt. So a high or medium entry counts as supported only if at least one
of its quotes is found, near the time it cites, in a saved recognition pass:
whisper.json, or any raw pass file passed on the command line.

Prints the unsupported entries; exits 0 either way.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
QUOTE = re.compile(r"«([^»]{2,400})»\s*(?:@\s*(\d+(?:\.\d+)?))?")
NUM = re.compile(r"@\s*(\d+(?:\.\d+)?)")
toks = lambda s: [w for w in re.sub(r"[^\w]+", " ", re.sub(r"@[\d.–\-]+", " ", s.lower())).split() if len(w) > 1]


def load_pool(extra):
    segs = list(json.loads((HERE / "whisper.json").read_text(encoding="utf-8"))["segments"])
    for p in extra:
        segs += json.loads(Path(p).read_text(encoding="utf-8"))["segments"]
    return segs


def supported(quote, t, pool, slack=4.0):
    q = toks(quote)
    if not q:
        return False
    near = [s for s in pool if s["start"] <= t + slack and s["end"] >= t - slack]
    have = set(w for s in near for w in toks(s["text"]))
    hit = sum(1 for w in q if w in have)
    return hit / len(q) >= 0.6


def audit(timing, pool):
    bad = []
    for r in timing:
        if r.get("conf") not in ("high", "medium"):
            continue
        ev = r.get("evidence", "") + " " + r.get("adjudication", "")
        quotes = []
        for m in QUOTE.finditer(ev):
            txt, t = m.group(1), m.group(2)
            if t is None:
                inner = NUM.search(txt)
                t = inner.group(1) if inner else None
            quotes.append((txt, float(t) if t else r["start"]))
        ok = any(supported(q, t, pool) for q, t in quotes)
        if not ok:
            bad.append({"i": r["i"], "start": r["start"], "conf": r["conf"], "method": r.get("method"),
                        "quotes": [q for q, _ in quotes][:3], "evidence": ev[:300]})
    return bad


if __name__ == "__main__":
    timing = json.loads((HERE / "timing.json").read_text(encoding="utf-8"))
    pool = load_pool(sys.argv[1:])
    bad = audit(timing, pool)
    conf = [r for r in timing if r.get("conf") in ("high", "medium")]
    print(f"{len(conf)} confident entries; {len(conf) - len(bad)} supported by saved recognition; {len(bad)} not")
    for b in bad:
        print(f"  item {b['i']:3d} @{b['start']:7.1f} {b['conf']:6s} {b['method']}: {b['quotes'] or b['evidence'][:120]}")
    json.dump(bad, open(HERE / "audit_unsupported.json", "w"), ensure_ascii=False, indent=1)
