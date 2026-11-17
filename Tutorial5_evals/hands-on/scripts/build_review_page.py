"""Render a one-page HTML review sheet of the answer key (for checking labels by eye).

    uv run python scripts/build_review_page.py            -> results/answer_key_review.html
"""
import html, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = ROOT / "data"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "answer_key_review.html"
OUT.parent.mkdir(exist_ok=True)
P = json.loads((D / "papers.json").read_text())
G = json.loads((D / "gold.json").read_text())
e = html.escape

PROJ = {"P1": "Detecting small MPs in drinking water",
        "P2": "Transport: urban rivers → estuary",
        "P3": "Capturing MPs from water with biochar"}

def chips(g):
    out = [f'<span class="chip {p}{" rel" if lv == "related" else ""}">{p} {lv}</span>' for p, lv in g["labels"].items()]
    out += [f'<span class="chip {p} ok" title="defensible extra — not penalised by a lenient grader">{p}?</span>' for p in g["acceptable"]]
    return "".join(out) or '<span class="chip none">not relevant</span>'

cards = []
for w in range(1, 9):
    items = [p for p in P if p["week"] == w]
    nrel = sum(1 for p in items if G[p["paper_id"]]["labels"])
    cards.append(f'<section class="wk"><h2 id="w{w}">Week {w} <small>{nrel} of {len(items)} relevant</small></h2>')
    for p in items:
        g = G[p["paper_id"]]
        tags = " ".join(list(g["labels"]) + sorted(set(g["labels"].values())) + [f"acc-{a}" for a in g["acceptable"]]
                        + [g["difficulty"]] + (["none"] if not g["labels"] else []))
        reasons = "".join(f'<li><b>{k} · {g["labels"][k]}</b> — {e(v)}</li>' for k, v in g["reasons"].items())
        note = f'<p class="note">{e(g["note"])}</p>' if g["note"] else ""
        cards.append(f'''
<article class="card" data-tags="{tags}">
  <header>
    <span class="pid">{p["paper_id"]}</span>{chips(g)}<span class="diff {g["difficulty"]}">{g["difficulty"]}</span>
  </header>
  <h3><a href="{e(p["url"])}" target="_blank" rel="noopener">{e(p["title"])}</a></h3>
  <p class="meta">{e(p["authors"])} · {e(p["source"])} · {e(str(p["posted"]))} · {e(str(p["license"]))}</p>
  {f'<ul class="reasons">{reasons}</ul>' if reasons else ''}{note}
  <details><summary>Abstract</summary><p>{e(p["abstract"])}</p></details>
</article>''')
    cards.append('</section>')

legend = "".join(f'<li><span class="chip {k}">{k}</span> {e(v)}</li>' for k, v in PROJ.items())
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gold Label Review</title>
<style>
:root{{--bg:#fff;--fg:#1d1d1f;--mut:#5f6368;--card:#f7f7f8;--line:#e3e3e6;--p1:#1f6feb;--p2:#0f8a6a;--p3:#b5470b;--none:#6b7280;--hard:#b42318}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141416;--fg:#ececf0;--mut:#a0a0a8;--card:#1d1d21;--line:#2c2c33;--p1:#5b9bff;--p2:#3cc39a;--p3:#f08a4b;--none:#9aa0aa;--hard:#ff7b72}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:900px;margin:0 auto;padding:24px 16px 64px}}h1{{font-size:24px;margin:0 0 4px}}
.lead{{color:var(--mut);margin:0 0 16px}}ul.legend{{list-style:none;padding:0;margin:0 0 12px}}ul.legend li{{margin:4px 0}}
.bar{{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px;z-index:1}}
.bar button{{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit;font-size:13px}}
.bar button.on{{border-color:var(--fg)}}
h2{{font-size:18px;margin:28px 0 8px}}h2 small{{color:var(--mut);font-weight:400;font-size:13px;margin-left:6px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}}
.card header{{display:flex;flex-wrap:wrap;gap:6px;align-items:center}}.pid{{font-family:ui-monospace,monospace;font-weight:600;margin-right:4px}}
.chip{{display:inline-block;border-radius:6px;padding:0 8px;font-size:12px;font-weight:600;color:#fff}}
.chip.P1{{background:var(--p1)}}.chip.P2{{background:var(--p2)}}.chip.P3{{background:var(--p3)}}.chip.none{{background:var(--none)}}
.chip.rel{{background:transparent;border:1.5px solid currentColor}}.chip.rel.P1{{color:var(--p1)}}.chip.rel.P2{{color:var(--p2)}}.chip.rel.P3{{color:var(--p3)}}.chip.ok{{background:transparent;border:1.5px dashed currentColor}}.chip.ok.P1{{color:var(--p1)}}.chip.ok.P2{{color:var(--p2)}}.chip.ok.P3{{color:var(--p3)}}
.diff{{font-size:12px;color:var(--mut);margin-left:auto}}.diff.hard{{color:var(--hard);font-weight:600}}
h3{{font-size:15px;margin:8px 0 2px}}h3 a{{color:inherit}}.meta{{color:var(--mut);font-size:12px;margin:0 0 6px;overflow-wrap:anywhere}}
.reasons{{margin:6px 0;padding-left:18px}}.note{{margin:6px 0;color:var(--mut);font-style:italic}}
details summary{{cursor:pointer;color:var(--mut);font-size:13px}}details p{{margin:6px 0 0}}
</style></head><body><main>
<h1>Example 1 — gold labels to review</h1>
<p class="lead">{len(P)} real paper abstracts (preprints + open-access journal articles) in 8 weekly feeds. Solid chip = core (directly advances an aim). Outlined chip = related (the lead would compare, borrow or cite it). Dashed chip with "?" = defensible extra that a lenient grader won't penalise. Reply with any changes by paper ID (e.g. "MP012 → P3 related").</p>
<ul class="legend">{legend}</ul>
<div class="bar" id="bar">
<button data-f="all" class="on">All {len(P)}</button><button data-f="hard">Hard only</button>
<button data-f="P1">P1</button><button data-f="P2">P2</button><button data-f="P3">P3</button>
<button data-f="core">Core</button><button data-f="related">Related</button><button data-f="none">Not relevant</button></div>
{''.join(cards)}
</main><script>
document.getElementById('bar').addEventListener('click',ev=>{{const b=ev.target.closest('button');if(!b)return;
document.querySelectorAll('#bar button').forEach(x=>x.classList.toggle('on',x===b));const f=b.dataset.f;
document.querySelectorAll('.card').forEach(c=>{{const t=c.dataset.tags.split(' ');c.style.display=(f==='all'||t.includes(f))?'':'none';}});
document.querySelectorAll('section.wk').forEach(s=>{{s.style.display=[...s.querySelectorAll('.card')].some(c=>c.style.display!=='none')?'':'none';}});}});
</script></body></html>'''
OUT.write_text(page)
print("wrote", OUT)
