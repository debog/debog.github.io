"""Render the misc-page video tickers from data/*_videos.json."""
import html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THUMB = "https://i.ytimg.com/vi/{id}/mqdefault.jpg"
WATCH = "https://www.youtube.com/watch?v={id}&amp;list={pl}"
PLIST = "https://www.youtube.com/playlist?list={pl}"


def card(v, pl):
    title = html.escape(v["title"], quote=True)
    dur = html.escape(v.get("duration") or "")
    badge = f'<span class="vid__dur">{dur}</span>' if dur else ""
    return (f'<li class="vid"><a href="{WATCH.format(id=v["id"], pl=pl)}">'
            f'<span class="vid__thumb">'
            f'<img src="{THUMB.format(id=v["id"])}" alt="" loading="lazy" '
            f'decoding="async" width="320" height="180">{badge}</span>'
            f'<span class="vid__title">{title}</span></a></li>')


def render(site):
    out = []
    for t in site.get("tickers", []):
        path = ROOT / "data" / t["data"]
        blob = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(blob, list):          # pre-`total` format
            blob = {"total": len(blob), "videos": blob}
        vids = blob["videos"]
        total = blob.get("total", len(vids))
        shown = vids[: t.get("show", 20)]
        pl = t["playlist"]
        label = html.escape(t["label"])
        cards = "\n".join(card(v, pl) for v in shown)
        out.append(f"""<section>
<h2>{label}</h2>
<div class="ticker" data-ticker aria-label="{label} videos" role="region" tabindex="0">
<ul class="ticker__track">
{cards}
</ul>
</div>
<p class="ticker__more"><a href="{PLIST.format(pl=pl)}">All {total} on YouTube</a></p>
</section>""")
    return "\n".join(out)
