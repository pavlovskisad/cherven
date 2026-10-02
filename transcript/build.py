"""Write the timed transcript into transcript.html.

    python3 transcript/parse.py     source.txt  -> turns.json
    python3 transcript/build.py     turns.json + timing.json -> transcript.html

timing.json holds one entry per item of turns.json, by index:
    {"i": 12, "start": 241.3, "end": 247.9, "conf": "high", "evidence": "..."}

The page wants start-ordered lines (it binary-searches them), so this refuses
to write if the starts are not non-decreasing in transcript order. The
transcript is in playback order, so an inversion means bad timing, and it
should be fixed in timing.json rather than papered over here.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
PAGE = HERE.parent / "transcript.html"
DUR = 2704.9


def main():
    items = json.loads((HERE / "turns.json").read_text(encoding="utf-8"))
    timing = {t["i"]: t for t in json.loads((HERE / "timing.json").read_text(encoding="utf-8"))}
    missing = [it["i"] for it in items if it["i"] not in timing]
    if missing:
        sys.exit(f"no timing for items {missing}")

    out, prev = [], -1.0
    for it in items:
        tm = timing[it["i"]]
        s, e = float(tm["start"]), float(tm["end"])
        if not (0 <= s <= DUR and s <= e):
            sys.exit(f"item {it['i']}: bad span {s}..{e}")
        if s < prev:
            sys.exit(f"item {it['i']} starts at {s} before item {it['i']-1} at {prev}: order inverted")
        prev = s
        row = {"kind": it["kind"], "text": it["text"], "start": round(s, 2), "end": round(min(e, DUR), 2)}
        if it["kind"] == "turn":
            row = {"kind": "turn", "spk": it["spk"], **{k: row[k] for k in ("text", "start", "end")}}
        ls = tm.get("line_starts")
        if ls:
            # verse timed line by line: one start per line, in order, inside the turn
            n_lines = it["text"].count("\n") + 1
            if len(ls) != n_lines:
                sys.exit(f"item {it['i']}: {len(ls)} line starts for {n_lines} lines")
            if any(b < a for a, b in zip(ls, ls[1:])) or ls[0] < s - 0.01 or ls[-1] > e + 0.01:
                sys.exit(f"item {it['i']}: line starts out of order or outside {s}..{e}")
            row["lines"] = [round(x, 2) for x in ls]
        out.append(row)

    html = PAGE.read_text(encoding="utf-8")
    data = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    new, n = re.subn(r"/\*TURNS\*/.*?/\*END\*/", lambda m: "/*TURNS*/" + data + "/*END*/", html, flags=re.S)
    if n != 1:
        sys.exit("could not find exactly one /*TURNS*/.../*END*/ block in transcript.html")
    PAGE.write_text(new, encoding="utf-8")
    print(f"wrote {len(out)} items into {PAGE.name} ({len(data)} bytes of data)")


if __name__ == "__main__":
    main()
