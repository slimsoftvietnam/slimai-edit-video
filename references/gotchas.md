# Gotchas

Failures that actually happened, and what fixed them.

## Toolchain

- **skia-python must stay on 87.9.** Version 144.x was about 100x slower here on translucent fills. `doctor.py` warns.
- **Translucent solid fills in skia 87.9 are slow**; `engine.fill()` routes them through a 2-stop gradient shader. Heavy per-pixel work uses OpenCV uint8 ops, not numpy floats.
- **`cv2.subtract(array, np.uint8(x))` fails on OpenCV 5.** Use `np.full_like(array, x)`.
- **`cv2.imwrite` fails silently when the folder is missing or the path has some Unicode characters.** Create the folder first and check the result.
- **Windows `open()` defaults to the system code page.** Always pass `encoding="utf-8"` and run with `PYTHONIOENCODING=utf-8`, or Vietnamese crashes.
- **`multiprocessing` on Windows re-imports the main script**; keep argument parsing under `__main__` and pass settings through env, as `render.py` does.
- **Long shell heredocs for patches can fail with "unexpected EOF"**. Write a file, then run it.
- **Foreground `sleep` may be blocked** by the environment; run long jobs in the background.
- **Memory at 4K decides the render speed.** On a 16 GB laptop with Chrome open, three 4K workers at 2.1 GB each pushed Windows to 57,000 page faults per second, and a 40 minute render was heading for 3 hours while the whole machine crawled. The fix cut each worker to about 1.2 GB: skia draws directly into numpy arrays, reused float buffers, one grain field read at shifting offsets, 2 decoder threads, 3 encoder threads and a shorter lookahead at 4K. If the first chunks are still slow (compare ms/f in the log with `--range` on one process), use `--parallel 2`.
- **Never trust a render's ETA from memory; check the first chunks.** A parallel render prints each finished chunk, and a rerun resumes from there.
- **Killing a parallel render on Windows leaves its workers and ffmpeg children running.** Check with `Get-CimInstance Win32_Process` and stop only the ones whose command line is yours.

## Rendering

- **Stale pixels and flicker on diacritics.** Stacked Vietnamese marks (Ấ, Ế, Ỗ) rise above the font ascent. A partial clear left old pixels behind in 20 frames of one delivered video. `Layer.begin()` now always clears everything and `draw_text` marks real glyph bounds.
- **Anything drawn without `L.mark()` never reaches the frame.**
- **Depth words collided** with the other person's head, the rail, and the top of frame until the placement logic got `HEADBOX`, `label_right` and `glyph_top`. Keep those fields of `project.json` accurate.
- **Chips anchored to screen coordinates** landed on a face after a cut. On 16:9 use scene-locked `anc()` offsets.
- **Ultra-short shot segments flicker**, so segments under 0.5 s merge into the previous one.
- **Zero-length round-cap lines draw a dot.** Check the progress is above 0 before drawing an animated underline.

## Colour

- **HLG/PQ needs the transfer decoded before the LUT.** A LUT on the wrong transfer looks plausible and then wrong on skin. `init_project.py` records the transfer; check it for files with missing metadata.
- **SDR needs its highlights expanded before the tone map.** The tone map expects scene light far above 1.0, so plain SDR white landed at 70% grey and every SDR clip looked murky. `film_look.decode` now restores that headroom. HLG was never affected, which is why the first real video hid the bug; it took a test on another source type to find it. Look at a graded frame on any new kind of source.
- **Log footage is not supported yet.** S-Log, D-Log and the like would be read as SDR and look flat. It needs a camera-specific decode added to `film_look.decode`. Say so rather than grading it blind.
- **JPEG stills show an 8 px lattice on blurred backdrops.** That is the JPEG, not the render. Confirm on PNG before chasing it.
- **Colour tags**: `finish.py` rewrites H.264 VUI to BT.709 so that players do not guess.

## Speech

- **Whisper mishears names and jargon.** Give a prompt, then correct by hand. Re-hear doubtful passages with `--range`, beam search is on there.
- **A keyword-list prompt can make Whisper drop nearly everything, with no error.** Given "Claude Cowork, ChatGPT Work, repo, GitHub, ..." on a 54 s clip, it returned one sentence shaped like the prompt and treated the rest as silence. Write the prompt as one natural sentence in the video's language. `transcribe.py` now compares the words with the audio's speech envelope and re-hears any skipped stretch without the prompt. Read what it prints, and read the transcript before trusting it.
- **Do not run Whisper while a 4K render is going.** A 2 minute job took 40 minutes.
- **Whisper word times drift at pauses.** `build_timeline.py` refines cuts on the audio envelope. Use `hard` in `select.json` when it still clips a syllable.
- **Pitch-based speaker labels failed**: an excited male voice read as female. Raw mouth motion works: 55 of 55 clips checked by eye. Normalising it per person was far worse (22 of 38). Verify by eye anyway.

## Mattes

- Mattes are per source frame, named `{frame:06d}.png`; frame numbers assume `fps` from `project.json`. Changing `fps` invalidates them.
- RVM's recurrent state needs a few frames to settle; `matte.py` primes on the first frame.
- The matte is soft on thin hair and fingers, which suits text behind heads, but avoid a bright word directly behind fine hair.

## Environment limits

- The SendUserFile limit is 30 MiB: send previews, give paths for masters.
- You cannot hear audio. Check levels by numbers and say that taste is unverified.
- You see stills, not motion. Frame sequences show timing and direction, but not everything, so ask the user to watch it.
