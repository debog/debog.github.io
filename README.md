# debog.github.io

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
Files/                   PDFs of papers, talks, resume, CV
archive/                 superseded files, kept for reference
```

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

## Travel-video ticker

`content/misc.html` holds a horizontally scrolling strip of videos from the
YouTube Travel playlist, between Photography and Travel and events. The card
data lives in `data/travel_videos.json` (id, title, duration); the page uses
the 30 most recent and links to the full playlist.

To refresh the list after adding videos, re-extract it from the playlist page
(YouTube renders the list client-side, so the data sits in the `ytInitialData`
blob and is keyed by `lockupViewModel`):

```
curl -sA "Mozilla/5.0" \
  "https://www.youtube.com/playlist?list=PLCJJtCoWifB_frF7nO8uVv8o0NTtx5wF6" \
  > /tmp/pl.html
```

then pull `contentId`, the metadata title, and the duration badge out of each
`lockupViewModel` into `data/travel_videos.json` and rebuild. Thumbnails are
hotlinked from `i.ytimg.com` at `/vi/<id>/mqdefault.jpg` and lazy-loaded.

The strip auto-scrolls via a small inline script that clones the cards once so
the wrap is seamless, and pauses on hover, focus and drag. Without JavaScript
it stays an ordinary scrollable strip, and it does not move at all under
`prefers-reduced-motion: reduce`.

## Photo gallery

Each year in `content/misc.html` is a `<section class="year">` holding a
heading and one `<ul>`. The two-column flow is applied to the `<ul>`, so a
year's albums stay under their own heading instead of running across the
whole gallery. Years with few entries use a single column; below roughly
560px everything collapses to one column.

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
