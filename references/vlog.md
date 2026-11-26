# Vlog cut: chill, on the music's beat

For a request like "kiểu vlog du lịch", "thật chill", "nhịp chậm", "khớp nhạc", or the style "Vlog chill (khớp nhạc)" picked from the demo. It is a calm, chaptered YouTube edit of a conversation that keeps most of what was said, and its picture moves with the music: every cut, every graphic and every reframe lands on a beat of a lo-fi track written in code for that cut. The user asked for it on tập 16 (Playwright, 2026-11-25): "phong cách tiêu chuẩn thật chill kiểu vlog du lịch", then "biên tập hình nên khớp beat nhạc mới tạo cảm xúc", and put it in the skill after watching it.

- **Worked example:** `examples/playwright-vlog/` (4:44 from a 6.5-minute talk, two people outdoors, 7 chapters, `cine_warm`). Copy its shape.
- **Format:** the horizontal YouTube cut only (1920x1080). It has not been designed for 9:16; offer the standard edit or the trailer for TikTok.
- **Source:** a landscape two-shot (or one person) from a static camera. The B-roll comes from the same file: the minutes before and after the talk, people listening, setting up, laughing, walking off.
- **What stays from the standard edit:** word captions, words behind the speaker, chips, diagrams in the picture-in-picture stage, the end card, the colour question (warm film looks suit it), lowercase titles.

## Shape

| Part | Length | What happens |
|---|---|---|
| Opening | 4 beats (2.9 s) | A J-cut: B-roll of the shoot (she walks in and sits down) while the first speaker's voice already asks the episode's question. The title block stands over the sky on the side away from the people: kicker "tập NN · chủ đề", the question in two lines, its key phrase in amber serif with a marker line on beat 4. On the bar-2 downbeat the picture cuts to the speaker. |
| Chapters | 5-8 | Each one starts on a downbeat, after a **chapter card**: 2 beats of silent B-roll with "02 / 07", a rule and the title in cream serif italic. A small tag at the top left names the chapter for its first 2.4 s. |
| Inside a chapter | | The talk, cut at its natural pauses. Wide and medium shots alternate every two bars (cuts on bar lines). Ideas pop on beats: words behind the speaker, plates in the top band, chips at the frame's edge beside the speaker, a paper card for a definition, a diagram in the stage for a worked example (the speaker shrinks into the card in half a beat and grows back on the next clip's cut). |
| Ending | 4 + 6 beats + end card | After the last line the picture holds 4 beats on the reaction (a laugh), with the music only. Then a B-roll ending starts on a downbeat, ideally mirroring the first shot (she walks off to stop the camera). The end card comes up over it: the one line to remember, and the call to comment. |

The music carries the mood: calm under questions and summaries, fuller under the worked examples, a fill under every card, a small bell on every chapter's downbeat, a lift for the last chapter and an outro under the ending.

## Cut: `vlog_cut.json` and `beat_fit.py`

**Own project folder.** Copy `transcript.json` (with its word fixes and merged re-listens), `audio16k.wav`, `audio48k*.wav`, `project.json` and `matte/` from the main project. Set `"look"` and `"episode"` in `project.json`. Then:

```bash
python <skill>/scripts/beat_fit.py PROJECT --show    # vlog_cut.json -> select.json, beats.json, end_hold
python <skill>/scripts/clamp_words.py PROJECT        # word edges into the clips
python <skill>/scripts/build_timeline.py PROJECT     # keep_pauses: the pauses are already timed
python <skill>/scripts/build_master.py PROJECT --look cine_warm   # adds the overlay frames ("extra")
python <skill>/scripts/matte.py PROJECT
```

The schema is at the top of `scripts/beat_fit.py`. What matters when writing it:

- **Keep the talk.** A vlog cut keeps most of the conversation and its warm asides. Cut repetition, false starts, lines Whisper could not make out (never caption a guess), off-script talk, and exchanges too thin to stand alone.
- **One clip per breath of thought**, from the first word to the last, in story order. A sentence that continues in the same take after a pause can stay one clip: `beat_fit` keeps its pauses as they are.
- **Chapters at the questions.** Mark the first clip of each chapter with `"chapter": n` and put a card before it: `{"beat": "card3", "broll": 6.6, "card": true}`. A card's B-roll is 2 beats (about 1.5 s) from a moment with no speech you want, or with speech you will mute: people settling, listening, between takes.
- **The opening overlay**: `"overlays": [{"src": 1.9, "at": "open", "beats": 4, "zoom": [1.0, 1.045], "focus": [0.5, 0.52]}]`.
- **The end**: `"hold_beats": 4` on the last spoken clip, then the ending B-roll as the last clip (`"beats": 6`); `"end_hold_beats": 4` for the end card's last frames.
- **Beat:** `"beat_frames": 22` at 30 fps is 81.8 BPM, an unhurried lo-fi pulse. It must be even. A faster talk can take 20 (90 BPM).

**Check the table `beat_fit.py --show` prints before building anything.** For every speech clip it measured the first and last sound (`s..e`) from the audio near Whisper's times, and the silence around them. Whisper's word times are often 0.1-0.3 s off, in both directions:
- A start can be late and clip the first word (tập 16 had "Tất" at 255.15 s, Whisper said 255.46). Look at the words and sound runs printed under the clip.
- A start can catch the end of the word before. Pin `s` (or `e`) in the clip.
- A line that starts or ends mid-sentence is flagged "mid-speech": set `cut_in` / `cut_out` at a low point between words.
- `adj` true means the next clip continues the same take after one pause. The two clips then share that pause, so its silence is not counted twice.

The fit then chooses how much of each clip's silence to keep so that each cut lands on a beat. Where a speaker talks straight on with no silence to spare, the cut lands on a half beat instead. It lists any cut it could not place on the grid ("OFF THE GRID"): give that clip more room (`tail_av`, `lead_av`) or end it at another pause.

## Design: `scripts/vlog.py`

```python
from vlog import *          # the story kit plus the vlog kit
import vlog as V
import ui as U              # mock software pieces: window, field, button, cursor, chat bubble, code panel

TITLES = {1: "AI tự điều khiển máy tính?", 2: "playwright là gì?", ...}           # lowercase
setup(TITLES, yt_chapters={1: "AI tự điều khiển máy tính bằng cách nào?", ...}, tag_holds={1: 2.6}, no_tags=(7,),
      pip_view={"M": (800, 12), "W": (720, -22)})
V.ARRANGE.update({1: [(1, "intro", "main"), (2, "stroll", "main"), (5, "light", "main")], ...})
```

`setup()` does the fixed parts: the reframing every two bars, the cards and tags, captions off over B-roll, a 2 % push on each chapter's downbeat, light leaks at the cards, soft automatic cues, clean cuts into and out of B-roll, the YouTube chapter list, and the opening overlay. The design writes only the content, chapter by chapter.

- **Timing.** Take every time from `on(clip, word)`: the word's time moved to the nearest half beat. A graphic that pops on the beat also lands within 0.18 s of its word. `qb()` snaps to whole beats, `gb(n)` is beat n, and `bar(ch, n, beat)` is a position in a chapter. A sequence of actions (four steps re-running, twenty ticks) moves at half or quarter beats.
- **Where things go on 16:9.**
  - The top band (y 120-300) holds plates and chips; both heads sit lower. `mini()` plates go two side by side (cx 680 and 1250, cy 212, about 540x156) or three (cx 372, 960, 1548).
  - `side_chip()` puts a short chip at the frame's edge beside a speaker, at shoulder height: three or four words.
  - Words behind the speaker (`depth_word`): serif italic amber for questions and feelings ("làm sao?", "kịch bản?"), black with a mint gradient for terms ("playwright", "đọc mã").
  - Captions stay at y 968.
- **Diagrams** go in the stage (`panel()`, about 600 px tall) with a `PIP` window that starts half a beat before the word that opens it and ends on the next clip's cut. Let the panel stay to that cut (`t1 = PIP end + 0.25`), so it leaves while the speaker grows back. Show what is to come as empty slots (`step_slot()`), fill each step on its word, and replay a sequence at half beats when the speaker says "run it again".
- **A paper card** (`paper()` inside `tilt()`, -2°) holds a definition or a takeaway: serif title, an italic line under it. Phonetic symbols need `ipa_font()`.
- **Mock software** comes from `ui.py`: a browser window, fields typed letter by letter, a button that presses, a cursor that clicks and leaves a ripple, chat bubbles, a code panel. Draw plain generic shapes. A brand name may appear as text, but no logos or copied screens. Say in the notes that they are illustrations.
- **Palette.** Mint for the concept, amber for emphasis, coral for the problem, sky for the second thing. The cards are cream on a soft shade, the plates dark glass.
- **Avoid**:
  - words behind a speaker over B-roll (the matte belongs to the clip underneath);
  - chips that run under the other person;
  - punch-ins beyond the downbeat pushes;
  - booms. The music's fills carry the transitions.

## Sound: `vlog_mix.py`

```bash
python <skill>/scripts/vlog_mix.py --project PROJECT            # music, cues, voice -> audio_youtube/final_audio.wav
python <skill>/scripts/vlog_mix.py --project PROJECT --reuse-music   # after changing only cues
```

- **The music** is `vlog_music.py`: the skill's lo-fi recipe (electric piano, pad, bass, soft drums, the pluck motif, vinyl hiss) played on `beats.json`. Bars count from each chapter's downbeat. Under every card a fill plays: a dominant chord and a pluck run that climbs into the downbeat, with no drums.
- **Sections** come from `vlog.ARRANGE`: `{chapter: [(first bar from 1, style, progression)]}`.
  - Styles: `intro` (no kick), `break` (no drums, filtered), `light`, `stroll` (light with the motif), `groove`, `lift`, `outro`. Progressions: `main`, `calm`.
  - What worked: a `break` under a question for a bar or two, `light` / `stroll` under explanations, `groove` under worked examples, `light calm` under summaries, `lift` for the last chapter, `outro` from the ending's downbeat.
  - A chapter without an entry gets `vlog_music.default_arrange()`.
- **The mix.**
  - The bed sits at -21 LUFS and ducks 6.5 dB under speech, so the beat is felt.
  - Over B-roll the clip's own sound fades out and the music steps up 3.5 dB. The same goes for the hold after the last line and the end; `vlog.QUIET` adds windows.
  - Loudness -14 LUFS, a 20 ms fade-in at the start.
- **You cannot hear it.** Tell the user, and ask them to listen to the bed under the voice, the cards, and the cuts named in the notes.

Render with `--parallel 2` on a 16 GB machine: about 27 min for 4:44. Then finish, captions, thumbnails and the kit as in SKILL.md.

## Check

- **The `beat_fit` table** before anything else: every edge, every OFF THE GRID cut.
- **Stills of every scene, then the edges.**
  - Each card: 0.05 s before, on, and 2 beats after. Each panel: in, full, and out.
  - The opening title over the walking person. The end card over the walk-off.
  - In the render: `review.py seq` at a card, at a PiP exit and at the ending.
- **The captions after the first render** (`export_captions.py` into a scratch folder).
  - Read every cue. Add `COMPOUNDS` for pairs a line must not end between ("bước 1:", "cái ô", "tốn token").
  - Pin `hold`-length lines that read badly.
- **The claims on screen** match the speaker's words. For example, the end card says "tiết kiệm token" because he said "tiết kiệm token hơn rất nhiều", not "không tốn token".
- **The notes file** lists what was cut and why (especially lines Whisper could not hear), the words you corrected by guess, and every illustration you added.
