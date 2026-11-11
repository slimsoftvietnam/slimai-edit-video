# Trailer cut

For a request in the style of a film trailer: "kiểu trailer phim", "có twist", "nhịp điệu dồn dập". It runs on the same pipeline. What changes is the shape of the story, the black title cards between beats, and a score made of trailer sounds instead of the composed music. Worked example: `examples/vibe-code-trailer/`, a 55 s TikTok trailer cut from a 3-minute interview. The user approved it and asked for it to become part of the skill.

Trailers are made for TikTok first, 45-60 s. The kit also renders 16:9: the bars become a letterbox and the captions sit on the lower bar like film subtitles. The example places its step counter and chips for 9:16 only, so give them `pick()` positions before delivering a 16:9 version.

## Shape

| Part | Example | What happens |
|---|---|---|
| Hook | 0-7 s | The strongest social-proof line or question, on picture from the first frame. A boom as the thin bars slide in. A black card over a word of the question ("RỐT CUỘC", voice over black), then a braam on the question word. A one-line trailer kicker such as "DỰA TRÊN MỘT CUỘC TRÒ CHUYỆN CÓ THẬT" only if it is true. |
| The old way | 7-27 s | A card ("TRƯỚC ĐÂY"), then the problem as a montage. Each cut is one fragment of 1-2 s, a word behind the head and a drum hit. A counter grows (BƯỚC 01 → 08), a clock doubles its speed halfway, and `dim_room` darkens the room. It ends on the pain line ("quay lại… rất mất thời gian"): the counter rewinds, a riser builds, then a hard stop into silence. |
| The turn | 1.6 s card | A date and a name on black with a braam: "THÁNG 2 · 2025 / MỘT CÁI TÊN / ra đời." |
| The reveal | 29-39 s | Who coined it (chips), the question line, 0.3 s of silence, then the answer with something visibly collapsing. Here the eight steps are struck out on "triệt" and thrown out on "tiêu", in a PiP panel. |
| Escalation | 39-49 s | A card sets up a word the speaker then says ("NGÔN NGỮ LẬP TRÌNH / mới nhất là…" → "bằng tiếng Việt"). Then four or five cuts in about 8 s, each with a flash frame, a depth word and a hit, over the drive. A riser ends in a hard cut to black on the last word. |
| Twist and title | 49-55 s | A beat of silence, the twist, then the title on black with the one line to remember under it. |

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

**Colour stays the user's choice** (default `iphone`). The film feel comes from the bars, the cards, the rhythm, the dimmed room and the fade under the top bar, not from a grade.

## Cut: `select.json`

- **Own project folder.** Copy the transcript, the audio, the look cube, `project.json` and `matte/` from the main project, so the earlier edit stays reproducible. Then run `build_timeline.py`, `build_master.py` and `matte.py`; `matte.py` only computes the frames that are missing.
- **`gap_after`** (seconds) on a clip leaves that much silence after it. `story.gap(beat)` returns `(t0, t1)`. Through a gap the camera holds the shot before it and the picture freezes on that clip's last frame, which the card covers.
- **End hold.** Set `"end_hold": {"tiktok": 6.8}` in `project.json` for the twist and the title. `@card(DUR, TOTAL + 1, close=0, open_=0)` cuts to black on the last word.

## Design: `scripts/trailer.py`

`from story import *` then `from trailer import *`. The kit draws in this order: the bars, fades and dimming go first (`story.PRE`), then the events, then the captions, then the cards and flashes (`story.POST`). Captions hide while a card covers the frame.

| Call | Use |
|---|---|
| `@card(t0, t1, close=0.16, open_=0.24)` | A black card. The bars close before `t0` and open after `t1`; `fn(ctx, t, t0, t1)` draws its text. |
| `card_text(ctx.ui, t, t0, t1, text, dy, kind, size, rgb, track, delay, glow, push)` | One line, its baseline `dy` px below the frame centre, in 9:16 px. |
| `flash(t)` | A white flash frame: one pure white frame, one fading. |
| `top_fade()` | A dark fade under the top bar, room only, for titles and chips on a bright sky. |
| `dim_room(t0, t1, amount=100)` | Darkens the room but not the people. Depth words stay on top. |
| `prompt_box(ctx.ui, t, text, t_in, t_type0, t_type1, t_enter, t_out)` | A chat box that types the text; its send button lights up at `t_enter`. |
| `title_slam(ctx.ui, t, t0, title, sub)` | The title slams in from 1.22x, with a glint across it and a line under it. |

The step counter, the clock and the collapsing list are recipes in the example's `design.py`, not part of the kit.

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

## Check

- **Stills at both edges of every card**, 0.05 s before and after, on the flash frames, and through the twist. Then `review.py seq` around each card in the render.
- **You cannot hear the score.** Ask the user to listen to the braam under the key line and to the drive under the speech.
