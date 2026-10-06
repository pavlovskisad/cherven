# Installing Cherven on a Mac with a projector

For musikprotokoll, Graz. Everything runs from files on the laptop: no
network is needed once it is copied over.

## 1. Before you leave — copy it onto the Mac

Needs **Google Chrome** (google.com/chrome). Then in Terminal:

```
cd ~ && curl -L -o cherven.zip https://github.com/pavlovskisad/cherven/archive/refs/heads/main.zip && unzip -q -o cherven.zip && rm cherven.zip && chmod +x cherven-main/install/*.command && open cherven-main/install
```

That makes the folder `cherven-main` in your home folder (about 70 MB, the
audio included) and opens `install/`. Running the same line again updates it.
Keep it in the home folder, not Downloads, Desktop or Documents: macOS asks
permission before Chrome may read those, and the prompt hides behind a full
screen page.

## 2. Start it

Double-click one of:

- **Cherven wall.command**: the cue sheet with speech.
- **Cherven transcript.command**: the edited transcript (subtitles or scroll).

Chrome opens full screen and the piece starts by itself and loops. A Terminal
window opens behind it; leave it there. **Cmd+Q** quits. Double-clicking again
restarts it.

If macOS says the file can't be opened, right-click it, choose **Open**, then
**Open** again. You only have to do that once.

## 3. Tune it on the wall

Press **C** for the settings panel. Every slider and switch is **saved
automatically** and comes back on every restart. **Reset settings** at the
bottom of the panel returns to the defaults. Settings are kept separately for
the wall and the transcript.

- Type size and margin should fit the throw.
- **Edge feather** dissolves the bright edge of the projected rectangle into
  the wall. It is off by default; raise it until the frame stops reading.
- On the transcript page: **S** switches subtitles/scroll, **D** cues on/off,
  and **Linger** sets how long a line stays.
- **Sync offset** (transcript page): if words land late against the sound,
  usually because of a delay in the sound system, move it until they match.
- **← / →** seek 10 s (shift: 60 s). **Space** pauses. **F** fullscreen.

Close the panel with **C** when done. The cursor hides itself after 2 s.

## 4. The Mac, once

System Settings:

- **Displays**: set the projector to its native resolution. Make it the main
  display (Arrange: drag the white menu bar onto it), or mirror. Chrome opens
  on the main display.
- **Lock Screen**: "Turn display off" set to **Never**, and screen saver
  **Never**. (The launcher also keeps the Mac awake while it runs, but set
  these anyway.)
- **Energy / Battery → Options**: prevent automatic sleeping when the display
  is off; for a mains-powered desktop Mac, turn on "Start up automatically
  after a power failure".
- **Focus**: Do Not Disturb on, so no notification lands on the wall.
- **Sound**: output to the venue's system. Use a cable or the venue's
  interface, not Bluetooth (Bluetooth adds delay, drops out, and re-encodes
  the sound). The pages play `cherven.mp3` exactly as it is: no volume
  change, no processing.
  - Open **Audio MIDI Setup** (Applications → Utilities), select the output
    device and set Format to **44,100 Hz**, the file's own rate, so macOS
    doesn't resample it.
  - Set the Mac's volume to full and control the level at the venue's
    mixer.
- **Software Update**: turn off automatic updates for the duration.

## 5. Surviving a power cut (optional, for an unattended day)

- **Users & Groups → Automatically log in as** your user.
- **General → Login Items → +** and add the `.command` you are showing.

The Mac then boots straight into the piece.

## 6. Check before doors open

- [ ] Sound comes out of the venue's speakers, not the laptop.
- [ ] Watch a minute with speech: the text matches the voices.
- [ ] Quit (Cmd+Q) and start again: your settings came back.
- [ ] Leave it running for 10 minutes untouched. The screen stays on and the
      cursor stays hidden.

## If something goes wrong

- **The "Let's go" screen stays up**: Chrome was not allowed to start the
  sound by itself. Quit Chrome completely (Cmd+Q) and double-click the
  launcher again, or just click *Let's go* once.
- **"Could not load the audio"**: `cherven.mp3` is missing from the folder.
  Run the command in step 1 again.
- **Online fallback**: `https://cherven.vercel.app` (wall) and
  `https://cherven.vercel.app/transcript` work in any browser, but need one
  click to start, and the venue's internet.
