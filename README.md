# debog.github.io

> Adding a publication? Follow
> [UPDATING_PUBLICATIONS.md](UPDATING_PUBLICATIONS.md).

Source for <https://debog.github.io>. Every `.html` file at the repository root
(and under `codes/`) is **generated**. Do not edit them; edit the sources below
and rebuild.

## Layout

```
data/publications.yaml   canonical publication list -- the single source of truth
data/site.yaml           profile, navigation, per-page <title> and description
content/*.html           body copy for each page (plain HTML fragments)
content/codes/*.html     body copy for the software sub-pages
assets/style.css         the stylesheet (hand-maintained, no build step)
tools/build_site.py      content/ + data/  ->  *.html, sitemap.xml, robots.txt
tools/build_cv.py        data/publications.yaml -> LaTeX for the CV and resume
tools/render_pubs.py     publication-page renderer
tools/layout.py          shared <head>, masthead, nav, footer
tools/check_site.py      tag balance, dead local links, required metadata
tools/check_links.py     external link checker
tools/check_new_publications.py  ORCID + Crossref gap check
Files/                   PDFs of papers, talks, resume, CV
archive/                 superseded files, kept for reference
```

## Deploying

GitHub Pages publishes this site from the **`gh-pages`** branch, not `master`.
Pushing to `master` alone changes nothing on the live site. Both branches are
kept at the same commit:

```
git push origin master
git push origin master:gh-pages
```

A build takes a couple of minutes; `gh api repos/debog/debog.github.io/pages/builds/latest --jq .status`
reports progress. HTTPS is enforced, so `http://` 301-redirects to `https://`.

## Building

```
python3 tools/build_site.py     # rebuild every page, sitemap and robots.txt
python3 tools/check_site.py     # tag balance, dead local links, required metadata
python3 tools/check_links.py    # every external link (slow; run occasionally)
```

`check_links.py` separates genuine 404s from hosts that merely block scripted
requests (doi.org and most publishers return 403 to a bot but work fine in a
browser), so only the first group needs action.

To preview locally:

```
python3 -m http.server 8777
```

then open <http://localhost:8777>.

## Adding a publication

Append an entry to `data/publications.yaml`:

```yaml
- section: journal          # journal | preprint | book | proceedings
                            # invited | talk | thesis | report
  authors: "Lastname, A. B., Ghosh, D."
  title: "Title of the paper"
  citation: "Journal Name, 12 (3), 2026, 123456"
  year: 2026
  month: 4                  # optional; drives ordering within a year
  doi: "10.xxxx/yyyy"
  selected: true            # optional; shows it on the 2-page resume
  links:
    - {label: "full text", href: "Files/2026_Author_EtAl_JRNL.pdf"}
```

Then:

```
python3 tools/build_site.py                          # updates the website
cd ~/OneDrive/Documents/Resume/Current && make       # updates the CV and resume
```

Entries are sorted newest-first by `(year, month)`. Order inside the file does
not matter.

### Policy

- **Preprints are not listed.** When a preprint appears, check whether it has
  been published and add the published version instead. Crossref title search
  finds it:
  `curl -s 'https://api.crossref.org/works?query.bibliographic=TITLE&rows=5'`
- **Only substantive software contributions are listed** on `codes.html` and in
  the CV. Build fixes, refactors and packaging updates do not count.

### Keeping the list complete

ORCID is the easiest cross-check. Fetch the record and diff it against the YAML:

```
curl -sH "Accept: application/json" \
  https://pub.orcid.org/v3.0/0000-0003-3910-2613/works
```

Crossref resolves a DOI to authoritative metadata:

```
curl -s https://api.crossref.org/works/10.1016/j.cpc.2026.110039
```

Google Scholar blocks scripted HTTP access, but it *can* be read through a
real signed-in browser session, and it catches items ORCID misses (conference
abstracts, lab reports). Worth checking a couple of times a year:
<https://scholar.google.com/citations?user=NL34xJcAAAAJ&hl=en&sortby=pubdate>

## Video tickers

The `misc.html` sidebar carries two vertical, auto-scrolling strips of YouTube
videos. They are **generated at build time** from the data files, which are in
turn refreshed from YouTube by a script — the page is not live.

```
YouTube playlist
  -> tools/fetch_playlists.py   -> data/*_videos.json
  -> tools/build_site.py        -> misc.html
```

| Playlist | Data file | Playlist id |
|---|---|---|
| Travel | `data/travel_videos.json` | `PLCJJtCoWifB_frF7nO8uVv8o0NTtx5wF6` |
| Live performances | `data/live_videos.json` | `PLCJJtCoWifB9UBbEbQzD9FxYV8ryCVfBN` |

Which strips appear, and how many cards each shows, is declared under
`tickers:` in `data/site.yaml`.

### Refreshing

```
python3 tools/fetch_playlists.py            # update the data files
python3 tools/fetch_playlists.py --check    # report drift, write nothing (exit 1 if stale)
python3 tools/build_site.py                 # regenerate the pages
```

`.github/workflows/refresh-playlists.yml` runs this weekly and on demand, and
commits only when something actually changed. It is inert until pushed.

### Why it is scraped

- The **Data API** would need a key. A browser-side key on a public static site
  is exposed to anyone who views source, and carries a quota.
- The **playlist RSS feed** (`youtube.com/feeds/videos.xml?playlist_id=...`)
  needs no key, but returns only the 15 newest entries and sends no
  `Access-Control-Allow-Origin` header, so a browser on this site cannot fetch
  it at all. It is no substitute for the full list.

So the data is scraped from the public playlist page. Things to know:

- The list is rendered client-side; the data sits in the `ytInitialData` blob
  and is keyed by **`lockupViewModel`**. That key was `playlistVideoRenderer`
  until ~2025 and will change again. A fetch returning 0 videos means the key
  moved; the script exits non-zero rather than writing an empty list.
- The first page caps at **100 entries**, so a longer playlist is truncated.
  The strips show 20, so this does not matter for display, but the "All N on
  YouTube" label must use the playlist's own reported total, which the script
  records as `total`. Travel lists 100 of **150**; Live performances lists 98
  of **103** (the gap is private or deleted entries, which YouTube counts but
  does not show).
- Back-to-back requests occasionally return a page without the data blob. The
  script retries three times with backoff.
- YouTube may serve a bot check to datacentre IPs such as GitHub's runners. If
  the workflow starts failing, that is the likely cause; run the script locally
  instead.

### Behaviour

A small inline script at the end of `content/misc.html` drives both strips: it
clones each list once so the scroll wraps without a visible jump, and pauses on
hover, focus and drag. Without JavaScript they stay ordinary scrollable lists,
and they do not move under `prefers-reduced-motion: reduce`.

The same script sizes each strip to **three cards and half of the fourth**, so
the clipped card signals that the list scrolls on its own. The height is
measured from a real card rather than hard-coded, and recomputed on resize via
a `ResizeObserver` keyed on width (keyed on width so that setting the height
cannot retrigger it). Card heights are made uniform by clamping titles to two
lines and reserving two lines even for short ones; without that, "half a card"
would vary with the title.

Where the sidebar stacks under the gallery the cards go full-width and three
and a half of them would overflow the screen, swallowing the page scroll, so
the height is capped at 78% of the viewport and snapped down to the largest
half-card count that fits (1.5 cards at 375x812).

Thumbnails are hotlinked from `i.ytimg.com` at `/vi/<id>/mqdefault.jpg`
(320x180) and lazy-loaded. Some carry pillarboxing baked into the source image
by YouTube; that is in the JPEG, not the CSS.

## Photo gallery

**Edit `content/misc.html`, never `misc.html`.** Every root `.html` is
generated and is overwritten by the next `tools/build_site.py` run, so a hand
edit there is lost. If one has already been made, recover it from git
(`git show <commit>:misc.html`) before rebuilding.

Each year in `content/misc.html` is a `<section class="year">` holding a
heading and one `<ul>`. The two-column flow is applied to the `<ul>`, so a
year's albums stay under their own heading instead of running across the
whole gallery. Years with few entries use a single column; below roughly
560px everything collapses to one column.

To add a year, copy an existing `<section class="year">` block and keep the
shape exactly:

```html
<section class="year">
<h3 id="yYYYY">YYYY</h3>
<ul>
<li><a href="...">YYYY Month: Place</a></li>
</ul>
</section>
```

The `<ul>` must wrap the items. Bare `<li>` elements outside a `<ul>` miss the
`.year ul` rule that supplies the two columns and removes the bullet markers,
so that year renders as a single indented bulleted list while every other year
is in two columns. Add the matching `<li><a href="#yYYYY">YYYY</a></li>` to the
year-nav list at the top, newest first.

## Search Console

Property: `https://debog.github.io/` (URL-prefix), verified by the existing
`google*.html` files. HTTPS is enforced, so `http://` 301-redirects.

State as of 2 October 2026:

- The sitemap was submitted on 1 October and still reports **"Couldn't fetch"**
  with no "Last read". The sitemap itself is fine -- it serves HTTP 200 as
  `application/xml` with the correct namespace, and `robots.txt` both allows
  everything and points at it. URL Inspection confirms `Crawl allowed: Yes`,
  `Page fetch: Successful`, `Indexing allowed: Yes`.
- The underlying situation is that Google's **last crawl of the site was
  16 April 2026**, months before the rebuild, and inspected pages report
  "No referring sitemaps detected". Google simply has not come back yet.
- Indexing was requested (priority crawl queue) for the home page,
  `research.html`, `publications.html`, `resume.html` and `codes.html`.

If the sitemap still reads "Couldn't fetch" after a week of the pages being
re-crawled, remove and re-add it in the Sitemaps panel. Do not treat it as a
site fault without first re-checking the three signals above.

## Notes

- There are no external fonts or scripts. The stylesheet is the only asset,
  which keeps the pages fast and avoids the mixed-content problem the old
  site had (it loaded fonts over `http://` on an `https://` host, so they
  were silently blocked).
- Light and dark rendering both come from `assets/style.css` via
  `prefers-color-scheme`.
- `google*.html` are Search Console verification files. Leave them alone.
- `404.html` is generated like any other page but is marked `noindex` and kept
  out of `sitemap.xml`. GitHub Pages serves it automatically.
- `codes/hypar.html`, `codes/tridiaglu.html` and
  `codes/tridiaglu_scalability.html` are meta-refresh redirect stubs to the
  project sites, not content pages; the checker skips them.
- `mypic.jpg` is re-encoded at quality 84 (145 KB to 30 KB, same dimensions).
  The original is in `archive/`.
- `CRWENO/` is a self-contained exported site and is not part of this build.
- StatCounter (project 8725416) is emitted by `tools/layout.py`, now over
  `https://` and loaded `async`. The legacy snippet used `http://`, which an
  https page blocks as mixed content, so it was probably under-recording. Set
  `profile.statcounter_project` to `""` in `data/site.yaml` to switch it off.
- Dead outbound links were stripped in October 2026 (conference abstract pages
  that organisers took down). One link is knowingly left in place:
  `cpht.polytechnique.fr` returns a persistent `503`, which means unavailable
  rather than gone, so it may recover.
