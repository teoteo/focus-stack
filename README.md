# Focus Stack — myFocuserPro2 or Ardufocus focuser + camera for microscopy

*English · [Italiano](README.it.md)*

Controls, from Safari on macOS, a DIY **myFocuserPro2** or **Ardufocus** focuser mounted on a
microscope and a **Sony / Nikon / Canon** camera over USB, running automatic
*move → settle → shoot* sequences ready for **Helicon Focus**.

The app and its PDF user guide are available in **Italian, English, French, German and Spanish**.

## Supported focusers

| Board | Firmware | Notes |
|---|---|---|
| **myFocuserPro2** (Robert Brown), DRV8825 driver version | Focus Stack's, bundled with the app | with the original myFocuserPro2 firmware it connects straight away and the app offers a one-click update |
| **Ardufocus** (rev1 PCB with DRV8825) | Focus Stack's, built with `ARDUFOCUSPCB` | the original Ardufocus firmware (Moonlite protocol) is **not** supported: load ours by hand the first time (below); after that it updates from the app |

Both boards run the same firmware (a modified myFocuserPro2 330, see [Firmware](#firmware)) and the
same serial protocol; the app detects the board and picks the right file for updates.

**First flash on an Ardufocus.** The Ardufocus does not reset over USB: press the board's reset button
and right after run (with [avrdude](https://github.com/avrdudes/avrdude), `brew install avrdude`):

```
avrdude -p m328p -c arduino -b 57600 -P /dev/cu.wchusbserialXXXX \
  -U flash:w:"/Applications/Focus Stack.app/Contents/Resources/app/firmware/build/firmware-ardufocus.hex":i
```

`57600` is the speed of the Arduino Nano's old bootloader; with the new bootloader use `115200`.
If avrdude cannot find the board, try again pressing reset a moment earlier. It is worth saving the
original firmware first (`-U flash:r:ardufocus-original.hex:i`) so you can put it back.

## Why a local server + PWA (and not a plain PWA)

Safari supports neither Web Serial nor WebUSB, so a web page cannot talk directly to the Arduino
or the camera. The app is therefore split in two:

```
Safari (PWA, interface)  ⇄  http://localhost:8765  ⇄  Python server
                                                       ├─ pyserial  → focuser (USB serial)
                                                       └─ libgphoto2 → camera (USB PTP)
```

The server listens on `127.0.0.1` only, so it cannot be reached from other computers. The optional
*Smartphone progress* page (see below) is a separate, read-only server.

## Installation

1. Download `FocusStack-<version>.zip` from the [latest release](https://github.com/teoteo/focus-stack/releases/latest)
   and open it: **Focus Stack** appears. The PDF user guides are attached to the same release.
2. Drag *Focus Stack* into the **Applications** folder (before opening it).
3. Open it. macOS warns that it cannot verify the developer (the app is not signed by Apple):
   open **System Settings › Privacy & Security**, scroll down and click **Open Anyway**.
   This is needed only the first time.

The app contains everything (Python, libraries, firmware): nothing else to install. It runs on
Apple Silicon Macs (macOS 14 or later) and Intel Macs (macOS 13 or later).

**Updates:** at start-up, and then every 6 hours, the app checks the GitHub releases. When there is a
new version, a bar with **Update and restart** appears at the top: the app downloads the new version,
quits and reopens by itself. The same check can be run by hand in *Configuration › Updates*.

**Focuser firmware:** the app also contains the firmware. When the connected focuser has an older
firmware (or the original myFocuserPro2 one), the top bar says so and *Configuration › Updates*
updates it with one click (about 20 seconds; the focuser settings are kept). Flashing goes through the
Arduino bootloader, without avrdude or the Arduino IDE. The app picks the firmware for the board
(myFocuserPro2 or Ardufocus). The Ardufocus does not reset over USB: during the update the app asks you
to press the focuser's reset button.

## Running

**As a Mac app:** Focus Stack.app starts the server without a Terminal window, opens Safari and stays
in the Dock while the server runs; clicking the Dock icon brings the page back to the front. If the
server does not start, it shows an alert; the log is in `~/Library/Logs/FocusStack.log`.

**Quitting:** quit Focus Stack (⌘Q, or Quit from the Dock icon's menu). The server first stops any
running sequence (the app asks for confirmation) and halts the motor, then shuts down; the Safari page
shows “Focus Stack is closed” and reloads by itself when you reopen the app.
Closing Safari does *not* stop the server.
If you open the app while the server is already running, it just shows the page; to reload the code
after an update, quit the app and open it again.

**From source (development):**

1. Double-click **`Avvia Focus Stack.command`**. The first time it creates the Python environment and
   installs the dependencies; then it opens Safari at `http://localhost:8765`. It also replaces an
   already running server with the updated code.
2. To try it without hardware, tick **Simulator** in the Focuser and Camera cards.

From the Terminal: `.venv/bin/python run.py [--port 8765] [--no-browser]` (stop it with `Ctrl+C`).

Requirements: macOS with Python 3.10 or later (`brew install python`). The libgphoto2 library is
already included in the `gphoto2` pip package, so Homebrew is not needed for the camera.

## Languages

The app speaks **Italian, English, French, German and Spanish**. With *Configuration › Language* set
to “Automatic” it follows the macOS language (English if it is none of these); a fixed language can
also be chosen. It applies to the interface, messages, the Log and the app's dialogs.

- Translation keys are the Italian texts; translations live in `web/lang/<lang>-web.json` (page) and
  `web/lang/<lang>-server.json` (server), shared by `backend/i18n.py` and `web/i18n.js`.
- To add a language: the two JSON files, the code in `SUPPORTED` (`backend/i18n.py`), the locale in
  `web/i18n.js`, the entry in the Language menu of `web/index.html` and the launcher's texts.
- `python3 tools/i18n_check.py --lang <lang>` lists untranslated texts (exits with 1 if any are missing).

## User guide (PDF and in the app)

One guide per language, attached to every release as a PDF: the interface with annotated screenshots, and the
calculations for the mechanical setup and the sequence step. The same text is also **inside the app** as an HTML
page with a table of contents and search: it opens from the **?** at the top right (at the chapter of the current
tab) and from the **?** in the card titles. It is regenerated with a test instance on port 8799 with a separate home
(see `docs/guida/cattura_schermate.py`):

```
python3.11 docs/guida/cattura_schermate.py --lang en    # screenshots (once per language, test server restarted)
python3.11 docs/guida/genera_guida.py all               # PDFs in docs/
python3.11 docs/guida/genera_guida_web.py               # HTML guide in web/guide/ (also rebuilt by build_release.sh)
```

The app's links point to fixed chapter names (`ALIASES` in `genera_guida_web.py`): if chapters are renumbered,
only that table needs updating.

## Interface

The dark theme is the default; the ◐ button at the top right switches to the light theme.
The app has three tabs:

- **Session**: position, limits bar, manual moves, sequence, camera and latest shot.
- **Configuration**: limits, mechanics, manual controls, motor (firmware), language, updates,
  temperature and depth-of-field calculator.
- **Log**: every event of the session.

**Manual moves:** a click on *Away*/*Closer* moves by the chosen step size (in powers of ten, up to
1000, 10,000 or 100,000 steps depending on *Configuration › Manual controls*). Holding the button
down keeps the motor moving; on release it slows down and stops. If the page stops responding, the
server stops the motor after about one second.

In the bar below the position:

- the **red hatched zones** are forbidden;
- the **blue band** is the sequence range, with a tick for each shot;
- the **white line** is the current position.

Keyboard in the Session tab:

| Key | Action |
|---|---|
| ↑ | move the objective away |
| ↓ | move the objective closer |
| ⇧ with ↑ or ↓ | step ×10 |
| 1, 2, 3, … | step size: 1, 10, 100, … steps (as many as the sizes chosen in *Manual controls*) |
| Esc | STOP |

## Limits (microscope safety)

In **Configuration › Safety limits** you set the lower and upper limits, also with
*⌖ Use current position*, and tell the app in which direction the objective gets closer to the specimen.

- **Moves commanded by the app**: the server checks go-to, jog, sequence and backlash compensation
  *before* moving the motor. Jogging stops at the limit; a sequence that would go beyond the limits does not start.
- **Focuser hardware buttons**: they drive the motor without going through the app.
  - The server reads the position every 0.2–0.5 s. If it goes beyond the limits it sends STOP and shows
    a red alarm, but between two readings the motor can overshoot the limit by a few dozen steps.
  - Recommended protection, enforced by the firmware itself on the buttons too:
    1. move the objective to the lowest safe point and press **Set zero here**
       (limits and sequence are shifted accordingly);
    2. move the objective to the highest safe point, use it as the upper limit and press
       **Write maximum to firmware**.
  - Check once, by hand and slowly, that your firmware really stops the buttons at 0 and at the maximum.
- **Buttons pressed during a sequence**: the sequence pauses and, on resume, repeats the shot from the
  correct position.

## Mechanics and motor

- **µm per step**: calculated from motor steps per revolution × microstep (read from the firmware) ×
  gear ratio and from the fine-focus travel per knob turn. Alternatively, entered by hand.
- **Motor**: microstep, speed, coils powered when idle (they hold the position), reverse rotation,
  firmware backlash (enable and IN/OUT steps, 0 to 255). The firmware compensates backlash at every
  change of direction, with the hardware buttons too; the sequence has its own compensation: use one
  or the other, not both.
- **Temperature**: chart of the last hour. The value at each shot is saved in `sequence.json`.

## Focuser: connection

- Connect the Arduino and choose the port `/dev/cu.usbserial-…`, `/dev/cu.wchusbserial…` or
  `/dev/cu.usbmodem…`. The speed is 9600 baud.
- Opening the port resets the Arduino: connecting takes about 2–3 s.
- Protocol: the INDI `myfocuserpro2` driver's (`:00#` position, `:05xxxx#` go to, `:27#` stop, …),
  implemented in `backend/focuser.py`.

## Shot viewer

Click the latest shot or **Open viewer ↗**: it opens in a separate window that you can move to a
second monitor. If the live view is on, the viewer opens straight on the live view.

| Control | Key | Effect |
|---|---|---|
| **−** / **+** | − / + | zoom |
| **Fit** / **Reset** | 0 or R | whole image in the window |
| **100%** | 1 | one sensor pixel = one screen pixel. Above 150% pixels stay sharp, without interpolation blur |
| Drag with the mouse | — | pan |
| Scroll wheel (or trackpad pinch) | — | zoom centred on the pointer |
| Double-click | — | toggle fit ↔ 100% |
| ◀ ▶ and thumbnails at the bottom | ← → | previous or next shot |
| **● Live** | L | camera live view with zoom, 100% and pan; ◀ ▶ or a thumbnail go back to the shots |
| **Follow latest** | U | show every new shot automatically |
| **Lock view** | K | keep zoom and position when changing shot, to compare focus at the same spot |
| **Inspector** | I | side panel, read only: R, G, B and brightness histograms, burnt (channels at 255) and black (channels at 0) pixels under a chosen rule, red/blue marks on the image, values under the pointer and min/max/mean/median of the whole image. It also works on the live view (updated twice a second) |
| Full screen | F | — |

The Inspector measures the 8-bit image on screen: for a RAW shot that is the conversion for the screen,
and the RAW itself has more headroom in highlights and shadows (the panel says so).

RAW shots are converted to JPEG with macOS `sips`, first a preview and then full resolution.
The conversion is cached in `~/Library/Caches/MyFocuserStack`.

## Camera

| Brand | Camera settings |
|---|---|
| Sony | USB menu → **PC Remote**; mode **M** |
| Nikon | mode **M**; turn off image review |
| Canon | mode **M**; the shot goes to RAM, or to the card if *Destination = card* |

- **Detect cameras** (⟳) and then **Connect**. From here you set shutter speed, ISO, aperture,
  format and destination; after each change the app reads back the value the camera actually accepted.
- **Bulb (seconds)** > 0 uses a bulb exposure controlled by the computer, for times beyond 30 s.
- **Mirror delay (DSLR)**, 0.5 to 2.5 s: wait between raising the mirror and the shot, to let
  vibrations die down. Nikon: the app sets the camera's *exposure delay mode* to the first available
  value equal or longer. Canon: enable *mirror lockup* in the camera menu; the app raises the mirror,
  waits, then shoots. Sony and mirrorless: not needed.
- **If connecting fails:** macOS (`ptpcamerad`) grabs the camera as soon as you plug it in. The app
  kills that process before connecting; if that is not enough, quit Photos, Preview, Image Capture,
  EOS Utility and NX Studio, then try again.
- The **test shot** goes to the gallery and opens in the viewer like the sequence shots.
- **● Live** (*Latest shot* card) shows the camera live view, up to 15 frames per second; double-click
  for full screen. The focuser controls, keyboard included, stay active. During the sequence the live
  view is turned off and resumes at the end; a test shot pauses it only for the shot. The server reads
  the frames with libgphoto2's `capture_preview` and sends them as MJPEG (`GET /api/camera/live`); if
  the live view is open both here and in the viewer, the two windows receive the same frames. Canon and
  Nikon keep the mirror up while the live view is on. Sony cameras must allow live view in *PC Remote*.

## Sequence

| Field | Meaning |
|---|---|
| Stack name | at the top of the card, because it changes often. Every stack goes into its own `<name>_<date-time>/` folder, so two stacks can share a name. When a stack is finished, **＋ New stack** sets the sequence back to *Ready* and selects the name to change it (the viewer and the saved files are not touched) |
| Start / End | positions in steps (⌖ copies the current position) |
| Step / Number of shots | linked: changing one recalculates the other |
| Settle time after moving | lets vibrations die down before the shot (1–3 s on a microscope) |
| Pause after the shot, for card and flash | after each shot, before the next move: time to write to the card and recharge the flash |
| Backlash compensation | before the first shot the motor backs off N steps and then advances, so every shot is reached from the same direction |
| Capture mode | **Download to the Mac** (recommended), **Memory card only**, **Trigger only** (fastest; set the destination to the card) |

**Save folder:** in the Sequence card, *Save to* row. **Choose…** opens the macOS “Choose folder”
panel; **Open** shows the folder in the Finder. Safari cannot read disk paths, so the panel is opened
by the server. If the folder does not exist it is created and, before saving it, the app checks that it
can write there.

Shots are saved in the chosen folder (default `~/Pictures/FocusStack`), in a `<name>_<date-time>/`
subfolder, named `<name>_0001.ARW`, `_0002…`. With **Shots per position** greater than 1 (default 1) the
camera fires several times at each position and the files are named `<name>_0001_1.ARW`, `<name>_0001_2.ARW`…:
the fusion software averages them to reduce noise.

The same folder holds `sequence.json`, the stack manifest: positions in µm, times, rail, camera,
optics, filter and illumination (*Settings › Optics, filter and illumination*). It is rewritten after
every shot, so it stays valid even if the sequence is interrupted; the images are never modified. The
format is described in [docs/sequence-json.md](docs/sequence-json.md). Next to it, `sequence.txt` is a short
human-readable summary (in the app language) of the sequence, the shooting settings and the optics.
At the end of the sequence **Open in Finder** opens the stack folder.

Pause, resume and abort are always available; **STOP** also halts the motor at once.
Sequences can be saved as **presets**, for example one per objective.

## Optics: microscope or photographic macro

Each optics profile (*Optics* tab) is either **Microscope** (objective magnification × intermediate
magnification changer × camera adapter, NA from the objective) or **Photographic macro**:

- **Lens**: searched in the [Lensfun](https://lensfun.github.io) database (≈1,160 interchangeable lenses,
  CC BY-SA 3.0, see below) plus a few dedicated macro lenses Lensfun lacks (`web/data/lenses-extra.json`) and
  your **personal list** (*＋ Add to my list*, saved in the settings). Make, model, focal length and widest aperture
  can always be typed by hand.
- **Lens reproduction ratio** at the focus used (1 = 1:1, 0 = focused at infinity) and **aperture set**.
- **Extension tubes / bellows** (mm) and up to three **close-up lenses** (diopters; common ones such as
  Raynox DCR-250 are suggested).

Magnification is a thin-lens estimate: m1 = m0 + extension / f, then m = m1 + ΣD/1000 · f · (1 + m1).
Effective aperture N·(1 + m1) and equivalent object-side NA = m / (2 N (1 + m1)) feed the depth-of-field
step suggestion. For exact scale, measure the µm per pixel with a ruler or stage micrometer.
The manifest gets `optics.kind = "macro"` and the macro keys (see [docs/sequence-json.md](docs/sequence-json.md)).

**Updating the lens database.** The app ships a snapshot; new lenses arrive with the next app release:

```bash
git clone --depth 1 https://github.com/lensfun/lensfun.git /tmp/lensfun
python3 tools/lensfun_import.py /tmp/lensfun/data/db     # rewrites web/data/lenses-lensfun.json
git diff --stat web/data/                                # then commit and publish as usual
```

The file records the Lensfun commit and date it was built from. Lenses in the personal list live in the
settings and are not affected by an update.

## Calibration frames and automatic exposure

The **Calibration** tab has three cards:

- **Light exposure**: with the focuser in the middle of the stack, it takes a few test shots, measures the
  RAW data and sets the shutter speed so that the brightest channel reaches a target level (default: 99.5th
  percentile at 85 % of saturation; or the mean). Exposure is computed once, before the stack, never per frame.
- **Calibration frames**: darks (lens cap, same ISO and shutter speed as the lights), flats (evenly lit field,
  shutter speed found automatically for a target mean level, default 50 %) and flat darks (lens cap, the
  flats' ISO and shutter speed). The app asks to fit the cap before darks.
- **Calibration library**: the sets in `<save folder>/_calibrazione/`, and which ones the next stack would use.

Sets are shared by all stacks: each stack's `sequence.json` points to the most recent suitable sets (same
camera, ISO and shutter speed for darks; same optics profile for flats). Format: [docs/calibration-json.md](docs/calibration-json.md).

Measurements use `fs-rawstat`, a small tool built from **LibRaw 0.22.3** (git submodule `third_party/LibRaw`,
the same version Focus Fusion uses) that reads RAW values without demosaicing; JPEG/PNG are read with macOS
ImageIO and marked as estimates. For development build it once:

```bash
git submodule update --init third_party/LibRaw
python3 tools/rawstat/build.py          # → build/rawstat/fs-rawstat (universal arm64 + x86_64)
```

`build_release.sh` builds it into the app (`Contents/Resources/app/bin`).

## Smartphone progress

*Configuration › Smartphone progress* turns on a read-only page on the local network (port 8766): shots
taken, time left, expected end time and, on request, a small preview of the latest shot (made only when
asked for, about 640 px). It is a second server separate from the one that drives the hardware, and it has
no commands; every request needs the code in the link (*New link* changes it). Open it on the smartphone by
scanning the QR code (generated by macOS CoreImage). The first time, the macOS firewall asks whether to
allow incoming connections.

With *Alert me with a sound when the sequence ends* the page plays a sound (Web Audio, unlocked by the tap as
iOS requires; it also vibrates on Android) when the stack finishes or stops on an error, and keeps the screen on
(Wake Lock). The Mac also plays a sound at the end of the sequence (system sounds Glass / Basso) unless
*Sound on the Mac when the sequence ends* is unchecked.

## Publishing a new version

On the development Mac you need `gh` authenticated (`gh auth login`), `arduino-cli` with the
`arduino:avr` core and the myFocuserPro2 libraries in `~/Documents/Arduino/libraries`.

1. Bump the number in `VERSION` (e.g. `1.0.0` → `1.0.1`).
2. If you changed the firmware, also bump `FSBUILD` in `firmware/myFP2F_DRV8825_330/fsbuild.h`:
   it is the number the app uses to tell that the focuser needs an update.
3. Commit and push the changes.
4. Run `./build_release.sh --publish`: it builds the firmware, downloads Python for Apple Silicon and
   Intel, assembles the universal app (~60 MB) and creates the `v<VERSION>` release on GitHub.
   Without `--publish` it only creates `build/dist/FocusStack-<VERSION>.zip` for testing.
5. Attach the PDF guides (`docs/*.pdf`) with `gh release upload` and write the release notes with
   `gh release edit --notes-file`.

Installed apps see the new release within 6 hours (or at once with *Check now*).

## Firmware

`firmware/myFP2F_DRV8825_330` is Robert Brown's myFocuserPro2 330 (MIT licence, see the copyright
notes in the files) for the DRV8825 board, with: buttons, temperature probe, flicker-free three-line
OLED display (Position, Target, Temp); buttons with continuous movement at increasing speed
(`PB_SPEED*` in `focuserconfig.h`); acceleration and deceleration ramps for commanded moves (`MOVE_*`);
command `:97#` returning the build number (`fsbuild.h`) and `:98#` returning the board
(0 = myFocuserPro2, 1 = Ardufocus).

**Ardufocus board:** with `ARDUFOCUSPCB` (a line in `focuserconfig.h`, or `-DARDUFOCUSPCB` as
`build_release.sh` does for `firmware-ardufocus.hex`) the same firmware uses the wiring of the
Ardufocus rev1 PCB with DRV8825: motor on D4 (DIR), D5 (STEP), D6 (SLEEP); buttons to ground on
D2 (OUT) and D3 (IN). DS18B20 probe, OLED, LEDs and buzzer are disabled. Speeds are higher, meant for a
NEMA 17 with a 27:1 gearbox.

## Structure

```
backend/focuser.py     myFocuserPro2 serial driver + simulator
backend/camera.py      camera control (python-gphoto2, persistent session) + simulator
backend/sequence.py    sequence engine
backend/main.py        REST API + status WebSocket
backend/settings.py    settings in ~/Library/Application Support/MyFocuserStack/
backend/updater.py     version, updates from GitHub, bundled firmware
backend/flasher.py     firmware upload to the Arduino (bootloader STK500 protocol)
backend/i18n.py        current language and server-side translations
packaging/             app launcher (AppleScript) and icon
build_release.sh       build and publish the universal app
firmware/              focuser firmware source
web/index.html …       main interface (PWA, no external dependencies)
web/viewer.*           viewer with zoom and pan
web/inspector.js       viewer Inspector (histograms, burnt/black pixels)
backend/optics.py      magnification (microscope, macro) and the manifest's optics
web/data/              lens database (Lensfun, CC BY-SA 3.0) and extra macro lenses
tools/lensfun_import.py rebuilds web/data/lenses-lensfun.json from a Lensfun checkout
backend/calibration.py calibration library, darks/flats capture, automatic exposure
backend/rawstat.py     runs fs-rawstat (RAW levels)
backend/remote.py      read-only progress page for the local network (smartphone)
tools/rawstat/         fs-rawstat source and build script (LibRaw)
third_party/LibRaw     LibRaw 0.22.3 (git submodule)
web/i18n.js, web/lang/ interface and message translations
docs/guida/            PDF and HTML guide generator (testo_<lang>.py)
tools/i18n_check.py    translation check
```

## Licence

MIT (see `LICENSE`). The firmware in `firmware/` derives from myFocuserPro2 by Robert Brown and
contributors, also MIT-licensed: the original copyright notes are in the files.

`web/data/lenses-lensfun.json` is derived from the [Lensfun](https://github.com/lensfun/lensfun) lens
database and, like it, is licensed under **Creative Commons Attribution-Share Alike 3.0** (CC BY-SA 3.0),
© the Lensfun contributors. It is a separate data file: the licence of the app's code does not change.

`fs-rawstat` is statically linked with [LibRaw](https://www.libraw.org/) 0.22.3 (git submodule in
`third_party/LibRaw`, unmodified), used under the **CDDL 1.0** (LibRaw is dual-licensed LGPL 2.1 / CDDL 1.0);
LibRaw's source is in the submodule, © LibRaw LLC.
