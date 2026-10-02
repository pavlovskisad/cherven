"""First-pass timing: match each English turn to the speech in the audio.

    python3 transcript/align.py   turns.json + whisper.json -> timing_auto.json

whisper.json is Whisper large-v3 run over cherven.mp3 in transcribe mode
(Russian and Ukrainian, per-segment language detection, word timestamps).
The English transcript is a translation of that speech, so the match is
cross-lingual: LaBSE embeds both sides into one space built for exactly this
(finding translation pairs), and each turn is scored against windows of 1-6
consecutive Whisper segments.

The transcript is in playback order, so the assignment is monotone: a dynamic
program picks one start segment per turn, never moving backwards, maximising
total similarity. Monotonicity is what makes short lines ("Home!", "Damn.")
land correctly — on their own they match half the piece; between two anchored
neighbours they have one plausible place.

Confidence is graded on the match score. Turns below the floor keep their
order but get their time interpolated between confident neighbours by text
length, and are flagged for review. Stage directions carry no speech; they sit
between their neighbours.

This pass is a proposal. transcript/README.md describes the review that
reconciled it against an independent reading of the Whisper text.
"""
import json, re
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
MAX_SEGS, MAX_SPAN, MAX_GAP = 6, 75.0, 8.0
HIGH, MED = 0.55, 0.42

# Whisper's well-known hallucinations on music and silence, mostly YouTube
# subtitle credits from its training data. Matched, dropped, counted.
HALLU = re.compile(r"(субтитр|подпис|продолжение следует|спасибо за просмотр|редактор|корректор|"
                   r"dimatorzok|amara|ставьте лайк|до новых встреч|дякую за перегляд)", re.I)


def load_segments():
    raw = json.loads((HERE / "whisper.json").read_text(encoding="utf-8"))["segments"]
    segs, dropped, prev = [], 0, None
    for s in raw:
        t = s["text"].strip()
        if not t or HALLU.search(t) or t == prev:
            dropped += 1
            continue
        segs.append(s)
        prev = t
    return segs, dropped


def windows(segs):
    out = []
    for j in range(len(segs)):
        txt, end = [], None
        for k in range(MAX_SEGS):
            if j + k >= len(segs):
                break
            s = segs[j + k]
            if k and (s["start"] - segs[j + k - 1]["end"] > MAX_GAP or s["end"] - segs[j]["start"] > MAX_SPAN):
                break
            txt.append(s["text"].strip())
            out.append((j, k + 1, " ".join(txt)))
    return out


def main():
    from sentence_transformers import SentenceTransformer
    items = json.loads((HERE / "turns.json").read_text(encoding="utf-8"))
    segs, dropped = load_segments()
    wins = windows(segs)
    model = SentenceTransformer("sentence-transformers/LaBSE", device="cpu")
    turns = [it for it in items if it["kind"] == "turn"]
    E_t = model.encode([t["text"].replace("\n", " ") for t in turns], batch_size=32,
                       normalize_embeddings=True, show_progress_bar=False)
    E_w = model.encode([w[2] for w in wins], batch_size=64,
                       normalize_embeddings=True, show_progress_bar=False)
    sim = E_t @ E_w.T                                   # turns x windows

    M = len(segs)
    S = np.full((len(turns), M), -1.0)
    K = np.zeros((len(turns), M), dtype=int)
    for w, (j, k, _) in enumerate(wins):
        better = sim[:, w] > S[:, j]
        S[better, j] = sim[better, w]
        K[better, j] = k

    # monotone max-sum assignment: best[i, j] = S[i, j] + max_{j' <= j} best[i-1, j']
    N = len(turns)
    best = np.zeros((N, M))
    arg = np.zeros((N, M), dtype=int)
    best[0] = S[0]
    for i in range(1, N):
        run_v, run_j = -1e9, 0
        for j in range(M):
            if best[i - 1, j] > run_v:
                run_v, run_j = best[i - 1, j], j
            best[i, j] = S[i, j] + run_v
            arg[i, j] = run_j
    js = [int(np.argmax(best[-1]))]
    for i in range(N - 1, 0, -1):
        js.append(int(arg[i, js[-1]]))
    js.reverse()

    prop = []
    for t, j in zip(turns, js):
        i = turns.index(t)
        k = int(K[i, j])
        sc = float(S[i, j])
        conf = "high" if sc >= HIGH else "medium" if sc >= MED else "low"
        prop.append({"i": t["i"], "j": j, "k": k, "score": round(sc, 3), "conf": conf,
                     "start": segs[j]["start"], "end": segs[j + k - 1]["end"],
                     "asr": " ".join(s["text"].strip() for s in segs[j:j + k])})

    # Low-confidence turns: keep order, place by text length between the
    # nearest confident neighbours on either side.
    anchors = [p for p in prop if p["conf"] != "low"]
    for n, p in enumerate(prop):
        if p["conf"] != "low":
            continue
        a = next((q for q in reversed(prop[:n]) if q["conf"] != "low"), None)
        b = next((q for q in prop[n + 1:] if q["conf"] != "low"), None)
        lo = a["end"] if a else 0.0
        hi = b["start"] if b else 2704.9
        run = [q for q in prop[(prop.index(a) + 1 if a else 0):(prop.index(b) if b else len(prop))]]
        lens = [len(next(t for t in turns if t["i"] == q["i"])["text"]) for q in run]
        tot = sum(lens) or 1
        acc = sum(lens[:run.index(p)])
        span = max(hi - lo, 0.0)
        p["start"] = round(lo + span * acc / tot, 2)
        p["end"] = round(lo + span * (acc + lens[run.index(p)]) / tot, 2)
        p["interpolated"] = True

    # Starts must not run backwards in transcript order.
    for n in range(1, len(prop)):
        if prop[n]["start"] < prop[n - 1]["start"]:
            prop[n]["start"] = prop[n - 1]["start"]
            prop[n]["end"] = max(prop[n]["end"], prop[n]["start"])

    by_i = {p["i"]: p for p in prop}
    out = []
    for n, it in enumerate(items):
        if it["kind"] == "turn":
            out.append(by_i[it["i"]])
            continue
        prev = next((by_i[x["i"]] for x in reversed(items[:n]) if x["kind"] == "turn"), None)
        nxt = next((by_i[x["i"]] for x in items[n + 1:] if x["kind"] == "turn"), None)
        s = prev["start"] if prev else 0.0
        if prev and nxt and nxt["start"] > prev["end"]:
            s = prev["end"]
        if nxt:
            s = min(s, nxt["start"])     # a direction never runs ahead of the line after it
        e = nxt["start"] if nxt else min(s + 10, 2704.9)
        out.append({"i": it["i"], "start": round(s, 2), "end": round(max(e, s), 2), "conf": "direction"})

    (HERE / "timing_auto.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    c = {k: sum(1 for p in prop if p["conf"] == k) for k in ("high", "medium", "low")}
    print(f"{len(segs)} segments ({dropped} hallucinated or repeated, dropped), {len(wins)} windows")
    print(f"turns: {c['high']} high, {c['medium']} medium, {c['low']} low (interpolated)")


if __name__ == "__main__":
    main()
