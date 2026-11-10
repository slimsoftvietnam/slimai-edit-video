# Platform delivery

Checked in November 2026. YouTube's numbers come from its own help page. TikTok publishes no full upload spec, so its numbers come from third-party guides that disagree: treat them as guidance and check the upload screen. Search again if this file has aged.

## YouTube

YouTube's recommended upload settings (support.google.com/youtube/answer/1722171):

| SDR | 24-30 fps | 48-60 fps |
|---|---|---|
| 2160p | 35-45 Mbps | 53-68 Mbps |
| 1440p | 16 Mbps | 24 Mbps |
| 1080p | 8 Mbps | 12 Mbps |

MP4 with Fast Start, H.264 High Profile, progressive, 4:2:0, AAC-LC 48 kHz (stereo 384 kbps). These are recommendations, not caps. `finish.py` produces this format; our CRF 15 file runs well above the 1080p figure on purpose, because YouTube re-encodes everything.

**HD is the default; the user chose it.** A 4K upload is only an option if they ask. YouTube's help confirms 4K uploads are delivered in VP9 for 4K viewing. That 1080p viewers also get a better stream from a 4K upload is reported by creators but not confirmed by YouTube, so state it as possible, not as fact. It would still be upscaled picture on a 1080p source, and it costs about four times the render time.

New uploads process in stages: low resolutions appear first. Tell the user not to judge quality in the first hour.

### Publishing kit

Write the kit in the video's language as `NAME_YouTube_kit.txt` next to the video, with `=== ... ===` sections in this order: titles, description, tags, pinned comment, upload notes, notes. Check it with `scripts/youtube_meta.py measure`, then put the titles, description, tags and pinned comment in the reply as well, ready to paste. `examples/vibe-code/youtube_kit.txt` follows this section; `examples/repo-ai-agent/youtube_kit.txt` is an earlier kit, written when only one title could be used.

YouTube does not publish how it ranks videos. What creator-tool sites reported by November 2026, all of them third party:

- Test & Compare tests titles as well as thumbnails: up to three titles, or three title-and-thumbnail pairs, set up in YouTube Studio on a computer. The winner is the variant with the largest share of watch time, not of clicks, and a test runs for up to about two weeks. Shorts are not covered. Sources: [Search Engine Journal](https://www.searchenginejournal.com/youtube-title-a-b-testing-rolls-out-globally-to-creators/562571/), [vidIQ](https://vidiq.com/blog/post/youtube-launches-new-title-testing-tool), [Gyre](https://gyre.pro/blog/youtubes-new-title-ab-testing-tool-everything-creators-need-to-know), [ThumbnailTest](https://thumbnailtest.com/news/youtube-releases-title-test-compare/).
- Distribution follows viewer satisfaction: watch time, likes, survey answers, "Not interested". A title that over-promises wins the click and loses the viewer, and the video is then shown less. The search phrase belongs at the start of the title and of the description; tags count for little. Sources: [OutlierKit](https://outlierkit.com/resources/youtube-viewer-satisfaction-algorithm-2026/), [SocialPilot](https://www.socialpilot.co/blog/youtube-algorithm), [Fluxnote](https://fluxnote.io/guides/youtube-algorithm-2026-how-it-works).

**Keywords come first.** `youtube_meta.py suggest` prints YouTube's own search suggestions for the viewer's language and country, so they are phrases people actually type. Seed it with the topic, the topic plus "là gì" (or "what is" in the video's language), and the problem the video solves, such as "làm app bằng ai". Use a phrase only where the video covers it. Leave out a popular tool or brand that the video never names, however often people search for it: YouTube's spam policy treats it as misleading metadata, and the viewers it brings leave early. Put it in the notes as an idea for a later video.

- **Titles**: three, each from a different angle, so that a test is worth running. Each starts with a phrase from the suggestions, stays under about 70 characters (`measure` counts them) and promises only what the video delivers. Angles that worked:
  - the question the video itself asks in its first seconds, so viewers see the promise kept straight away: "Vibe code là gì mà ai cũng khoe tự làm được cả CRM?"
  - the plain search answer, saying what the viewer gets and for whom: "Vibe code là gì? Hiểu trong 2 phút, kể cả khi không biết code"
  - the other common phrasing of the keyword, or the result: "Vibe coding là gì? Nói ý tưởng bằng tiếng Việt, AI tự code, tự test"

  Mark one as the default for a channel without the test, with a one-line reason.
- **Description**: the first line holds the search phrase, its other common phrasing and the promise, all within about 100 characters, because search results and the watch page show little more before "more". Then the question the video opens with, what the viewer learns in plain sentences with each secondary phrase used once, the chapters, one question for the comments, a subscribe line, and three hashtags at the end (the first three show above the title). YouTube rejects `<` and `>` in titles and descriptions.
- **Chapters**: start at 0:00, at least 3, each at least 10 s, with the same names as the chapter rail in the video. `export_captions.py` writes and validates them from `YT_CHAPTERS`.
- **Captions**: upload the `.srt`. It has the corrected words, which also helps search.
- **Tags**: about fifteen: phrases from the suggestions, their unaccented Vietnamese forms and common misspellings. YouTube's 500-character limit counts the commas and the quotes it adds around a tag that contains a space; `measure` counts the same way.
- **Thumbnails**: two, 1280x720, under 2 MB. Three to five words, big, one face, a question or tension that no title repeats. Render them from the master in the colour the user chose. If the colour changed after they were made, render them again under new names.
- **Test plan**: round 1 tests the three titles with the thumbnail whose words appear in none of them; round 2 tests the two thumbnails under the winning title. Without the test, use the default title with that thumbnail.
- **Pinned comment**: a question everyone can answer, not only people who have already done the thing, with one example answer so replying takes no effort.
- **Upload notes**:
  - the files: the master in the chosen colour, the `.srt`, the thumbnails;
  - the test plan;
  - the end screen: the last 8 s keep the right half free for one suggested video and the Subscribe element;
  - a playlist with a keyword in its name, the category, the language;
  - altered or synthetic content: "No" for cuts, captions, graphics, colour, sharpening and music written in code; "Yes" only when something realistic was made or changed, such as a real person saying what they did not, a real event or place altered, or a realistic scene that never happened;
  - made for kids: no, unless the video is aimed at children;
  - when to post: an hour or two before the peak in Analytics > Audience > "When your viewers are on YouTube";
  - in the first hour: pin the comment, answer the first comments, and do not judge picture quality yet.

## TikTok

- **Format**: 1080x1920, 9:16, H.264 MP4, 30 fps. Avoid HEVC, since it is reported to re-encode with more loss.
- **Bitrate and size**: guides suggest 10-15 Mbps at 30 fps. File caps vary by app, platform, country and account: one guide lists 287.6 MB for iOS and 72 MB for Android, others list 287.6 MB for both; web and TikTok Studio allow far more. A 2-minute file at CRF 15 came out at 232 MB (15.7 Mbps), inside the iOS figure. If the upload fails or the file is too big for the phone, upload from desktop, or re-encode a copy at the size limit.
- **Settings**: turn on "Allow high-quality uploads" or "Upload HD" (Settings and privacy, or "More options" on the post screen; the name and location change between versions).
- **How to upload**: desktop or Wi-Fi. Avoid cellular and re-sharing from another app, which compresses twice.
- **Layout safe zones**: `design-playbook.md`.
- **Cover**: a still with the strongest depth word. Choose a frame where the word is fully formed.

TikTok re-encodes every upload at a much lower bitrate, so the file on the platform always looks softer than the master. Large high-contrast type, wide shots and uncluttered frames survive it best.

## Reels and Shorts

The TikTok render fits both. Shorts: under 3 minutes for vertical videos to be classed as Shorts. Check current limits if it matters.
