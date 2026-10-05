#!/bin/bash
# Double-click: the transcript page full screen, playing. Cmd+Q quits.
# Subtitles or scroll, cues on or off: set them in the room (S, D, or the panel
# under C); the choice is kept.
exec "$(dirname "$0")/launch.sh" transcript.html
