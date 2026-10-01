# Updating publications

Instructions for an agent asked to bring the publication record on
<https://debog.github.io> up to date. Written to be followed from a cold
start, with no memory of previous sessions.

Run this when a new paper appears, when a preprint is published, or every few
months as a check.

---

## 1. Scope

Publications appear in five places. All of them derive from one file.

| Place | Source | Generated how |
|---|---|---|
| `publications.html` | `data/publications.yaml` | `tools/build_site.py` |
| Citations on `research.html` | hand-written in `content/research.html` | `tools/build_site.py` |
| Software descriptions on `codes.html` | hand-written in `content/codes.html` | `tools/build_site.py` |
| CV and resume PDFs | `data/publications.yaml` | see `../Resume/Current/UPDATING.md` |
| `Files/*.pdf` | manual uploads | n/a |

`data/publications.yaml` is the single source of truth. Never hand-edit
`publications.html`; it is overwritten on every build.

---

## 2. Automated and manual parts

What is automated:

- **Detecting** missing publications. `tools/check_new_publications.py`
  queries ORCID and Crossref and reports anything absent from the YAML.
- **Rendering**. Once an entry is in the YAML, every page and PDF picks it up.

What is not, and needs judgement:

- Which section an entry belongs in.
- Which research-page bullets should now cite it.
- Whether it belongs among the selected publications on the 2-page resume.
- Whether a preprint has been superseded by a published version.

So: run the script to find the gap, then use this document to close it.

---

## 3. Sources

Check in this order. The first two are scriptable; the third is not.

### 3.1 ORCID (primary, scriptable)

ORCID iD `0000-0003-3910-2613`. This is the curated record and the most
reliable source.

```
python3 tools/check_new_publications.py
```

Exits 0 when nothing published is missing, 1 when something is. It also lists
preprints separately, because preprints are deliberately excluded (§5.1).

Raw record, if needed:

```
curl -sH "Accept: application/json" https://pub.orcid.org/v3.0/0000-0003-3910-2613/works
```

### 3.2 Crossref (authoritative metadata, scriptable)

Use Crossref to confirm every detail before writing an entry: full author
list, journal name, volume, issue, article number, year, month.

```
curl -s "https://api.crossref.org/works/<DOI>"
```

Two traps, both hit before:

- **Do not search Crossref by author name.** "Ghosh" is a very common
  surname and returns dozens of unrelated papers. Filter on the ORCID
  instead: `https://api.crossref.org/works?filter=orcid:0000-0003-3910-2613`.
- **Crossref rate-limits concurrent callers.** Several parallel requests
  return spurious "not found" results. Query serially with a short delay. If
  a DOI appears unregistered, retry once on its own before believing it.

### 3.3 Google Scholar (catches what the others miss, manual)

Scholar blocks scripted access — a plain fetch returns "unusual traffic".
Do not try to work around it. Read it through a signed-in browser instead,
using **Claude in Chrome**:

```
https://scholar.google.com/citations?user=NL34xJcAAAAJ&hl=en&sortby=pubdate
```

Scholar is worth checking because it lists items ORCID and Crossref do not:
conference abstracts, IEEE conference records, lab technical reports, and
software releases. Past checks found an ICOPS abstract and an LLNL report
this way.

Also read the citation metrics while there — total citations, h-index and
i10-index appear on that page. They are quoted on the CV and resume, so note
them if they have moved.

### 3.4 Other sources

- **arXiv**: `http://export.arxiv.org/api/query?search_query=all:Ghosh_D`
  is noisy. Prefer a direct arXiv ID when one is known.
- **The user**. Ask about work in press, accepted but not yet posted, and
  conference talks given since the last update. Talks rarely reach any of the
  above.

---

## 4. Procedure

1. Run `python3 tools/check_new_publications.py`.
2. Check Google Scholar in a browser (§3.3) for anything the script missed.
3. For each new item, fetch its Crossref record and confirm the metadata.
4. Add an entry to `data/publications.yaml` (§5).
5. Decide whether any `research.html` bullet should now cite it (§6).
6. Rebuild and validate:
   ```
   python3 tools/build_site.py
   python3 tools/check_site.py
   python3 tools/check_links.py        # slow; worth running after a batch
   ```
7. Rebuild the CV and resume: see `../Resume/Current/UPDATING.md`.
8. Commit, and push **both branches** (§8).

---

## 5. Entry format

Append anywhere in `data/publications.yaml`; entries are sorted on build.

```yaml
- section: journal
  authors: "Lastname, A. B., Ghosh, D., Other, C. D."
  title: "Title in sentence case as published"
  citation: "Journal Name, 12 (3), 2026, 123456"
  year: 2026
  month: 4
  doi: "10.xxxx/yyyy"
  selected: true                 # optional; shows on the 2-page resume
  links:
    - {label: "full text", href: "Files/2026_Author_EtAl_JRNL.pdf"}
```

Sections: `journal`, `book`, `proceedings`, `invited`, `talk`, `thesis`,
`report`. There is no `preprint` section — see below.

Rules learned the hard way:

- **Author format is `Surname, A. B.`** and the subject's own name must read
  exactly `Ghosh, D.` so the renderer can bold it. Do not write `Ghosh., D.`
- **Sorting is by `(year, month)` descending.** Supply `month` whenever
  Crossref gives one, otherwise entries within a year sit in arbitrary order.
- **Do not let a page range become the year.** `2074-2080` parses as a year
  if the extraction is naive. The build rejects any year outside 1995-2027.
- **`links` are optional.** Add a local PDF under `Files/` when one exists.

### 5.1 Preprints

Preprints are **not listed**. When the checker reports one:

1. Search Crossref by title for a published version:
   ```
   curl -s "https://api.crossref.org/works?query.bibliographic=<TITLE>&rows=5"
   ```
2. If published, add the published version as a normal entry.
3. If not, do nothing. Leave it out.

A preprint may already be present under its published title with slightly
different wording ("Reduced Ordering" vs "Reduced Order"), so check the list
before concluding it is missing.

---

## 6. Citations on the research page

Bullets on `research.html` carry inline citations to the papers that support
them, written by hand in `content/research.html`:

```html
<li>Claim text <span class="cite">(<a href="https://doi.org/10.xxxx/yyy">J.
Abbrev. 2026</a>; <a href="...">Other J. 2024</a>)</span>.</li>
```

Use short journal abbreviations and the year. Several citations are separated
by semicolons. Local PDFs use a plain relative path (`Files/...`) and must
**not** be given a `https://doi.org/` prefix.

### 6.1 Bullets awaiting papers

These describe work with no published paper yet. **Cite them as soon as the
corresponding paper appears** — this is the main reason to re-read this
document.

| Section | Bullet | Waiting on |
|---|---|---|
| Particle-based methods | Super-droplet cloud microphysics, including ice | the ERF super-droplet paper (currently a preprint) |
| Particle-based methods | Agent-based epidemiological models | the medical-workforce ABM paper (currently a preprint) |
| Scientific machine learning | ERF-SDM generated the warm-rain ROM training data | already cited; keep in step if a follow-up appears |
| Numerical methods | Multirate and extrapolated multirate for AMR | no paper; may stay uncited |
| High-performance computing | AMReX portability and multi-GPU training | no paper |
| Earlier research | Semi-implicit and multirate integration in NUMA | no paper |

Do not attach a loosely related citation to make a bullet look supported. An
uncited bullet is better than a misleading one.

### 6.2 Machine-learning framing

The learned-denoiser work on `research.html` is labelled early-stage and
unpublished, deliberately. Do not upgrade that language until a paper or
conference presentation exists. The same restraint applies to the resume.

---

## 7. Checks before committing

- `python3 tools/check_site.py` — tag balance, dead local links, required
  metadata. Must print `ALL PAGES OK`.
- `python3 tools/check_links.py` — external links. It separates genuine 404s
  from hosts that merely block scripted requests (doi.org and most publishers
  return 403 to a bot but work in a browser); only the first group needs
  action.
- Confirm every new DOI resolves in Crossref, serially (§3.2).
- Confirm the new entry appears in the right section, in the right position,
  on `publications.html`.

---

## 8. Deploying

GitHub Pages publishes from the **`gh-pages`** branch, not `master`. Pushing
to `master` alone changes nothing on the live site.

```
git push origin master
git push origin master:gh-pages
```

A build takes a couple of minutes. Check progress with:

```
gh api repos/debog/debog.github.io/pages/builds/latest --jq .status
```

Then confirm the live page shows the new entry.
