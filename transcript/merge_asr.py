"""Pool several Whisper passes into transcript/whisper.json.

    python3 transcript/merge_asr.py p1.json p2.json p3.json

Layered audio defeats any single recognition pass in a different place each
time: the plain pass hears voices the VAD-gated pass misses, and the pass on
Demucs-isolated vocals hears voices both miss under a music bed. So all
passes are kept and merged.

Two segments are the same hearing only if they overlap in time AND say much
the same thing; then the more confident one is kept. Overlapping segments that
say different things are usually two voices at once, and both stay.
"""
import json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).parent
HALLU = re.compile(r"(субтитр|подпис|продолжение следует|спасибо за просмотр|редактор|корректор|"
                   r"dimatorzok|amara|ставьте лайк|до новых встреч|дякую за перегляд|звучит музыка|"
                   r"звучить музика|играет музыка|музыкальная заставка|^\W*$)", re.I)
norm = lambda s: re.sub(r"[^\w]+", " ", s.lower()).strip()


def main(paths):
    pool, dropped = [], 0
    for p in paths:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        name = d.get("pass") or Path(p).stem
        for s in d["segments"]:
            if HALLU.search(s["text"].strip()):
                dropped += 1
                continue
            s = dict(s)
            s.setdefault("pass", name)       # a file may label its own segments (targeted runs do)
            s.pop("lang", None)
            pool.append(s)
    pool.sort(key=lambda s: (s["start"], s["end"]))

    kept = []
    for s in pool:
        dup = None
        for k in reversed(kept[-12:]):
            ov = min(s["end"], k["end"]) - max(s["start"], k["start"])
            short = max(min(s["end"] - s["start"], k["end"] - k["start"]), 0.3)
            if ov / short > 0.5 and SequenceMatcher(None, norm(s["text"]), norm(k["text"])).ratio() > 0.55:
                dup = k
                break
        if dup is None:
            kept.append(s)
        elif (len(s["words"]), s["avg_logprob"]) > (len(dup["words"]), dup["avg_logprob"]):
            kept[kept.index(dup)] = s
    kept.sort(key=lambda s: (s["start"], s["end"]))
    out = {"model": "large-v3", "passes": [Path(p).name for p in paths], "segments": kept}
    (HERE / "whisper.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    by = {}
    for s in kept:
        by[s["pass"]] = by.get(s["pass"], 0) + 1
    print(f"{len(pool)} segments pooled, {dropped} hallucinations dropped, {len(kept)} kept after dedup: {by}")
    print(f"covers {sum(s['end'] - s['start'] for s in kept) / 60:.1f} min of speech (with overlaps)")


if __name__ == "__main__":
    main(sys.argv[1:])
