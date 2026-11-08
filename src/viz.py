"""Shared chart styling + dashboard HTML builder (matplotlib for README PNGs, Plotly for the web dashboard)."""
from __future__ import annotations
import html
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Validated categorical order (light mode) + one-hue sequential ramp
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e7e6e2", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "font.family": "DejaVu Sans", "font.size": 10.5, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left",
    "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
})


def save(fig, path):
    fig.savefig(path)
    plt.close(fig)


def style_fig(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK2),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRID, font=dict(color=INK, size=12)),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11)),
        colorway=C, bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, ticks="", zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def dashboard(title: str, subtitle: str, kpis: list[tuple[str, str, str]],
              sections: list[tuple[str, str, go.Figure | str, str]], out_path, repo_url: str,
              insights: list[str]) -> None:
    """kpis: (label, value, note). sections: (title, caption, figure-or-html, width 'full'|'half')."""
    first = True
    cards = []
    for t, cap, body, width in sections:
        if isinstance(body, go.Figure):
            body = body.to_html(full_html=False, include_plotlyjs=False,
                                config={"displayModeBar": False, "responsive": True})
        cards.append(f'<section class="card {width}"><h2>{html.escape(t)}</h2>'
                     f'<p class="cap">{html.escape(cap)}</p>{body}</section>')
    kpi_html = "".join(f'<div class="kpi"><div class="kl">{html.escape(l)}</div>'
                       f'<div class="kv">{html.escape(v)}</div><div class="kn">{html.escape(n)}</div></div>'
                       for l, v, n in kpis)
    ins_html = "".join(f"<li>{i}</li>" for i in insights)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"></script>
<style>
:root{{color-scheme:light;--bg:#f4f3f0;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e7e6e2;--accent:#2a78d6}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif}}
header{{padding:28px 24px 8px;max-width:1240px;margin:0 auto}}
h1{{margin:0;font-size:26px;letter-spacing:-.01em}} .sub{{color:var(--ink2);margin:6px 0 0;font-size:14px}}
.sub a{{color:var(--accent)}}
main{{max-width:1240px;margin:0 auto;padding:16px 24px 40px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.kpis{{grid-column:1/-1;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
.kpi{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.kl{{font-size:12px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}}
.kv{{font-size:26px;font-weight:700;margin-top:4px;font-variant-numeric:tabular-nums}}
.kn{{font-size:12px;color:var(--ink2);margin-top:2px}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 16px 8px;min-width:0}}
.card.full{{grid-column:1/-1}} .card h2{{margin:0;font-size:15px}} .cap{{margin:4px 0 8px;color:var(--ink2);font-size:13px}}
.insights{{grid-column:1/-1;background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;padding:14px 20px}}
.insights h2{{font-size:15px;margin:0 0 6px}} .insights li{{margin:6px 0;font-size:14px;line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}}
th{{color:var(--ink2);font-weight:600}} td.n{{text-align:right;font-variant-numeric:tabular-nums}}
.tw{{overflow-x:auto}}
footer{{text-align:center;color:var(--ink2);font-size:12px;padding:0 16px 28px}}
@media (max-width:820px){{main{{grid-template-columns:1fr;padding:12px 16px 32px}}header{{padding:20px 16px 4px}}}}
</style></head><body>
<header><h1>{html.escape(title)}</h1><p class="sub">{subtitle} · <a href="{repo_url}">Source code on GitHub</a></p></header>
<main><div class="kpis">{kpi_html}</div>
<section class="insights"><h2>Key insights</h2><ul>{ins_html}</ul></section>
{''.join(cards)}</main>
<footer>Built by Pragati Gautam · Python · SQL (DuckDB) · Plotly</footer>
</body></html>"""
    out_path.write_text(page, encoding="utf-8")


def table_html(df, num_cols=()) -> str:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        tds = "".join(f'<td class="n">{html.escape(str(r[c]))}</td>' if c in num_cols
                      else f"<td>{html.escape(str(r[c]))}</td>" for c in df.columns)
        rows.append(f"<tr>{tds}</tr>")
    return f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
