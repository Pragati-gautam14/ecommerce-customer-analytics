"""Builds README charts (outputs/charts/*.png) and the interactive dashboard (docs/index.html)."""
from pathlib import Path
import duckdb
import numpy as np
import plotly.graph_objects as go
from viz import C, SEQ, INK, INK2, plt, save, style_fig, dashboard, table_html

ROOT = Path(__file__).resolve().parents[1]
CH = ROOT / "outputs" / "charts"; CH.mkdir(parents=True, exist_ok=True)
REPO = "https://github.com/Pragati-gautam14/ecommerce-customer-analytics"
con = duckdb.connect(str(ROOT / "data" / "retail.duckdb"), read_only=True)
q = lambda s: con.sql(s).df()

kpi = q("SELECT * FROM headline_kpis").iloc[0]
monthly = q("SELECT * FROM monthly_kpis")
seg = q("SELECT * FROM rfm_segment_summary")
coh = q("SELECT * FROM cohort_retention WHERE cohort_month < DATE '2011-12-01'")
pareto = q("SELECT revenue_rank, cum_revenue_pct, cum_product_pct FROM product_pareto")
dh = q("SELECT * FROM revenue_by_day_hour")
countries = q("SELECT * FROM country_summary WHERE country <> 'United Kingdom' LIMIT 10")
rep = q("SELECT * FROM repeat_rate").iloc[0]
canc = q("SELECT * FROM cancellations_summary").iloc[0]
rules = q("""SELECT product_a, product_b, baskets_together, confidence_pct, lift
             FROM basket_rules WHERE product_a < product_b
             ORDER BY baskets_together DESC LIMIT 10""")
n80 = int(pareto.loc[pareto.cum_revenue_pct >= 80, "revenue_rank"].min())
pct80 = round(100 * n80 / len(pareto), 1)
uk_share = q("SELECT pct_revenue FROM country_summary WHERE country='United Kingdom'").iloc[0, 0]
full = monthly[~monthly.is_partial_month]
q4_share = round(100 * full[full.month.astype(str) >= "2011-09-01"].revenue.sum()
                 / full[full.month.astype(str) >= "2010-12-01"].revenue.sum(), 1)
champ = seg[seg.segment == "Champions"].iloc[0]
risk = seg[seg.segment == "At Risk (High Value)"].iloc[0]
m1 = coh[coh.month_number == 1].retention_pct.mean()
dayrev = dh.groupby("weekday").revenue.sum().sort_values(ascending=False)
hourrev = dh.groupby("hour").revenue.sum()

fmt = lambda v: f"£{v/1e6:.2f}M" if v >= 1e6 else f"£{v/1e3:.0f}K"

# ---------------- README PNGs ----------------
fig, ax = plt.subplots(figsize=(10, 4))
x = monthly.month.dt.strftime("%b-%y")
cols = [C[0] if not p else "#b7d3f6" for p in monthly.is_partial_month]
ax.bar(x, monthly.revenue / 1e3, color=cols, width=0.65)
ax.set_title("Monthly revenue (£K) — Nov-2011 peak; Dec-2011 is a partial month (9 days)")
ax.set_ylabel("£K"); ax.grid(axis="x", visible=False)
save(fig, CH / "01_monthly_revenue.png")

fig, ax = plt.subplots(figsize=(10, 4.2))
s = seg.sort_values("pct_revenue")
y = np.arange(len(s))
ax.barh(y + 0.2, s.pct_customers, height=0.38, color=C[0], label="% of customers")
ax.barh(y - 0.2, s.pct_revenue, height=0.38, color=C[1], label="% of revenue")
ax.set_yticks(y, s.segment); ax.legend(frameon=False, loc="lower right")
ax.set_title("RFM segments — Champions are 22% of customers but 67% of revenue")
ax.grid(axis="y", visible=False)
save(fig, CH / "02_rfm_segments.png")

pv = coh.pivot(index="cohort_month", columns="month_number", values="retention_pct")
fig, ax = plt.subplots(figsize=(10, 5))
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("b", SEQ)
data = pv.drop(columns=0).values
im = ax.imshow(data, cmap=cmap, aspect="auto", vmin=0, vmax=50)
ax.set_xticks(range(data.shape[1]), [str(c) for c in pv.columns[1:]])
ax.set_yticks(range(len(pv)), [d.strftime("%b-%y") for d in pv.index])
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        if not np.isnan(data[i, j]):
            ax.text(j, i, f"{data[i, j]:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if data[i, j] > 30 else INK)
ax.set_xlabel("Months since first purchase"); ax.grid(False)
ax.set_title("Cohort retention (%) — Dec-2010 cohort retains far better than later cohorts")
save(fig, CH / "03_cohort_retention.png")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(pareto.cum_product_pct, pareto.cum_revenue_pct, color=C[0], lw=2)
ax.axhline(80, color=INK2, lw=0.8, ls="--"); ax.axvline(pct80, color=INK2, lw=0.8, ls="--")
ax.annotate(f"{pct80}% of products → 80% of revenue", (pct80, 80), (pct80 + 8, 60),
            arrowprops=dict(arrowstyle="->", color=INK2), color=INK)
ax.set_xlabel("% of products (ranked by revenue)"); ax.set_ylabel("Cumulative % of revenue")
ax.set_title("Product Pareto curve")
save(fig, CH / "04_product_pareto.png")

order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
hm = dh.pivot_table(index="weekday", columns="hour", values="revenue", aggfunc="sum").reindex(order).fillna(0)
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.imshow(hm.values / 1e3, cmap=cmap, aspect="auto")
ax.set_xticks(range(hm.shape[1]), hm.columns); ax.set_yticks(range(len(order)), order); ax.grid(False)
ax.set_xlabel("Hour of day")
ax.set_title("Revenue by weekday × hour — peak Thursday, 10:00–13:00; no Saturday trading")
save(fig, CH / "05_weekday_hour_heatmap.png")

# ---------------- Interactive dashboard ----------------
f1 = go.Figure(go.Bar(x=monthly.month.dt.strftime("%b %Y"), y=monthly.revenue,
                      marker_color=cols, customdata=np.c_[monthly.orders, monthly.avg_order_value, monthly.mom_growth_pct.fillna(0)],
                      hovertemplate="<b>%{x}</b><br>Revenue £%{y:,.0f}<br>Orders %{customdata[0]:,}<br>AOV £%{customdata[1]:,.0f}<br>MoM %{customdata[2]:+.1f}%<extra></extra>"))
f1.update_yaxes(tickprefix="£", tickformat="~s")

s2 = seg.sort_values("pct_revenue")
f2 = go.Figure([
    go.Bar(y=s2.segment, x=s2.pct_customers, orientation="h", name="% of customers", marker_color=C[0],
           hovertemplate="%{y}<br>%{x}% of customers<extra></extra>"),
    go.Bar(y=s2.segment, x=s2.pct_revenue, orientation="h", name="% of revenue", marker_color=C[1],
           hovertemplate="%{y}<br>%{x}% of revenue<extra></extra>")])
f2.update_layout(barmode="group"); f2.update_xaxes(ticksuffix="%")

f3 = go.Figure(go.Heatmap(z=data, x=[str(c) for c in pv.columns[1:]], y=[d.strftime("%b %Y") for d in pv.index],
                          colorscale=[[i / 6, c] for i, c in enumerate(SEQ)], zmin=0, zmax=50,
                          text=[["" if np.isnan(v) else f"{v:.0f}" for v in row] for row in data],
                          texttemplate="%{text}", textfont=dict(size=10), xgap=2, ygap=2,
                          hovertemplate="Cohort %{y}<br>Month +%{x}: %{z:.1f}% retained<extra></extra>",
                          colorbar=dict(ticksuffix="%", thickness=10)))
f3.update_yaxes(autorange="reversed", showgrid=False); f3.update_xaxes(title="Months since first purchase")

f4 = go.Figure(go.Scatter(x=pareto.cum_product_pct, y=pareto.cum_revenue_pct, mode="lines",
                          line=dict(color=C[0], width=2),
                          hovertemplate="Top %{x:.1f}% of products<br>%{y:.1f}% of revenue<extra></extra>"))
f4.add_hline(y=80, line_dash="dash", line_color=INK2, line_width=1)
f4.add_vline(x=pct80, line_dash="dash", line_color=INK2, line_width=1)
f4.update_xaxes(ticksuffix="%", title="% of products"); f4.update_yaxes(ticksuffix="%")

f5 = go.Figure(go.Heatmap(z=hm.values, x=[f"{h}:00" for h in hm.columns], y=order,
                          colorscale=[[i / 6, c] for i, c in enumerate(SEQ)], xgap=2, ygap=2,
                          hovertemplate="%{y} %{x}<br>£%{z:,.0f}<extra></extra>", colorbar=dict(thickness=10)))
f5.update_yaxes(autorange="reversed", showgrid=False)

cs = countries.sort_values("revenue")
f6 = go.Figure(go.Bar(y=cs.country, x=cs.revenue, orientation="h", marker_color=C[0],
                      customdata=np.c_[cs.customers, cs.revenue_per_customer],
                      hovertemplate="<b>%{y}</b><br>Revenue £%{x:,.0f}<br>Customers %{customdata[0]}<br>£%{customdata[1]:,.0f} per customer<extra></extra>"))
f6.update_xaxes(tickprefix="£", tickformat="~s")

for f, h in [(f1, 340), (f2, 340), (f3, 420), (f4, 300), (f5, 300), (f6, 340)]:
    style_fig(f, h)
f3.update_layout(margin=dict(l=10, r=10, t=10, b=40))

rules_t = rules.rename(columns={"product_a": "Product A", "product_b": "Product B", "baskets_together": "Baskets",
                                "confidence_pct": "Confidence %", "lift": "Lift"})
insights = [
    f"<b>Customer concentration:</b> Champions are {champ.pct_customers}% of customers but drive <b>{champ.pct_revenue}% of revenue</b> (avg spend £{champ.avg_spend:,.0f}) → protect with a loyalty / early-access programme.",
    f"<b>Win-back opportunity:</b> {int(risk.customers)} high-value customers are 'At Risk' (avg {risk.avg_recency_days:.0f} days since last order) holding £{risk.revenue/1e3:,.0f}K of historic revenue → priority list for a reactivation campaign.",
    f"<b>Retention is the main lever:</b> only {m1:.0f}% of new customers buy again in month 1, yet repeat buyers ({rep.repeat_customer_pct}% of customers) generate {rep.repeat_revenue_pct}% of revenue.",
    f"<b>Seasonality:</b> Sep–Nov 2011 delivered {q4_share}% of the year's revenue → stock and staff up for Q4 from August.",
    f"<b>Long tail:</b> {pct80}% of products ({n80} SKUs) generate 80% of revenue; cancellations cost {canc.cancel_rate_pct}% of gross sales (£{canc.cancelled_value/1e3:,.0f}K).",
    f"<b>Cross-sell:</b> product pairs like teacup sets and lunch bags are bought together 7–18× more than chance (lift) → bundle and 'frequently bought together' recommendations.",
]
dashboard(
    "E-commerce Customer Analytics",
    "UK online gift retailer · 541,909 transactions · Dec 2010 – Dec 2011",
    [("Revenue", fmt(kpi.total_revenue), "after cleaning"), ("Orders", f"{int(kpi.total_orders):,}", ""),
     ("Customers", f"{int(kpi.total_customers):,}", f"{int(kpi.countries)} countries"),
     ("Avg order value", f"£{kpi.avg_order_value:,.0f}", ""), ("Repeat customers", f"{rep.repeat_customer_pct}%", f"{rep.repeat_revenue_pct}% of revenue"),
     ("UK share", f"{uk_share:.0f}%", "of revenue")],
    [("Monthly revenue", "Hover for orders, AOV and month-over-month growth. Dec 2011 is a partial month.", f1, "full"),
     ("RFM segments: customers vs revenue", "Share of the customer base compared with share of revenue", f2, "half"),
     ("Top international markets", "Excluding the UK. Hover for revenue per customer.", f6, "half"),
     ("Cohort retention", "% of each monthly acquisition cohort that purchased again N months later (the last diagonal is the partial Dec 2011 month)", f3, "full"),
     ("Product Pareto", f"{pct80}% of products generate 80% of revenue", f4, "half"),
     ("Revenue by weekday and hour", "When customers buy (no Saturday trading)", f5, "half"),
     ("Frequently bought together", "Top product pairs by co-occurrence; lift > 1 means bought together more than chance", table_html(rules_t, ["Baskets", "Confidence %", "Lift"]), "full")],
    ROOT / "docs" / "index.html", REPO, insights)

# key numbers for README
print(dict(revenue=kpi.total_revenue, orders=kpi.total_orders, customers=kpi.total_customers, aov=kpi.avg_order_value,
           champ=(champ.pct_customers, champ.pct_revenue), risk=(int(risk.customers), risk.revenue, risk.avg_recency_days),
           m1=round(m1, 1), repeat=(rep.repeat_customer_pct, rep.repeat_revenue_pct), q4=q4_share, pareto=(pct80, n80),
           cancel=(canc.cancel_rate_pct, canc.cancelled_value), uk=uk_share, day=dayrev.index[0], hour=int(hourrev.idxmax())))
