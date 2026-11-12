# Film look and sharpness

The default look is `iphone`: the camera's own colour, no grade (see Looks below). Everything in the next section applies only when the user asks for a film look.

## The film look: a real print pipeline, not a filter

`scripts/film_look.py` builds a 65-point 3D LUT that runs directly on the camera signal:

1. **Decode** the camera transfer to scene-linear light (`hlg`, `pq`, `sdr`). Grading before any 8-bit step is what keeps skies and skin smooth. SDR has no real highlight data, so its top end is expanded to give the tone map something to roll off; clipped skies stay clipped.
2. **Filmic tone map** (AgX-style). Highlights roll off and lose saturation gradually, so bright skies stay soft instead of clipping to flat white or yellow. This is most of what makes it read as film.
3. **Print look in OKLab**: selective hue moves with a lightness gate, subtractive density, an S-curve, split toning, black and white points.
4. **Display gamma 2.2**, BT.709.

Spatial film effects cannot live in a LUT, so `engine.Finish` applies them per frame: halation (warm glow bleeding from highlights into dark edges), a vignette and luminance-weighted fine grain. Overlays on `ctx.front` and `ctx.ui` sit above the finish, so type stays clean.

### Looks

| Look | Character | Use |
|---|---|---|
| `iphone` | no grade: the camera's colours on an ordinary screen | **default**: the user prefers the phone's own colour |
| `cine_warm` | golden print, deep moss greens, natural skin | on request: outdoors and warm interiors |
| `teal_orange` | stronger hue separation, cooler greens | on request: commercial, high energy |
| `neutral` | filmic roll-off, no hue moves | on request: corporate, skin-critical |

`iphone` skips the film tone map and the print look, and on an HLG source it skips the LUT as well. `build_master.py` decodes HLG with zscale (BT.2100, nominal peak 250 nits, `film_look.IPHONE_NPL`), then applies ffmpeg's Möbius tone map without desaturation (`film_look.iphone_vf`).

- **Why the change.** The first version placed HDR reference white just under screen white and rolled every brighter value off into the last few percent. A talk shot in direct sun went pale and flat: the user called it "mờ và nhòe" and asked for the iPhone original.
- **The test.** A plain crop through the Möbius tone map kept the knit of a light shirt and the form of a sunlit face. The look now matches that crop.
- **Tried and rejected.** Möbius at 203 and 300 nits, Hable at 400, and Möbius at 1000. 250 matched the original best.
- **Other sources.** SDR passes through. PQ still uses the older `natural()` model, which has not been run on a real clip.

No conversion can reproduce HDR playback on an iPhone screen, where highlights go brighter than white. Say so when the user compares the edit with the original on the phone. For this look:

- `render.py` turns off grain, halation, vignette and light leaks;
- `build_master.py` skips the temporal denoise;
- `engine.py` skips the detail pass (see Sharpness).

Set it with `init_project --look`, or `"look"` in `project.json`, then rerun `build_master.py`. `look_preview.py` shows all four looks on one frame. To test a film look on stills without touching the project:

```bash
python <skill>/scripts/film_look.py cine_warm hlg look.cube
ffmpeg -ss 10 -i SOURCE -frames:v 1 -vf "zscale=filter=lanczos:min=2020_ncl|709:rin=limited|full:r=full,format=gbrpf32le,lut3d=file=look.cube:interp=tetrahedral,format=rgb24" still.png
```

For the `iphone` look on HLG, `film_look.source_frame(SOURCE, t, (w, h), "hlg", iphone=True)` returns the frame exactly as the master grades it.

### Tuning for new footage

Selective entries are `(center hue, width, hue shift, chroma gain, lightness gain[, L gate])`, in OKLab degrees. Hue windows are specific to what is in the shot, so **measure first** rather than guessing: sample the grass, sky, skin and clothes in OKLab after the tone map.

Measured on the worked example: grass h 115-121, C .11, L .65-.75; sky h 80, C .02-.04, L .9; skin h 38-48, C .065, L .72-.75.

What went wrong there, and why it matters:

- A green window centred on 138° when the grass sat at 118° turned grass into straw and turquoise.
- A sky window without a lightness gate caught mixed chroma at skin/grass edges and painted an orange fringe around cheeks and ears. Sky entries use an L gate of 0.80.
- Skin chroma gain above about 1.2 starts to look sunburnt. Check faces after any change.

The grey gate `smooth(0.006, 0.03, C)` protects near-neutral colours such as grey clothes from selective moves.

Finish overrides in `project.json`: `{"finish": {"grain": 1.3, "halation": 0.7, "vignette": 0.20, "detail": 1}}`. Env `EDIT_GRAIN`, `EDIT_HALATION`, `EDIT_DETAIL` for tests.

## Sharpness: every step that used to lose detail

Sharpness is mostly **not losing it**. Applying a stronger sharpen at the end only makes noise and halos more visible.

| Step | What it does | Why |
|---|---|---|
| Grade in float | no 8-bit step before the LUT | avoids banding and early rounding |
| Temporal denoise | `atadenoise` before grading, film looks only (`--denoise` forces it for `iphone`) | static-camera grain and macroblock boil drop (grass flicker 0.54 -> 0.35) while edge detail is unchanged, so the encoder spends bits on real detail. The `iphone` look keeps the phone's own texture, because the user compares it with the original |
| Near-lossless master | x264 4:4:4 CRF 6 of only the used frames | no generation loss, no chroma smear on edges |
| Wide shots | zoom 1.0-1.15 on vertical, 1.08-1.28 on 16:9 | every 10% of zoom is 10% less real resolution, and the user dislikes tight faces anyway |
| Detail pass | luma Richardson-Lucy deconvolution matched to the zoom, with coring and a local min/max clamp; film looks only (`EDIT_DETAIL=1` or `"finish": {"detail": 1}` turns it on for `iphone`) | restores what the scale softened; the clamp blocks digital halos and the coring leaves codec noise alone |
| Vector overlays | graphics drawn natively at device resolution | always razor sharp, which also lifts perceived sharpness |
| Generous encode | x264 CRF 15 preset slow, `aq-mode=3`, low deblock, slight psy trellis | gives the platform's encoder clean detail to work from |
| 4K, only if asked | `--ss 2`, CRF 18 | see `platforms.md`; the default is HD |

### Honest limits

- **The source sets the ceiling.** A 1080p phone clip at 8.6 Mbps has no more real detail than that; compression already removed the finest texture. The biggest possible gain is shooting 4K at a high bitrate. A 4K source needs no upscale on vertical at all.
- **Phone sharpening is baked in.** Light outlines around shoulders against grass come from the camera's own processing. Deconvolution cannot remove them.
- **AI upscaling was deliberately left out.** On this CPU it costs hours per minute of video, it can flicker and invent faces, and it needs a model download. If a user wants it, treat it as a separate pass on a machine with a GPU, and compare frames honestly.
- **Grain does not survive platform encoders at low bitrate, and does not harm them.** In a test at 4 Mbps, detail measures (Laplacian on face, shirt, grass) were equal within noise for grain 0, 1 and 2. Keep grain subtle, for texture on the delivered file and on high-bitrate playback. Grain 1.0 costs about 10% more file size, grain 2.0 about 65%.
- **A vertical cut from a 1080p landscape source is a 1.78-1.98x blow-up.** The user compares it with the original on the iPhone, at full resolution and in HDR. Say so plainly when they compare.
- **Judge sharpness on the delivered file**, never on the preview (1080p at about 2.5 Mbps for a 90 s video).

### Measuring

Compare crops at 100%, not whole frames, and read numbers next to your eyes: `cv2.Laplacian(gray, cv2.CV_32F).var()` on a static region. A higher number with visible halos is worse, not better.

When the user says the edit looks soft or hazy next to the original, run a controlled test before changing anything:

1. Make a plain crop of the same source frame with ffmpeg: no look, no denoise, no sharpening.
2. Scale it to the render's view. Template-match it to place it exactly.
3. Compare 100% crops of the face and the clothes against our master and the render: Laplacian variance, and luma mean and spread.

This test found that the old `iphone` look was flattening sunlit highlights. Sharpness and the flash frames were not the cause.

### Shooting advice for the user

Worth mentioning when relevant: 4K, highest bitrate or ProRes if the phone has it, tripod, sun behind the camera or to the side, lock exposure and focus, external mics per person. Faces at least 15% of frame height help matte quality.
