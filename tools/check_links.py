#!/usr/bin/env python3
"""Check every external link in the generated pages.

  python3 tools/check_links.py            # all pages
  python3 tools/check_links.py --page publications.html

Reports only genuine failures. A 403 usually means the host blocks scripted
requests (doi.org and most publishers do) rather than a dead link, so those
are listed separately and not counted as errors.
"""
import argparse, concurrent.futures as cf, html, re, ssl, sys, urllib.error, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")   # some hosts 404 a non-browser UA
CTX = ssl.create_default_context()
SOFT = {401, 403, 405, 429, 999}      # bot-blocking, not a dead link
RETRY_GET = SOFT | {404, 400}         # some hosts answer HEAD badly; confirm with GET


def check(url, timeout):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return url, r.status
        except urllib.error.HTTPError as e:
            if e.code in RETRY_GET and method == "HEAD":
                continue
            return url, e.code
        except Exception as e:
            if method == "HEAD":
                continue
            return url, type(e).__name__
    return url, "ERROR"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", help="limit to one page")
    ap.add_argument("--timeout", type=float, default=12)
    ap.add_argument("--jobs", type=int, default=24)
    args = ap.parse_args()

    pages = ([ROOT / args.page] if args.page else
             [p for p in ROOT.glob("*.html") if not p.name.startswith("google")]
             + list((ROOT / "codes").glob("*.html")))

    where = defaultdict(set)
    for p in pages:
        txt = p.read_text(encoding="utf-8")
        # only <a href>: <link rel=canonical> points at this site's own pages,
        # which 404 until the build is deployed.
        for u in re.findall(r'<a [^>]*href="(https?://[^"]+)"', txt):
            # hrefs are HTML-escaped in the output; &amp; must become & before
            # the URL is requested, or the query string is wrong.
            where[html.unescape(u)].add(p.relative_to(ROOT).as_posix())

    print(f"checking {len(where)} unique external links from {len(pages)} pages...\n")
    results = {}
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        for u, s in ex.map(lambda u: check(u, args.timeout), where):
            results[u] = s

    hard, soft = {}, {}
    for u, s in results.items():
        if isinstance(s, int) and s < 400:
            continue
        (soft if s in SOFT else hard)[u] = s

    if hard:
        print(f"BROKEN ({len(hard)}):")
        for u, s in sorted(hard.items(), key=lambda kv: str(kv[1])):
            print(f"  [{s}] {u}")
            print(f"        on: {', '.join(sorted(where[u]))}")
    else:
        print("No broken links.")

    if soft:
        print(f"\nBlocked by the host, probably fine in a browser ({len(soft)}):")
        hosts = defaultdict(int)
        for u in soft:
            hosts[re.sub(r"^https?://([^/]+).*", r"\1", u)] += 1
        for h, n in sorted(hosts.items(), key=lambda kv: -kv[1]):
            print(f"  {h}: {n}")

    print(f"\n{len(results) - len(hard) - len(soft)} OK, {len(soft)} blocked, {len(hard)} broken")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
