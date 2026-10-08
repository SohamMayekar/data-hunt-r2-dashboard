from pathlib import Path
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from clean import clean_orders
from theme import COLORS

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "R_Questions.csv"
OUT = ROOT / "data" / "cleaned_orders.csv"
st.set_page_config(page_title="What the revenue number leaves out", layout="wide", initial_sidebar_state="collapsed")


def money(v, decimals=0):
    return "₹" + f"{v:,.{decimals}f}"


def money_m(v):
    return f"₹{v / 1_000_000:.2f}M"


def validation_report(d, audit):
    orders = d.groupby("order_id").agg(status=("order_status", "first"), date=("order_date", "first"), customer=("customer_id", "first"))
    cats = d.groupby("category").agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
    monthly = d.groupby(d.order_date.dt.month).revenue.sum()
    products = d.groupby("product_id").agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
    products["margin"] = products.profit / products.revenue
    low = products[products.margin < .26]
    pending = d[d.order_status.eq("Pending")].groupby("order_id").agg(date=("order_date", "first"), revenue=("revenue", "sum"))
    old = pending[(pd.Timestamp("2025-12-31") - pending.date).dt.days > 90]
    cust_profit = d.groupby("customer_id").profit.sum().sort_values(ascending=False)
    status_counts = orders.status.value_counts()
    checks = [
        ("Lines", len(d), 11647, lambda a, e: a == e),
        ("Orders", len(orders), 7995, lambda a, e: a == e),
        ("Customers", d.customer_id.nunique(), 1492, lambda a, e: a == e),
        ("Booked revenue", d.revenue.sum(), 47291531.56, lambda a, e: abs(a-e)<.01),
        ("Booked profit", d.profit.sum(), 15240690.01, lambda a, e: abs(a-e)<.01),
        ("Booked margin %", d.profit.sum()/d.revenue.sum()*100, 32.23, lambda a, e: round(a,2)==e),
        ("Delivered orders", int(status_counts.get("Delivered", 0)), 6309, lambda a, e: a == e),
        ("Delivered rate %", status_counts.get("Delivered",0)/len(orders)*100, 78.91, lambda a, e: round(a,2)==e),
        ("Cancelled orders", int(status_counts.get("Cancelled",0)), 658, lambda a,e: a==e),
        ("Cancelled rate %", status_counts.get("Cancelled",0)/len(orders)*100, 8.23, lambda a,e: round(a,2)==e),
        ("Returned orders", int(status_counts.get("Returned",0)), 622, lambda a,e: a==e),
        ("Return rate %", status_counts.get("Returned",0)/len(orders)*100, 7.78, lambda a,e: round(a,2)==e),
        ("Pending orders", int(status_counts.get("Pending",0)), 406, lambda a,e: a==e),
        ("Pending rate %", status_counts.get("Pending",0)/len(orders)*100, 5.08, lambda a,e: round(a,2)==e),
        ("AOV", d.revenue.sum()/len(orders), 5915, lambda a,e: round(a)==e),
        ("Profit per order", d.profit.sum()/len(orders), 1906, lambda a,e: round(a)==e),
        ("Delivered revenue", d.loc[d.order_status.eq("Delivered"),"revenue"].sum(), 37380000, lambda a,e: round(a/10000)*10000==e),
        ("Delivered share %", d.loc[d.order_status.eq("Delivered"),"revenue"].sum()/d.revenue.sum()*100, 79.04, lambda a,e: round(a,2)==e),
        ("Delivered profit", d.loc[d.order_status.eq("Delivered"),"profit"].sum(), 12072930.08, lambda a,e: abs(a-e)<.01),
        ("Low-margin products", len(low), 28, lambda a,e: a==e),
        ("Low-margin revenue", low.revenue.sum(), 13810000, lambda a,e: round(a/10000)*10000==e),
        ("Low-margin profit", low.profit.sum(), 3020000, lambda a,e: round(a/10000)*10000==e),
        ("Low-margin revenue share %", low.revenue.sum()/d.revenue.sum()*100, 29.2, lambda a,e: round(a,1)==e),
        ("Low-margin profit share %", low.profit.sum()/d.profit.sum()*100, 19.8, lambda a,e: round(a,1)==e),
        ("Pending older than 90 days", len(old), 291, lambda a,e: a==e),
        ("Stale pending revenue", old.revenue.sum(), 1670000, lambda a,e: round(a/10000)*10000==e),
        ("Pending older than 180 days", int(((pd.Timestamp("2025-12-31")-pending.date).dt.days>180).sum()), 200, lambda a,e:a==e),
        ("Pending older than 180 revenue", pending.loc[(pd.Timestamp("2025-12-31")-pending.date).dt.days>180,"revenue"].sum(), 1150000, lambda a,e:round(a/10000)*10000==e),
        ("Customer top 10% profit share %", cust_profit.iloc[:149].sum()/cust_profit.sum()*100, 21.4, lambda a,e: round(a,1)==e),
        ("Customer top 20% profit share %", cust_profit.iloc[:298].sum()/cust_profit.sum()*100, 37.4, lambda a,e: round(a,1)==e),
        ("Raw lines", audit["raw_rows"], 11679, lambda a,e: a==e),
        ("Raw revenue", audit["raw_revenue"], 47359158, lambda a,e: round(a)==e),
        ("Raw profit", audit["raw_profit"], 15263479, lambda a,e: round(a)==e),
    ]
    for cat, expected in {"Electronics":14080094,"Sports":9406076,"Books":8459553,"Home":8067335,"Fashion":7278475}.items():
        checks.append((f"{cat} revenue", cats.loc[cat,"revenue"], expected, lambda a,e: round(a)==e))
    for cat, expected in {"Electronics":33.6,"Sports":28.3,"Books":32.7,"Home":30.9,"Fashion":35.6}.items():
        checks.append((f"{cat} margin %", cats.loc[cat,"profit"]/cats.loc[cat,"revenue"]*100, expected, lambda a,e: round(a,1)==e))
    for month, expected in {3:4126810,7:4130653,2:3748717,9:3765703}.items():
        checks.append((f"Month {month} revenue", monthly.loc[month], expected, lambda a,e: round(a)==e))
    checks += [
        ("Discount total", d.discount_amount.sum(),3720000,lambda a,e: round(a/10000)*10000==e),
        ("15% and 20% discount lines", int(d.discount_pct.isin([.15,.20]).sum()),2334,lambda a,e:a==e),
        ("15% and 20% discount amount", d.loc[d.discount_pct.isin([.15,.20]),"discount_amount"].sum(),1690000,lambda a,e:round(a/10000)*10000==e),
    ]
    print("SECTION O VALIDATION (actual | expected | result)")
    results=[]
    for label, actual, expected, compare in checks:
        ok=compare(actual,expected); results.append(ok)
        print(f"{label}: {actual} | {expected} | {'PASS' if ok else 'MISMATCH'}")
    return all(results), checks


df, audit = clean_orders(RAW)
df.to_csv(OUT, index=False)
valid, validation_checks = validation_report(df, audit)
if not valid:
    raise RuntimeError("Section O validation mismatch. Dashboard stopped. See printed actual and expected values above.")
d = df

def show_chart(fig, container=st):
    fig.update_layout(template="editorial",paper_bgcolor=COLORS["paper"],plot_bgcolor=COLORS["paper"],font={"family":"Arial, sans-serif","size":12,"color":COLORS["ink"]},title_font={"family":"Georgia, serif","size":19,"color":COLORS["ink"]})
    container.plotly_chart(fig,use_container_width=True,theme=None)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:wght@400;500;600&display=swap');
html, body, [class*="css"] {font-family:'IBM Plex Sans',Arial,sans-serif;color:#1B1B1B;}
.stApp {background:#F6F3EC;} .block-container {max-width:1280px;padding-top:2rem;padding-bottom:4rem;}
header[data-testid="stHeader"] {display:none;} div[data-testid="stToolbar"] {display:none;}
h1,h2,h3 {font-family:'Source Serif 4',Georgia,serif!important;font-weight:500!important;color:#1B1B1B;}
.st-key-sticky {position:fixed!important;top:0;left:max(16px,calc((100vw - 1280px)/2));z-index:999;background:#F6F3EC;padding:8px 0 4px;width:min(1280px,calc(100vw - 32px));box-sizing:border-box;}
.filter-spacer {height:140px;}
.kpirow {display:grid;grid-template-columns:repeat(4,1fr);gap:24px;border-top:1px solid #1B1B1B;border-bottom:1px solid #D9D3C7;padding:18px 0;margin:20px 0 10px;}
.kpi {min-width:0}.klabel {font-size:12px;color:#6B6B6B!important}.kvalue {font:36px 'Source Serif 4',Georgia,serif; font-variant-numeric:tabular-nums;color:#1B1B1B!important;}.kdetail {font-size:12px;color:#6B6B6B!important;line-height:1.4}
.section-intro {color:#6B6B6B!important;margin-top:-8px;margin-bottom:22px;font-size:15px}.note {border-top:1px solid #D9D3C7;padding:12px 0;color:#6B6B6B;font-size:13px}
.stApp [data-testid="stCaptionContainer"] p,.stApp [data-testid="stWidgetLabel"],.stApp [data-testid="stWidgetLabel"] *, .stApp [data-testid="stRadio"] label * {color:#6B6B6B!important;}
.customer-table {width:100%;border-collapse:collapse;font-size:13px;background:#F6F3EC;color:#1B1B1B;}
.customer-table th {text-align:left;border-bottom:1px solid #1B1B1B;padding:10px 8px;font-weight:600;color:#6B6B6B;}
.customer-table td {border-bottom:1px solid #D9D3C7;padding:10px 8px;color:#1B1B1B;}
.action {border-top:2px solid #2F5D62;padding:12px 8px 18px 0;min-height:205px}.action h3 {font-size:21px!important;margin-bottom:8px}.anchorlinks a {color:#1B1B1B;text-decoration:none;margin-right:18px;font-size:13px}
div[data-testid="stVerticalBlock"] div:has(> div[data-testid="stPlotlyChart"]) {border:0}
</style>""", unsafe_allow_html=True)

# Persistent global controls. Controls are rendered before page content.
with st.container(key="sticky-filters"):
    fc = st.columns([1.5,1,1,1,1.25,1.1])
    months = pd.date_range(df.order_date.min().replace(day=1), df.order_date.max().replace(day=1), freq="MS")
    with fc[0]:
        start_month, end_month = st.select_slider("Date range", options=list(months), value=(months[0], months[-1]), format_func=lambda x:x.strftime("%b %Y"))
    with fc[1]: region = st.selectbox("Region", ["All"]+sorted(df.region.unique()), index=0)
    with fc[2]: category = st.selectbox("Category", ["All"]+sorted(df.category.unique()), index=0)
    with fc[3]: segment = st.selectbox("Segment", ["All"]+sorted(df.segment.unique()), index=0)
    with fc[4]: basis = st.radio("Revenue basis", ["Booked","Delivered only"], horizontal=True, index=0)
    view0=df[(df.order_date>=start_month)&(df.order_date<end_month+pd.offsets.MonthBegin(1))].copy()
    for col,val in [("region",region),("category",category),("segment",segment)]:
        if val!="All": view0=view0[view0[col].eq(val)]
    order_n=view0.order_id.nunique()
    with fc[5]: st.markdown(f"<div style='padding-top:26px;font-size:13px;color:#6B6B6B'><b>{order_n:,}</b> orders in view</div>",unsafe_allow_html=True)
    st.markdown("<div class='anchorlinks'><a href='#headline'>Headline</a><a href='#money'>Money</a><a href='#problems'>Problems</a><a href='#customers'>Customers</a><a href='#actions'>Actions</a></div>",unsafe_allow_html=True)
st.markdown("<div class='filter-spacer'></div>",unsafe_allow_html=True)

if view0.empty:
    st.info("No orders match these filters. Widen the date range or clear a filter.")
    st.stop()
view=view0[view0.order_status.eq("Delivered")].copy() if basis=="Delivered only" else view0.copy()
orders=view.groupby("order_id").agg(status=("order_status","first"),revenue=("revenue","sum"),profit=("profit","sum"),customer=("customer_id","first"),date=("order_date","first"))
rev, profit, n=orders.revenue.sum(),orders.profit.sum(),len(orders)
margin=profit/rev if rev else 0
status_orders=view0.groupby("order_id").order_status.first()
n_total=len(status_orders)
returned=int((status_orders=="Returned").sum()); cancelled=int((status_orders=="Cancelled").sum())
rate=returned/n_total if n_total else 0

st.markdown("<div id='headline'></div>",unsafe_allow_html=True)
st.title("What the revenue number leaves out")
st.markdown("<p class='section-intro'>Use the filters above to explore sales, profit, orders and customers.</p>",unsafe_allow_html=True)
st.markdown(f"""<div class="kpirow">
<div class="kpi"><div class="klabel">Revenue · {basis}</div><div class="kvalue">{money_m(rev)}</div><div class="kdetail">Basis: {n_total:,} orders in view</div></div>
<div class="kpi"><div class="klabel">Profit</div><div class="kvalue">{money_m(profit)}</div><div class="kdetail">{margin:.1%} of revenue</div></div>
<div class="kpi"><div class="klabel">Orders</div><div class="kvalue">{n_total:,}</div><div class="kdetail">Unique orders in this view</div></div>
<div class="kpi"><div class="klabel">Return rate</div><div class="kvalue">{rate:.1%}</div><div class="kdetail">{returned:,} returned orders</div></div></div>""",unsafe_allow_html=True)
if basis=="Booked":
    st.caption(f"Also in this view: cancellation rate {cancelled/n_total:.1%}. Delivered sales are {view0.loc[view0.order_status.eq('Delivered'),'revenue'].sum()/view0.revenue.sum():.1%} of booked sales.")
wf=view0.groupby("order_status").revenue.sum()
booked=float(wf.sum()); delivered=float(wf.get("Delivered",0))
st.subheader(f"Of every ₹100 booked, only {delivered/booked:.0%} was delivered" if booked else "Booked revenue to delivered revenue")
st.caption("This chart shows how booked sales split across order statuses.")
steps=[("Booked",booked),("Cancelled",-float(wf.get("Cancelled",0))),("Returned",-float(wf.get("Returned",0))),("Pending",-float(wf.get("Pending",0))),("Delivered",delivered)]
fig=go.Figure(go.Waterfall(x=[x for x,y in steps],y=[y/1e6 for x,y in steps],measure=["absolute","relative","relative","relative","total"],text=[f"₹{abs(y)/1e6:.2f}M" if x in ("Booked","Delivered") else f"−{abs(y)/booked:.1%}" for x,y in steps],textposition="outside",connector={"line":{"color":COLORS['hairline']}},increasing={"marker":{"color":COLORS['teal']}},decreasing={"marker":{"color":COLORS['accent']}},totals={"marker":{"color":COLORS['ink']}},hovertemplate="%{x}<br>₹%{y:.2f}M<extra></extra>"))
fig.update_layout(title="Booked revenue to delivered revenue",yaxis_title="Revenue (₹ million)",showlegend=False,height=370)
show_chart(fig)

def heading(id_,title,lead):
    st.markdown(f"<div id='{id_}'></div>",unsafe_allow_html=True); st.header(title); st.markdown(f"<p class='section-intro'>{lead}</p>",unsafe_allow_html=True)


heading("money","2  Sales and profit","Compare each category's share of sales with its share of profit.")
cat_view=view.groupby("category").agg(revenue=("revenue","sum"),profit=("profit","sum"))
cat_view["rev_share"]=cat_view.revenue/cat_view.revenue.sum()*100; cat_view["profit_share"]=cat_view.profit/cat_view.profit.sum()*100; cat_view["gap"]=cat_view.profit_share-cat_view.rev_share; cat_view["margin"]=cat_view.profit/cat_view.revenue
topgap=cat_view.gap.idxmin() if len(cat_view) else ""
title=(f"{topgap} earns {cat_view.loc[topgap,'rev_share']:.1f}% of revenue but {cat_view.loc[topgap,'profit_share']:.1f}% of profit" if topgap and cat_view.loc[topgap,"gap"]<0 else "Revenue share vs profit share by category")
fig=go.Figure()
for name,row in cat_view.sort_values("gap").iterrows():
    fig.add_trace(go.Scatter(x=[row.rev_share,row.profit_share],y=[name,name],mode="lines",line={"color":COLORS["accent"] if row.gap<0 else COLORS["context"],"width":2},showlegend=False,hoverinfo="skip"))
fig.add_trace(go.Scatter(x=cat_view.rev_share,y=cat_view.index,mode="markers",name="Revenue share",marker={"color":COLORS["ink"],"size":10},customdata=np.c_[cat_view.revenue,cat_view.margin],hovertemplate="Revenue share %{x:.1f}%<br>Revenue ₹%{customdata[0]:,.0f}<br>Margin %{customdata[1]:.1%}<extra></extra>"))
fig.add_trace(go.Scatter(x=cat_view.profit_share,y=cat_view.index,mode="markers",name="Profit share",marker={"color":COLORS["teal"],"size":10},customdata=np.c_[cat_view.profit,cat_view.margin],hovertemplate="Profit share %{x:.1f}%<br>Profit ₹%{customdata[0]:,.0f}<br>Margin %{customdata[1]:.1%}<extra></extra>"))
fig.update_layout(title=title,xaxis_title="Share of total (%)",height=350,legend={"orientation":"h","y":1.08}); show_chart(fig)

byprod=view.groupby(["product_id","product_name","category"]).agg(revenue=("revenue","sum"),profit=("profit","sum")); byprod["margin"]=byprod.profit/byprod.revenue; byprod["low"]=byprod.margin<.26
low=byprod[byprod.low]; low_rev=low.revenue.sum(); low_share=low_rev/byprod.revenue.sum()*100 if len(byprod) else 0
st.subheader(f"{len(low)} products earn under 26% margin and carry {low_share:.0f}% of revenue")
fig=go.Figure(); fig.add_trace(go.Scatter(x=byprod.revenue/1e6,y=byprod.margin*100,mode="markers",marker={"color":np.where(byprod.low,COLORS['accent'],COLORS['context']),"size":9,"opacity":.8},customdata=np.c_[byprod.index.get_level_values(1),byprod.index.get_level_values(2),byprod.profit],hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>Revenue ₹%{x:.2f}M<br>Margin %{y:.1f}%<extra></extra>"))
overall=byprod.profit.sum()/byprod.revenue.sum()*100 if len(byprod) else 0
fig.add_hline(y=overall,line_dash="dash",line_color=COLORS['muted'],annotation_text=f"Overall {overall:.1f}%")
for ix,row in low.sort_values("revenue",ascending=False).head(5).iterrows(): fig.add_annotation(x=row.revenue/1e6,y=row.margin*100,text=ix[1],showarrow=True,arrowhead=0,ax=20,ay=-24,font={"size":10})
fig.update_layout(title=f"{len(byprod)} products, separated by product ID",xaxis_title="Product revenue (₹ million)",yaxis_title="Profit margin (%)",height=440); show_chart(fig)

st.subheader("Profit margin by region and customer group")
dimcols=st.columns(2)
for col,dim in zip(dimcols,["region","segment"]):
    q=view.groupby(dim).agg(revenue=("revenue","sum"),profit=("profit","sum")); q["margin"]=q.profit/q.revenue*100; q["gap"]=(q.profit/q.profit.sum()-q.revenue/q.revenue.sum())*100
    f=go.Figure(go.Bar(x=q.margin,y=q.index,orientation="h",marker_color=COLORS['teal'],text=[f"{x:.1f}%  ·  {g:+.1f} pp" for x,g in zip(q.margin,q.gap)],textposition="outside",hovertemplate="%{y}<br>Margin %{x:.1f}%<extra></extra>")); f.add_vline(x=profit/rev*100,line_dash="dash",line_color=COLORS['muted']); f.update_layout(title=dim.title(),xaxis_title="Profit margin (%)",height=280); show_chart(f,col)

st.subheader("Revenue and margin, " + (f"{start_month:%b}–{end_month:%b %Y}"))
mon=view.assign(month=view.order_date.dt.to_period("M").dt.to_timestamp()).groupby("month").agg(revenue=("revenue","sum"),profit=("profit","sum")); mon["margin"]=mon.profit/mon.revenue*100
fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.12,row_heights=[.63,.37])
fig.add_trace(go.Scatter(x=mon.index,y=mon.revenue/1e6,name="Revenue",mode="lines+markers",line={"color":COLORS['ink'],"width":2}),row=1,col=1)
fig.add_trace(go.Scatter(x=mon.index,y=mon.profit/1e6,name="Profit",mode="lines+markers",line={"color":COLORS['teal'],"width":2}),row=1,col=1)
fig.add_trace(go.Scatter(x=mon.index,y=mon.margin,name="Margin",mode="lines+markers",line={"color":COLORS['accent'],"width":2}),row=2,col=1)
if len(mon):
    q1=mon[mon.index.quarter==1].margin.mean(); q4=mon[mon.index.quarter==4].margin.mean()
    fig.add_hline(y=q1,line_dash="dash",line_color=COLORS['context'],row=2,col=1,annotation_text=f"Q1 {q1:.1f}%")
    fig.add_hline(y=q4,line_dash="dot",line_color=COLORS['muted'],row=2,col=1,annotation_text=f"Q4 {q4:.1f}%")
    mom=mon.revenue.pct_change()*100
    for month_no,label in [(3,"Mar"),(9,"Sep")]:
        match=mon.index[mon.index.month==month_no]
        if len(match) and pd.notna(mom.loc[match[0]]):
            fig.add_annotation(x=match[0],y=mon.loc[match[0],"revenue"]/1e6,text=f"{label} {mom.loc[match[0]]:+.1f}%",showarrow=True,arrowhead=0,ax=0,ay=-28,font={"size":10,"color":COLORS['muted']},row=1,col=1)
    if len(mon):
        peak=mon.revenue.idxmax()
        fig.add_annotation(x=peak,y=mon.loc[peak,"revenue"]/1e6,text=f"{peak:%b} peak",showarrow=True,arrowhead=0,ax=0,ay=-28,font={"size":10,"color":COLORS['muted']},row=1,col=1)
fig.update_layout(height=470,title="Monthly revenue, profit and margin",legend={"orientation":"h","y":1.08}); fig.update_yaxes(title_text="Revenue and profit (₹ M)",row=1,col=1); fig.update_yaxes(title_text="Margin (%)",row=2,col=1); show_chart(fig)
heading("problems","3  Where it goes wrong","Review order returns, cancellations, shipping times and discount levels.")

def wilson(k,n,z=1.96):
    if n==0: return 0,0
    p=k/n; den=1+z*z/n; mid=(p+z*z/(2*n))/den; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half,mid+half

groups=[("Category","category"),("Region","region"),("Payment","payment_method"),("Shipping days","shipping_band")]
rate_view=view0
order_meta=rate_view.groupby("order_id").agg(status=("order_status","first"),region=("region","first"),category=("category","first"),payment_method=("payment_method","first"),segment=("segment","first"),customer=("customer_id","first"))
ship_order=rate_view.groupby("order_id").shipping_days.mean()
order_meta["shipping_band"]=pd.cut(ship_order,[0,2,4,6,np.inf],labels=["1–2","3–4","5–6","7+"])
base_return=(order_meta.status=="Returned").mean() if len(order_meta) else 0; base_cancel=(order_meta.status=="Cancelled").mean() if len(order_meta) else 0
too_few=order_meta.order_id.nunique() if "order_id" in order_meta else len(order_meta)
if len(order_meta)<30:
    st.info("Too few orders to read")
else:
    for start in (0, 2):
        ratecols=st.columns(2)
        for col,(label,dim) in zip(ratecols,groups[start:start+2]):
            grp=order_meta.groupby(dim,observed=True).status.agg(
                n="size",returns=lambda s:(s=="Returned").sum(),cancellations=lambda s:(s=="Cancelled").sum()
            ).dropna()
            grp["return_rate"]=grp.returns/grp.n*100
            grp=grp.sort_values("return_rate",ascending=True)
            if grp.empty:
                col.info("No orders in this group.")
                continue
            fig=go.Figure()
            y=np.arange(len(grp),dtype=float)
            bounds=[]
            for status,colname,color,base,offset in [
                ("Returned","returns",COLORS["accent"],base_return,-0.13),
                ("Cancelled","cancellations",COLORS["teal"],base_cancel,0.13),
            ]:
                rates=grp[colname]/grp.n*100
                lohi=[wilson(int(k),int(n)) for k,n in zip(grp[colname],grp.n)]
                bounds.extend([lo*100 for lo,hi in lohi]+[hi*100 for lo,hi in lohi]+[base*100])
                fig.add_trace(go.Scatter(
                    x=rates,y=y+offset,mode="markers",name="Return rate" if status=="Returned" else "Cancellation rate",
                    marker={"color":color,"size":8},
                    error_x={"type":"data","symmetric":False,
                        "array":[hi*100-rate for (lo,hi),rate in zip(lohi,rates)],
                        "arrayminus":[rate-lo*100 for (lo,hi),rate in zip(lohi,rates)],
                        "color":COLORS["muted"],"thickness":1},
                    customdata=np.c_[grp.index.astype(str),grp[colname],grp.n],
                    hovertemplate="%{customdata[0]}<br>Rate %{x:.1f}%<br>%{customdata[1]} of %{customdata[2]} orders<extra></extra>"
                ))
                fig.add_vline(x=base*100,line_dash="dash" if status=="Returned" else "dot",line_color=color,line_width=1)
            fig.update_yaxes(
                tickmode="array",tickvals=y,ticktext=grp.index.astype(str).tolist(),
                range=[len(grp)-0.5,-0.5],automargin=True,showgrid=False,zeroline=False
            )
            fig.update_xaxes(title_text="Order rate (%)",range=[max(0,min(bounds)-0.8),min(100,max(bounds)+0.8)],gridcolor=COLORS["grid"])
            fig.update_layout(
                title=f"Return and cancellation rates by {label.lower()}",height=350,
                margin={"l":12,"r":20,"t":58,"b":70},
                legend={"orientation":"h","y":-0.28,"x":0},
                showlegend=True
            )
            show_chart(fig,col)
    st.caption("Dots show each group's rate. Whiskers show a 95% range. Dashed lines show the overall return and cancellation rates. Hover over a dot for the order count.")

st.subheader("Ratings and return rates are similar across shipping and discount groups")
from scipy.stats import spearmanr, pointbiserialr
relation_cols=st.columns(3)
rel=rate_view.copy(); rel["ship_band"]=pd.cut(rel.shipping_days,[0,2,4,6,np.inf],labels=["1–2","3–4","5–6","7+"])
rel["discount_tier"]=(rel.discount_pct*100).round().astype(int).astype(str)+"%"
shiprating=rel.dropna(subset=["shipping_days","rating"]); disc_rating=rel.dropna(subset=["rating"]); disc_return=rel
metrics=[(shiprating.shipping_days,shiprating.rating,"shipping days",shiprating.groupby("ship_band",observed=True).rating.agg(["mean","count"])),
         (disc_rating.discount_pct,disc_rating.rating,"discount",disc_rating.groupby("discount_tier").rating.agg(["mean","count"])),
         (disc_return.discount_pct,(disc_return.order_status=="Returned").astype(int),"discount",disc_return.groupby("discount_tier").agg(mean=("order_status",lambda s:(s=="Returned").mean()),count=("order_status","size")))]
for col,(xv,yv,xlabel,summary) in zip(relation_cols,metrics):
    good=pd.Series(xv).notna() & pd.Series(yv).notna()
    if good.sum()>2:
        corr,pv=spearmanr(np.asarray(xv)[good],np.asarray(yv)[good])
    else: corr,pv=np.nan,np.nan
    vals=summary["mean"] if "mean" in summary else summary["rating"]
    ns=summary["count"]
    err=[1.96*(np.std(np.asarray(yv)[good])/math.sqrt(max(int(n_),1))) for n_ in ns]
    f=go.Figure(go.Scatter(x=[str(x) for x in summary.index],y=vals,mode="lines+markers+text",text=[f"n={int(x)}" for x in ns],textposition="top center",marker={"color":COLORS['teal'],"size":8},error_y={"type":"data","array":err,"visible":True},hovertemplate="%{x}<br>Mean %{y:.2f}<extra></extra>"))
    # Replace the terse chart title with the specific measure and reported association.
    measure="return rate" if yv.dtype.kind in "biu" and len(np.unique(yv))==2 else "rating"
    f.update_layout(title=f"{xlabel.title()} vs {measure}<br><sup>r={corr:.3f}, p={pv:.2g}</sup>",xaxis_title=xlabel,yaxis_title=measure.title(),yaxis={"range":[0,1] if measure=="return rate" else [3.5,4.5]},showlegend=False)
    show_chart(f,col)
st.caption("The rating scale is zoomed in to make small differences easier to see. Some ratings and shipping times are recorded on orders that were not delivered.")

st.subheader("Average units stay similar across discount levels; recorded profit leaves out discount cost")
disc=view.groupby("discount_pct").agg(revenue=("revenue","sum"),profit=("profit","sum"),list_profit=("profit_list_cost","sum"),quantity=("quantity","mean"),gross=("gross_sales","sum"))
disc["recorded_margin"]=disc.profit/disc.revenue*100; disc["sensitivity_margin"]=disc.list_profit/disc.gross*100
fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.08,row_heights=[.68,.32])
fig.add_trace(go.Scatter(x=disc.index*100,y=disc.recorded_margin,name="Recorded margin",mode="lines+markers",line={"color":COLORS['teal'],"width":2},hovertemplate="Discount %{x:.0f}%<br>Recorded margin %{y:.1f}%<extra></extra>"),row=1,col=1)
fig.add_trace(go.Scatter(x=disc.index*100,y=disc.sensitivity_margin,name="Sensitivity: cost held at list price (our assumption)",mode="lines+markers",line={"color":COLORS['accent'],"width":2,"dash":"dash"},hovertemplate="Discount %{x:.0f}%<br>Sensitivity margin %{y:.1f}%<extra></extra>"),row=1,col=1)
fig.add_trace(go.Bar(x=disc.index*100,y=disc.quantity,marker_color=COLORS['context'],name="Average quantity per line",hovertemplate="Discount %{x:.0f}%<br>Average quantity %{y:.2f}<extra></extra>"),row=2,col=1)
fig.update_yaxes(title_text="Margin (%)",row=1,col=1); fig.update_yaxes(title_text="Units per line",row=2,col=1); fig.update_xaxes(title_text="Discount tier (%)",row=2,col=1); fig.update_layout(height=440,title="Margin under two cost views, with quantity below",legend={"orientation":"h","y":1.1}); show_chart(fig)

pending_base=df[df.order_status.eq("Pending")].copy()
for col,val in [("region",region),("category",category)]:
    if val!="All": pending_base=pending_base[pending_base[col].eq(val)]
pending_lines=pending_base
pending_orders=pending_lines.groupby("order_id").agg(date=("order_date","first"),revenue=("revenue","sum"),profit=("profit","sum"))
pending_orders["age"]=(pd.Timestamp("2025-12-31")-pending_orders.date).dt.days
pending_orders["bucket"]=pd.cut(pending_orders.age,[-1,30,90,180,np.inf],labels=["0–30 days","31–90 days","91–180 days","181+ days"])
pg=pending_orders.groupby("bucket",observed=True).agg(orders=("revenue","size"),revenue=("revenue","sum"))
stale_pending=int((pending_orders.age>90).sum())
st.subheader(f"{stale_pending} Pending orders are older than 90 days")
fig=go.Figure(go.Bar(x=pg.index.astype(str),y=pg.orders,marker_color=COLORS['accent'],text=[f"{int(n):,} orders<br>{money(v)}" for n,v in zip(pg.orders,pg.revenue)],textposition="outside",hovertemplate="%{x}<br>%{y} orders<extra></extra>")); fig.update_layout(title="Pending order age at 31 Dec 2025",xaxis_title="Age bucket",yaxis_title="Orders",height=340); show_chart(fig)

heading("customers","4  Customers","See which cities and customers account for profit.")
city=view.groupby("city").agg(profit=("profit","sum"),customers=("customer_id","nunique")); city["per_customer"]=city.profit/city.customers; city=city.sort_values("profit")
all_per=d.groupby("customer_id").profit.sum().mean()
fig=go.Figure()
fig.add_trace(go.Bar(y=city.index,x=city.profit/1e6,orientation="h",marker_color=COLORS['teal'],name="Profit",customdata=city.profit,hovertemplate="%{y}<br>Profit ₹%{customdata:,.0f}<extra></extra>"))
fig.add_trace(go.Scatter(y=city.index,x=city.per_customer,xaxis="x2",mode="markers",marker={"color":COLORS['accent'],"size":9},name="Profit per customer",customdata=city.customers,hovertemplate="%{y}<br>Profit per customer ₹%{x:,.0f}<br>%{customdata} customers<extra></extra>"))
fig.add_trace(go.Scatter(y=[city.index[0],city.index[-1]],x=[all_per,all_per],xaxis="x2",mode="lines",line={"color":COLORS['muted'],"dash":"dash"},name="Overall average",hoverinfo="skip"))
fig.update_layout(title="Biggest cities are not the best customers",height=570,legend={"orientation":"h","y":1.04},xaxis={"title":"City profit (₹ million)"},xaxis2={"title":"Profit per customer (₹)","overlaying":"x","side":"top","range":[0,max(city.per_customer.max(),all_per)*1.15]}); show_chart(fig)

cust=d.groupby("customer_id").profit.sum().sort_values(ascending=False)
rank=np.arange(1,len(cust)+1); cumulative=cust.cumsum()/cust.sum()*100; pct=rank/len(cust)*100
top10=cumulative.iloc[min(148,len(cumulative)-1)]; top20=cumulative.iloc[min(297,len(cumulative)-1)]
fig=go.Figure(); fig.add_trace(go.Scatter(x=pct,y=cumulative,mode="lines",line={"color":COLORS['teal'],"width":2},name="Cumulative profit share",hovertemplate="Customer rank %{x:.1f}%<br>Cumulative profit %{y:.1f}%<extra></extra>")); fig.add_trace(go.Scatter(x=[0,100],y=[0,100],mode="lines",line={"color":COLORS['context'],"dash":"dash"},name="Perfect equality",hoverinfo="skip"))
fig.add_trace(go.Scatter(x=[10,20],y=[top10,top20],mode="markers+text",text=[f"10% · {top10:.1f}%",f"20% · {top20:.1f}%"],textposition="top center",marker={"color":COLORS['accent'],"size":10},showlegend=False))
fig.update_layout(title=f"Top 20% of customers earn {top20:.0f}% of profit: no Pareto risk",xaxis_title="Customers ranked by profit (%)",yaxis_title="Cumulative profit share (%)",height=380); show_chart(fig)

st.subheader("Top 10 customers by profit")
custprof=d.groupby("customer_id").profit.sum().nlargest(10).index
top=d[d.customer_id.isin(custprof)].groupby(["customer_id","city","segment"]).agg(orders=("order_id","nunique"),revenue=("revenue","sum"),profit=("profit","sum")).reset_index().sort_values("profit",ascending=False)
top["Revenue"]=top.revenue.map(lambda x:money(x)); top["Profit"]=top.profit.map(lambda x:money(x)); top_view=top[["customer_id","city","segment","orders","Revenue","Profit"]].rename(columns={"customer_id":"Customer","city":"City","segment":"Segment","orders":"Orders"}); st.markdown(top_view.to_html(index=False,classes="customer-table",border=0),unsafe_allow_html=True)

heading("actions","5  Suggested next steps","These ideas are based on the patterns shown above.")
lowcount=int(len(byprod[byprod.margin<.26])); lowrev=byprod[byprod.margin<.26].revenue.sum(); lowprofit=byprod[byprod.margin<.26].profit.sum(); lowimpact=(.30*lowrev-lowprofit)
disc_all=d.groupby("discount_pct").agg(discount=("discount_amount","sum"),quantity=("quantity","mean"),profit=("profit","sum"),revenue=("revenue","sum"),gross=("gross_sales","sum"),list_profit=("profit_list_cost","sum"))
high_tiers=disc_all.loc[disc_all.index.isin([.15,.20])]
high_lines=d[d.discount_pct.isin([.15,.20])]
delta_revenue=float((high_lines.gross_sales*(high_lines.discount_pct-.10)).sum())
delta_profit_recorded=float((high_lines.gross_sales*(high_lines.discount_pct-.10)*(1-high_lines.cost_ratio)).sum())
pending_all=d[d.order_status.eq("Pending")].groupby("order_id").agg(date=("order_date","first"),revenue=("revenue","sum"),profit=("profit","sum")); pending_all["age"]=(pd.Timestamp("2025-12-31")-pending_all.date).dt.days; stale=pending_all[pending_all.age>90]
action_cols=st.columns(3)
actions=[
    (f"Lift {lowcount} products below 26% margin",f"They carry {money_m(lowrev)} revenue and {money_m(lowprofit)} profit. A 30% margin target would add about {money_m(lowimpact)} profit. The data cannot show whether a price rise would reduce orders."),
    ("Test a cap on 15% and 20% discounts",f"These tiers account for {money_m(high_tiers.discount.sum())} of discounts across {len(high_lines):,} lines. A 10% cap retains about {money_m(delta_revenue)} revenue and {money_m(delta_profit_recorded)} profit under the recorded cost formula. Test in one category first. The list-price cost view is a sensitivity."),
    ("Resolve old Pending orders",f"{len(stale):,} Pending orders are over 90 days old, with {money_m(stale.revenue.sum())} booked revenue. Use a clear confirmation or cancellation rule across the pipeline. No segment stands out as a hotspot."),
]
for col,(title,body) in zip(action_cols,actions):
    col.markdown(f"<div class='action'><h3>{title}</h3><p>{body}</p></div>",unsafe_allow_html=True)

st.markdown("<div id='notes'></div>",unsafe_allow_html=True)
with st.expander("Data notes and cleaning log",expanded=True):
    st.markdown(f"""<div class='note'><b>Cleaning log</b><br>
Raw rows: {audit['raw_rows']:,}. Removed {audit['duplicate_rows']} exact duplicate rows ({money(audit['duplicate_revenue'])} revenue and {money(audit['duplicate_profit'])} profit impact).<br>
Removed {audit['bad_discount_rows']} lines with discount above 100% (their recorded revenue totals {money(audit['bad_discount_revenue'])}; true discount is unknown).<br>
Set {audit['negative_shipping_rows']} negative shipping values to missing. Other missing values stay blank. No values were imputed.<br>
Clean result: {len(df):,} lines, {df.order_id.nunique():,} orders, {df.customer_id.nunique():,} customers. Created category/subcategory labels, month, age bands and status flags.<br><br>
Booked revenue and profit include all statuses as recorded. Return and cancellation rates use distinct orders. Margin is profit divided by revenue, using sums. Shipping is a line-level field. Pending age uses 31 Dec 2025 as the reference date.<br>
Cost is calculated from discounted revenue in the source. The chart's list-price cost line is a sensitivity based on the assumption that cost does not fall with discount. It is not observed fact.<br>
The data has no campaign, traffic or inventory fields, so it cannot explain why monthly order counts changed or whether a price rise would reduce demand. Customer age has a floor at 18. Some ratings and shipping days appear on non-delivered lines.</div>""",unsafe_allow_html=True)
