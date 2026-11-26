# Motion viral cut (TikTok)

For a request like "hiệu ứng viral", "giữ chân 2 giây đầu", "motion đẹp, mới lạ", "kiểu tập 16", or the style "Motion viral (TikTok)" picked from the demo. It is a 60-95 s TikTok cut built for retention: the topic is said and shown with motion and a hit in the first 2 seconds, something visibly new happens every 2-3 seconds, a visual motif tied to the topic runs through the whole video, and the call to act comes right after the strongest proof. It runs on the trailer kit (`trailer.py`, `score()`), with colour captions after the TikTok creator @raw.to.reel and a licensed track cut on its bars. The user asked for it on tập 16 (Playwright, 2026-11-25): "2s đầu bằng mọi cách phải giữ chân được user… vượt 5s thì video sẽ viral > hãy dùng hiệu ứng đẹp, mới lạ và viral nhất bạn biết trong các video motion, giữ chân user đến giây cuối". She put it in the skill after watching it (2026-11-26).

- **Worked example:** `examples/playwright-tiktok/` (89 s from a 6.6-minute talk, two people outdoors, `iphone` colour). Its music is a licensed track that is not in the skill (the design's header says where it comes from).
- **Format:** TikTok 1080x1920 only. Stay inside the safe zone: y 240-1500, x 70-1010 (`design-playbook.md`).
- **What it shares with the trailer** (`references/trailer.md`): the story's shape (hook, setup, reveal, escalation, payoff), cards over silences, the score in `score()` events, at most two booms, wide shots, no darkened picture.

## Shape

| Part | Example | What happens |
|---|---|---|
| Frame 0 and the first 2 s | 0-2.2 s | The speaker cut out like a sticker (white outline) on a flat colour sunburst, the topic as a 3D title ("AI TỰ ĐIỀU KHIỂN MÁY TÍNH"), the motif already on screen (a mouse cursor). Boom, crash and the track's drop on frame 0. The voice says the topic within 2.2 s; pick that line from anywhere in the talk. |
| 3-6 s | "tự mở web, tự bấm, tự gõ" | What is said happens on screen as it is said: a window opens, a button is pressed, a field types itself. Then the open question. |
| The reveal | 9-11 s | The frame goes black and the key word's letters are windows onto the speaker (`mask_title`). On the word itself the camera flies through a letter and the music drops (boom 2 of 2). |
| The promise | 11 s | A pill that promises the payoff ("cuối video: cách nhận skill…") and a thin story bar of the parts left (`story_bar`). |
| The body | 11-60 s | One visual per idea, each built on the words: a dictionary card, a step-by-step demo that re-runs itself at speed, an x-ray where the page turns into its code under a scan line, a counter. The motif drives each one: the cursor clicks, types and presses. |
| The call to act | right after the strongest proof | Not at the end. Here it came after "gửi cho 20 người… tiết kiệm token": the cursor types the keyword into a comment box and presses send. |
| The human ending | last 6-10 s | A real reaction or outtake (his laugh "cái chữ đó rất khó viết đúng", with typos on screen), then an end card whose last move returns to frame 0's colour, so the video loops. |

**Pick the motif from the topic.** A cursor for an AI that drives a computer. A chat bubble, a terminal or a phone would suit other topics. It appears on frame 0 and comes back in every scene that has a mock screen.

## Captions: `rawstyle.py`, `rawgroups.py`

Every spoken phrase is a magazine stack over the speaker. The lead-in words sit small and white above the left end of the key word, the key word is huge, and the words after it sit small under its right end. The key word stands behind the head (the matte); the small words stand in front. Treatments of the key word (`rawstyle.TREAT`): `aqua`, `orange` (heavy rounded lowercase), `red`, `white` (heavy capitals), `blue`, `teal`, `navy` (black serif). Words come in as they are spoken; the key word pops.

- **Stacks are set by hand**, phrase by phrase: `G.group([("đừng tìm cách", "s"), ("tiết kiệm token", "white"), ("nữa", "s")])`. Rows are matched in order to the spoken words, so each word appears as it is said and a recut keeps the timing. `G.event(hidden=...)` draws them. `base=`, `scale=`, `front=True` give a compact stack at a fixed height (under a window).
- **A bright sky** behind the words needs a dark rim: `RS.OUTLINE = ((8, 12, 26), 0.055, 0.92)`.
- **Captions hide** under a card or a full-screen scene (`CAPTION_OFF`, `hidden=`).

## Effects: `fx.py`, `ui.py`

- `backdrop(ctx, t, a, rgb, rgb2, cx, cy, rays, spin, reveal)` with `sticker(ctx, t, a, r)`: the frame-0 look, a flat sunburst behind the cut-out speaker with a white outline.
- `extrude(c, text, f, x, y, a, rgb, side, depth)`: 3D title letters.
- `mask_title(ctx, t, t0, t_zoom, zoom_dur, lines, pivot)`: letters as windows, then the fly-through into a letter; `glyph_point()` finds the point to fly into.
- `shockwave()` and `speedlines()`: a ring and streaks from behind the speaker on a drop.
- `underline()`, `circle()`, `arrow()`, `highlight()`: marker doodles drawn on.
- `story_bar()`: the parts left. `beat_pulses(t0, n, beat)`: small camera pulses on the music's beats after a drop.
- `ui.py` holds the mock software pieces: `Cursor(keys, clicks)` glides, presses and ripples; `window()`, `field()` (typed letter by letter), `button()` (press, done), `tick()`, `cross()`, `code_panel()`, `bubble()`, `card()`, `pill()`. Draw plain generic shapes: a brand name may appear as text, but never a logo or a copied screen. Say in the notes that they are illustrations.

## Sound: a licensed track, `track_music.py`, `trailer_mix.py`

- **The track** is one the user picks or approves. Download it only from its licence page, into a folder of its own, and decode it to a 48 kHz wav in the project (`music_work/`). Tell the user what its page says: a track marked "Content ID Registered" or "AI generated" is fine on TikTok but can be claimed on YouTube.
- `python <skill>/scripts/music_analyse.py music_work/track.wav music_work/track` prints the tempo, every bar's start and energy, and a spectrogram with bar lines. Find the first downbeat, the drop, the break and the outro. Register it: `TM.add_track("banger", "music_work/trapbanger.wav", bar0=2.282, bpm=96.69)`.
- **Arrange it on the edit** with `score("track", t, track=..., src_t=TM.bar_of(name, n), dur=...)`.
  - The drop on frame 0 under the hook.
  - A build under the question: the same bars with `hp=(20, 900, 1.6)` draining the bass, a `roll`, a `stutter` and a riser into a dead stop.
  - The track's brightest bars on the reveal, the melody alone under a card, the drop again on the strongest proof.
  - The melody alone under the call to act, so the typing is heard. The beat under the end card, fading out.
- `modern_score.py` adds score kinds: `hit`, `subdrop`, `shepard`, `whoosh_up`, `stutter`, `rev_hit`, `pulse`, `beat`, `drone`, `ticks`. `modern_sfx.py` makes the clicks and pops crisp, tuned to the track's key: `MS.set_key(58, minor=True)` for Bb minor, and `f1=MS.note(...)` on pops.
- **Mix** with `python <skill>/scripts/trailer_mix.py PROJECT --fmt tiktok` instead of audio_mix.py. The end card (from `T_END`, or `SOLO_WINDOWS`) is levelled on its own, so the track is heard there without lowering it under the voice. Booms: at most two, on frame 0 and on the reveal.

## Check

- **The first 5 s frame by frame** (`review.py sheet VIDEO SHEET 0 5 0.25 6`): the topic readable on frame 0, the motif present, nothing in TikTok's caption area (y over 1500) or under its side buttons (x over 1010).
- **Every scene's stills**, then frame-by-frame through the reveal, the call to act and the loop.
- **Claims on screen** match the talk. A promise to the viewer, such as "viết sai cũng được", needs the user's OK.
- **You cannot hear the mix.** Ask the user to listen to the first 2 s (the voice over the boom) and the call to act.
