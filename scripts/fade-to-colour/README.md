# fade-to-colour

Fades the video to black, to white, or to a colour you pick. Each fade is a true crossfade, so the picture goes cleanly to the target colour without a tint on the way.

## Setup

1. Put a **Video processor** on the track (or item) whose video you want to fade.
2. Put it **after** any colour effects in the FX chain, such as Colorize. If one comes later, it tints the fade.
3. Paste the contents of [`fade-to-colour.eel`](./fade-to-colour.eel) into its code editor and save it as a preset.
4. Automate a fade parameter from 0 to 1.

**Replacing the older version:** you previously used a modified Brightness/Contrast preset with "fade to white" and "fade to black" added. This script keeps those two at the same parameter numbers (8 and 9). If you paste this code into those existing Video processor instances, their fade envelopes keep working. Brightness, contrast and saturation are gone; their defaults left the picture unchanged, so a project that never moved them looks the same.

## Parameters

| # | Name | Range | Default | What it does |
|---|---|---|---|---|
| 8 | Fade to white | 0–1 | 0 | 0 = untouched video, 1 = solid white. |
| 9 | Fade to black | 0–1 | 0 | 0 = untouched video, 1 = solid black. |
| 10 | Fade to colour | 0–1 | 0 | 0 = untouched video, 1 = solid custom colour. |
| 11–13 | Colour red / green / blue | 0–255 | 128 | The custom colour, as RGB values from any colour picker. The default is mid-grey. |

Numbering starts at 8 to stay compatible with the older version (see above).

## Notes

- The fades stack in this order: colour, then white, then black on top. Black at 1 always gives black, so you can fade to a colour and then to black at the end without resetting anything.
- Fading through a gap between items works: with no video, the script starts from black, so a fade held at 1 still shows its colour.
- To fade to grey, use Fade to colour with red, green and blue all equal (128 is mid-grey).

## Test checklist (in REAPER)

- [ ] Loads without a compile error.
- [ ] Each fade at 0 leaves the video untouched; at 1 gives a solid colour.
- [ ] Fade to white after a sepia Colorize reaches pure white, with no yellow on the way.
- [ ] Fade to colour with a picked RGB value reaches that colour (compare with a colour picker).
- [ ] Black at 1 wins over white and colour.
- [ ] Pasted over the old Brightness/Contrast-based preset, existing fade-to-white and fade-to-black envelopes still work.

## Changelog

### 1.0.0
- First version in this repo. Based on the Brightness/Contrast preset with fade to white and fade to black added; brightness, contrast and saturation removed, fade to a custom colour added, and the fades rewritten as crossfades.
