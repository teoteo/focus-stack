# Calibration frames — library and `calibration.json` (format `focus-stack-calibration`, version 1)

Focus Stack keeps calibration frames in a **shared library** inside the folder where stacks are saved:

```
<save folder>/
  _calibrazione/
    dark_20261116-172039/        calibration.json + dark_0001.NEF, dark_0002.NEF, …
    flat_20261116-172041/        calibration.json + flat_0001.NEF, …
    flat-dark_20261116-172046/   calibration.json + flat-dark_0001.NEF, …
  bee_eye_20261116-173000/       a stack: sequence.json points to the sets above
```

- **dark**: lens cap on, same ISO and shutter speed (or bulb time) as the lights.
- **flat**: evenly lit field, same optics, aperture and optics profile as the lights. The shutter speed is
  found automatically for a target level (mean of the brightest channel, default 50 % of saturation).
- **flat_dark**: lens cap on, ISO and shutter speed of the latest flat set of the same camera.
- No bias frames: darks at the lights' exposure already contain the bias.
- `focusfusion/` inside a set folder is written **only by Focus Fusion**: its calibration masters
  (`master_<kind>_<key>.tif` + `master_<kind>_<key>.json`, format `focus-fusion-master`). Focus Stack never reads or
  changes it; it is safe to delete (Focus Fusion rebuilds the masters) and it goes to the Trash with its set.

Frames are never copied into stacks. When a stack starts, its `sequence.json` gets a `calibration` key with
the **most recent suitable completed set** of each type (paths relative to the stack folder):

| Key | Chosen when |
|---|---|
| `calibration.darks` | same camera model and ISO, same shutter speed (or same bulb time) |
| `calibration.flats` | same camera model and optics profile (same aperture preferred) |
| `calibration.flat_darks` | same camera model, ISO and shutter speed as the chosen flats |

Each entry: `set` (folder name), `path` (e.g. `../_calibrazione/dark_20261116-172039`), `frames`, `created`,
`iso`, `shutterspeed`, `aperture`, `bulb_s`, `temperature_c` (`{min, max, mean}`), `optics_profile` (flats),
`outliers` (Focus Stack 1.4.2+: 1-based numbers of the frames very unlike the rest of the set, see below; also for
sets made before the check existed). A missing key means no suitable set was found.

## `calibration.json`

| Key | Meaning |
|---|---|
| `format`, `version` | `"focus-stack-calibration"`, `1` |
| `software` | e.g. `"Focus Stack 1.1.0"` |
| `type` | `dark`, `flat`, `flat_dark` |
| `state` | `running`, `completed`, `interrupted`, `error` (only `completed` sets are linked to stacks) |
| `created`, `updated`, `finished` | ISO 8601 with milliseconds and time zone |
| `camera` | `model`, `iso`, `shutterspeed`, `aperture`, `imageformat` at capture time |
| `bulb_s` | darks taken with bulb, like the lights |
| `exposure` | flats: `{shutter, level_pct, target_pct, stat, within_tolerance, linear, attempts}` |
| `optics_profile`, `optics`, `illumination` | flats: as in `sequence.json` |
| `flat_set` | flat darks: folder name of the flat set they match |
| `temperature_c` | `{min, max, mean}` from the focuser probe, when present |
| `mean_level_pct` | mean level per channel `{R, G, B}` over all frames (from 1.4.2: without the `outlier` frames) |
| `outliers` | 1.4.2+, only when some frames are unlike the others: their 1-based numbers |
| `frames[]` | `index`, `time`, `files` (names in the folder), `temperature_c`, `stats`, `outlier` (1.4.2+, `true` when present) |
| `frames[].stats` | `mean_pct` per channel, `p99_5_pct` (brightest channel), `burnt_pct`, `center_mean_pct`, `linear` |

**Frames unlike the others** (1.4.2+). A set is only good if its frames look alike: a flat taken after the
light went off or changed, or a dark with the cap off or light entering through the viewfinder, spoils the mean.
With at least 3 measured frames, a frame is an outlier when its level (`stats.mean_pct`, brightest channel)
differs from the median of the set by more than ±10 % of it (flats) or is more than 1 percentage point above it
(darks, flat darks). Focus Stack warns while shooting, marks the frames when the set completes and shows them in
the library; the files stay in the folder and in `frames[]`, so a reader can leave them out or reject the set.

Levels are percentages between the black level and the saturation level of the sensor, measured on the
RAW data (no demosaicing) by `fs-rawstat`, built from LibRaw 0.22.3 — the same version Focus Fusion uses
(`tools/rawstat`). `linear: false` means the frame was a JPEG/PNG: values are estimated through the sRGB curve.
