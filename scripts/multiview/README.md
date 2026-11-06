# multiview

Shows 1, 2, 3, 4 or 6 videos in a grid. When you change the number of videos, the tiles animate into their new positions.

## Setup

1. Put the video sources on separate tracks.
2. Put a **Video processor** on a track **below** them (the same place as REAPER's stock 2x2 preset).
3. Paste the contents of [`multiview.eel`](./multiview.eel) into its code editor and save it as a preset.
4. Automate **Videos** to switch layouts during the project.

Video slots are numbered the same way as in the stock preset (`input_track(0)` is video 1).

## Layouts

```
1:  [1]

2:  [1] [2]

3:  [2] [1] [3]

4:  [1] [2]
    [3] [4]

6:  [2] [1] [3]
    [4] [5] [6]
```

5 rounds up to 6.

## Parameters

| # | Name | Range | Default | What it does |
|---|---|---|---|---|
| 1 | Videos | 1–6 | 4 | Number of videos (1/2/3/4/6). |
| 2 | Transition length | 0–3 s | 0.6 | Length of the layout animation. 0 = cut. |
| 3 | Transition | 0–2 | 0 | 0 = zoom (tiles grow/shrink from their centre and fade), 1 = spring (zoom with a little overshoot), 2 = slide (tiles enter/leave through the nearest frame edge). |
| 4 | Gap | 0–80 px | 0 | Space between tiles and around the edge. |
| 5 | Crop to fill | 0/1 | 0 | 0 = fit the whole video in its tile, with bars. 1 = crop the video so it fills the tile. |
| 6 | Background brightness | 0–1 | 0 | Colour behind the tiles, black to white. |
| 7–18 | V1–V6 focus X / Y | 0–1 | 0.5 | Only with Crop to fill: where the subject is in each source video (0 = left/top, 1 = right/bottom). The script keeps that point as close to the tile centre as the crop allows. |

## Notes

- Transitions animate only while the transport is running. If you change **Videos** while stopped, or after a seek or loop jump, the new layout appears straight away.
- If you change **Videos** again in the middle of a transition, the tiles carry on from where they are, so the movement stays smooth.
- With landscape footage, the 2-up, 3-up and 6-up tiles crop only the sides, so only the focus **X** values matter. Focus **Y** matters for portrait or square footage.
- Automate a focus X/Y if the subject moves around the frame.

## Test checklist (in REAPER)

- [ ] Loads without a compile error.
- [ ] Each layout (1, 2, 3, 4, 6) matches the diagram above.
- [ ] Each transition style animates every layout change, including 1 → 6 and 6 → 1.
- [ ] Changing layout mid-transition stays smooth.
- [ ] Stopped transport: changing Videos switches at once.
- [ ] Crop to fill + focus: moving focus X pans the crop and never shows black edges.
- [ ] Gap and background behave at 0 and at max.

## Changelog

### 1.3.0
- New 3-video layout: `[2] [1] [3]`. 3 no longer rounds up to 4.

### 1.2.0
- In 6-video mode, video 1 takes the top-centre position and video 2 moves to top-left.

### 1.1.0
- Per-video focus X/Y for Crop to fill.

### 1.0.0
- First version: 1/2/4/6 layouts, zoom/spring/slide transitions, gap, crop to fill, background.
