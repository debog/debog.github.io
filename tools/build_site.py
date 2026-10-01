#!/usr/bin/env python3
"""Build every root .html page, sitemap.xml and robots.txt.

  python3 tools/build_site.py

Sources:
  data/site.yaml          profile, nav, per-page <title>/description
  data/publications.yaml  canonical publication list
  content/<page>.html     body fragment for each page (publications is generated)
"""
import sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import yaml
import layout
import render_pubs


def load(name):
    with open(ROOT / "data" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    site = load("site.yaml")
    pubs = load("publications.yaml")

    pub_body, groups = render_pubs.body(pubs)
    pub_jsonld = render_pubs.jsonld(groups)

    written = []
    for page_file in site["pages"]:
        if page_file == "publications.html":
            body, extra = pub_body, pub_jsonld
        else:
            frag = ROOT / "content" / page_file
            if not frag.exists():
                print(f"  !! missing content/{page_file}, skipped")
                continue
            body, extra = frag.read_text(encoding="utf-8").rstrip(), ""
        depth = page_file.count("/")
        prefix = "../" * depth
        out = layout.render(site, page_file, body, extra_jsonld=extra, prefix=prefix)
        out = layout.GEN_WARNING.format(src=page_file) + "\n" + out
        (ROOT / page_file).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / page_file).write_text(out, encoding="utf-8")
        written.append(page_file)
        print(f"  wrote {page_file:22s} {len(out)//1024:3d} KB")

    write_sitemap(site, [p for p in written if p != "404.html"])
    write_robots(site)
    print(f"\n{len(written)} pages, {len(pubs)} publications")


def write_sitemap(site, pages):
    base = site["profile"]["base_url"].rstrip("/")
    today = datetime.date.today().isoformat()
    prio = {"index.html": "1.0", "publications.html": "0.9", "research.html": "0.9",
            "resume.html": "0.8", "codes.html": "0.7", "misc.html": "0.3"}
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        loc = f"{base}/" if p == "index.html" else f"{base}/{p}"
        L += ["  <url>", f"    <loc>{loc}</loc>",
              f"    <lastmod>{today}</lastmod>",
              f"    <priority>{prio.get(p, '0.5')}</priority>", "  </url>"]
    L.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("  wrote sitemap.xml")


def write_robots(site):
    base = site["profile"]["base_url"].rstrip("/")
    txt = f"""User-agent: *
Allow: /

Sitemap: {base}/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(txt, encoding="utf-8")
    print("  wrote robots.txt")


if __name__ == "__main__":
    main()
