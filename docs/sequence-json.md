# `sequence.json` — stack manifest (format `focus-stack-manifest`, version 1)

Focus Stack writes a `sequence.json` file into every stack folder, next to the images.
The images (RAW/JPEG) are never modified: all acquisition data lives in this file.
Next to it the app writes `sequence.txt`, a short human-readable summary in the app language,
generated from the manifest and rewritten with it. Programs should read only `sequence.json`.

## Rules

- **Atomic and incremental.** The file is rewritten after every shot (temporary file, then rename).
  If the acquisition stops, the file is still valid up to the last frame taken; `state` says why it ended.
- **Explicit units.** Positions in µm (`*_um`) and motor steps (`*_steps`) side by side, with
  `rail.um_per_step`. Times are ISO 8601 with milliseconds and time zone. Wavelengths in nm.
- **Missing ≠ none.** A missing key means *unknown / not specified*. `"filter": null` means
  *no filter fitted*; a missing `filter` key means *not specified*.
- **Optics profiles.** Optics, filter and illumination come from a named profile (app tab *Optics*),
  chosen in the *Stacking sequence* card; its name is in `optics_profile`. Without a profile the
  manifest has `"filter": null` and no `optics`, `illumination` or `optics_profile` keys. A profile
  may itself leave the filter *not specified*: then the `filter` key is missing.
- **Unknown keys must be preserved.** Readers should ignore keys they do not know and copy the whole
  manifest into exported metadata. `extra` is reserved for future or user data.
- **Versioning.** `format` + `version`. New optional keys may be added without changing `version`;
  `version` changes only if existing keys change meaning.

## z axis

`z_um` is the height of the focal plane relative to frame 0, **positive toward the objective**
(as in a height map). The sign comes from the *Toward the specimen* setting, so it is correct
whichever way the motor is mounted. `position_steps` is the absolute motor position.

`rail.position_feedback` is `"open_loop"`: the focuser has no encoder, so there is no measured
position (`z_measured_um` is never written). The app checks before every shot that the motor is
at the commanded position and has not been moved by the hardware buttons; if it was, the sequence
pauses and the shot is repeated from the correct position.

`rail.approach` is the direction in which every frame was reached (`toward_objective` or
`away_from_objective`); with backlash compensation (`backlash_overshoot_*`) the approach direction
is the same for all frames.

## Several shots per position

`sequence.shots_per_position` (default 1). Each frame has an `exposures` list (always a list, also
with a single shot). Files are named `<name>_0001.ext` with one shot per position and
`<name>_0001_1.ext`, `<name>_0001_2.ext`… with more. The fusion software is expected to average
(or sigma-clip) the exposures of one frame.

## Keys

| Key | Meaning |
|---|---|
| `format`, `version` | `"focus-stack-manifest"`, `1` |
| `software` | e.g. `"Focus Stack 1.0.8"` |
| `state` | `running`, `completed`, `interrupted` (by the user), `error` |
| `started`, `updated`, `finished` | ISO 8601; `finished` only when not `running` |
| `session_name` | name typed in the app |
| `z_axis` | `{unit: "um", origin: "first_frame", positive: "toward_objective"}` |
| `rail.model` | `myFocuserPro2`, `Ardufocus` or `Simulator` |
| `rail.firmware` | firmware version (and Focus Stack build) |
| `rail.um_per_step`, `rail.um_per_step_source` | `computed_from_mechanics` or `entered` |
| `rail.microstep` | microstep set in the firmware |
| `rail.backlash_overshoot_steps` / `_um` | overshoot used to always approach from the same side |
| `rail.settle_ms`, `rail.post_shot_ms` | wait after the move, pause after each shot |
| `sequence` | `start_steps`, `end_steps`, `step_steps`, `step_um`, `span_um`, `positions`, `shots_per_position`, `capture_mode` (`download`, `card`, `trigger`), `mirror_delay_ms`, `bulb_s` |
| `camera` | `model`, `iso`, `shutterspeed`, `aperture`, `imageformat` as read at the start (per-frame values are in the EXIF) |
| `optics` | `objective`, `magnification` (total on the sensor), `na`, `immersion` (`air`, `water`, `oil`, `glycerol`, `silicone`), `sensor_pixel_um`, `pixel_size_um` + `pixel_size_source` (`calibrated` or `sensor_pixel / magnification`) |
| `filter` | absent, `null`, or `{name, type, center_nm, bandwidth_nm, edge_nm}`; `type` = `bandpass`, `longpass`, `shortpass`, `neutral_density`, `polarizer`, `other` |
| `illumination` | `{type, level_percent}` (free text type) |
| `notes` | free text |
| `optics_profile` | name of the optics profile used (absent = no profile) |
| `frames[]` | `index` (0-based), `z_um`, `position_steps`, `temperature_c`, `exposures[]` |
| `frames[].exposures[]` | `repeat` (0-based), `time`, `files` (names relative to the folder; RAW+JPEG gives two; empty with `card`/`trigger` capture), `temperature_c` |
| `extra` | `{}` reserved |

With `card` or `trigger` capture the folder contains only `sequence.json`: the files stay on the
camera card and must be paired with the frames in shooting order.

## Example

```json
{
  "format": "focus-stack-manifest",
  "version": 1,
  "software": "Focus Stack 1.0.8",
  "state": "completed",
  "started": "2026-11-12T14:02:10.831+01:00",
  "updated": "2026-11-12T14:02:27.932+01:00",
  "finished": "2026-11-12T14:02:27.932+01:00",
  "session_name": "prova",
  "z_axis": { "unit": "um", "origin": "first_frame", "positive": "toward_objective" },
  "rail": { "model": "myFocuserPro2", "firmware": "330 build 3", "position_feedback": "open_loop",
            "settle_ms": 1500, "post_shot_ms": 500, "um_per_step": 0.0833,
            "um_per_step_source": "computed_from_mechanics", "microstep": 4,
            "backlash_overshoot_steps": 50, "backlash_overshoot_um": 4.165, "approach": "toward_objective" },
  "sequence": { "start_steps": 1000, "end_steps": 1200, "step_steps": 100, "positions": 3,
                "shots_per_position": 2, "capture_mode": "download", "mirror_delay_ms": 0,
                "return_to_start": true, "step_um": 8.33, "span_um": 16.66 },
  "camera": { "model": "Nikon DSC D5600", "iso": "100", "shutterspeed": "1/60", "imageformat": "NEF (Raw)" },
  "optics": { "objective": "Plan 10×/0,25", "magnification": 10.0, "na": 0.25, "immersion": "air",
              "sensor_pixel_um": 3.9, "pixel_size_um": 0.39, "pixel_size_source": "sensor_pixel / magnification" },
  "filter": { "name": "GFP", "type": "bandpass", "center_nm": 525.0, "bandwidth_nm": 50.0 },
  "illumination": { "type": "LED ring light", "level_percent": 60.0 },
  "optics_profile": "10× GFP",
  "frames": [
    { "index": 0, "z_um": 0.0, "position_steps": 1000, "temperature_c": 20.9,
      "exposures": [
        { "repeat": 0, "time": "2026-11-12T14:02:21.383+01:00", "files": ["prova_0001_1.NEF"], "temperature_c": 20.9 },
        { "repeat": 1, "time": "2026-11-12T14:02:22.004+01:00", "files": ["prova_0001_2.NEF"], "temperature_c": 20.9 }
      ] }
  ],
  "extra": {}
}
```
