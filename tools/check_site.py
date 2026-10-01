#!/usr/bin/env python3
"""Sanity checks on the generated site: tag balance, local link targets, metadata."""
import re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []
    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))
    def handle_endtag(self, tag):
        if tag in VOID: return
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>"); return
        if self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            for i in range(len(self.stack)-1, -1, -1):
                if self.stack[i][0] == tag:
                    unclosed = [t for t,_ in self.stack[i+1:]]
                    self.errors.append(
                        f"line {self.getpos()[0]}: </{tag}> closes but leaves open {unclosed}")
                    del self.stack[i:]
                    break
            else:
                self.errors.append(f"line {self.getpos()[0]}: </{tag}> never opened")

fail = 0
pages = sorted([p for p in ROOT.glob("*.html") if not p.name.startswith("google")]
               + list((ROOT / "codes").glob("*.html")))
for page in pages:
    txt = page.read_text(encoding="utf-8")
    if "http-equiv=\"refresh\"" in txt.lower().replace("'", '"'):
        print(f"{str(page.relative_to(ROOT)):26s} redirect stub, skipped")
        continue
    c = Check(); c.feed(txt); c.close()
    probs = list(c.errors)
    if c.stack:
        probs.append(f"unclosed at EOF: {[t for t,_ in c.stack]}")
    for need, label in [("<meta name=\"viewport\"", "viewport"),
                        ("<meta name=\"description\"", "description"),
                        ("rel=\"canonical\"", "canonical"),
                        ("<h1", "h1")]:
        if need not in txt:
            probs.append(f"missing {label}")
    if txt.count("<h1") != 1:
        probs.append(f"{txt.count('<h1')} <h1> tags (want exactly 1)")
    if "http://fonts" in txt or "http://www.freecsstemplates" in txt:
        probs.append("insecure http:// asset reference")
    # local link targets
    for href in re.findall(r'href="([^"#?:][^"]*)"', txt):
        href = href.split("#")[0].split("?")[0]
        if not href or href.startswith(("http","mailto","data:","//")) or "@" in href.split("/")[0]:
            continue
        if not (page.parent / href).resolve().exists():
            probs.append(f"dead local link: {href}")
    status = "FAIL" if probs else "ok"
    if probs: fail += 1
    print(f"{str(page.relative_to(ROOT)):26s} {status}")
    for p in dict.fromkeys(probs):
        print(f"    - {p}")

print()
print("ALL PAGES OK" if not fail else f"{fail} page(s) with problems")
sys.exit(1 if fail else 0)
