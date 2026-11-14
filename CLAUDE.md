# Cherven — projected titles

The projected titles for **Cherven**, an audio documentary by Ian Spektor
(Kyiv Dispatch). The home page plays the piece and shows the artist's edited
English transcript as **film subtitles**, synced to the audio, with the cue
sheet's **cards** above — **white on black** by default. It is projected in a
gallery and is also the public site, https://cherven.vercel.app.

Running time 45:04. 53 cues. 159 speech turns, 11 stage directions, 38
speakers.

The project began as "the wall": the cue sheet itself as projected titles,
black Times on white, with an older transcript. The page described here was
built beside it in October 2026, became the home page in November 2026, and
the wall was removed at the artist's request. See §10 for where it lives on.

---

## 1. What ships

```
index.html        the page: markup, CSS, JS, Inter, the timed transcript and the cue sheet, all embedded
transcript.html   forwards to index.html, keeping the query (old /transcript links, older launchers)
cherven.mp3       the audio, the master byte for byte (see §6)
vercel.json       static config; cleanUrls, so transcript.html is served at /transcript
.vercelignore     keeps transcript/, install/ and INSTALL.md off the site
transcript/       the cue sheet (cues.json), the transcript's source and timing, build and video tools
install/          the Mac kiosk launcher for the gallery laptop — see §6
INSTALL.md        the installation checklist for the venue
fonts/            Inter, the page's typeface (embedded in index.html), its licence
README.md         the short version
CLAUDE.md         this file
```

No build step for the site, no dependencies, no framework. The page is one
self-contained file. Keep it that way unless there is a reason not to.
`transcript/build.py` writes data *into* index.html; the deployed page never
depends on `transcript/`.

---

## 2. The physical situation, which drives every decision

A projector throwing onto a white wall in a lit room.

**A projector cannot emit black.** It can only light the wall or leave it
unlit. The page therefore has no alpha channel and should not have one; do not
"add transparency support", it does nothing here.

- **White on black** (the default, the artist's choice) is type made of
  projected light on the projector's own unlit grey. The type is bright and
  crisp; the "black" is never black, so the projected rectangle's edge and any
  spill show. DLP leaks less into blacks than LCD.
- **Black on white** (`I`, or `?invert=0`) is the opposite object: the letters
  are left unlit inside a lit field, so contrast is capped by ambient light and
  the type reads as very dark grey.
- The **edge feather** ramps the image to black at the borders so the frame
  dissolves into the wall. It is two `mix-blend-mode: multiply` overlays,
  default 0 (off), because the right value depends on throw distance and must
  be set on site.
- Every control that affects appearance is a live slider in the panel (`C`)
  for this reason. The room decides, not the code. Do not bake in "better
  defaults" from a laptop. (The defaults that ship are the sizes the artist set
  for the festival video, §4.)

---

## 3. The cue sheet — `transcript/cues.json`

The cue sheet is the artist's list of the recordings that make up the piece.
`transcript/cues.json` is its one copy; `build.py` copies it into index.html's
`CUES` array (number, title, description, start, end). Edit it there and
rebuild. One object per cue:

```js
{
  "n": 34,                       // cue number, 1..53, source ordering
  "title": "Marvel car",
  "desc": "Liokha, my stepdad, shows us …  Summer 2023",
  "date": "Summer 2023",         // parsed from the tail of desc (not used by the page)
  "start": 1231, "end": 1383     // seconds
}
```

### Known data problems — do not silently "fix"

1. **Ten cues share a start of exactly 2:01**: numbers 5, 6, 13, 14, 15, 16, 17,
   18, 19, 20. The list otherwise climbs in start order, and 13–20 sit between
   neighbours starting at 4:44 and 6:27, so eight of them almost certainly lost
   their real in-points and were backfilled with one value. **Ian needs to check
   the session.** Until then the display is correct and the data is wrong; the
   one-card queue (§4) makes them arrive up to ~2 min late.
2. **Cue 53 ended at 45:05**, one second past the audio. Clamped to 45:04 in the
   data. Real fix belongs upstream.
3. Cue 40's timestamp sat after the date in the source document rather than in
   the heading. Already parsed correctly.

### Cue structure — the thing that surprises people

This is **not** a tracklist. Cues overlap heavily: mean 6.9 sound at once,
median 6, **peak 14 at 2:01**. Lengths run 7 s (cue 1) to 37:43 (cue 42, under
almost the whole piece). 31 of 53 cues carry speech; 22 are pure sound. The
page still shows **one card at a time** (§4) — that is a presentation choice,
not a claim about the data. Do not "clean up" the overlap to make it tidy; the
overlap is the piece.

---

## 4. The page — `index.html`

### What it opens as

Always the same: **subtitles, cue cards, white on black**, with nothing on
screen but the piece — no buttons (the artist's call). The **gate** (`Let’s
go`, cue 1's own words, set in the page's type and underlined) is the one click
a browser needs before it will play sound (§6). The cursor hides after 2 s.

- A URL can ask for another view: `?mode=scroll|subs`, `&cues=0|1`,
  `&invert=0|1`, plus `&autostart=1` and `&audio=<file>` (§6).
- The panel buttons and the keys `S` (subtitles/scroll), `D` (cues) and `I`
  (colours) change the view **for the rest of the visit only, never saved**, so
  a stray key at the installation cannot leave the next visitor a different
  page. (These used to be remembered, under `cherven-transcript`; that key is no
  longer read.)
- The panel's sliders **are** saved (below), because they are the room's tuning.

### Subtitles — one at a time, as in a film

Only what is being said, low and centred. **One subtitle is on screen at a
time**, always at the same foot, and the next replaces it whole: nothing
stacks, moves or lingers elsewhere. Two earlier designs failed on the wall: a
stack from the foot (each new line pushed the others up; a glide only softened
it) and three fixed rows (lines appearing and leaving in three places at once —
"chaotic").

- Speeches are cut into sentence-sized pieces (≤ ~84 characters; long sentences
  at commas and dashes), and a turn's span is shared between its pieces by
  length.
- The schedule is planned for the whole piece, as a subtitler would with the
  script: words arriving before the subtitle on screen has had its reading time
  (1.2 s + 1 s per 14 characters, at least 1.8 s) join it if the result fits
  three lines — the same voice runs on in its line, a second voice gets a line
  of its own (a dialogue pair, both named) — but nothing goes up more than 3 s
  before it is said. Each subtitle stays at least 1 s.
- In a pause the last subtitle stays for **Linger** (default 3 s), then fades in
  1 s and the screen clears. History: 1.5 s + 6 s fade (too long), 0.5 + 1.5
  (everything vanished), 1.2 (still too short), then 3.
- Names show when the voice changes or a speech begins. Decided once, in the
  schedule: deciding per frame once made lines re-wrap under the reader.
- **The prayer shows one line at a time.** One soldier reads each line and the
  group repeats it (~4 s a line; line starts verified against loudness onsets
  in the WAV). A verse line holds while it is said and repeated and goes in
  0.3 s when the next lead begins; a lingering line had made the text read one
  line behind the voices. Its 35 line times are in `timing.json`.
- Stage directions span the sound they describe (the anthem-and-bugle one
  covers 168 s) but show only for a reading time, 3–6 s, at 0.78 size.
- Result: 293 subtitles, 36 dialogue pairs; 42 get under 80% of comfortable
  reading time (median 68% of it), all in dense overlapping speech. Stepped
  frame by frame at 1920×1080 and 1280×800: 0 px movement, no re-wraps.
- Rendering: one `.ev` block per subtitle, opacity on the block (tests read it
  there).

### Cue cards — one at a time

Title and description, no number, top left, at most 24em wide. **Never two
situations on screen**, even if a card comes late (the artist's rule).

- Cards queue in order of their start, **"Let's go" always first**. A card gets
  its reading time (9–30 s by length) and the **Cue linger** extra (default
  +8 s) only when no other card is waiting, so the queue drains: half the cards
  show within ~5 s of their moment, the worst ~2 min late in the 2:01 pile-up
  (§3). Every card is shown; two come up just after their sound has ended.
- **Cards follow their speakers.** The sheet starts each recording at its
  ambience, so a card could come up minutes before the person it describes
  spoke ("Anya" 55 s early, "Pidkova" 4 min, "Artery" 25 s late). `CUE_VOICE`
  maps 27 speech cues to the speaker (and a phrase, where needed) of their first
  line; the card shows 0.5 s before that line, its time read from `TURNS`, so
  re-timing carries through. Cue 1, sound-led cues (the trumpets, Tokha's
  funeral, the luncheon, Libkind's tour) and cues without speech keep the
  sheet's start. Some anchors are low-confidence lines (±~10 s).
- The schedule is computed once (again when Cue linger moves), so seeking is
  exact. `fitCue` sets a card smaller if it would reach the subtitles' room; at
  one card and 24em none needs it (checked frame by frame at two sizes).

### Typography and sizes

- **Inter**, the artist's choice over Times for reading on the wall (tall
  lowercase, open shapes, minimal): the variable font, subset to the page's
  characters and embedded as a data URI (~104 KB), so the page stays one file
  and works offline from `file://`. Source, licence (OFL) and how to re-subset:
  `fonts/`. The panel stays Helvetica so the interface never reads as part of
  the work.
- Tiers: speaker names and cue titles at weight 600; cue descriptions and stage
  directions at 0.78, the quieter tier; subtitles a step larger than cue titles,
  so the voices lead.
- **Sizes at 1920×1080: subtitles 52 px, cue titles 42 px** — the festival
  video's, set by the artist in the panel (they grew from 37/32 by +20%, +10%,
  then the panel). On any other screen they scale with the 1920×1080 frame
  fitted inside it, as a video would (`min(vw, vh)` terms), so the composition
  is the same everywhere; width-led formulas had let long cards reach the
  subtitles at 1280×800 and 4:3.
- Black on white or white on black: colours go through `--ink` / `--paper` on
  `:root`.

### The scroll view (`S`, `?mode=scroll`)

The full transcript in one column under a fixed **reading line**: the line being
spoken sits on it at full ink, spoken lines fall to the *spoken weight*, coming
lines are faint; a long turn travels through the reading line linearly (a
reading aid, not word sync); the prayer is lit line by line; tap a line to jump
to it. Two rules carried over from the wall:

- **Padding, never margin, inside a measured block.** `offsetHeight` includes
  padding and border, not margin; a margin is space the layout cannot see.
- **Justification needs measure.** Below ~24em the column sets ragged right,
  because narrow justified lines open rivers.

### Controls and the panel

| key | |
|---|---|
| `C` | the panel |
| `F` | fullscreen (also the panel's button; no button on screen) |
| `Space` | play / pause |
| `←` `→` | seek 10 s, with shift 60 s |
| `S` `D` `I` | scroll view, cues, colours — this visit only |

Panel sliders: position (a preview scrub that runs the page with no audio, for
tuning in silence), sync offset, type size and line spacing and column width
(scroll view), linger, subtitle size, height from the bottom, width, cue size,
cue linger, reading line, spoken and coming weight (scroll view), edge feather.

**Saved settings** (`localStorage`, key `cherven-transcript-settings`): only the
sliders someone actually moved, so a changed default still reaches a browser
that saved earlier. Sizes saved by hand were scaled with the +20% and +10%
changes (versions 4 and 5). **Reset settings** clears them.

---

## 5. Timing — read before trusting or editing it

`transcript/source.txt` holds the edited transcript exactly as supplied and is
the source of truth for the words: edited by the artist, paraphrased in places,
some phrases absent, and **in playback order**. Every line's time came from the
audio. `timing.json` records per line: start, end, confidence, method and the
recognised speech it was matched to. **83 high, 15 medium, 61 low.**

- **high / medium** — matched to recognised speech that is **reproducible from
  saved, unprompted recognition** (`whisper.json`). Starts good to ~1–2 s.
- **low** — no recognisable speech (children, voices under music, sung
  liturgy). Kept in order between confident neighbours (median bracket 9 s),
  placed by text length or by the sound itself (energy/pitch onsets). Its exact
  second is an estimate.

Three things about the method are not obvious and cost time to learn:

1. **Whisper on the plain mix hears only about a third of the speech.** Music
   beds make it emit training-data subtitle credits («Субтитры сделал
   DimaTorzok») instead of decoding; `hallucination_silence_threshold` then
   skips ahead and discards real speech. Recall came from pooling passes that
   fail differently: the plain mix, **Demucs-isolated vocals**, VAD-gated and
   short-window focused decodes. Each hears lines the others miss.
2. **Prompted decodes are not evidence.** A decode given the expected words as
   `initial_prompt` can echo them. Every confident claim is audited against
   saved recognition (`audit_evidence.py`: 99 of 100 supported; the one is the
   anthem stage direction, heard as "music playing"), and each one not found
   there was re-decoded unprompted *in the reviewer's own window* — Whisper is
   window-sensitive, so a different window failing proves nothing. Outcomes are
   in `transcript/verified_overrides.json`, applied last.
3. **Memory.** Shell-launched processes share a ~8 GB cgroup cap; two
   concurrent large-v3 decodes (4 GB each) get OOM-killed. Run decodes one at a
   time, one process per job (CTranslate2 keeps what it allocates).

`transcript/README.md` has the files, the commands, and how to change words or
cues without redoing the timing. `Sync offset` compensates for a delaying sound
chain; do not edit timings for that.

---

## 6. Deployment

Static. No server. `vercel.json` sets `cleanUrls`, a long cache on the audio
and no-cache on the pages.

**The audio is in the repo: `cherven.mp3` is the master, unchanged** — 68 MB,
211 kbps VBR, sha256 `8fefd409…`, identical to the asset on the `audio`
release. It was not re-encoded: the audio is the work, and a second lossy
generation was judged a poor trade for 26 MB. Keep it that way; if size ever
forces a re-encode, encode once from this file and never from a copy.

**The lossless master is a WAV** on the `lossless-audio` release: 24-bit,
44.1 kHz, 716 MB — too big for the repo (GitHub's 100 MB file limit) and the
site. It is the same edit as the MP3, sample for sample (cross-correlated at
five points: zero offset, r ≥ 0.999), so every timing holds for it. The page
accepts `?audio=<bare file name>` to play a file beside it instead of
`CONFIG.AUDIO`; the installation launcher passes `audio=cherven.wav` when that
file is in the folder. Chrome plays the 24-bit WAV from `file://`, seeking
included (tested).

**Audio must be served same-origin, or from a host that sends a real audio
type.** It was first hotlinked from the GitHub release. That worked on every
desktop browser and failed on every iOS one with MediaError code 4: the release
CDN sends `application/octet-stream` with `Content-Disposition: attachment`,
and iOS hands media to AVFoundation, which trusts the declared type rather than
sniffing the bytes. Vercel serves `.mp3` as `audio/mpeg`. Linux WebKit
(GStreamer) also sniffs, so it is **not** a stand-in for iOS on this point.

`CONFIG` at the top of the page's script: `AUDIO: './cherven.mp3'` (null falls
back to a file picker), `LOOP: true` (installations run all day),
`START_AT: 0`.

### One click is unavoidable

Browsers block autoplay with sound without a user gesture; the gate is that
gesture and should not be engineered away. For an unattended kiosk:

```
chrome --kiosk --autoplay-policy=no-user-gesture-required \
       --user-data-dir=<a profile of its own> index.html?autostart=1
```

That flag genuinely removes the click; nothing in the page can. With it,
`?autostart=1` calls `play()` on load and lifts the gate once playback begins.
Without the flag `play()` is refused and the gate simply stays.

**Never `--incognito`**: it wipes the saved slider settings on every launch.

### The installation build — `install/` and `INSTALL.md`

The gallery laptop (a Mac) runs a **local copy**, not the site: the venue
network is not trusted, and the page needs nothing but its folder.
`install/Cherven.command` is a double-click launcher; it calls
`install/launch.sh index.html`, which opens Chrome in kiosk mode on the
`file://` URL with `?autostart=1` (and `&audio=cherven.wav` when present), on
the dedicated profile `~/.cherven-chrome`, under `caffeinate` so the Mac never
sleeps. A previous kiosk on that profile is closed first: otherwise Chrome
hands the URL to the running copy and ignores the new flags. `INSTALL.md` is
the setup checklist (copy, launch, tune, macOS settings, autologin).

Laptops set up before November 2026 still hold the old `Cherven wall.command`
and `Cherven transcript.command` after updating (unzip adds, never deletes).
Both still work: the first opens index.html, the second transcript.html, which
forwards there with the query intact.

Tested in Chromium from `file://`: audio plays, autostart lifts the gate with
the flag and leaves it without, settings survive a reload, reset clears them,
the forwarder keeps the query. Not tested on a real Mac here; `launch.sh` was
dry-run with stand-ins for Chrome and `caffeinate`, from a path with spaces.

### Robustness already in place

- The update loop is wrapped in `try/catch`: a layout error costs one frame,
  not the session. Errors log to console, capped at 5.
- A 250 ms timer picks up whenever `requestAnimationFrame` is throttled, which
  browsers do when the window is backgrounded; without it, switching apps froze
  the display.

Preserve both. They exist because the display stopped during testing.

---

## 7. The video

`transcript/render_video.js` renders the page frame by frame on a virtual clock
(so picture and sound line up exactly), at 2× (3840×2160 frames, same
composition), from lossless PNG frames; `OUT=hd` encodes 1920×1080 straight
from them (lanczos, H.264 High 4.1, BT.709) for players that cannot take 4K;
`SETTINGS` passes panel values; `QUERY` another view. Unchanged frames reuse
the previous screenshot (verified identical to a full render). Four workers on
four cores take ~35 min for HD.

**The audio is copied, never re-encoded**: the WAV's PCM goes into a MOV, or as
ALAC (Apple Lossless) into an MP4 when an MP4 is required — decoded samples hash
the same as the WAV's. An AAC encode, once from the WAV, is only the fallback
for a player that cannot play ALAC. The first export re-encoded MP3 to AAC and
was redone. Splitting a video into parts and re-joining with `-c copy` keeps
every frame and sample (verified each time). Commands: `transcript/README.md`.

The festival video (October 2026) is the page's current default view: HD,
subtitles and cues, white on black, subtitles 52 px, cues 42 px, linger 3 s,
cue linger +8 s.

---

## 8. Open tasks

1. **Confirm the 2:01 block with Ian** and correct the starts in
   `transcript/cues.json`. The only outstanding correctness issue.
2. **Listen through once** at the low-confidence lines (children, the factory
   meeting, the Easter and funeral liturgy, the lullaby). A human ear settles
   in seconds what recognition could not; nudge `start` in `timing.json` and
   rebuild. A tap-along tool in the page that records corrected times was
   proposed, not built.
3. Possible typos in `transcript/source.txt`, left verbatim because the words
   are the artist's: "Fleet5" (the older transcript had "Fleet51"), "Hektor"
   (elsewhere "Hek"), "Captain Buger". Confirm, then edit and rebuild.
4. Settle the slider values in the room and write them into the `:root`
   defaults, so the site opens the same. Read them in the browser's console:
   `localStorage['cherven-transcript-settings']`.

## 9. Things not to do

- Do not add an alpha channel or transparency. See §2.
- Do not put more than one cue card on screen, or stack, move or re-wrap
  subtitles once shown. Each was tried and failed on the wall (§4).
- Do not make the page remember mode, cues or colours: a stray key at the
  installation would change the page for the next visitor.
- Do not load anything from the network at runtime (fonts included): the
  gallery laptop runs offline from `file://`.
- Do not re-encode the audio, in the page's folder or in a video. See §6, §7.
- Do not remove the gate. See §6.
- Do not "clean up" the overlapping cue data. See §3.
- Do not use margins inside a measured block of the scroll view. See §4.

## 10. History: the wall

Until November 2026 the home page was "the wall": the 53 cues themselves as
projected titles — black Times on white, typography modelled on a Ukrainian
Ministry of Defence contract form, a flow-packing layout engine that allocated
space by each cue's weight (and guaranteed every note was shown once per pass),
an opacity envelope per cue, and an older 93-turn transcript nested inside its
cues, placed by cue windows to within ~30 s. The artist asked for it to be
removed once the transcript page had replaced it. Its last version, with its
full specification (this file's §3–§8 at the time), is commit `2469f2a`
(`git show 2469f2a:index.html`, `git show 2469f2a:CLAUDE.md`). Its cue data
lives on in `transcript/cues.json`; its older transcript only in that commit.
