# cherven

Projected titles for **Cherven**, an audio documentary by Ian Spektor
(Kyiv Dispatch): the edited transcript as film subtitles, synced to the audio,
with the cue sheet's cards above, white on black. Live at
https://cherven.vercel.app.

45:04 · 53 cues · 159 speech turns

## Run

Open `index.html` next to `cherven.mp3`. Click *Let's go*. That is the whole
setup. For the gallery laptop (full screen, starts by itself, works offline,
plays the lossless WAV) see `INSTALL.md`.

## Keys

`C` panel (sizes, timing, feather; saved) · `F` fullscreen · `Space` play ·
`←` `→` seek · `S` `D` `I` scroll view, cues, colours (this visit only)

## Deploy

Static site, no build step: Vercel serves the repository (`vercel.json`).
`transcript/build.py` writes the timed transcript and the cue sheet into
`index.html`; `transcript/render_video.js` renders it to video.

See `CLAUDE.md` for the full specification.
