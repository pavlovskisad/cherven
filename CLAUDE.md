# Cherven — projected titles

A single-file web display for **Cherven**, an audio documentary by Ian Spektor
(Kyiv Dispatch). It projects the work's cue sheet and transcript onto a white
gallery wall, synced to the audio, as black text on a white field.

Running time 45:04. 53 cues. 93 speech turns.

---

## 1. What ships

```
index.html        the wall: cue sheet + speech, markup, CSS, JS, all data embedded
transcript.html   the edited transcript alone, synced to the audio — see §11
cherven.mp3       the audio, the master byte for byte (see §7)
vercel.json       static config; cleanUrls, so the second page is /transcript
.vercelignore     keeps transcript/ (tooling and intermediate data) off the site
transcript/       how transcript.html's timing was made, and how to remake it
CLAUDE.md         this file
```

No build step for the site, no dependencies, no framework. Each page is one
self-contained file. Keep it that way unless there is a reason not to.
`transcript/` holds Python tooling that writes data *into* transcript.html; the
deployed page never depends on it.

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

**Upgrade path when someone wants real sync:** most of it now exists. The
second page (§11) is timed from the audio itself, and `transcript/whisper.json`
holds pooled Whisper large-v3 recognition of the whole piece with word
timestamps. The wall's own transcript is a *different, older* text (93 turns,
not in playback order), so its turns cannot simply borrow §11's times; to sync
the wall, align its `turns[].text` against `whisper.json` the same way —
`transcript/README.md` describes the method and what failed. Regenerate
`turns[].at` only; nothing else in the wall changes. Diarization was not needed:
playback order plus recognised speech placed the edited transcript without it.

---

## 5. Layout engine — read this before touching `place()`

Four phases, in order. Runs only when the live set or the visible turn count
changes, not every frame.

1. **Measure.** One pass with everything open: `headH`, `noteH`, per-turn
   heights, and `chrome` (the rule and padding on the `.talk` container, which
   is not part of any individual turn's height).
2. **Allocate.** Titles are the fixed cost and never drop. The remaining budget
   is spent in order of `env` (current weight): **any note not yet seen this
   pass** first, then newest speech, then the remaining notes. Within a cue,
   older turns fall away before newer ones.

   The unseen-note tier exists because weight alone starved three cues
   completely. Stepping the whole piece at 1920×1080, the notes for cues 8, 23
   and 24 were never shown once: they are short or speechless cues sitting in
   the 6:00–10:00 crowd, so they lost every pass. Ranking an unseen note above
   speech fixes that and costs speech nothing measurable — turn-seconds went
   *up* slightly (13445 → 13482), because seating a note early changes what the
   retry loop manages to pack. It applies at most once per cue per pass.

   `seen` is set on render, not inside `allocate()`, which retries. It is
   cleared whenever time moves backwards, so a looping installation re-guarantees
   every note on each play rather than only for whoever watched the first one.
   Verified: all 53 notes appear on both passes, at opacity ≥ 0.5.
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
- The panel stays in Helvetica so the interface never reads as part of the work.
  The gate is Helvetica too, with one deliberate exception: its own word, `Let’s
  go` — cue 1, the first line of the piece — is set in Times at `var(--size)`,
  underlined, no box. The entry screen is the work beginning, not a button in
  front of it, so it tracks the type-size slider along with the wall. Everything
  else the gate can say (the file picker, the failed-load message) is apparatus
  and stays Helvetica.

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

**The audio is in the repo: `cherven.mp3` is the master, unchanged** — 68 MB,
211 kbps VBR, sha256 `8fefd409…`, identical to the asset on the `audio`
release. It was not re-encoded: the audio is the work, and a second lossy
generation was judged a poor trade for 26 MB. Keep it that way; if size ever
forces a re-encode, encode once from this file and never from a copy.

**It must be served same-origin, or from any host that sends a real audio
type.** It was first hotlinked from the GitHub release. That worked on every
desktop browser and failed on every iOS one with MediaError code 4: the release
CDN sends `application/octet-stream` with `Content-Disposition: attachment`,
and iOS hands media to AVFoundation, which trusts the declared type rather than
sniffing the bytes. Desktop engines sniff, so the fault is invisible until it
reaches a phone. Vercel serves `.mp3` as `audio/mpeg`. Note that Linux WebKit
(GStreamer) also sniffs, so it is **not** a stand-in for iOS on this point.

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

Every key above needs a keyboard, and the panel needs one to open at all, so a
touch screen had no way into fullscreen. There is a **fullscreen button** in the
bottom right on the same 2s fade as the cursor: it appears on mouse move or
touch and is off the wall while the piece runs. It sits above the gate, so the
room can be set before starting, and a tap on it will not start the piece. It
toggles, since a touch screen has no `Escape`. Where the Fullscreen API is
missing the script removes the button instead of leaving a dead control —
iPhone Safari has no element fullscreen at all, and the way to lose the browser
chrome there is Add to Home Screen.

The **preview scrub** drives the display with no audio loaded at all, which is
how to tune the wall in silence before the room is ready.

Sliders: type size, note size, speech size, line spacing, columns, margin, hold,
decay share, decay curve, dormant weight, elapsed weight, edge feather, shrink
dormant.

### Shrink dormant — scale instead of drop

`Shrink dormant to` (default 1, off) is the alternative to dropping content when
the screen is over capacity. Each block is scaled by its own weight before the
measuring pass: full weight sets at full size, and the further into its decay a
cue is, the smaller it sets, down to the floor. Everything inside `.row` is
em-relative, so a single `font-size` on the row moves title, note and speech
together — **the ratio between the three tiers is preserved exactly**, which is
the point. Nothing else in `place()` changes; the packer just sees smaller
heights.

Stepping the whole piece at 1920×1080:

| floor | note-seconds | turn-seconds | notes dropped | smallest type |
|---|---|---|---|---|
| 1.00 (off) | 9559 | 13342 | 4020 | 22.0px |
| 0.90 | 11394 | 13699 | 2185 | 19.8px |
| 0.80 | 12674 | 13825 | 905 | 17.6px |
| 0.70 | 12912 | 14060 | 667 | 15.4px |
| 0.60 | 13069 | 14105 | 510 | 13.2px |

0.8 is the knee: a third more note-seconds and 77% fewer dropped notes, with
the smallest type still at 17.6px. Below that the returns flatten while the
type keeps shrinking, and 13px on a wall is not a reading size.

**It is not monotonic per moment.** At 21:33 the floor at 0.8 showed fewer notes
than off, because the freed space went to speech: a note is one large
indivisible block while turns are small and divisible, so under pressure many
small turns outcompete a single note. Aggregate is much better; any given
second may not be. Set it in the room against the actual throw.

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
5. **Listen through `/transcript` once** with `timing.json` open, at the
   low-confidence lines especially (children, the factory meeting, the Easter
   and funeral liturgy, the lullaby). A human ear settles in seconds what
   recognition could not; nudge `start` in `timing.json` and rebuild.
6. Possible typos in `transcript/source.txt`, left verbatim because the words
   are the artist's: "Fleet5" (the wall's older text has "Fleet51"), "Hektor"
   (elsewhere "Hek"), "Captain Buger". Confirm, then edit and rebuild.

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

---

## 11. The transcript page — `transcript.html`, served at `/transcript`

The **edited** English transcript alone, synced to the same `cherven.mp3`. It
is a separate text from the one embedded in the wall: edited by the artist,
paraphrased in places, some phrases absent, and — crucially — **in playback
order**. `transcript/source.txt` holds it exactly as supplied and is the source
of truth for the words. 159 speech turns, 11 stage directions, 38 speakers.
Timing: **83 high, 15 medium, 61 low**; the low lines sit in a median 9 s
bracket between confident neighbours, the widest being sung or liturgical.

### Display

Same physical rules as the wall (§2): white field, black Times, live sliders,
the same gate (`Let’s go`), the same fullscreen button and loop robustness. One
column moves under a fixed **reading line**; the line being spoken sits on it at
full ink, spoken lines fall to the *spoken weight*, upcoming lines are faint.
A long turn travels through the reading line linearly in time (a reading aid,
not word sync). The **prayer is timed line by line** — 35 verse lines, each lit
as it is recited — because it was recognised well enough to allow it. Below
~24em of measure the column sets ragged right (§6, justification needs measure).
Tap a line to jump to it. `Sync offset` compensates for a delaying sound chain.

### Timing — read before trusting or editing it

Every line's time came from the audio, not from cue windows. `timing.json`
records per line: start, end, confidence, method and the recognised speech it
was matched to. Confidence means:

- **high / medium** — matched to recognised speech that is **reproducible from
  saved, unprompted recognition** (`whisper.json`). Starts good to ~1–2 s.
- **low** — no recognisable speech (children, voices under music, sung
  liturgy). Kept in order between confident neighbours, placed by text length
  or by the sound itself (energy/pitch onsets). Its exact second is an estimate.

Three things about the method are not obvious and cost time to learn:

1. **Whisper on the plain mix hears only about a third of the speech.** Music
   beds make it emit training-data subtitle credits («Субтитры сделал
   DimaTorzok») instead of decoding; `hallucination_silence_threshold` then
   skips ahead and discards real speech. Recall came from pooling passes that
   fail differently: the plain mix, **Demucs-isolated vocals**, VAD-gated and
   short-window focused decodes. Each hears lines the others miss.
2. **Prompted decodes are not evidence.** A decode given the expected words as
   `initial_prompt` can echo them. Some reviewers used them. Every confident
   claim is therefore audited against saved recognition, and each one not
   found there was re-decoded unprompted *in the reviewer's own window* —
   Whisper is window-sensitive, so a different window failing proves nothing.
   Outcomes are in `transcript/verified_overrides.json`, applied last.
3. **Memory.** Shell-launched processes share a ~8 GB cgroup cap; two
   concurrent large-v3 decodes (4 GB each) get OOM-killed. Run decodes one at a
   time, one process per job (CTranslate2 keeps what it allocates).

`transcript/README.md` has the files, the commands and how to change words
without redoing the timing.
