# REAPER Video processor: working notes

These notes cover what this repo relies on. Each fact is marked with where it comes from. If something here turns out to be wrong in REAPER, fix this file in the same change that fixes the script.

Sources:
- **[API]** Video processor API reference (Ultraschall mirror of the REAPER docs): <https://raw.githubusercontent.com/Ultraschall/ultraschall-lua-api-for-reaper/Ultraschall-API-5.1/ultraschall_api/Documentation/Reaper_API_Video_Documentation.html>
- **[Official]** REAPER's own page: <https://www.reaper.fm/sdk/vidproc/vidproc_doc.php> (it couldn't be fetched when these notes were written, so check it when in doubt).
- **[Tested]** Confirmed by a script in this repo working in REAPER.
- **[Stock]** Seen in REAPER's own Video processor presets.

## Parameters

`//@param` lines at the top of the script create the knobs **[API]**:

```
//@param1:varname 'Shown name' default min max mid step
```

- The index is 1–40, so a script can have at most **40 parameters** **[API]**.
- If you leave values out, the defaults are default 0, min 0, max 1, mid = midpoint, step 0.005 **[API]**.
- `//@param 1:name` (with a space) is also accepted **[API]**.
- Every parameter can be automated with an envelope. That's the main way to drive a script over time.

## Built-in variables **[API]**

| Variable | Meaning |
|---|---|
| `time` | Time in seconds (item time when used as item FX). |
| `project_w`, `project_h` | Project video size. Code can override them before drawing. |
| `framerate` | Project FPS. |
| `param_wet` | Wet/dry mix when used as FX. |
| `gfx_r gfx_g gfx_b gfx_a` | Current colour/alpha (0..1). `gfx_a` also sets the opacity of `gfx_blit`. |
| `gfx_mode` | Blend mode: 0 normal, 1 additive, 3 multiply. Flags: `0x100` filtering on blit, `0x10000` use source alpha (RGBA only). |
| `gfx_dest` | Destination image, -1 = the output frame. |

## Functions used so far

| Function | Notes |
|---|---|
| `input_info(0, project_w, project_h)` + `gfx_blit(0)` | Input `0` is the video coming into this FX (the track's or item's own video). This pair draws it at its native size by setting the output size to the input's **[Stock]** (Brightness/Contrast preset). Use it for single-video effects such as fades. |
| `input_track(n)` | Video input from the tracks above. `input_track(0)` is the one the stock 2x2 preset puts top-left. |
| `input_info(input, w, h)` | Returns 1 if the input exists and sets `w`/`h` to its size. Use it to skip missing inputs and to get the aspect ratio. **[Tested]** |
| `gfx_blit(input, preserve_aspect, x, y, w, h, srcx, srcy, srcw, srch)` | Draws an input or image. `preserve_aspect=1` letterboxes and fills the pad areas; `-1` letterboxes without filling them. The `src*` arguments crop the source. Returns 1 on success **[API]**. |
| `gfx_set(r [, g, b, a, mode, dest])` | Sets colour/alpha/mode. With only `r`, it's grey **[API]**. |
| `gfx_fillrect(x, y, w, h)` | Fills with the current colour **[API]**. |
| `gfx_img_alloc([w, h, clear])` / `gfx_img_free` | Off-screen images, up to 32. Contents are undefined unless `clear` is set **[API]**. Not used yet; needed for proper crossfades (draw a layout into an image, then blit it with `gfx_a`). |
| `gfx_procrect(x, y, w, h, table)` | Maps every pixel through lookup tables: `table[0..255]` for Y, `table[256..511]` and `table[512..767]` for U and V. The Brightness/Contrast preset sets `colorspace = 'YV12'` first (unless it's `'YUY2'`) **[Stock]**. Each channel maps independently, so it can't do anything that mixes channels. |
| `gfx_img_info(img, w, h)` | Size of an image you allocated **[API]**. For inputs, use `input_info`. |

## How a script runs

- The whole script runs once per output frame.
- **Variables and memory (`buf[i]`) keep their values between frames** **[Tested]**: multiview's transitions depend on it. So a script can be a state machine: remember the previous parameter value and the time a change happened.
- When the transport is stopped, the script still runs when something changes, but `time` stays the same. Animations based on `time` would then freeze half-way, so jump straight to the end state when `time` hasn't moved (see multiview).
- After a seek or loop jump, `time` jumps. Detect `abs(time - last_time) > 0.5` and reset any animation.

## Colour

- **Pixels are often YUV.** Raising only lightness (Y) keeps the colour (U/V), so bright areas end up "full brightness plus the old tint": a sepia-tinted clip turned yellow instead of white **[Tested]**. To fade to a colour, move all channels together. The simplest way is a fill over the frame with `gfx_a = amount` (see `scripts/fade-to-colour`).
- `gfx_set` takes RGB (0..1) even when the frame is YUV; REAPER converts it. The `0x80000` mode flag makes it take YUV instead **[API]**.
- **Effect order matters:** a colour effect placed after a fade tints the fade. Put fades last in the chain **[Tested]**.
- REAPER's stock Colorize preset takes hue as an angle on the YUV colour plane, where 0 is blue rather than red. A standard hue of 35° (sepia) is about 145 there. This matched a screenshot but isn't documented **[Tested, informally]**.

## Gotchas (checked by `tools/vp.py check`)

1. **Names ignore case.** `t` and `T` are the same variable, so a loop counter `t` would overwrite a constant `T`. Use distinct, descriptive names.
2. **Parenthesize ternaries used as values.** Write `x = (c ? a : b);`, and `c ? (x = 1) : (y = 2);` when a branch assigns. Without parentheses, EEL2 can bind the assignment to the condition, or assign to whichever branch the ternary returns.
3. **`%` is integer modulo** and `floor()` truncates. Grid maths uses both.
4. **Functions** are defined with `function name(args) local(vars) ( body );`. Any variable not listed in `local()` is global, which is handy for reading parameters inside functions. Keep scratch variables local so they don't clobber globals.
5. **Memory arrays** use one shared address space. Give each array a fixed base (multiview uses 0, 64, 128, 192) and a stride, and leave gaps so they can grow.
6. **Blitting with `preserve_aspect=1`** fills the letterbox bars, which covers neighbouring tiles while they move. To letterbox yourself, use `input_info` to work out the destination rectangle and pass `preserve_aspect=0`.

## Reusable patterns (see `scripts/multiview`)

- **Animated state changes:** store a `FROM` snapshot of what's on screen and compute the `TO` target every frame. Interpolate with an eased `t = (time - t_start) / duration`. If the value changes mid-animation, take a new `FROM` from the current interpolated state.
- **Fade / crossfade to a colour:** draw the frame, then `gfx_set(r, g, b, amount); gfx_fillrect(0, 0, project_w, project_h);`. Stack several fills for several fades; the last one drawn wins at 1.
- **Keep envelopes working when replacing a script:** reuse the old `//@param` indices for the parameters that carry over. Gaps in the numbering are fine (the stock presets have them).
- **Crop to fill with a focus point:** `srcx = clamp(fx*iw - srcw/2, 0, iw - srcw)`.
- **Easing:** in-out cubic, and "back" (overshoot) for a springy feel.
