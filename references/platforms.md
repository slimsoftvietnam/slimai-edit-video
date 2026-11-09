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

Write these in the video's language, in one text file next to the video:

- **Title** (three options, pick one): under about 60-70 characters, main search phrase first, an honest promise. Do not bait what the video does not deliver.
- **Description**: the first two lines carry the search phrase and the hook, since they show before "more". Then what the viewer learns, in plain sentences with the keywords used naturally, chapters, one question to invite comments, three to five hashtags.
- **Chapters**: start at 0:00, at least 3, each at least 10 s. `export_captions.py` writes and validates them from `YT_CHAPTERS`.
- **Captions**: upload the `.srt`. It has the corrected words, which also helps search.
- **Tags**: few, including common misspellings and unaccented Vietnamese forms. They count for little, so don't over-invest.
- **Thumbnail**: 1280x720, under 2 MB; two variants for Test & Compare if the channel has it. Three to five words, big, one face, a question or tension the title does not repeat.
- **End screen**: the last 8 s keep the right half free. One suggested video and the Subscribe element.
- **Pinned comment**: a concrete question that viewers can answer from their own experience.
- **Playlist** with a keyword in its name, category, language.

The worked example's kit is in `examples/repo-ai-agent/youtube_kit.txt`.

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
