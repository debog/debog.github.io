#!/usr/bin/env python3
"""One-off: extract structured publication records from the legacy publications.html.

Writes data/publications.yaml. After this runs and is verified, publications.html
is generated FROM the yaml by tools/build.py and this script is no longer needed.
"""
import re, sys, json, html as htmlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "publications.html"

SECTION_MAP = {
    "Journal Articles": "journal",
    "Book Chapters": "book",
    "Conference Proceedings": "proceedings",
    "Invited and Minisymposium Talks": "invited",
    "Theses": "thesis",
    "Technical Reports": "report",
    "Other Conferences/Meetings/Talks/Posters": "talk",
}

def clean_attrs(s):
    """The legacy file writes `href="x", target=blank` with a stray comma."""
    s = re.sub(r'",\s*target\s*=\s*"?blank"?', '"', s)
    s = re.sub(r"\s*,\s*target\s*=\s*\"?blank\"?", "", s)
    return s

def text_of(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

def main():
    raw = SRC.read_text(encoding="utf-8")
    # keep only the #content div
    body = raw.split('<div id="content">', 1)[1].split('<!-- end #content -->', 1)[0]
    parts = re.split(r"<h3>(.*?)</h3>", body, flags=re.S)
    records = []
    for i in range(1, len(parts), 2):
        sec_name = text_of(parts[i])
        key = SECTION_MAP.get(sec_name)
        if key is None:
            print(f"!! unmapped section: {sec_name!r}", file=sys.stderr)
            continue
        chunk = parts[i + 1]
        # entries are <li> ... up to next <li> or </p>
        items = re.findall(r"<li>(.*?)(?=<li>|</p>)", chunk, flags=re.S)
        for it in items:
            rec = parse_item(clean_attrs(it), key)
            if rec:
                records.append(rec)
    out = ROOT / "data" / "publications.yaml"
    write_yaml(records, out)
    counts = {}
    for r in records:
        counts[r["section"]] = counts.get(r["section"], 0) + 1
    print(f"wrote {out} : {len(records)} records")
    for k, v in counts.items():
        print(f"  {k:12s} {v}")

def parse_item(it, section):
    it = it.strip()
    if not it:
        return None
    # split off the trailing link row (everything after the LAST <br> that is
    # followed only by nbsp-padded parenthesised links)
    m = re.search(r"<i>(.*?)</i>", it, flags=re.S)
    if not m:
        print(f"!! no <i> title in: {text_of(it)[:80]}", file=sys.stderr)
        return None
    authors = text_of(it[: m.start()]).rstrip(", ")
    title = text_of(m.group(1))
    tail = it[m.end():]

    # links: all anchors that sit inside parentheses in the tail
    links = []
    for lm in re.finditer(r"\(\s*<a\s+href=\"([^\"]+)\"[^>]*>\s*(?:<strong>)?(.*?)(?:</strong>)?\s*</a>\s*\)", tail, flags=re.S):
        href, label = lm.group(1), text_of(lm.group(2))
        if label:
            links.append({"label": label, "href": href})
    # citation = tail up to the first <br>, anchors preserved
    cite_html = re.split(r"<br\s*/?>", tail, 1)[0]
    cite_html = cite_html.strip().lstrip(",").strip()
    # drop the doi anchor from the citation; it is stored separately
    doi = None
    dm = re.search(r"https?://(?:dx\.)?doi\.org/([^\"]+)", cite_html)
    if dm:
        doi = dm.group(1)
        cite_html = re.sub(r",?\s*<a\s+href=\"https?://(?:dx\.)?doi\.org/[^\"]+\"[^>]*>.*?</a>", "", cite_html, flags=re.S)
    cite_html = cite_html.strip().rstrip(".").rstrip(",").strip()

    # "also at:" continuation lines
    also = None
    am = re.search(r"also at:\s*(.*?)(?:<br|$)", tail, flags=re.S | re.I)
    if am:
        also = text_of(am.group(1)).rstrip(".")

    # page ranges look like years ("2074-2080"); bound to a plausible window
    years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", text_of(cite_html))]
    years = [y for y in years if 1995 <= y <= 2027]
    year = years[-1] if years else None

    rec = {"section": section, "title": title, "citation": cite_html}
    if authors:
        rec["authors"] = authors
    if year:
        rec["year"] = year
    if doi:
        rec["doi"] = doi
    if also:
        rec["also"] = also
    if links:
        rec["links"] = links
    return rec

def yq(s):
    """Quote a scalar for YAML, always double-quoted and escaped."""
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + s + '"'

def write_yaml(records, path):
    L = ["# Canonical publication list. Edit this file; then run tools/build.py.",
         "# section: journal | book | proceedings | invited | thesis | report | talk",
         ""]
    for r in records:
        L.append(f"- section: {r['section']}")
        if "authors" in r:
            L.append(f"  authors: {yq(r['authors'])}")
        L.append(f"  title: {yq(r['title'])}")
        L.append(f"  citation: {yq(r['citation'])}")
        if "year" in r:
            L.append(f"  year: {r['year']}")
        if "doi" in r:
            L.append(f"  doi: {yq(r['doi'])}")
        if "also" in r:
            L.append(f"  also: {yq(r['also'])}")
        if "links" in r:
            L.append("  links:")
            for lk in r["links"]:
                L.append(f"    - {{label: {yq(lk['label'])}, href: {yq(lk['href'])}}}")
        L.append("")
    path.write_text("\n".join(L), encoding="utf-8")

if __name__ == "__main__":
    main()
