"""Reconcile the review into transcript/timing.json.

    python3 transcript/merge_review.py review_result.json [more_results.json ...]

Each result file is the review workflow's output: per stretch, a reader's
timing for every item and, where reader and matcher disagreed, an
adjudicator's decision. Precedence per item: adjudicated decision, then the
reader, then the matcher (timing_auto.json) as a last resort. Later result
files override earlier ones item by item, so a targeted second round only has
to cover the lines it re-examined.

Playback order is checked, not assumed. A start that runs backwards is pulled
up to its predecessor and reported, so a bad decision cannot silently scramble
the page.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).parent
DUR = 2704.9


def main(paths):
    items = json.loads((HERE / "turns.json").read_text(encoding="utf-8"))
    auto = {a["i"]: a for a in json.loads((HERE / "timing_auto.json").read_text(encoding="utf-8"))}
    final = {i: {"i": i, "start": a["start"], "end": a["end"],
                 "conf": "low" if a.get("interpolated") or a.get("conf") in (None, "low", "direction") else a["conf"],
                 "method": "matcher", "evidence": a.get("asr", "")} for i, a in auto.items()}

    for p in paths:
        for st in json.loads(Path(p).read_text(encoding="utf-8")):
            if st and "group" in st and "items" not in st:
                # final skeptic pass: upheld / adjusted / refuted, one verdict per claim
                for v in st.get("verdicts") or []:
                    row = final[v["i"]]
                    row["skeptic"] = f"{v['verdict']}: {v['reason']}"
                    if v["verdict"] in ("adjusted", "refuted"):
                        row.update({"start": v["start"], "end": v["end"], "conf": v["confidence"]})
                        row["method"] = row.get("method", "") + f", skeptic {v['verdict']}"
                continue
            if st and "group" in st:
                # second round: gap readers, with a skeptic's verdict on each promotion
                verdict = {v["i"]: v for v in (st.get("verdicts") or [])}
                for x in st.get("items") or []:
                    v = verdict.get(x["i"])
                    if x["confidence"] != "low" and v is None:
                        continue                      # no verdict for this promotion: never take it unchecked
                    row = {"i": x["i"], "start": x["start"], "end": x["end"], "conf": x["confidence"],
                           "method": "gap-reader", "evidence": x.get("evidence", "")}
                    if v is not None:
                        if v["upheld"]:
                            row["method"] = "gap-reader, upheld"
                        else:
                            row.update({"start": v["start"], "end": v["end"], "conf": v["confidence"],
                                        "method": "gap-reader, refuted"})
                        row["skeptic"] = v["reason"]
                    final[x["i"]] = row
                continue
            if not st or not st.get("reader"):
                continue
            for x in st["reader"]["items"]:
                row = {"i": x["i"], "start": x["start"], "end": x["end"], "conf": x["confidence"],
                       "method": "reader", "evidence": x.get("evidence", "")}
                if x.get("note"):
                    row["note"] = x["note"]
                if x.get("line_starts"):
                    row["line_starts"] = x["line_starts"]
                final[x["i"]] = row
            for d in st.get("decisions") or []:
                row = final[d["i"]]
                row.update({"start": d["start"], "end": d["end"], "conf": d["confidence"],
                            "method": f"adjudicated:{d['winner']}", "adjudication": d["reason"]})

    # Verification outcomes are applied last, so a re-run of the merge can never
    # quietly restore a confidence that failed an unprompted re-decode.
    ov_path = HERE / "verified_overrides.json"
    if ov_path.exists():
        for o in json.loads(ov_path.read_text(encoding="utf-8")):
            row = final[o["i"]]
            for k in ("start", "end", "conf"):
                if k in o:
                    row[k] = o[k]
            row["verification"] = o["note"]

    out, fixed, prev = [], [], 0.0
    for it in items:
        r = final[it["i"]]
        r["start"] = round(min(max(float(r["start"]), 0.0), DUR), 2)
        if r["start"] < prev:
            fixed.append((it["i"], r["start"], prev))
            r["start"] = prev
        r["end"] = round(min(max(float(r["end"]), r["start"]), DUR), 2)
        ls = r.get("line_starts")
        if ls:
            n = it["text"].count("\n") + 1
            ls = [min(max(float(x), r["start"]), r["end"]) for x in ls][:n]
            for k in range(1, len(ls)):
                ls[k] = max(ls[k], ls[k - 1])
            if len(ls) == n:
                r["line_starts"] = [round(x, 2) for x in ls]
            else:
                r.pop("line_starts")
        prev = r["start"]
        out.append(r)

    (HERE / "timing.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    turns = [r for r, it in zip(out, items) if it["kind"] == "turn"]
    tally = {c: sum(1 for r in turns if r["conf"] == c) for c in ("high", "medium", "low")}
    meth = {}
    for r in turns:
        meth[r["method"]] = meth.get(r["method"], 0) + 1
    print(f"{len(turns)} turns: {tally}")
    print(f"decided by: {meth}")
    if fixed:
        print(f"{len(fixed)} start(s) ran backwards and were pulled up to their predecessor:")
        for i, s, p in fixed:
            print(f"  item {i}: {s} -> {p}")


if __name__ == "__main__":
    main(sys.argv[1:])
