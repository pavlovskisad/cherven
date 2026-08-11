# cherven

Projected titles for **Cherven**, an audio documentary by Ian Spektor
(Kyiv Dispatch). Black text on a white field, synced to the audio, for
projection onto a white wall.

45:04 · 53 cues · 93 speech turns

## Run

Drop `cherven.mp3` next to `index.html` and open it. That is the whole setup.

Without the audio file the page still runs: press `C` and drag the preview
scrub to move through all 45 minutes in silence.

## Keys

`C` panel · `F` fullscreen · `Space` play · `1` `2` modes · `D` notes ·
`T` transcript · `←` `→` seek

## Deploy

Static site, no build step.

```
vercel --prod
```

See `CLAUDE.md` for the full specification: data model, layout engine,
typography, projection notes, and open tasks.
