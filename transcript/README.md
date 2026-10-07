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
| `whisper.json` | pooled Whisper large-v3 recognition of the whole piece, word timestamps, `pass` per segment |
| `merge_asr.py` | pools recognition passes into `whisper.json`, dropping hallucinations and duplicate hearings |
| `align.py` | first-pass timing by cross-lingual matching → `timing_auto.json` |
| `review/` | the review outcomes: readers + adjudicators, the gap round, the skeptic pass |
| `verified_overrides.json` | results of unprompted re-decodes; applied last, so a re-merge can't undo them |
| `merge_review.py` | matcher + review + overrides → `timing.json`, enforcing playback order |
| `audit_evidence.py` | checks every confident timing against saved recognition |
| `timing.json` | **final timing** — per line: start, end, confidence, method, evidence, notes |
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

1. **Recognise the audio** (`whisper.json`). Whisper large-v3 (faster-whisper,
   int8, CPU). One pass on the plain mix heard only ~15 of 45 minutes: on music
   beds Whisper emits training-data subtitle credits («Субтитры сделал
   DimaTorzok») instead of decoding. So several passes that fail differently
   are pooled: the plain mix; **Demucs-isolated vocals**; VAD-gated and
   short-window focused decodes over the weak stretches; and unprompted
   re-decodes made during verification. `merge_asr.py` drops hallucinations
   and folds duplicate hearings. 483 segments, ~29 minutes of speech.
2. **Match automatically** (`align.py` → `timing_auto.json`). LaBSE embeds the
   English turns and windows of 1–6 Whisper segments into one cross-lingual
   space; a dynamic program assigns each turn a start, never moving backwards.
   It anchored 88 of 159 turns, but tends to latch onto the *middle* of a long
   turn — its best-matching window — rather than its start.
3. **Read it.** Eight reviewers read Whisper's Russian/Ukrainian against the
   English, one stretch each, timing every line from word timestamps and
   quoting the speech matched. Where reader and matcher disagreed, an
   adjudicator tried to refute both (36 disputes, settled on quoted evidence).
4. **Second round on the gaps.** Lines still unmatched were re-examined with the
   focused recognition. No new speech matches; sung and chanted passages were
   placed by sound instead (energy and pitch onsets in the vocal stem).
5. **Verify.** Some reviewers had used *prompted* decodes, which can echo their
   prompt. Every confident claim was audited (`audit_evidence.py`) and every
   claim not found in saved recognition was re-decoded unprompted in the
   reviewer's stated window; failures were lowered
   (`verified_overrides.json`). Finally 41 single-source claims went to
   skeptics: 26 upheld, 7 adjusted, 8 refuted.

Result: of 159 turns, **83 high, 15 medium** — every one reproducible from
saved unprompted recognition — and **61 low**. A low line is still pinned
between confident neighbours: median bracket 9 s, 43 of 61 within 30 s. The 18
in wider brackets are nearly all sung or liturgical (the Easter troparion,
"Lord, have mercy", the commander's flag order under the anthem, Sasha's
lullaby) and were placed by sound.

To rebuild from the saved data:

```
python3 transcript/merge_review.py transcript/review/round1.json \
        transcript/review/round2_gaps.json transcript/review/skeptic.json   # → timing.json
python3 transcript/audit_evidence.py                                         # confident ⇒ reproducible
python3 transcript/build.py                                                  # → transcript.html
```

`timing.json` carries, per line, the method that decided it, the recognised
speech it rests on, and any adjudication, skeptic or verification note — so a
doubtful line can be judged without re-running anything.

## Limits

- The audio is layered. Children's voices under adult speech (Hek, Frania,
  Platon), the factory meeting, and anything sung are largely unrecognisable;
  those lines are `low`. They keep their order; their exact second is an
  estimate.
- Starts are good to about a second where confident. Within a long turn the
  page scrolls linearly through the text — a reading aid, not word sync. The
  prayer is the exception: timed line by line from the recitation.
- If the room's sound chain adds latency (Bluetooth, some AV processors), set
  the **Sync offset** slider on the page rather than editing timings.

## Video

`render_video.js` renders the page to video frame by frame on a virtual clock
(`performance.now` and `requestAnimationFrame` replaced, piece time set through
a hook added to a served copy), so picture and sound line up exactly — a
real-time screen recording drops frames and drifts. It records the cinema view,
subtitles with cue cards, at the page's default settings (`QUERY='?mode=scroll'`
for the scrolling column). **3840×2160**, 25 fps: the layout is the page at
1920×1080 drawn at two device pixels per CSS pixel (`SCALE`, default 2), so
the composition is unchanged and every glyph has twice the detail — the 1080p
render looked soft once a large or Retina screen upscaled it. Lossless PNG
frames into x264, `-preset slow -crf 12 -tune stillimage`. A frame whose
on-screen state (subtitle and cue elements, body classes) matches the one
before reuses its screenshot; a test with and without that gave identical
frames, and it draws about a quarter of them. Run segments in parallel (each starts 6 s early so anything in motion
has settled by its first kept frame), then join and add the audio:

```
for seg in "0 676.24" "676.24 1352.48" "1352.48 2028.72" "2028.72 2704.92"; do
  set -- $seg; node transcript/render_video.js $1 $2 seg_$1.mp4 &
done; wait
ls seg_*.mp4 | sort -t_ -k2 -g | sed "s/.*/file '&'/" > segs.txt
ffmpeg -f concat -safe 0 -i segs.txt -i cherven.wav -map 0:v -map 1:a \
       -c copy -movflags +faststart Cherven-transcript.mov
```

**Settings and HD in one pass.** `SETTINGS` takes the panel's values as JSON
and `OUT=hd` encodes 1920×1080 straight from the 2× frames (lanczos, High
4.1, BT.709) — sharper than scaling a compressed 4K file. The October 2026
festival render, white on black:

```
SCALE=2 OUT=hd QUERY='?mode=subs&cues=1&invert=1' \
SETTINGS='{"offset":0,"linger":3,"subsize":52,"subpos":9,"submeasure":34,"cuesize":42,"cuelinger":8}' \
node transcript/render_video.js T0 T1 seg.mp4
```

**For a player that cannot take 4K**, make HD from the 4K render rather
than rendering at 1080p: each output pixel then averages four drawn ones, so
the type is cleaner than drawing it at 1080p.

```
ffmpeg -i video-4k.mp4 -vf "scale=1920:1080:flags=lanczos+accurate_rnd+full_chroma_int" \
       -c:v libx264 -preset slow -crf 10 -tune stillimage -profile:v high -level 4.1 \
       -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_primaries bt709 \
       -color_trc bt709 -movflags +faststart video-hd.mp4
```

High profile, level 4.1 and BT.709 tags are what hardware players expect of
1080p25; white sits at video-range 235, as it should.

**The audio is copied, never re-encoded** (`-c copy`). With the lossless master
(`cherven.wav`, 24-bit 44.1 kHz, the `lossless-audio` release) the result is
a MOV carrying the WAV's PCM untouched; MOV, because MP4 has no standard place
for PCM. The WAV and `cherven.mp3` are the same edit sample for sample
(cross-correlated at five points: zero offset, r ≥ 0.999), so the timing
measured on the MP3 holds. **When an `.mp4` is required** (H.264 MP4 is
the usual festival spec), MP4 has no standard place for PCM, so the WAV goes
in as ALAC, Apple Lossless: `-c:v copy -c:a alac`, about 500 MB at 4K.
Lossless — the decoded 24-bit samples hash the same as the WAV's
(`-c:a pcm_s24le -f md5`). For a small file, `-i cherven.mp3` and an `.mp4`
name instead copies the MP3 frames as they are. The first export re-encoded
to AAC, a second lossy generation, and was redone. No `-shortest`, which could
drop the last audio frame. Never join or convert in QuickTime's "Export As": it
re-encodes.


