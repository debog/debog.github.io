#!/usr/bin/env python3
"""Find publications that are not yet in data/publications.yaml.

  python3 tools/check_new_publications.py

Queries ORCID and Crossref, both of which are machine-readable, and reports
anything missing. Exits 1 when something is missing, 0 when the list is
complete, so it can gate a periodic check.

What this does NOT do: decide which section an entry belongs in, which
research-page bullets should cite it, or whether it belongs on the 2-page
resume. Those are judgement calls -- see UPDATING_PUBLICATIONS.md.

Google Scholar is not queried: it blocks scripted access. It does surface
items the other two miss (conference abstracts, lab reports), so check it by
hand in a signed-in browser. The document explains how.
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORCID = "0000-0003-3910-2613"
MAILTO = "debojyoti.ghosh@gmail.com"
UA = f"debog.github.io publication check (mailto:{MAILTO})"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def known():
    import yaml
    recs = yaml.safe_load((ROOT / "data" / "publications.yaml").read_text(encoding="utf-8"))
    dois = {(r.get("doi") or "").lower().strip() for r in recs if r.get("doi")}
    titles = {norm(r["title"]) for r in recs}
    return recs, dois, titles


def from_orcid():
    data = get(f"https://pub.orcid.org/v3.0/{ORCID}/works")
    out = []
    for group in data.get("group", []):
        s = group["work-summary"][0]
        doi = None
        for eid in (group.get("external-ids") or {}).get("external-id", []):
            if eid.get("external-id-type") == "doi":
                doi = eid.get("external-id-value")
        out.append({
            "title": s["title"]["title"]["value"],
            "year": (s.get("publication-date") or {}).get("year", {}).get("value"),
            "journal": (s.get("journal-title") or {}).get("value"),
            "type": s.get("type"),
            "doi": doi,
            "source": "ORCID",
        })
    return out


def from_crossref():
    """Crossref works carrying this ORCID.

    An author-name search is useless here: "Ghosh" is a very common surname
    and returns dozens of unrelated papers. Filtering on the ORCID is exact.
    """
    q = urllib.parse.urlencode({
        "filter": f"orcid:{ORCID}",
        "rows": 100,
        "sort": "published", "order": "desc",
        "select": "title,DOI,type,container-title,published",
    })
    items = get("https://api.crossref.org/works?" + q)["message"]["items"]
    out = []
    for it in items:
        dp = (it.get("published") or {}).get("date-parts", [[None]])[0]
        out.append({
            "title": (it.get("title") or ["?"])[0],
            "year": dp[0] if dp else None,
            "journal": (it.get("container-title") or [None])[0],
            "type": it.get("type"),
            "doi": it.get("DOI"),
            "source": "Crossref",
        })
    return out


def main():
    recs, dois, titles = known()
    print(f"data/publications.yaml holds {len(recs)} entries "
          f"({len(dois)} with a DOI)\n")

    found, seen = [], set()
    for fetch, label in ((from_orcid, "ORCID"), (from_crossref, "Crossref")):
        try:
            items = fetch()
            print(f"  {label}: {len(items)} works")
        except Exception as e:
            print(f"  {label}: FAILED ({type(e).__name__}: {e})")
            continue
        for it in items:
            doi = (it.get("doi") or "").lower().strip()
            key = doi or norm(it["title"])
            if key in seen:
                continue
            seen.add(key)
            if doi and doi in dois:
                continue
            t = norm(it["title"])
            if any(t[:60] and t[:60] in k for k in titles):
                continue
            found.append(it)
        time.sleep(1.0)      # Crossref rate-limits concurrent callers

    PRE = ("posted-content", "preprint")
    preprints = [i for i in found if (i.get("type") or "") in PRE]
    real = [i for i in found if (i.get("type") or "") not in PRE]

    def show(items):
        for it in sorted(items, key=lambda x: str(x.get("year") or ""), reverse=True):
            print(f"  [{it.get('year') or '????'}] {it['title']}")
            print(f"       {it.get('journal') or '-'}  |  {it.get('type')}  "
                  f"|  doi:{it.get('doi') or '-'}  |  via {it['source']}")

    if real:
        print(f"\n{len(real)} publication(s) MISSING from data/publications.yaml:\n")
        show(real)
    else:
        print("\nNo published work is missing.")

    if preprints:
        print(f"\n{len(preprints)} preprint(s) -- excluded by policy, but check "
              f"whether each has since been published:\n")
        show(preprints)

    print("\nNext: follow UPDATING_PUBLICATIONS.md.")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
