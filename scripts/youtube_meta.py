"""Keyword research and checks for the YouTube publishing kit described in references/platforms.md.

python youtube_meta.py suggest "vibe code" "vibe code là gì" "làm app bằng ai" [--hl vi --gl VN]
    YouTube's own search suggestions for each seed, as viewers with that language and country
    see them: phrases people really type.

python youtube_meta.py measure KIT.txt [--keyword "vibe code là gì" --keyword "vibe coding là gì"]
    Checks a kit whose "=== ... ===" sections come in this order: titles, description, tags,
    pinned comment, upload notes. Titles are the lines that start with [1], [2], [3].
    Prints title lengths, the start of the description that shows before "more", the hashtags
    shown above the title, the chapters, and the tag length the way YouTube counts it.
    A keyword counts as present when all its words appear; any one of the keywords is enough.
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

TITLE_SOFT = 70     # phones cut titles well before YouTube's 100-character cap
KEYWORD_LATE = 30   # a title's keyword should start within its first words
FOLD = 120          # about what search results and the watch page show of a description before "more"
DESC_MAX = 5000
TAGS_MAX = 500
STAMP = r"^((?:\d+:)?\d{1,2}:\d\d)[ \t]+\S"


def suggest(seeds, hl, gl):
    for k, seed in enumerate(seeds):
        if k:
            time.sleep(0.4)
        query = urllib.parse.urlencode({"client": "firefox", "ds": "yt", "hl": hl, "gl": gl, "q": seed})
        req = urllib.request.Request("https://suggestqueries.google.com/complete/search?" + query,
                                     headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode(resp.headers.get_content_charset() or "utf-8", "replace")
        except OSError as err:
            sys.exit(f"cannot reach YouTube suggestions: {err}")
        found = re.search(r"\[.*\]", body, re.S)      # plain JSON, or JSONP from other clients
        items = json.loads(found.group(0))[1] if found else []
        print(seed)
        for item in items:
            print("   ", item if isinstance(item, str) else item[0])
        if not items:
            print("    (none: too few searches; try a shorter seed)")


def keyword_at(text, keywords):
    """Where the earliest keyword starts in text, or -1."""
    best = -1
    for kw in keywords:
        hits = [re.search(r"\b" + re.escape(w) + r"\b", text, re.I) for w in kw.split()]
        if hits and all(hits):
            at = min(h.start() for h in hits)
            best = at if best < 0 else min(best, at)
    return best


def seconds(stamp):
    return sum(int(p) * 60 ** i for i, p in enumerate(reversed(stamp.split(":"))))


def measure(path, keywords):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^===.*===[ \t]*$", text, flags=re.M)[1:]     # text before the first header is a preamble
    if len(parts) < 3:
        sys.exit("expected '=== ... ===' sections in this order: titles, description, tags, pinned comment, ...")
    titles_txt, desc, tags_txt = parts[0], parts[1].strip(), parts[2]
    warn = []

    print("titles")
    titles = re.findall(r"^\[(\d+)\][ \t]+(.+)$", titles_txt, re.M)
    if not titles:
        warn.append("no titles: start each one with [1], [2], [3]")
    for num, title in titles:
        title = re.split(r"\s+<-", title)[0].strip()      # older kits put a note after "<-"
        print(f"  [{num}] {len(title):3d}  {title}")
        if len(title) > TITLE_SOFT:
            warn.append(f"title [{num}] has {len(title)} characters; phones cut it early")
        if re.search(r"[<>]", title):
            warn.append(f"title [{num}] contains < or >, which YouTube rejects")
        if keywords:
            at = keyword_at(title, keywords)
            if at < 0:
                warn.append(f"title [{num}] has none of the keywords")
            elif at > KEYWORD_LATE:
                warn.append(f"title [{num}] reaches its keyword only at character {at}")

    print(f"description  {len(desc)} of {DESC_MAX} characters")
    print("  before \"more\":", desc[:FOLD].replace("\n", " / "))
    if len(desc) > DESC_MAX:
        warn.append("the description is too long")
    if re.search(r"[<>]", desc):
        warn.append("the description contains < or >, which YouTube rejects")
    if keywords and keyword_at(desc[:FOLD], keywords) < 0:
        warn.append(f"none of the keywords is in the first {FOLD} characters of the description")
    hashtags = re.findall(r"#\w+", desc)
    print("  hashtags above the title:", " ".join(hashtags[:3]) or "none")
    if len(hashtags) > 5:
        warn.append(f"{len(hashtags)} hashtags; three to five is enough")
    stamps = re.findall(STAMP, desc, re.M)
    print("  chapters:", " ".join(stamps) or "none")
    if stamps:
        secs = [seconds(s) for s in stamps]
        if secs[0] != 0:
            warn.append("the first chapter must start at 0:00")
        if len(secs) < 3:
            warn.append("YouTube shows chapters only when there are at least 3")
        if any(b - a < 10 for a, b in zip(secs, secs[1:])):
            warn.append("each chapter must last at least 10 s")

    tags = [t.strip() for t in re.split(r"[,\n]", tags_txt) if t.strip()]
    # YouTube counts the quotes it adds around a tag with a space in it, and the commas between tags
    used = sum(len(t) + 2 * (" " in t) for t in tags) + max(len(tags) - 1, 0)
    print(f"tags  {len(tags)} tags, {used} of {TAGS_MAX} characters as YouTube counts them")
    if used > TAGS_MAX:
        warn.append("the tags are over YouTube's limit")

    for w in warn:
        print("!", w)
    print("ok" if not warn else f"{len(warn)} to fix")


ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("suggest", help="YouTube's search suggestions for each seed")
s.add_argument("seeds", nargs="+")
s.add_argument("--hl", default="vi", help="interface language (default vi)")
s.add_argument("--gl", default="VN", help="country (default VN)")
m = sub.add_parser("measure", help="check a publishing kit file")
m.add_argument("kit")
m.add_argument("--keyword", action="append", default=[], help="main search phrase; repeat for other phrasings")
args = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")     # Vietnamese text on a Windows console
if args.cmd == "suggest":
    suggest(args.seeds, args.hl, args.gl)
else:
    measure(args.kit, args.keyword)
