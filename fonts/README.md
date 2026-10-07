# fonts/

`InterVariable.woff2` is Inter 4.1 (rsms.me/inter), the full variable font
(weight 100–900, optical size 14–32), kept here as the source.
`Inter-LICENSE.txt` is its licence (SIL Open Font License 1.1), which allows
bundling and redistribution.

`transcript.html` does not load this file. It embeds a **subset** as a data
URI in its `@font-face` rule, so the page stays one self-contained file and
works offline on the gallery laptop (`file://` pages cannot reliably load
fonts beside them). The subset keeps both axes and every OpenType feature,
and covers ASCII, Latin-1, Latin Extended-A, common punctuation and every
character the page uses: about 104 KB.

If new characters enter the transcript or the cue sheet (a name with a
diacritic not yet covered, say), re-subset and re-embed:

```
python3 -m venv /tmp/ft && /tmp/ft/bin/pip install fonttools brotli
python3 -c "s=open('transcript.html',encoding='utf-8').read(); print(','.join('U+%04X'%c for c in sorted({ord(c) for c in s if ord(c)>0x7e})))" > /tmp/chars.txt
/tmp/ft/bin/pyftsubset fonts/InterVariable.woff2 \
  --unicodes="U+0020-007E,U+00A0-017F,U+2010-2027,U+2030-203A,U+20AC,U+2122,$(cat /tmp/chars.txt)" \
  --layout-features='*' --flavor=woff2 --output-file=/tmp/Inter-subset.woff2
```

Then replace the base64 inside `url(data:font/woff2;base64,…)` in
`transcript.html` with `base64 -w0 /tmp/Inter-subset.woff2`.
