# Design playbook

How to write a project's `design.py`. It does `from story import *`, registers everything at import time, and the same file renders both formats. Worked examples: `examples/cowork-40s/design.py` (short), `examples/repo-ai-agent/design.py` (long, more recipes).

## Contents

1. File structure
2. Coordinates and the camera
3. Layers: where to draw
4. Safe zones per format
5. Components
6. Camera, PiP, split screen and transitions
7. Sound cues and music
8. Recipes
9. Checklist before a long render

## 1. File structure

```python
import math
import skia
from story import *

# anchors: at(word, near) = output time of `word` closest to `near`, from words.txt
for key, word, near in [("agent0", "Agent", 0.28), ("rat1", "rất", 3.94)]:
    A[key] = at(word, near)

KEYS.update({"trí nhớ": ("serif_ib", AMBER, 1.22)})  # caption styling: phrase -> (font, colour, size multiple)
KEEP_CASE.update({"repository": "Repository"})       # lower-case word -> displayed form
NO_BREAK.update({"Anh"})                             # capitalised words that are not a sentence start
COMPOUNDS.update({"cái kho"})                        # word pairs a caption line must not split

SHOT_OVERRIDES.extend([...]); PUNCHES.extend([...]); PIP.extend([...])
LEAKS.extend([...]); LABELS.extend([...]); YT_CHAPTERS.extend([...]); MUSIC.update(...)

@ev(A["rat1"] - 0.1, A["next"] + 0.1)      # event: fn(ctx, t) is called for frames in this window
def safe(ctx, t):
    depth_word(ctx, t, A["rat1"] - 0.08, A["next"], "RẤT AN TOÀN", size=pick(250, 200), enter="rise")

cue(A["rat1"], "shimmer", 0.5)
```

Anchor everything to words, never to raw seconds, so graphics and sound stay in sync when the cut changes. Times outside an element's life must draw nothing: the component helpers already return early, your own drawing must check `v > 0`.

Registries:

| Name | Entry | Meaning |
|---|---|---|
| `SHOT_OVERRIDES` | `(t0, t1, "M_close")` | force a shot; names are `{spk}_{wide,med,close}`, `TWO_{spk}` |
| `PUNCHES` | `(t, amount, attack, hold, release)` | brief zoom on a word; amount 0.04-0.05 is enough |
| `PIP` | `(t_in, t_out)` | speaker shrinks over `PIP_T` from `t_in`, grows back from `t_out` |
| `SPLIT` (via `split_screen(t0, t1, top=None, bottom=None)`) | `(t0, t1, top, bottom)` | both people at once, one per half, TikTok only; section 6 |
| `SPLIT_FRAME` | `{spk: (cx, cy, h)}` | optional: what a half shows of that person, in source px; section 6 |
| `LEAKS` | `t` | warm light leak, good at chapter changes |
| `LABELS` | `(t, "02", "title")` | chapter rail (YouTube only) |
| `YT_CHAPTERS` | `(t, "title")` | description chapters: starts at 0:00, at least 3, each at least 10 s |
| `MUSIC` | `drop`, `sections`, `stops`, `bpm`, `transpose`, `tail` | see section 7 |
| `SCORE` (via `score(kind, t, ...)`) | trailer sounds | replaces the composed music; `references/trailer.md` |
| `PRE`, `POST` | `fn(ctx, t)` | drawn before every event / after the captions (the trailer kit uses them) |
| `CAPTION_OFF` | `fn(t) -> bool` | hides the captions while true, e.g. under a black card |

Whip pans, rail pops and PiP whooshes are automatic. `gap(beat)` returns the silence select.json's `gap_after` left after that clip; through it the camera holds the shot before it.

## 2. Coordinates and the camera

Everything is drawn in layout px: 1080x1920 or 1920x1080. Layers scale to device px, so type stays vector-sharp at 4K. Source positions are source px. `src_to_screen(ctx.cam, x, y)` converts, including during a PiP morph.

- `head(ctx, spk=None)` -> face x, head-top y, face y, px per source px on screen.
- `anc(ctx, dx, dy, spk=None)` -> screen point (dx, dy) source px from the face. Scene-locked, so it follows cuts and punches.
- `place(ctx, (dx, dy, anchor), (x, y, anchor), spk=None)` -> YouTube uses the scene-locked offset (space beside the speaker), TikTok a screen position (the free zone above the head). Returns `(x, y, anchor)`.
- `ctx.spk` = current speaker, `ctx.cam` = camera, `ctx.pip` = PiP amount 0..1, `ctx.pip_rect` = the view rectangle.
- `ctx.split` is True while a split screen runs. `ctx.cam` is then the camera of the speaker's own half, so `head()`, `anc()` and depth words land in that half.

## 3. Layers: where to draw

Order on screen, bottom to top:

| Layer | Use | Notes |
|---|---|---|
| `ctx.behind` | depth words | matted behind the person, clipped to the view rect |
| stage, glass | set automatically by `panel()` | blurred wide shot at half brightness while in PiP |
| `ctx.mid` | diagram content | on the stage, under the speaker card, so a panel never covers the speaker |
| film finish | vignette, halation, grain | everything below gets film texture |
| `ctx.front` | chips, badges, marks that must stay crisp | above the finish |
| `ctx.ui` | captions, chapter rail | above the finish |

Skia draws go through `L.c` (a canvas). **Any draw that does not use `draw_text`, `chip`, `big_text` or `glass_panel` must call `L.mark(x0, y0, x1, y1)`**, otherwise those pixels are never composited.

`ctx.cctv = v` turns on the surveillance grade. `ctx.end` is set by `takeaway`.

## 4. Safe zones per format

Profiles live in `story.PROFILES`.

**TikTok 1080x1920.** Keep important things in y 240-1500 and x 70-1010. The platform UI covers the top ~200 px, the bottom ~400 px and the right ~120 px at lower height.

- Captions: baseline y 1352, width up to 900.
- PiP layout: panel area x 60-1020, y centred on 525, up to 550 tall. Speaker card x 125-955, y 823-1290 (the whole two-shot at 16:9). Caption below it.
- Chips stack in the zone above the head at y ~250, 345, 440, usually two at most.
- Depth word size 200-300, `max_w` is capped by the margins automatically.
- Split screen: the seam is at y 960 and the captions sit on it (baseline 1000). Text goes over the top person's legs (y ~760-900) or behind the bottom person's head (baseline ~1230), never over a face.

**YouTube 1920x1080.**

- Captions: baseline y 968, width up to 1500. Nothing important below y 1000 where the player bar appears.
- Chapter rail top-left at x 96, y 70-160.
- PiP layout: panel x 120-1150, centred on y 500, up to 640 tall. Speaker card x 1196-1836, y 320-680.
- Scene-locked chips beside the head: offsets of 150-250 source px.
- End card: left half only, 8 s, right half free for end-screen elements.

## 5. Components

`t` is the current time; `t0, t1` the element's life. All return early when hidden.

**Depth word**
```python
depth_word(ctx, t, t0, t1, text, size=280, rgb=WHITE, kind="black", enter="rise", glow=None, gradient=None,
           overlap=None, max_w=None, xoff=0.0, yoff=0.0, layer="behind", tracking=-0.025, stagger=0.035,
           alpha=1.0, fade_out=0.28, sheen=None, t_ref=None, spk=None)
```
Stands behind the speaker's head, locked to the scene. `size` is the on-screen size at the tightest shot of the word's life. It avoids other people's heads, the frame margins and the chapter rail. `enter`: `rise`, `pop`, `settle`, `scale`, `type`, `none`. `overlap`: how far the word sinks behind the head (fraction of cap height). `sheen`: seconds until a glint sweeps across. Use `kind="serif_ib"` with `tracking=0.0` for an emotional word, `black` with a gradient for a concept.

**Big text** (`big_text(layer, t, t0, t1, text, cx, base_y, size, ...)`) is the free-placement version.

**Chip**
```python
chip(layer, t, t0, t1, x, y, text, icon_kind=None, style="glow", size=40, accent=AMBER, anchor="center",
     text_rgb=WHITE, font_kind="semi", pop=True, alpha=1.0)   # -> rect or None
```
`style`: `glow`, `solid`, `dark`.

**Panel**
```python
v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h, r=44, accent=None)
if v <= 0:
    return
c = ctx.mid.c
a = 255 * v
```
Lay out inner content proportionally to `h`, adding `dy` to every y, because the panel slides in. Heights: pick(590, 530) is a typical pair. Register the matching `PIP` window so that the panel starts about 0.3 s after `t_in` and ends at `t_out`.

**Other**
- `badge(ctx, t, t0, t1, x, y, r, "shield", MINT)`: round icon that springs in.
- `arrow(c, x0, y, x1, prog, rgb, a)`, `draw_on_path(c, path, prog, paint)`, `dot(c, x, y, r, rgb, a)`, `strike(layer, t, t0, x0, x1, y, rgb, width, t1, dur)`.
- `kicker(layer, t, t0, t1, text, x, y, size)`: tracked small caps line.
- `takeaway(ctx, t, t0, line1, line2, chip_text, kick="TÓM LẠI")`: end card.
- `icon(c, kind, x, y, s, rgb, a, sw=None, prog=1.0)` kinds: folder file box clock history branch shield robot user undo link code calendar list check cross warn star fork camera spark brain trash upload database browser chat.
- `draw_text(layer, text, fnt, x, y, rgb, a, align, tracking, shadow, shadow_a, glow, glow_blur, glow_a, scale, per_char, gradient, outline)`, `font(kind, size)`, `text_width(text, fnt, tracking)`. Baseline-anchored. Font kinds: black xbold bold semi medium regular light italic serif_i serif_ib serif serif_b.
- Helpers: `env(t, t0, t1, fade_in, fade_out)`, `clamp01`, `lerp`, `spring`, `ease_out_cubic`, `ease_in_out_cubic`, `ease_out_back`, `ease_out_expo`, `fill(rgb, a, blur)`, `stroke(rgb, a, width, blur, cap)`, `rrect`. Colours: WHITE AMBER GOLD CORAL MINT SKY INK.

Colour language: mint = the good thing, the concept being taught. Amber = emphasis and memory. Coral = the problem or mistake. Sky = neutral secondary.

## 6. Camera, PiP, split screen and transitions

The camera comes from the clip's `shot` in `select.json`, with slow push-ins and small jump-cut punches, all compressed above a knee so that nothing becomes a tight face shot. Tables are in `engine._TABLE`. Keep their deliberately wide values.

Picture-in-picture morphs the view rect into the card while the source window glides to what the card shows. On vertical it opens from the 9:16 crop to the entire wide shot. Everything is scene-locked, so a depth word on screen morphs along with it.

Use a PiP when a diagram needs the screen, never a zoom. Up to about a third of screen time works (the worked example uses 35%), in windows of 3-9 s with the speaker back at full size between them. Longer starts to feel like slides.

### Split screen (TikTok)

The vertical single shot shows one person. When the other person's face is the point, show both: a question and the first beat of its answer, a reaction to the twist, a disagreement. `split_screen(t0, t1)` puts the man (`"M"`) in the top half and the woman (`"W"`) below. The user asked for this layout. Pass `top=` and `bottom=` for other names. `examples/mcp-trailer/design.py` uses it twice: her question (5.6 s) and her "À" at the twist (1.5 s).

```python
split_screen(0.0, beat_end("hook"))                     # her question, him listening on top
split_screen(beat_start("aha"), beat_end("aha"))        # her reaction to the twist
SPLIT_FRAME.update({"M": (1190, 668, 560), "W": (665, 621, 560)})   # optional framing, source px
```

- **Keep splits short, a line or two.** The single shot carries the explanation, because it has room for depth words and diagrams.
- **Start and end on cuts.** `beat_start()` and `beat_end()` give the edges. They snap to frames the way cuts do. The layout changes on the cut, and whip pans next to a split edge are skipped.
- **Framing.** Each half has its own camera with a slow push-in and a little drift. By default a half frames its person a touch wider than the single shot, with the face about a third of the way down. `SPLIT_FRAME` sets `(centre x, centre y, height)` of what a half shows, in source px. On a 1080p source, a height of 560 is about the single shot's blow-up. A smaller height is closer, and the user does not want close faces.
- **What is automatic.**
  - The captions and their shade move to the seam.
  - A caption line never crosses a split edge: it leaves on the cut.
  - `ctx.behind` goes behind the person in each half.
- **Placing text.** Free placement is often simplest. The example puts "MCP?" (`big_text` on `ctx.behind`) behind her head at y 1232, and chat chips over his legs at y 765-880.
- **Limits.** No PiP during a split. A 16:9 render ignores splits, because its two-shot already shows both people.

## 7. Sound cues and music

`cue(t, kind, gain, **kw)`:

| Kind | Options | Use |
|---|---|---|
| `whoosh` | `length`, `direction` | a big word or panel enters |
| `pop` | `f0`, `f1` | chip appears; raise the pitch through a sequence |
| `tick` | `f` | small list item or typed character |
| `impact` | `length` | a heavy claim |
| `swipe` | | strike-through, reversal |
| `shimmer` | | a positive reveal |
| `ding` | `f` | confirmation |
| `glitch` | | a problem or error |
| `rewind` | | undo, going back |
| `connect` | | two things link |
| `click` | | toggle |
| `beep`, `shutter` | | camera, record |
| `swell` | `length` | build into the next beat |
| `pluck` | `note` (MIDI) | a melodic sequence, such as branches |

Use gains of 0.3-0.7. Most cues should sit under the voice; the voice is always the point.

```python
MUSIC.update(drop=A["answer"] - 0.04, stops=[A["key_line"] - 0.32], bpm=96, sections=[
    (A["myth"], "groove", "main"), (A["thesis"], "break", "calm"), (A["closing"], "outro", "calm")])
```

The first downbeat lands on `drop`, preceded by a tense two-bar intro. Sections snap to bars. Styles: `intro build light groove lift break outro`. Progressions: `main calm tense`. A `stop` cuts the music for a beat just before a key line. Voice is mixed at -16 LUFS, music at -23.5 and ducked, the total at -14.

## 8. Recipes

- **Hook.** Big concept word behind the head, two kickers building the claim, then a coral serif question on the provocative word. Strike it when the speaker reverses it, then show the reassuring answer with a shield.
- **Definition.** A word typing itself out in the speaker's rhythm (`REPO` -> `REPOSITORY`), then the plain-language translation in serif.
- **Myth bust.** Panel: `A = ?`, the wrong answer arrives on the word, gets struck on "thực ra", then a depth word for the turn.
- **Before / after.** Same panel morphs: a list that forgets (rows dim, `?` marks) becomes a log that remembers (timeline, times, checks).
- **Branching.** A source icon glides left, the main line draws, branches peel off on each spoken name, the labels glow on the concluding word.
- **Rollback.** Timeline v1 v2 v3, a ring travels back on the word, a check appears after it lands.
- **Analogy.** Change the grade with the words: `ctx.cctv` plus REC frame for "camera giám sát".
- **Collapse.** Chips for each item fly into a single icon on "cũng được".
- **Question and reaction.** A split screen (section 6): her question with the key word behind her head and the question as chat chips over his legs; later her "À" at the twist, with the equation it lands ("HTTP = MCP") over his legs.
- **Takeaway.** The one line to remember, plus the action.

## 9. Checklist before a long render

- Every `PIP` window has a matching panel and no important depth word during it.
- First 3 s reviewed at 0.5, 1.5 and 2.5 s.
- No chip on a face, no word on the other person's head, in both formats.
- Vietnamese stacked diacritics (Ấ, Ế, Ỗ) not clipped at the top.
- YouTube rail labels do not collide with panels or depth words.
- Captions do not touch the card in the TikTok PiP layout.
- Every split screen starts and ends on a cut. Stills on both sides of each edge and in the middle show no text on a face, and the captions on the seam clear of both heads.
- `YT_CHAPTERS` validates (`export_captions.py` warns).
