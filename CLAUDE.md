# Cherven — projected titles

A single-file web display for **Cherven**, an audio documentary by Ian Spektor
(Kyiv Dispatch). It projects the work's cue sheet and transcript onto a white
gallery wall, synced to the audio, as black text on a white field.

Running time 45:04. 53 cues. 93 speech turns.

---

## 1. What ships

```
index.html        the entire display: markup, CSS, JS, all data embedded
cherven.mp3       the audio (NOT in this repo yet — see §7)
vercel.json       static config
CLAUDE.md         this file
```

No build step, no dependencies, no framework. One file. Keep it that way unless
there is a reason not to.

---

## 2. The physical situation, which drives every decision

Projector throwing onto a white wall in a lit room.

**A projector cannot emit black.** Black glyphs on a white wall are produced by
lighting the surround and leaving the letters unlit. So the file is a pure white
field with pure black text. There is no alpha channel and there should not be
one. Do not "add transparency support" — it does nothing here.

Consequences to preserve:

- Contrast is capped by ambient light. Text reads as very dark grey, never true
  black. DLP leaks less into blacks than LCD.
- The projected rectangle shows its own edge on the wall. The **feather**
  control ramps the image to black at the borders so the frame dissolves. It is
  two `mix-blend-mode: multiply` overlays. Default 0 (off) because the correct
  value depends on throw distance and must be set on site.
- Every control that affects appearance is a live slider for this reason. The
  room decides, not the code. Do not bake in "better defaults" from a laptop.

---

## 3. Data model

Everything is embedded in `index.html` as a `CUES` array. One object per cue:

```js
{
  n: 34,                        // cue number, 1..53, source ordering
  title: "Marvel car",
  desc:  "Liokha, my stepfather, shows us …  Summer 2023",
  date:  "Summer 2023",         // parsed from the tail of desc
  start: 1231, end: 1383,       // seconds
  turns: [                      // may be absent or empty
    { spk: "Liokha", text: "Yeah, yeah — that's where we were…", at: 1234.6 }
  ]
}
```

### Known data problems — do not silently "fix"

1. **Ten cues share a start of exactly 2:01**: numbers 5, 6, 13, 14, 15, 16, 17,
   18, 19, 20. The list otherwise climbs in start order, and 13–20 sit between
   neighbours starting at 4:44 and 6:27, so eight of them almost certainly lost
   their real in-points and were backfilled with one value. **Ian needs to check
   the session.** Until then the display is correct and the data is wrong.
2. **Cue 53 ended at 45:05**, one second past the audio. Clamped to 45:04 in the
   data. Real fix belongs upstream.
3. Cue 40's timestamp sits after the date in the source document rather than in
   the heading. Already parsed correctly.

### Cue structure — the thing that surprises people

This is **not** a tracklist. Cues overlap heavily.

- Mean 6.9 cues sound at once, median 6, **peak 14 at 2:01**.
- Lengths run 7s (cue 1) to 37:43 (cue 42, which sits under almost the whole
  piece).
- 31 of 53 cues carry speech; 22 are pure sound.

Any change that assumes one-cue-at-a-time will break immediately.

---

## 4. Transcript timing — accuracy and the upgrade path

The transcript arrived with **no timecodes**, in English, with speaker names,
and **not in playback order** (11% of anchored pairs invert, because the
transcriber had to flatten ~7 simultaneous layers into one column).

Current placement method:

1. Match each speaker name against the names in the cue descriptions.
   41% of turns anchor to exactly one cue; 52% have several candidates; 8%
   (mostly Ian, and background chatter) have none.
2. Walk the transcript forward, taking the earliest candidate that does not move
   backwards. Turns with no candidate inherit the window already in play —
   Ian is always talking to someone already named.
3. Distribute turns inside their window by cumulative word count, across the
   first 88% of the window.

**Accuracy is bounded by the window, median 168s.** A line can land ~30s from
its real moment. It will never appear under the wrong recording, which is the
error that would read as broken. This is accepted and deliberate.

**Upgrade path when someone wants real sync:** run Whisper on the mp3 with word
timestamps and speaker diarization (WhisperX + pyannote), which yields actual
Ukrainian/Russian segments with times, then align the English turns onto those
segments **using the cue windows as constraints**. That turns one 45-minute
alignment problem into 31 small ones. Regenerate `turns[].at` only; nothing else
in the pipeline changes.

---

## 5. Layout engine — read this before touching `place()`

Four phases, in order. Runs only when the live set or the visible turn count
changes, not every frame.

1. **Measure.** One pass with everything open: `headH`, `noteH`, per-turn
   heights, and `chrome` (the rule and padding on the `.talk` container, which
   is not part of any individual turn's height).
2. **Allocate.** Titles are the fixed cost and never drop. The remaining budget
   is spent in order of `env` (current weight): newest speech first, then notes.
   Within a cue, older turns fall away before newer ones.
3. **Pack.** Walk cues in order, accumulating height, break to the next column
   when full. No fixed addresses — cues keep order, not position.
4. **Retry.** If the pack spills, re-allocate with a smaller budget factor
   (0.97 stepping down by 0.08) until it fits.

### Invariant: measurement must stay honest

**Use `padding`, never `margin`, on anything inside a `.row`.** `offsetHeight`
includes padding and border under `box-sizing: border-box`; it does not include
margin. Every margin added inside a row is space the packer cannot see, and the
column silently overflows. `chrome` exists precisely because the `.talk` rule
sits on a container rather than on the turns.

### Why the space runs out

Measured at 1920×1080, Times 22px, two columns, notes plus speech:

| constraint | over capacity |
|---|---|
| whole screen, free packing | 24% of the piece |
| at least one column over (fixed split) | 70% |
| column A alone, cues 1–27 | 20% |
| column B alone, cues 28–53 | 50% |

Median demand is 68% of the screen; peak is 164% at 21:33. The old fixed column
split by cue number was the main waste — the funerals cluster in cues 28–53, so
that column peaked at 327% while the other sat half empty. Flow packing fixed
that. Roughly a quarter of the running time is a genuine shortage that only
priority solves. Pressure points: 3:00, 6:00, 9:00, 18:00, 21:00, 30:00.
Everything after 33:00 runs under 60%.

---

## 6. Typography spec

Modelled on a Ukrainian Ministry of Defence contract form. Reference the
parameters, not the decoration.

- **Times New Roman**, falling back to Times then Liberation Serif (metrically
  identical, matches on Linux playback machines).
- Three tiers: **titles** bold at full size; **notes** at 0.78 (your apparatus);
  **speech** at full size (the record). Notes are deliberately quieter than
  voices.
- Numbering as `1.` `42.`, left-aligned in a hanging indent, black, body size.
  Not a grey gutter figure.
- Notes: justified, `hyphens: auto`, 2.2em first-line indent, full measure.
- Speech: one indent deeper, justified, speaker name bold, hairline rule above
  the block at 16% black.
- Leading 1.3, on a slider. Zero letter-spacing (the negative tracking in the
  code is for the Helvetica toggle only).
- The panel and gate stay in Helvetica so the interface never reads as part of
  the work.

**Justification needs measure.** At three or four columns the notes get narrow
enough to open rivers. If more columns are wanted, drop note size first.

### Opacity envelope

Every cue's opacity is computed per frame, not handed to a CSS transition, so it
tracks position inside the cue and the scrub reflects it.

- Attack 0.25s fixed, just enough to avoid flicker.
- Decay across a share of the cue's own window (`fade`, default 1 = the whole
  window), shaped by `curve` (default 1.6). Same silhouette at every scale.
- **Short cues get a reading window.** A cue whose note needs more time than its
  sound gets `min(2 + chars/15, hold)` seconds. Only cue 1 currently qualifies:
  7s of sound, 262 characters, 19.5s window. Its text outlives its recording by
  design. `hold = 0` disables this.

---

## 7. Deployment

Static. No server. `vercel.json` sets long cache on the audio.

**The audio is not in the repo yet.** 45 minutes at 210 kbps is ~71 MB. Options,
best first:

1. Re-encode for the web and commit it:
   ```
   ffmpeg -i cherven.mp3 -c:a libmp3lame -b:a 128k cherven.mp3   # ~43 MB
   ```
2. Opus in WebM is roughly half that again at equal quality and is fine for a
   controlled kiosk (Chrome, Safari 15+). Change `CONFIG.AUDIO` to match.
3. Vercel Blob or any CDN if the repo should stay light. `CONFIG.AUDIO` takes an
   absolute URL.

Keep the master. Do not re-encode from an already lossy intermediate more than
once.

### Config

Top of the script block in `index.html`:

```js
const CONFIG = {
  AUDIO: './cherven.mp3',   // null falls back to the file picker
  LOOP: true,               // installations run all day
  START_AT: 0
};
```

### One click is unavoidable

Browsers block autoplay with sound without a user gesture. The gate screen is
that gesture and should not be engineered away. For an unattended kiosk:

```
chromium --kiosk --autoplay-policy=no-user-gesture-required \
         --disable-features=Translate --incognito https://<deploy>/
```

That flag genuinely removes the click. Nothing in the page can.

### Robustness already in place

- The update loop is wrapped in `try/catch`. A layout error costs one frame, not
  the session. Errors log to console, capped at 5.
- A 250ms timer picks up whenever `requestAnimationFrame` is throttled, which
  browsers do when the window is backgrounded. Without it, switching apps froze
  the wall.

Preserve both. They exist because the display stopped during testing.

---

## 8. Controls

Hidden by default; cursor auto-hides after 2s.

| key | |
|---|---|
| `C` | control panel |
| `F` | fullscreen |
| `Space` | play/pause |
| `1` `2` | flow packing / fixed register |
| `D` | notes |
| `T` | transcript |
| `←` `→` | seek 10s, with shift 60s |

The **preview scrub** drives the display with no audio loaded at all, which is
how to tune the wall in silence before the room is ready.

Sliders: type size, note size, speech size, line spacing, columns, margin, hold,
decay share, decay curve, dormant weight, elapsed weight, edge feather.

---

## 9. Open tasks

1. **Confirm the 2:01 block with Ian** and regenerate the cue data. This is the
   only outstanding correctness issue.
2. Decide whether the trailing date should be stripped from each note now that
   notes set as body text. On the reference form, dates live in captions and
   headers, never mid-sentence. The `date` field is already parsed out and there
   is a `Date in margin` toggle rendering it as a centred caption.
3. Lock the slider values in the room, then write them into the `:root` defaults
   so the deployed build opens correct with no panel visit.
4. Consider whether the panel should be removable from the production build, or
   just left behind the `C` key. Leaving it is probably right — a gallery
   technician will need it.

## 10. Things not to do

- Do not add an alpha channel or transparency. See §2.
- Do not add a fixed subtitle band at the bottom. Timing is window-accurate,
  ~±30s; a fixed strip promises real-time sync and reads as broken. Speech
  belongs nested inside its own cue.
- Do not assume one cue at a time. See §3.
- Do not use margins inside `.row`. See §5.
- Do not remove the gate. See §7.
- Do not "clean up" the overlapping cue data to make it tidy. The overlap is the
  piece.
