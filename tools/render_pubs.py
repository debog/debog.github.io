"""Render data/publications.yaml into the publications page body."""
import re, json, html

# display order -> (anchor, heading)
SECTIONS = [
    ("journal",     "journals",    "Journal Articles"),
    ("book",        "book",        "Book Chapters"),
    ("proceedings", "conf_proc",   "Conference Proceedings"),
    ("invited",     "invite",      "Invited and Minisymposium Talks"),
    ("talk",        "conf_talk",   "Other Conferences, Meetings, Talks and Posters"),
    ("thesis",      "theses",      "Theses"),
    ("report",      "rep",         "Technical Reports"),
]

SELF = re.compile(r"\bGhosh\.?,\s*D\.?(?:\s*,)?", re.I)


# "Surname, A. B., Other, C.-D." -> ["A. B. Surname", "C.-D. Other"]
AUTHOR_RE = re.compile(
    r"((?:(?:van|von|de|der|den|du|da|di|le|la)\s+)*"   # lowercase particles
    r"[A-Z][A-Za-z'\u2019\-]*"                          # surname
    r"(?:\s+(?:de|van|von|der|den|Jr\.?|III)\.?)?"
    r"(?:\s+[A-Z][A-Za-z'\u2019\-]*)?)"                # optional second word
    r",\s*"
    r"((?:[A-Z]\.?(?:\s*-\s*[A-Z]\.?)*\s*){1,4})"      # initials
)


def split_authors(s):
    out = []
    for surname, initials in AUTHOR_RE.findall(s or ""):
        ini = re.sub(r"\s+", " ", initials).strip().rstrip(",")
        out.append(f"{ini} {surname}".strip())
    return out


def bold_self(authors):
    """Make the subject's own name stand out in a long author list."""
    return SELF.sub(lambda m: f'<span class="pub__self">{m.group(0)}</span>', authors)


def doi_url(doi):
    return "https://doi.org/" + doi.lstrip("/")


def render_entry(rec):
    out = ['<li>']
    if rec.get("authors"):
        out.append(f'<span class="pub__authors">{bold_self(rec["authors"])}</span>, ')
    out.append(f'<span class="pub__title">{html.escape(rec["title"])}</span>')
    cite = rec.get("citation", "").strip()
    if cite:
        out.append(f', <span class="pub__cite">{cite}</span>')
    if rec.get("doi"):
        u = doi_url(rec["doi"])
        out.append(f', <a href="{html.escape(u, quote=True)}">doi:{html.escape(rec["doi"])}</a>')
    out.append(".")
    if rec.get("also"):
        out.append(f'<span class="pub__also">Also presented at: {rec["also"]}.</span>')
    links = rec.get("links") or []
    if links:
        out.append('<span class="pub__links">')
        for lk in links:
            out.append(f'<a href="{html.escape(lk["href"], quote=True)}">{html.escape(lk["label"])}</a>')
        out.append("</span>")
    out.append("</li>")
    return "".join(out)


def body(records):
    groups = {k: [] for k, _, _ in SECTIONS}
    for r in records:
        if r["section"] in groups:
            groups[r["section"]].append(r)
        else:
            raise SystemExit(f"unknown section {r['section']!r} in {r['title'][:50]!r}")
    # guard: a year outside this window means the citation was mis-parsed
    for r in records:
        y = r.get("year")
        if y is not None and not (1995 <= y <= 2027):
            raise SystemExit(f"implausible year {y} for {r['title'][:60]!r}")

    # strict reverse chronological: year, then month; undated months sort last
    # within their year, and file order breaks any remaining tie.
    for k in groups:
        groups[k].sort(key=lambda r: (r.get("year") or 0, r.get("month") or 0),
                       reverse=True)

    live = [(k, a, h) for k, a, h in SECTIONS if groups[k]]

    out = ['<div class="cols">', '<main id="main">']
    out.append('<ul class="pubnav">')
    for k, anchor, heading in live:
        out.append(f'<li><a href="#{anchor}">{heading} ({len(groups[k])})</a></li>')
    out.append("</ul>")

    for k, anchor, heading in live:
        out.append(f'<h2 id="{anchor}">{heading} <span class="pubcount">&mdash; {len(groups[k])}</span></h2>')
        out.append('<ol class="pubs">')
        for rec in groups[k]:
            out.append(render_entry(rec))
        out.append("</ol>")
        out.append('<p class="toplink"><a href="#main">Back to top</a></p>')

    out.append("</main>")
    out.append(sidebar(records))
    out.append("</div>")
    return "\n".join(out), groups


def sidebar(records):
    n_j = sum(1 for r in records if r["section"] in ("journal", "book"))
    n_c = sum(1 for r in records if r["section"] == "proceedings")
    n_t = sum(1 for r in records if r["section"] in ("invited", "talk"))
    return f"""<aside class="side">
<section>
<h2>At a glance</h2>
<dl class="factgrid">
<dt>Journal &amp; book</dt><dd>{n_j}</dd>
<dt>Proceedings</dt><dd>{n_c}</dd>
<dt>Talks &amp; posters</dt><dd>{n_t}</dd>
</dl>
<p>Indexed lists are also kept at <a href="https://scholar.google.com/citations?user=NL34xJcAAAAJ&amp;hl=en">Google Scholar</a> and <a href="https://orcid.org/0000-0003-3910-2613">ORCID</a>.</p>
</section>
<section>
<h2>Downloads</h2>
<ul>
<li><a href="Files/cv_ghosh.pdf">Full CV (PDF)</a></li>
<li><a href="Files/resume_ghosh.pdf">R&eacute;sum&eacute; (PDF)</a></li>
<li><a href="Files/publications_ghosh.pdf">Publication list (PDF)</a></li>
</ul>
</section>
</aside>"""


def jsonld(groups):
    """ItemList of peer-reviewed articles that carry a DOI."""
    items = []
    pos = 0
    for key in ("journal", "book", "proceedings"):
        for r in groups.get(key, []):
            if not r.get("doi"):
                continue
            pos += 1
            node = {
                "@type": "ListItem",
                "position": pos,
                "item": {
                    "@type": "ScholarlyArticle",
                    "name": r["title"],
                    "sameAs": doi_url(r["doi"]),
                    "identifier": r["doi"],
                },
            }
            if r.get("year"):
                node["item"]["datePublished"] = str(r["year"])
            names = split_authors(r.get("authors", ""))
            if names:
                node["item"]["author"] = [{"@type": "Person", "name": n} for n in names]
            items.append(node)
    data = {"@context": "https://schema.org", "@type": "ItemList",
            "name": "Publications of Debojyoti Ghosh",
            "numberOfItems": len(items), "itemListElement": items}
    return ('<script type="application/ld+json">\n'
            + json.dumps(data, ensure_ascii=False) + "\n</script>")
