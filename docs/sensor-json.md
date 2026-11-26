# Sensor profile (format `focus-stack-sensor`, version 1)

**Calibration › Sensor › Sensor analysis** measures the camera sensor at each ISO from pairs of flats and darks
(photon transfer). The result is one file per camera in the calibration library:

```
<save folder>/
  _calibrazione/
    _sensore/
      ILCE-6400.json                  the sensor profile (this format), latest analysis of that camera
      ILCE-6400_20261126-104500/      the analysis frames: flat_iso100/, dark_iso100/, …, analysis.json, run.json
```

The analysis frames are **not** calibration sets: `_sensore` has no `calibration.json`, so they are never chosen for a
stack. Focus Stack reads the profile for the summaries and copies the values for the stack's ISO into `sequence.json`
(`"sensor"`).

## Method

For each ISO: two flats (evenly lit field, about 50 % of saturation) and two darks (lens cap on, same ISO and shutter
speed). Only raw values are used: a central crop (800 × 800 photosites) of one green channel of the colour filter array,
no demosaicing, no white balance (`fs-rawstat --ptc`).

- `dark_mean` = mean of the two darks; signal = mean of each flat − `dark_mean`
- gain (e⁻/ADU) = (signal₁ + signal₂) / (var(flat₁ − flat₂) − var(dark₁ − dark₂))
- read noise (ADU) = √(var(dark₁ − dark₂) / 2); in electrons × gain
- full well (e⁻) = (`white` − `black`) × gain, with `white` from the RAW metadata (LibRaw `linear_max`, e.g. 15360 on Sony)
- dynamic range (stops) = log₂(full well / read noise)

The difference of two identical shots removes everything fixed (dust, vignetting, hot pixels, fixed pattern) and leaves
only the temporal noise.

## Keys

| Key | Meaning |
|---|---|
| `format`, `version` | `"focus-stack-sensor"`, `1` |
| `software` | e.g. `"Focus Stack 1.4.0"` |
| `camera` | `{model, iso, shutterspeed, aperture, imageformat}` at the time of the analysis |
| `created` | ISO 8601 date and time |
| `method` | short description of the method |
| `run` | name of the folder with the analysis frames (sibling of this file) |
| `simulated` | `true` only with the simulator (example values) |
| `iso` | list, by increasing ISO: `{iso, shutter, gain_e_adu, read_noise_e, read_noise_adu, full_well_e, dynamic_range_stops, flat_level_pct, black, white, dark_mean, saturated_pct, samples, reliable, reasons, flat_files, dark_files}` |
| `recommended` | `{max_dynamic_range_iso, low_noise_iso, avoid_iso: [...], reliable_up_to_iso}` |

`reliable` is `false` (with `reasons`) when the flats are saturated (`saturated`), when the black level of the darks
moves (`black_shift`), or when read noise drops more than 15 % below the previous ISO values while dynamic range does not rise
(`noise_filtered`: the camera filters noise in the RAW, typically at high ISO). A drop in read noise with a **rise** in
dynamic range is a real second conversion gain (e.g. Sony at ISO 400) and stays reliable. Once an ISO is
`noise_filtered`, all higher ones are too.

`recommended`: `max_dynamic_range_iso` = the reliable ISO with the widest range; `low_noise_iso` = the first reliable
ISO whose read noise is within 20 % of the lowest; `avoid_iso` = reliable ISO values for which a higher ISO has at
least the same range (same range with shorter exposures); `reliable_up_to_iso` = the highest reliable ISO.

## Example (Sony A6400, abridged)

```json
{
  "format": "focus-stack-sensor", "version": 1, "software": "Focus Stack 1.4.0",
  "camera": {"model": "ILCE-6400", "imageformat": "RAW", "aperture": "f/20"},
  "created": "2026-11-26T11:05:12.000+01:00",
  "run": "ILCE-6400_20261126-104728",
  "iso": [
    {"iso": 100, "shutter": "1/5", "gain_e_adu": 2.4966, "read_noise_e": 3.59, "full_well_e": 37070, "dynamic_range_stops": 13.33, "reliable": true},
    {"iso": 400, "shutter": "1/20", "gain_e_adu": 0.6178, "read_noise_e": 1.238, "full_well_e": 9174, "dynamic_range_stops": 12.86, "reliable": true},
    {"iso": 6400, "shutter": "1/320", "gain_e_adu": 0.0392, "read_noise_e": 0.851, "full_well_e": 581, "dynamic_range_stops": 9.42, "reliable": false, "reasons": ["noise_filtered"]}
  ],
  "recommended": {"max_dynamic_range_iso": 100, "low_noise_iso": 400, "avoid_iso": [160, 200, 250, 320], "reliable_up_to_iso": 3200}
}
```
