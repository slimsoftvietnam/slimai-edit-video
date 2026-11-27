---
name: slimai-edit-video
description: Edit a talking-head, interview or podcast video into a vertical (TikTok, Reels, Shorts) or horizontal HD (YouTube) video in code, in a style picked from a demo (standard, film trailer, chill vlog cut on the music's beat, or viral motion TikTok). Phone or film colour, maximum sharpness, word-by-word captions, text behind the speaker, motion graphics, picture-in-picture, code-written music and SFX, thumbnails, SRT, chapters, YouTube SEO titles and descriptions. Use it when the user hands over a video to edit, cut, caption, colour grade, sharpen or turn into a TikTok, YouTube video or trailer, even if they only say "edit video này", "dựng video", "làm video dọc", "làm video ngang", "cắt thành tiktok", "làm cho youtube", "làm kiểu trailer phim", "làm kiểu vlog chill", "cắt khớp nhạc", "hiệu ứng viral", "giữ chân 2 giây đầu", "chỉnh màu phim", "làm nét hơn", "thêm phụ đề", "thêm motion graphic", "soạn nội dung đăng youtube", "tối ưu seo youtube". Prefer it over ad-hoc ffmpeg beyond a simple trim.
---

# SlimAI Edit Video

Turn one source video into finished deliverables through a code pipeline. One project and one `design.py` render both formats:

| Format | Size | Encode | Notes |
|---|---|---|---|
| `tiktok` | 1080x1920, 30 fps | H.264 CRF 15 | stacked layout, chips in the free zone above the head, UI-safe margins |
| `youtube` | 1920x1080, 30 fps | H.264 CRF 15 | wide two-shot, chapter rail, 8 s end card with a free right half |

HD is what the user wants for YouTube. Render 4K (`--ss 2`, CRF 18) only if they ask for it: it takes about four times as long and pushes a 16 GB machine into heavy paging.

`<skill>` below means this skill's base directory. Run the scripts by full path; they find their own modules. Talk to the user in their language.

## Before starting

Run `python <skill>/scripts/doctor.py` once per machine; missing packages are in `<skill>/requirements.txt`, and Whisper downloads its model (about 1.5 GB) on first use, so ask before installing or downloading. Then settle five things:

- **Formats**: both unless the user names one. Do not ask.
- **Style**: always ask, with a demo, together with the colour, as step 1 describes, unless the request already names a style ("làm kiểu trailer phim"). The default is the standard edit. A trailer is made for TikTok; offer the 16:9 version only if they ask. The vlog style is a horizontal YouTube edit only, the motion style a TikTok edit only.
- **Colour**: always ask, with a preview, as step 1 describes, unless the request already says which colour. The default is `iphone`, the colour the phone recorded with no grade and no film grain, halation, vignette or light leaks. It also skips the denoise and the extra sharpening, and tone-maps HLG so that sunlit skin and clothes keep their texture. The user compares the edit with the original on the phone.
- **Episode**: every video is an episode, and its deliverables go in a folder of their own, `<working dir>/output/<NN>_<name>/` (step 9). The number is the one at the start of the source file name: `01_Phong_van.mov` is episode 01, and `init_project.py` records it. If the source name has no number, step 1 asks.
- **Project folder**: `<working dir>/projects/<slug>`. Do not ask. Never overwrite an earlier deliverable: a new version takes the next `_vN`.

Set expectations on time. On an i5 laptop a 2-minute edit from a 6-minute source takes about 20 min of transcription, 4 min for the master, 15 min for mattes (`matte.py`), and about 9 min each for the vertical and HD renders. Long steps go in the background, one heavy job at a time.

## Workflow

### 1. Set up and listen

```bash
python <skill>/scripts/init_project.py SOURCE PROJECT --language vi --prompt "Cuộc trò chuyện về Claude Cowork, ChatGPT Work và GitHub."
python <skill>/scripts/transcribe.py PROJECT                 # start in the background, then ask style and colour
python <skill>/scripts/look_preview.py PROJECT PROJECT/look_choices.jpg
python <skill>/scripts/find_faces.py PROJECT --names M,W
python <skill>/scripts/style_preview.py PROJECT PROJECT/style_choices.jpg
python <skill>/scripts/speaker_hints.py PROJECT
```

**Ask about style and colour on every new video**, unless the request already says which. Send `style_choices.jpg` (one frame of their video drawn in each style: three vertical frames per style, four 16:9 frames for the vlog) and `look_choices.jpg` (the same video in all four looks) with SendUserFile, then ask one AskUserQuestion with two questions. Add a third when `init_project` says the source name has no episode number. Leave out a question the request has already answered. If they want to see a style in motion, send the preview of an earlier edit in that style when one exists in the output folder. Before there is a project (the user asks what the styles look like), send `<skill>/docs/style_choices.jpg`: tập 16 drawn in all four.

Style: "Bạn muốn dựng theo phong cách nào? (xem ảnh minh họa vừa gửi)", header "Phong cách". Offer these four options in this order, the default first. A landscape source suits all four; for a portrait source leave out the vlog, which needs the wide two-shot:

| Label | Description | What it changes |
|---|---|---|
| Tiêu chuẩn (mặc định) | Nhịp nhanh, chữ đứng sau người nói, sơ đồ motion graphic, phụ đề từng chữ, nhạc nền nhẹ; ra cả bản dọc và ngang | the workflow below as written |
| Trailer phim | Mở bằng câu hỏi, màn đen chèn chữ, trống dồn, im lặng trước khi lật bài, twist ở cuối; 45-90 giây, cho TikTok | read `references/trailer.md` before step 2 |
| Vlog chill (khớp nhạc) | Nhịp chậm kiểu vlog du lịch, giữ gần hết câu chuyện, mọi nhát cắt và chữ hiện đúng phách nhạc lo-fi, thẻ chương trên cảnh hậu trường; bản ngang YouTube | read `references/vlog.md` before step 2 |
| Motion viral (TikTok) | 2 giây đầu nói rõ chủ đề: người tách nền như sticker trên nền tia sáng, tiêu đề 3D, nhạc drop; một hình ảnh xuyên suốt (như con trỏ chuột tự bấm), chữ khoét lỗ bay xuyên qua, phụ đề màu xếp tầng, kêu gọi ngay sau ý mạnh nhất; 60-95 giây | read `references/motion.md` before step 2 |

If the user describes a style of their own, use the closest one or mix them (trailer cards inside a standard edit, say), and tell them what you did. If there is no clear answer, use the standard edit. A new style needs a row here, a reference file and frames in `style_preview.py`.

Colour: "Bạn muốn video giữ màu nào? (xem ảnh 4 kiểu màu vừa gửi)", header "Màu video". Offer exactly these options, in this order: the default first, then at most three alternatives.

| Label | `--look` | Description |
|---|---|---|
| Màu gốc iPhone (mặc định) | `iphone` | Giữ nguyên màu máy quay, tươi và sáng như khi xem trên điện thoại |
| Màu phim ấm | `cine_warm` | Tông vàng ấm, cây cỏ xanh rêu, trời ngả kem; hợp cảnh ngoài trời, hoàng hôn |
| Màu phim tương phản | `teal_orange` | Da ấm trên nền xanh lạnh, tương phản mạnh; hợp quảng cáo, nội dung năng động |
| Màu trung tính | `neutral` | Vùng sáng mềm như phim, màu gần như giữ nguyên; hợp doanh nghiệp, cần màu da chuẩn |

Pass the answer to `build_master.py --look`. If the user writes their own description instead, pick the closest look and say which one you used. If there is no clear answer, use `iphone`. To show two looks side by side later, copy the project folder (keep `matte/` and `audio_*`), rebuild its master with the other `--look`, and render it.

Episode, only when the source name has no number: "Video này là tập mấy?", header "Số tập".
- Options: "Tập NN (số tiếp theo)" first, then "Không đánh số". NN comes from `episode.py --next OUTPUT`; the user may type another number.
- Then set `"episode"` in `project.json`: `NN_<name>` (`episode.normalise()` gives the form), or the name alone for "Không đánh số".

`--prompt` tells Whisper the names and jargon to expect. Write it as one natural sentence in the video's language: a bare keyword list can make Whisper skip most of the speech. `init_project` warns about thin sources; pass those warnings on. `transcribe` reports any speech it had to re-hear or could not place, so read that output. Then look at `faces_check.jpg`. Everything that sits behind a head depends on those markers, so correct `project.json` by hand when one is off. Treat `speakers.txt` as a draft: open frames for any segment with a score below about 1.3. Mouth motion is reliable, voice pitch is not. Names in `--names` go left to right.

Tested on landscape and portrait sources, 1080p and 4K, HLG and SDR, one person and two. PQ is written but has not been run on a real clip, so check a graded frame first. A portrait source makes a good vertical video, but its 16:9 version can only be a tight crop on the face, so offer the vertical alone. The camera is assumed static: a moving camera breaks the fixed face positions, so look at the footage first and say so if it does not fit, rather than forcing it. Log footage is not supported.

### 2. Decide the story: `select.json`

Read the whole transcript before cutting. This is the step that decides whether the video is any good.

- **Hook first.** Find the strongest claim or contradiction anywhere in the source and open on it. It must land inside the first 3 seconds.
- **One throughline.** Each clip either raises a question or answers one. Cut setup, repetition and asides, even good ones. A 6.5-minute talk became 2 minutes in the worked example.
- **Fix what Whisper misheard** in `fixes`. For a doubtful passage, re-listen: `transcribe.py PROJECT --range a b --prompt "expected words"`. Captions with wrong words read as careless, so check names and jargon especially.

Schema and field meanings are at the top of `scripts/build_timeline.py`; see `examples/repo-ai-agent/select.json`. A trailer has a shape of its own (hook, the old way, the turn, the reveal, the escalation, the twist and the title) and leaves silences for its black cards with `gap_after`; see `references/trailer.md` and `examples/ai-agent-trailer/select.json`. A motion cut follows the trailer's shape with the hook and the call to act placed as `references/motion.md` says; see `examples/playwright-tiktok/`. A vlog cut is written as `vlog_cut.json` (speech clips, chapter cards, B-roll) and `beat_fit.py` turns it into `select.json` with every cut on the music's beat; see `references/vlog.md` and `examples/playwright-vlog/`.

```bash
python <skill>/scripts/build_timeline.py PROJECT      # -> timeline.json, words.txt
```

`words.txt` lists every word with its output time. All design timing comes from it.

### 3. Build the picture

```bash
python <skill>/scripts/build_master.py PROJECT --look iphone    # the colour the user chose; near-lossless master of the used frames
python <skill>/scripts/matte.py PROJECT               # person matte for each of those frames
```

Rerun both after any change to the selected clips (`matte.py` skips frames it already has). Rerun `build_master.py` after changing the look.

### 4. Design once for both formats: `design.py`

Read `references/design-playbook.md` before writing it. Copy the shape of `examples/cowork-40s/design.py`, which is short enough to read in one go; `examples/repo-ai-agent/design.py` shows many more recipes on a 2-minute edit. Format differences go through `pick(youtube, tiktok)` and `place(ctx, yt, tk)`, so there is a single story and no second file to keep in sync. A trailer adds `from trailer import *` (curtain cards, flash frames, pills for text over the sky, the typed prompt, the title slam) and registers its score with `score()`; copy the shape of `examples/ai-agent-trailer/design.py`. A motion design adds `rawgroups` captions, `fx.py` effects, `ui.py` pieces and a licensed track (`track_music.py`); copy `examples/playwright-tiktok/design.py`. A vlog design starts with `from vlog import *` and `setup()`, takes its times from `on(clip, word)` so graphics land on the beat, and registers the music's sections in `ARRANGE`; copy `examples/playwright-vlog/design.py`. Take times from `word_in(beat, word)`, `beat_start(beat)` and `beat_end(beat)`, so a recut does not move them.

When two people are on camera and the listener's face matters, as in a question or a reaction to the twist, the TikTok cut can show both at once. `split_screen(t0, t1)` puts the man on top and the woman below, a layout the user asked for. Keep it to a line or two, on cuts (playbook, section 6; `examples/mcp-trailer/`).

### 5. Review stills, fix, repeat

```bash
python <skill>/scripts/render.py --project PROJECT --fmt tiktok --stills DIR auto
python <skill>/scripts/review.py stills DIR SHEET 8 2 240
python <skill>/scripts/render.py --project PROJECT --fmt youtube --stills DIR2 auto
python <skill>/scripts/review.py stills DIR2 SHEET2 3 3 640
```

`auto` gives two stills per event. Read every sheet. Then check transitions with explicit times every 0.1 s around a PiP entry, a speaker change and a split screen edge. Look for: words on a head or clipped by the frame, chips on a face, overlaps, stale text, captions under the PiP card, a speaker framed too tight. This loop is cheap, so run it until nothing bothers you before starting a long render.

### 6. Sound

```bash
python <skill>/scripts/audio_mix.py --project PROJECT --fmt tiktok
python <skill>/scripts/audio_mix.py --project PROJECT --fmt youtube
```

Rerun after any change to cues, music sections or the timeline. The mix follows the style through a preset (the first line it prints): `standard` (the composed music), `score` (a design with `score()` events gets the trailer score instead), `score_solo` (a motion edit with a licensed track: its end card is levelled on its own; set by `MIX = "score_solo"` in design.py) and `vlog` (music on the beat grid, B-roll muted under the music; `vlog.setup()` sets it, see `references/vlog.md`). `--preset` overrides it. You cannot hear the mix, so tell the user that and ask them to listen for level and taste. The numbers (`-14 LUFS`, peak) are checked by `finish.py`.

### 7. Render

```bash
python <skill>/scripts/render.py --project PROJECT --fmt tiktok --parallel 2 PROJECT/render/tiktok.mp4
python <skill>/scripts/render.py --project PROJECT --fmt youtube --parallel 2 PROJECT/render/youtube.mp4
```

A parallel render works through 10 s chunks and prints each one. If it is interrupted, run the same command again and it resumes. Use `--range t0 t1` for quick looks at a passage in motion. It uses fewer workers than asked when free memory is short, and renders a failed chunk once more on its own.

### 8. Watch it like a viewer

```bash
python <skill>/scripts/review.py sheet VIDEO SHEET.jpg 0 118 2 8
python <skill>/scripts/review.py seq VIDEO SEQ.jpg 17.4 20
```

Judge the first 3 seconds alone, then whether something new happens every few seconds. Check the frames on both sides of several cuts. Any change to the design re-renders the whole video, so collect all the fixes for one round.

### 9. Deliver

```bash
python <skill>/scripts/episode.py PROJECT OUTPUT TikTok          # prints EP_DIR, then TK, e.g. 01_Phong_van_TikTok_v1
python <skill>/scripts/finish.py --project PROJECT --fmt tiktok PROJECT/render/tiktok.mp4 TK --outdir EP_DIR
python <skill>/scripts/episode.py PROJECT OUTPUT YouTube_HD      # prints EP_DIR, then YT, e.g. 01_Phong_van_YouTube_HD_v1
python <skill>/scripts/finish.py --project PROJECT --fmt youtube PROJECT/render/youtube.mp4 YT --outdir EP_DIR
python <skill>/scripts/export_captions.py --project PROJECT --fmt youtube YT --outdir EP_DIR
python <skill>/scripts/thumbnail.py --project PROJECT --outdir EP_DIR --prefix YT
python <skill>/scripts/youtube_meta.py suggest "TOPIC" "TOPIC là gì"
python <skill>/scripts/youtube_meta.py measure EP_DIR/YT_kit.txt --keyword "TOPIC là gì"
```

- **One folder per episode.** `OUTPUT` is `<working dir>/output`, and `EP_DIR` is `OUTPUT/<episode>`, with the episode taken from `project.json`.
  - **Names.** Every file of a deliverable starts with its name: the video, `_preview_1080p.mp4` (`_preview_720p.mp4` for a long video), the TikTok cover `_cover.jpg`, `.srt`, `_chapters.txt`, `_kit.txt`, the thumbnails and `_nguon.txt`, the notes for the user: what was cut and why, the words corrected by guess, every illustration added.
  - **Variants.** `TikTok`, `TikTok_trailer`, `YouTube_HD`. A motion cut is a `TikTok_trailer` and a vlog cut a `YouTube_HD`, as tập 16 went out (`16_Playwright_TikTok_trailer_v1`, `16_Playwright_YouTube_HD_v1`). A second colour adds its look, as in `TikTok_cine_warm`.
- **Only the newest version stays on top.** When a new version passes, `finish.py` moves the earlier versions of that variant into `ban_cu/`. Comparison sheets and tests go in `so_sanh/`. Leave nothing loose in `OUTPUT`.
- `finish.py` prints PASS or FAIL for resolution, colour tags, pixel format, loudness, peak, the frame count, the soundtrack's length and whether the mix is newer than the design (a FAIL there means mix again; `--force` ships it with a WARN), and writes a 1080p preview under 30 MB (720p for a video longer than about 2.8 minutes). Send previews with SendUserFile; the masters are too big, so give their paths. A FAIL means fix it, not report around it.
- Thumbnails need a `thumbs.py` in the project; see the example. Name its `THUMBS` keys `thumbnail_A.jpg`, `thumbnail_B.jpg`, so that `--prefix` gives them the deliverable's name. For a TikTok cover, take a `--stills` frame with the strongest depth word and save it as `EP_DIR/TK_cover.jpg`.
- For YouTube, write the publishing kit as `references/platforms.md` describes: keywords from YouTube's own suggestions, three titles for Test & Compare, the description, tags, pinned comment and upload notes. Check it with `measure`, and put the parts the user will paste into the reply as well. Thumbnails come from the master in the colour the user chose.

### 10. Report honestly

Say what works and what does not, based on what you checked: frames reviewed, the PASS/FAIL report, file sizes. Name what you could not verify, such as how the audio sounds. Name limits that come from the source, such as resolution and bitrate. For example, a vertical cut of a 1080p landscape source is a 1.78x blow-up, and the iPhone plays the original in HDR. Previews are heavily compressed, so do not judge sharpness from them, and warn the user not to.

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
- `references/platforms.md`: delivery specs, upload settings, and the YouTube publishing kit: keywords, titles for Test & Compare, description, tags. Read before writing the kit.
- `references/trailer.md`: the trailer style: its shape, cards and gaps, the twist, the kit and the score. Read before cutting a trailer.
- `references/motion.md`: the motion style: the 2-second hook, the motif, the reveal, the raw.to.reel captions (`rawstyle.py`, `rawgroups.py`), the effects (`fx.py`, `ui.py`), a licensed track (`track_music.py`, `music_analyse.py`, the `score_solo` mix). Read before cutting one.
- `references/vlog.md`: the vlog style: its shape, the beat-fitted cut (`vlog_cut.json`, `beat_fit.py`), the design kit (`vlog.py`, `ui.py`), the music and mix. Read before cutting a vlog.
- `references/gotchas.md`: hard-won failures of the toolchain. Read when something breaks.
- `examples/cowork-40s/`, `examples/repo-ai-agent/`: real projects (`select.json`, `design.py`, `thumbs.py`). The second also has an earlier YouTube kit; `examples/playwright-vlog/youtube_kit.txt` is a kit in the current format. `examples/ai-agent-trailer/` is an 88 s trailer with its TikTok cut and its 16:9 YouTube version from one design, the one to copy (`select.json`, `design.py`, `thumbs.py`), and `examples/vibe-code-trailer/` an earlier 55 s TikTok-only one. `examples/mcp-trailer/` is an 89 s TikTok trailer that spells a term out letter by letter and shows both people in a split screen. `examples/playwright-tiktok/` is the motion style's 89 s TikTok cut of the same talk (`select.json`, `design.py`, `project.json`). `examples/playwright-vlog/` is a 4:44 YouTube vlog cut on the music's beat (`vlog_cut.json`, `design.py` with its second half `design_b.py`, `pieces.py`, `thumbs.py`, `youtube_kit.txt`).
