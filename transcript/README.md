# transcript/ — timing for transcript.html

`transcript.html` shows the edited English transcript alone, synced to
`cherven.mp3`. Nothing in this folder is served (see `.vercelignore`); it is
the material and tooling that produced the timing embedded in that page.

## Files

| file | what |
|---|---|
| `source.txt` | the edited transcript exactly as supplied — **the source of truth for the words** |
| `parse.py` | `source.txt` → `turns.json`; refuses to write unless the text reassembles character for character |
| `turns.json` | ordered items: speech turns (speaker, text) and stage directions |
| `whisper.json` | Whisper large-v3 over the mp3: Russian/Ukrainian segments with word timestamps |
| `align.py` | first-pass timing by cross-lingual matching → `timing_auto.json` |
| `timing.json` | **final timing**, reviewed — one entry per item, with confidence and evidence |
| `build.py` | `turns.json` + `timing.json` → the `TURNS` array inside `transcript.html` |

## To change the words

Edit `source.txt`, then:

```
python3 transcript/parse.py
python3 transcript/build.py
```

`build.py` matches timing to items by index. Fixing a typo or rewording a line
keeps every index, so nothing else changes. **Adding, removing or reordering a
line shifts the indices after it**, so `timing.json` must be redone for that
stretch — either by hand (each entry quotes the speech it was matched to, so
neighbours are easy to place) or by re-running the alignment.

## How the timing was made

The transcript arrived with no timecodes, but — unlike the one embedded in the
main wall — **in playback order**. That makes alignment a monotone matching
problem rather than a guess inside a cue window.

1. **Recognise the audio.** Whisper large-v3 (faster-whisper, int8, CPU) over
   the full 45:04, transcribe mode, per-segment language detection (the piece
   moves between Russian and Ukrainian), word timestamps, no VAD (quiet layered
   voices matter more than the occasional hallucination, which is filtered).
2. **Match automatically** (`align.py`). LaBSE embeds the English turns and
   windows of 1–6 Whisper segments into one cross-lingual space; a dynamic
   program assigns each turn a start segment, never moving backwards, maximising
   total similarity.
3. **Read it independently.** Agents read Whisper's original-language text
   against the English, one stretch of the piece each, and timed every line
   from the word timestamps, quoting the speech they matched.
4. **Adjudicate disagreements.** Where the two methods differed by more than a
   few seconds, a separate reviewer tried to refute both claims against the
   recognised speech and kept whichever survived.
5. **Check the whole.** Playback order enforced; the final timeline read once
   more end to end for anything implausible.

Results are summarised in the commit that introduced the page.

## Limits

- The audio is layered — several recordings at once — so Whisper misses quiet
  voices and sometimes merges speakers. Lines with no recognisable speech are
  marked `low` in `timing.json` and placed by text length between confident
  neighbours. They keep their order; their exact second is an estimate.
- Starts are accurate to about a second where confident. Within a long turn the
  page scrolls linearly through the text; that is a reading aid, not word sync.
- If the room's sound chain adds latency (Bluetooth, some AV processors), set
  the **Sync offset** slider on the page rather than editing timings.
