# Trailer cut

For a request in the style of a film trailer: "kiểu trailer phim", "có twist", "nhịp điệu dồn dập". It runs on the same pipeline. What changes is the shape of the story, the black title cards between beats, and a score made of trailer sounds instead of the composed music. Worked examples, both cut from a 3-minute talk and approved by the user:

- `examples/ai-agent-trailer/` (88 s, plus `thumbs.py`) is the one to copy. It is the cut after the user's notes: the camera's colour with no darkening, titles on dark pills, wide shots only, the good lines kept, and a funny call to follow. One design renders both the TikTok cut and a 16:9 YouTube version.
- `examples/vibe-code-trailer/` (55 s) was the first. Its shape and its score are still good, but it darkens the sky and the room, which the user later rejected.

Trailers are made for TikTok first, usually 45-90 s. Length comes second to what is said: keep the lines people would quote and the warm analogies, even past 60 s. The user rejected a cut that dropped "em biết quét nhà" to stay under a minute. The kit also renders 16:9: the bars become a letterbox and the captions sit on the lower bar like film subtitles. Before delivering a 16:9 version, give every hand-placed element a `pick()` position and review YouTube stills. The AI agent example shows what moved, and keeps its TikTok values unchanged:
- **Chips and kickers** ride in the sky band at y 215, above the depth words, which sit around y 310-480 on 16:9.
- **Layouts that start at the left edge** in 9:16 are shifted to the centre.
- **The step counter** moves into the top letterbox bar, on `ctx.ui`.
- **The end card** says "Đăng ký" instead of "Follow". It sits in the upper part of the frame, so the last 8 s (`end_hold` 8.0) leave the lower part free for YouTube's end-screen elements.

`examples/vibe-code-trailer/` is placed for 9:16 only.

## Shape

| Part | Example | What happens |
|---|---|---|
| Hook | 0-7 s | The strongest social-proof line or question, on picture from the first frame. A boom as the thin bars slide in. A black card over a word of the question ("RỐT CUỘC", voice over black), then a braam on the question word. A one-line trailer kicker such as "DỰA TRÊN MỘT CUỘC TRÒ CHUYỆN CÓ THẬT" only if it is true. |
| The old way | 7-27 s | A card ("TRƯỚC ĐÂY"), then the problem as a montage. Each cut is one fragment of 1-2 s, a word behind the head and a drum hit. A counter on a dark plate grows (BƯỚC 01 → 08), and a clock doubles its speed halfway. It ends on the pain line ("quay lại… rất mất thời gian"): the counter rewinds, a riser builds, then a hard stop into silence. |
| The turn | 1.6 s card | A date and a name on black with a braam: "THÁNG 2 · 2025 / MỘT CÁI TÊN / ra đời." |
| The reveal | 29-39 s | Who coined it (chips), the question line, 0.3 s of silence, then the answer with something visibly collapsing. Here the eight steps are struck out on "triệt" and thrown out on "tiêu", in a PiP panel. |
| Escalation | 39-49 s | A card sets up a word the speaker then says ("NGÔN NGỮ LẬP TRÌNH / mới nhất là…" → "bằng tiếng Việt"). Then four or five cuts in about 8 s, each with a flash frame, a depth word and a hit, over the drive. A riser ends in a hard cut to black on the last word. |
| Warm part (optional) | after the escalation | The drive stops for an everyday analogy that makes the idea human ("em biết quét nhà, biết nấu cơm, nhưng vẫn muốn có người làm thay"). A swell, a warm pad and bells. |
| Twist and title | last 6-7 s | A beat of silence, the twist, then the title on black with the one line to remember under it, then the call to follow. |

- **The hook's words can form one sentence across the beats**: VIBE CODE … RỐT CUỘC … LÀ GÌ?
- **Fragments start and end on whole words.** Check who speaks each one in `speakers.txt` and in the frames. A low-score line labelled as the other person is common.
- **Cards carry 2-6 words, centred, and last 0.6-1.6 s.** Caps with wide tracking are for statements; serif italic is for the emotional word. A card sits on a silence, or over a line when the words on the card are the words being spoken.
- **Something is silent before every reveal**: a gap between question and answer, or a card before the punchline.
- **Flash frames only on the hard cuts of the escalation**, never more than three a second.

**The twist must be true.** Two kinds have worked:
- **A line from the talk that reframes the build-up**, set up by a card.
- **The meta twist.** The trailer was edited from the user's own request, so show it typing itself in `prompt_box`.
  - Use their words, cleaned only of typos and of instructions that are not about the video.
  - Phrase the claim so that it stays true after revisions: "Trailer bạn vừa xem bắt đầu từ đúng câu này.", not "được làm từ đúng một câu".
  - Tell the user it reveals that AI edited the video, and that the ending can be cut.

Facts on cards (dates, names) are checked like captions. Karpathy named vibe coding in February 2025.

**The call to follow is a joke that lands the main point**, ideally a callback to the twist. In the AI agent trailer the twist is that AI is giving you work, and the end card reads "Follow để học cách giao việc cho AI… / trước khi AI giao thêm việc cho bạn." The setup comes in bold, the punchline 0.9 s later in serif italic amber, and the title moves up to make room. Allow about 6.6 s of end hold so it can be read. A bare "Follow để xem thêm" wastes the last frame.

**Colour stays the user's choice** (default `iphone`), and the picture stays as shot. The film feel comes from the bars, the cards and the rhythm, not from a grade and not from darkening. On iPhone footage the user read `top_fade()` and `dim_room()` as haze ("mờ và nhòe"), so they are opt-in, for a user who asks for a moodier picture. Text over a bright sky sits on `pill_text()`. A counter or HUD sits on its own dark plate.

**Shots stay wide.** Give every clip `"shot": "wide"` and leave `PUNCHES` empty. A vertical cut of a 1080p source is already a 1.78x blow-up, and the user does not want close faces. A cutaway to the listener is a wide shot of them (`SHOT_OVERRIDES` with `W_wide`).

## Cut: `select.json`

- **Own project folder.** Copy the transcript, the audio, the look cube, `project.json` and `matte/` from the main project, so the earlier edit stays reproducible. Then run `build_timeline.py`, `build_master.py` and `matte.py`; `matte.py` only computes the frames that are missing.
- **`gap_after`** (seconds) on a clip leaves that much silence after it. `story.gap(beat)` returns `(t0, t1)`. Through a gap the camera holds the shot before it and the picture freezes on that clip's last frame, which the card covers.
- **End hold.** Set `"end_hold": {"tiktok": 6.8}` in `project.json` for the twist and the title. `@card(DUR, TOTAL + 1, close=0, open_=0)` cuts to black on the last word.

## Design: `scripts/trailer.py`

`from story import *` then `from trailer import *`. The kit draws in this order: the bars, fades and dimming go first (`story.PRE`), then the events, then the captions, then the cards and flashes (`story.POST`). Captions hide while a card covers the frame.

Take times from the words, not from guesses. `word_in(beat, word, n=1)` gives the n-th time `word` is spoken inside that beat's clips. `beat_start(beat)` and `beat_end(beat)` give the beat's edges. All three come from `story.py` and survive any recut. The AI agent example builds every anchor from one table this way.

| Call | Use |
|---|---|
| `@card(t0, t1, close=0.16, open_=0.24)` | A black card. The bars close before `t0` and open after `t1`; `fn(ctx, t, t0, t1)` draws its text. |
| `card_text(ctx.ui, t, t0, t1, text, dy, kind, size, rgb, track, delay, glow, push)` | One line, its baseline `dy` px below the frame centre, in 9:16 px. |
| `flash(t)` | A white flash frame: one pure white frame, one fading. |
| `pill_text(ctx.front, t, t0, t1, text, x, y, size=30)` | Tracked caps on a dark pill that fades with them, for a kicker or a note over the sky. |
| `top_fade()` | A dark fade under the top bar, room only. Only when the user asks for a moodier picture. |
| `dim_room(t0, t1, amount=100)` | Darkens the room but not the people. Same rule as `top_fade()`. |
| `prompt_box(ctx.ui, t, text, t_in, t_type0, t_type1, t_enter, t_out)` | A chat box that types the text; its send button lights up at `t_enter`. |
| `title_slam(ctx.ui, t, t0, title, sub)` | The title slams in from 1.22x, with a glint across it, an accent line just above its tallest glyph and the subtitle under it. |

The step counter, the clock, the collapsing list and the turning delegation arrow are recipes in the examples' `design.py`, not part of the kit.

## Sound: `score()`

Any `score(kind, t, **kw)` event replaces the composed music. `trailer_score.py` lists every kind and option, and `audio_mix.py` mixes three stems:

| Stem | Kinds | Level |
|---|---|---|
| music | pad, ostinato, drive, bells, piano | -21 LUFS, ducked 9 dB under the voice, 5.5 dB while a drive plays |
| hits | boom, braam, taiko, riser, swell, crash | -17.5 LUFS, kept whole |
| perc | heartbeat, clock | -27 LUFS, kept whole |

The mix then goes through a limiter and a two-pass loudness pass to -14 LUFS and -1.5 dBTP. In the example the braams peak 1-2 LU above the speech in momentary loudness, and `finish.py` passed.

- **Hits are not ducked.** Put them between lines or on a word onset. A braam under a key line stays at gain 0.4 or lower.
- **A riser's `t` is where it ends**: on a hit, or on a hard cut to black.
- **Keystrokes:** `cue(t0, "typing", 1.0, until=t1)`.
- **The example's score by part:**
  - **Hook:** boom; low drone; heartbeat at 72 BPM; taiko and boom on the card; braam on the question.
  - **Old way:** clock at 100 BPM, 16ths from the fourth step; ostinato on i-VI-iv-V; taiko on every step; a dissonant tremolo swell and a riser into the stop.
  - **Turn:** braam (Bb).
  - **Reveal:** pads; a tremolo under the question; a swell into a low braam (D major) on the collapse; bells on the idea.
  - **Escalation:** a riser through the punchline card into a hit; a drive at 120 BPM on I-bVI-bVII-I; taiko on every cut; a riser into black.
  - **Twist and title:** piano under the typing; swell, braam, boom and crash on the title.
- **What the AI agent trailer adds:** a taiko on each word of a voice-over-black card; a low braam under the twist line; a warm part where the drive stops (swell, pad, bells on each "vẫn muốn có người làm thay"); a soft pad and a four-note piano under the call to follow.

## Check

- **Stills at both edges of every card**, 0.05 s before and after, on the flash frames, and through the twist. Then `review.py seq` around each card in the render.
- **You cannot hear the score.** Ask the user to listen to the braam under the key line and to the drive under the speech.
- **Send the 1080p preview** that `finish.py` writes. The user judges the edit on a phone.
