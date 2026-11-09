---
name: edit-video
description: Edit a talking-head, interview, podcast or single-shot video into a premium, retention-driven vertical video (TikTok, Reels, Shorts) and/or horizontal HD video (YouTube), entirely in code. Gives cinematic film colour, maximum sharpness, word-by-word captions, text standing behind the speaker, motion-graphics diagrams, picture-in-picture, code-written music and sound effects, thumbnails, SRT and chapters. Use this skill whenever the user hands over a video file and wants it edited, cut, captioned, colour graded, made cinematic or sharper, or turned into a TikTok or YouTube video, even if they only say "edit video này", "dựng video", "làm video dọc", "làm video ngang", "cắt thành tiktok", "làm cho youtube", "chỉnh màu phim", "làm nét hơn", "thêm phụ đề", "thêm motion graphic". Prefer it over ad-hoc ffmpeg commands for any edit longer than a simple trim.
---

# Edit Video

Turn one source video into finished deliverables through a code pipeline. One project and one `design.py` render both formats:

| Format | Size | Encode | Notes |
|---|---|---|---|
| `tiktok` | 1080x1920, 30 fps | H.264 CRF 15 | stacked layout, chips in the free zone above the head, UI-safe margins |
| `youtube` | 1920x1080, 30 fps | H.264 CRF 15 | wide two-shot, chapter rail, 8 s end card with a free right half |

HD is what the user wants for YouTube. Render 4K (`--ss 2`, CRF 18) only if they ask for it: it takes about four times as long and pushes a 16 GB machine into heavy paging.

`<skill>` below means this skill's base directory. Run the scripts by full path; they find their own modules. Talk to the user in their language.

## Before starting

Run `python <skill>/scripts/doctor.py` once per machine; missing packages are in `<skill>/requirements.txt`, and Whisper downloads its model (about 1.5 GB) on first use, so ask before installing or downloading. Then settle three things, and only ask when the request leaves one truly open:

- **Formats**: both unless the user names one.
- **Look**: `cine_warm` by default; `teal_orange` for stronger commercial contrast; `neutral` for corporate or skin-critical work.
- **Project folder**: `<working dir>/projects/<slug>`. Deliverables go to `<working dir>/output`. Never overwrite an earlier deliverable; use a new name.

Set expectations on time. On an i5 laptop a 2-minute edit from a 6-minute source takes about 20 min of transcription, 4 min for the master, 15 min for mattes (`matte.py`), and about 9 min each for the vertical and HD renders. Long steps go in the background, one heavy job at a time.

## Workflow

### 1. Set up and listen

```bash
python <skill>/scripts/init_project.py SOURCE PROJECT --look cine_warm --language vi --prompt "Cuộc trò chuyện về Claude Cowork, ChatGPT Work và GitHub."
python <skill>/scripts/transcribe.py PROJECT
python <skill>/scripts/find_faces.py PROJECT --names M,W
python <skill>/scripts/speaker_hints.py PROJECT
```

`--prompt` tells Whisper the names and jargon to expect. Write it as one natural sentence in the video's language: a bare keyword list can make Whisper skip most of the speech. `init_project` warns about thin sources; pass those warnings on. `transcribe` reports any speech it had to re-hear or could not place, so read that output. Then look at `faces_check.jpg`. Everything that sits behind a head depends on those markers, so correct `project.json` by hand when one is off. Treat `speakers.txt` as a draft: open frames for any segment with a score below about 1.3. Mouth motion is reliable, voice pitch is not. Names in `--names` go left to right.

Tested on landscape and portrait sources, 1080p and 4K, HLG and SDR, one person and two. PQ is written but has not been run on a real clip, so check a graded frame first. A portrait source makes a good vertical video, but its 16:9 version can only be a tight crop on the face, so offer the vertical alone. The camera is assumed static: a moving camera breaks the fixed face positions, so look at the footage first and say so if it does not fit, rather than forcing it. Log footage is not supported.

### 2. Decide the story: `select.json`

Read the whole transcript before cutting. This is the step that decides whether the video is any good.

- **Hook first.** Find the strongest claim or contradiction anywhere in the source and open on it. It must land inside the first 3 seconds.
- **One throughline.** Each clip either raises a question or answers one. Cut setup, repetition and asides, even good ones. A 6.5-minute talk became 2 minutes in the worked example.
- **Fix what Whisper misheard** in `fixes`. For a doubtful passage, re-listen: `transcribe.py PROJECT --range a b --prompt "expected words"`. Captions with wrong words read as careless, so check names and jargon especially.

Schema and field meanings are at the top of `scripts/build_timeline.py`; see `examples/repo-ai-agent/select.json`.

```bash
python <skill>/scripts/build_timeline.py PROJECT      # -> timeline.json, words.txt
```

`words.txt` lists every word with its output time. All design timing comes from it.

### 3. Build the picture

```bash
python <skill>/scripts/build_master.py PROJECT        # graded near-lossless master of only the used frames
python <skill>/scripts/matte.py PROJECT               # person matte for each of those frames
```

Rerun both after any change to the selected clips (`matte.py` skips frames it already has). Rerun `build_master.py` after changing the look.

### 4. Design once for both formats: `design.py`

Read `references/design-playbook.md` before writing it. Copy the shape of `examples/cowork-40s/design.py`, which is short enough to read in one go; `examples/repo-ai-agent/design.py` shows many more recipes on a 2-minute edit. Format differences go through `pick(youtube, tiktok)` and `place(ctx, yt, tk)`, so there is a single story and no second file to keep in sync.

### 5. Review stills, fix, repeat

```bash
python <skill>/scripts/render.py --project PROJECT --fmt tiktok --stills DIR auto
python <skill>/scripts/review.py stills DIR SHEET 8 2 240
python <skill>/scripts/render.py --project PROJECT --fmt youtube --stills DIR2 auto
python <skill>/scripts/review.py stills DIR2 SHEET2 3 3 640
```

`auto` gives two stills per event. Read every sheet. Then check transitions with explicit times every 0.1 s around a PiP entry and a speaker change. Look for: words on a head or clipped by the frame, chips on a face, overlaps, stale text, captions under the PiP card, a speaker framed too tight. This loop is cheap, so run it until nothing bothers you before starting a long render.

### 6. Sound

```bash
python <skill>/scripts/audio_mix.py --project PROJECT --fmt tiktok
python <skill>/scripts/audio_mix.py --project PROJECT --fmt youtube
```

Rerun after any change to cues, music sections or the timeline. You cannot hear the mix, so tell the user that and ask them to listen for level and taste. The numbers (`-14 LUFS`, peak) are checked by `finish.py`.

### 7. Render

```bash
python <skill>/scripts/render.py --project PROJECT --fmt tiktok --parallel 3 PROJECT/render/tiktok.mp4
python <skill>/scripts/render.py --project PROJECT --fmt youtube --parallel 3 PROJECT/render/youtube.mp4
```

A parallel render works through 10 s chunks and prints each one. If it is interrupted, run the same command again and it resumes. Use `--range t0 t1` for quick looks at a passage in motion. Lower `--parallel` if the machine runs short of memory.

### 8. Watch it like a viewer

```bash
python <skill>/scripts/review.py sheet VIDEO SHEET.jpg 0 118 2 8
python <skill>/scripts/review.py seq VIDEO SEQ.jpg 17.4 20
```

Judge the first 3 seconds alone, then whether something new happens every few seconds. Check the frames on both sides of several cuts. Any change to the design re-renders the whole video, so collect all the fixes for one round.

### 9. Deliver

```bash
python <skill>/scripts/finish.py --project PROJECT --fmt tiktok PROJECT/render/tiktok.mp4 NAME_TikTok --outdir OUTPUT
python <skill>/scripts/finish.py --project PROJECT --fmt youtube PROJECT/render/youtube.mp4 NAME_YouTube_HD --outdir OUTPUT
python <skill>/scripts/export_captions.py --project PROJECT --fmt youtube NAME_YouTube --outdir OUTPUT
python <skill>/scripts/thumbnail.py --project PROJECT --outdir OUTPUT
```

- `finish.py` prints PASS or FAIL for resolution, colour tags, pixel format, loudness and peak, and writes a 720p preview under 30 MB. Send previews with SendUserFile; the masters are too big, so give their paths. A FAIL means fix it, not report around it.
- Thumbnails need a `thumbs.py` in the project; see the example. For a TikTok cover, take a `--stills` frame with the strongest depth word.
- For YouTube, write title, description, tags and a pinned comment with `references/platforms.md`.

### 10. Report honestly

Say what works and what does not, based on what you checked: frames reviewed, the PASS/FAIL report, file sizes. Name what you could not verify, such as how the audio sounds. Name limits that come from the source, such as resolution and bitrate. Previews are heavily compressed, so do not judge sharpness from them, and warn the user not to.

## Editing rules

These come from real feedback on real edits. The reasons matter when a new video needs a judgement call.

- **Hook in the first 3 s, and a small new event every 2-3 s.** Depth word, chip, panel, sound, punch-in. Attention drops when the screen stops changing, but each event must carry meaning from the sentence being spoken. Decoration reads as noise.
- **Never push in tight on a face.** The user rejected it, and on a 1080p source it also softens the picture. The shot tables stay wide on purpose and stacked zooms are compressed above a knee. To make room for content, shrink the speaker into the card with `PIP`, then let them grow back. Do not zoom in to create space.
- **Text behind the person.** `depth_word` uses the matte and stays scene-locked, so it moves with the camera and never lands on another person's head. Keep it short: one to three words.
- **Diagrams explain, they do not repeat the caption.** A panel should show a relationship the sentence only describes: before versus after, a branch, a rollback. Build it in step with the words so it finishes when the sentence does.
- **Captions come from corrected words.** Keyword styling is for the two or three words per line that carry the meaning.
- **Motion is eased and connected.** Things enter along the direction of the story. Whips at speaker changes, soft settles after same-speaker cuts, no hard pop unless it is a deliberate punch.
- **Music follows the edit.** The first downbeat lands on the hook's answer, sections change with the chapters, and a brief stop before a key line gives it weight.
- **End on one sentence worth remembering** (`takeaway`).

## References

- `references/design-playbook.md`: `design.py` structure, layers, components, safe zones, sound and music cues, recipes. Read before writing a design.
- `references/look-and-sharpness.md`: how the film look and the sharpness chain work, how to tune them for new footage. Read when footage looks wrong or the user wants a different look.
- `references/platforms.md`: delivery specs, upload settings, YouTube title and description checklist. Read before writing upload notes.
- `references/gotchas.md`: hard-won failures of the toolchain. Read when something breaks.
- `examples/cowork-40s/`, `examples/repo-ai-agent/`: real projects (`select.json`, `design.py`, `thumbs.py`). The second also has a YouTube publishing kit.
