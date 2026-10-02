"""Parse transcript/source.txt into an ordered list of turns.

The source is the edited English transcript exactly as supplied: a speaker
label on its own line, then that speaker's text, which may run over several
lines (the prayer is verse and keeps its breaks). Stage directions sit on
their own line in [square brackets].

Speaker labels are matched against an explicit list, never guessed. A shape
heuristic ("short line, capitalised, no closing punctuation") would take the
verse line "And I shall dissolve within You" for a speaker.

Two irregularities in the source are handled rather than edited away:
  - a label run onto the end of a text line after tabs ("…fuck it.\t\tIan")
  - an inline "Name: text" line under [In the background]

Run:  python3 transcript/parse.py   ->  transcript/turns.json
The script refuses to write unless every source line is accounted for and the
reassembled text matches the source character for character, whitespace aside.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SPEAKERS = [
    "Andriy", "Frania", "Bohdan’s mother", "Serhii", "Bohdan’s sister",
    "Nikolaich", "Sania", "Hek", "Chapa", "Mrs. Anya", "Patient",
    "Another patient", "Woman at the Liquor Factory", "Hek and Frania’s grandpa",
    "Tour guide", "Vitalii Hodziatskyi", "Zenon", "Katya", "Soldier",
    "Soldier and choir of soldiers", "Choir", "Commander", "Kostya",
    "Funeral hostess", "Liokha", "Ian", "Frania (reacting to the air raid siren)",
    "Priests", "Congregation", "Ruslan", "Levin", "Dima", "Crowd", "Priest",
    "Sasha (singing)", "Sasha", "Zhanna", "Platon",
]
SPK = set(SPEAKERS)
TAIL = re.compile(r"^(.*\S)\t+\s*(" + "|".join(map(re.escape, SPEAKERS)) + r")\s*$")
INLINE = re.compile(r"^(" + "|".join(map(re.escape, SPEAKERS)) + r"):\s+(.+)$")


def parse(src):
    items, cur = [], None

    def close():
        nonlocal cur
        if cur is not None:
            cur["text"] = "\n".join(cur.pop("lines")).strip()
            if not cur["text"]:
                raise SystemExit(f"speaker {cur['spk']!r} has no text")
            items.append(cur)
            cur = None

    for n, raw in enumerate(src.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line in SPK:
            close()
            cur = {"kind": "turn", "spk": line, "lines": [], "src_line": n}
            continue
        if line.startswith("[") and line.endswith("]"):
            close()
            items.append({"kind": "dir", "text": line, "src_line": n})
            continue
        m = INLINE.match(line)
        if m and cur is None:
            items.append({"kind": "turn", "spk": m.group(1), "text": m.group(2).strip(), "src_line": n})
            continue
        m = TAIL.match(raw.rstrip("\n"))
        if m:
            if cur is None:
                raise SystemExit(f"line {n}: text before any speaker: {line!r}")
            cur["lines"].append(m.group(1).strip())
            close()
            cur = {"kind": "turn", "spk": m.group(2), "lines": [], "src_line": n}
            continue
        if cur is None:
            raise SystemExit(f"line {n}: text with no speaker: {line!r}")
        # collapse runs of spaces inside a line, keep the line break itself
        cur["lines"].append(re.sub(r"[ \t]{2,}", " ", line))
    close()
    for i, it in enumerate(items):
        it["i"] = i
    return items


def verify(src, items):
    """Reassemble every label and text and compare with the source, ignoring
    only whitespace. Any dropped, duplicated or altered character fails."""
    norm = lambda s: re.sub(r"\s+", "", s)
    rebuilt = []
    for it in items:
        if it["kind"] == "turn":
            rebuilt.append(it["spk"])
        rebuilt.append(it["text"])
    a, b = norm(src), norm("".join(rebuilt))
    # the inline "Frania: Mister Poopoo!" loses its colon when split into label + text
    b_cmp = b
    a_cmp = a.replace("Frania:MisterPoopoo!", "FraniaMisterPoopoo!")
    if a_cmp != b_cmp:
        k = next(i for i, (x, y) in enumerate(zip(a_cmp, b_cmp)) if x != y)
        raise SystemExit(f"reassembly mismatch near: {a_cmp[max(0,k-40):k+40]!r}")
    return len(a)


if __name__ == "__main__":
    src = (HERE / "source.txt").read_text(encoding="utf-8")
    items = parse(src)
    chars = verify(src, items)
    turns = [i for i in items if i["kind"] == "turn"]
    dirs = [i for i in items if i["kind"] == "dir"]
    (HERE / "turns.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    used = sorted({t["spk"] for t in turns})
    unused = [s for s in SPEAKERS if s not in used]
    print(f"{len(turns)} turns, {len(dirs)} directions, {len(used)} speakers; "
          f"{chars} non-space chars reassemble exactly")
    if unused:
        print("speakers listed but never used:", unused)
