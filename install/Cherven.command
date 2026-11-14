#!/bin/bash
# Double-click: Cherven full screen, playing (subtitles, cue cards, white on
# black). Cmd+Q quits. Sizes and timing can be tuned in the room in the panel
# (C); those settings are kept.
exec "$(dirname "$0")/launch.sh" index.html
