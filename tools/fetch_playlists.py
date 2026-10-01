#!/usr/bin/env python3
"""Refresh the video data behind the misc-page tickers.

  python3 tools/fetch_playlists.py            # update data/*_videos.json
  python3 tools/fetch_playlists.py --check    # report drift, write nothing

Scrapes the public playlist pages. No API key is needed, but note:

  * YouTube renders the list client-side; the data lives in the `ytInitialData`
    blob and is keyed by `lockupViewModel`. That key has changed before
    (`playlistVideoRenderer` until ~2025) and will change again. If a fetch
    returns 0 videos, that is the first thing to check.
  * The playlist RSS feed (youtube.com/feeds/videos.xml?playlist_id=...) needs
    no scraping but returns only the 15 newest entries and sends no CORS
    header, so it is no use either for the full list or for a browser fetch.

Order follows the playlist's own sort order on YouTube.

The initial page load carries only the first 100 entries, so a longer playlist
is truncated. The tickers show 20, so that is harmless, but the "All N on
YouTube" label must use the playlist's own reported total, which is recorded
as `total` alongside the videos.
"""
import argparse, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")

PLAYLISTS = {
    "travel_videos.json": "PLCJJtCoWifB_frF7nO8uVv8o0NTtx5wF6",
    "live_videos.json":   "PLCJJtCoWifB9UBbEbQzD9FxYV8ryCVfBN",
}


def walk(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for v in obj.values():
            yield from walk(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, key)


def fetch(playlist_id):
    """Return (videos, total). `total` is what YouTube reports for the whole
    playlist, which can exceed len(videos): the first page caps at 100, and
    private or deleted entries are counted but not listed."""
    url = "https://www.youtube.com/playlist?list=" + playlist_id
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    # Back-to-back requests occasionally come back without the data blob.
    # Retry a couple of times before treating it as a real breakage.
    m = None
    for attempt in range(3):
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
        if m:
            break
        time.sleep(3 * (attempt + 1))
    if not m:
        raise SystemExit("ytInitialData not found after 3 attempts; "
                         "the page shape has probably changed")
    data = json.loads(m.group(1))

    vids, seen = [], set()
    for lv in walk(data, "lockupViewModel"):
        vid = lv.get("contentId")
        if not vid or len(vid) != 11 or vid in seen:
            continue
        seen.add(vid)
        title_node = (lv.get("metadata", {})
                        .get("lockupMetadataViewModel", {})
                        .get("title", {}))
        title = title_node.get("content") or "".join(
            r.get("text", "") for r in (title_node.get("runs") or []))
        duration = ""
        for badge in walk(lv, "thumbnailBadgeViewModel"):
            if re.match(r"^\d+:\d{2}", badge.get("text", "")):
                duration = badge["text"]
                break
        vids.append({"id": vid, "title": title.strip(), "duration": duration})

    totals = [int(n) for n in re.findall(r'"(\d+) videos?"', json.dumps(data))]
    total = max(totals) if totals else len(vids)
    return vids, max(total, len(vids))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report whether anything changed; write nothing")
    args = ap.parse_args()

    changed = False
    for name, pid in PLAYLISTS.items():
        path = ROOT / "data" / name
        old = json.loads(path.read_text()) if path.exists() else {}
        if isinstance(old, list):           # pre-`total` format
            old = {"total": len(old), "videos": old}
        vids, total = fetch(pid)
        if not vids:
            raise SystemExit(f"{name}: 0 videos parsed -- the lockupViewModel key "
                             f"has probably changed again")
        new = {"playlist": pid, "total": total, "videos": vids}
        same = old.get("videos") == vids and old.get("total") == total
        changed |= not same
        oldids = [v["id"] for v in old.get("videos", [])]
        if same:
            note = "no change"
        elif oldids == [v["id"] for v in vids]:
            note = "metadata changed"
        else:
            note = "ORDER OR CONTENT CHANGED"
        print(f"  {name:22s} {len(oldids):3d} -> {len(vids):3d} listed "
              f"({total} in playlist), {note}")
        if not args.check and not same:
            path.write_text(json.dumps(new, indent=1) + "\n", encoding="utf-8")

    if args.check:
        print("\ndrift detected" if changed else "\nup to date")
        return 1 if changed else 0
    if changed:
        print("\ndata updated -- now run tools/build_site.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
