import os

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

# ----------------------------------------------------------------------------
# Page setup + Zomato branding
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "zomato_icon.png")
# Drop the official Zomato logo here (optional) and it will be used in the header
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
DATA_PATH = os.path.join(BASE_DIR, "zomato_dataset.csv")

ZOMATO_RED = "#E23744"
DARK_RED = "#B71C2B"
LIGHT_RED = "#FFF5F6"
RED_SCALE = ["#FFD6DA", "#F59AA3", "#E23744", "#B71C2B", "#7A0F1B"]

page_icon = Image.open(ICON_PATH) if os.path.exists(ICON_PATH) else "🍴"
st.set_page_config(
    page_title="Zomato Analytics Dashboard",
    page_icon=page_icon,
    layout="wide",
)

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 1.5rem; }}
    .zomato-header {{
        background: linear-gradient(90deg, {ZOMATO_RED} 0%, {DARK_RED} 100%);
        padding: 1.2rem 1.6rem; border-radius: 16px; color: white;
        display: flex; align-items: center; gap: 1rem; margin-bottom: 1.2rem;
    }}
    .zomato-header img {{ height: 56px; border-radius: 12px; }}
    .zomato-wordmark {{
        font-size: 2.4rem; font-weight: 800; font-style: italic;
        letter-spacing: -1px; line-height: 1;
    }}
    .zomato-sub {{ opacity: .9; font-size: .95rem; margin-top: .25rem; }}
    .kpi {{
        background: {LIGHT_RED}; border-left: 5px solid {ZOMATO_RED};
        border-radius: 12px; padding: .9rem 1rem; margin-bottom: .8rem;
    }}
    .kpi .label {{ font-size: .78rem; color: #6b6b6b; text-transform: uppercase;
                   letter-spacing: .04em; }}
    .kpi .value {{ font-size: 1.6rem; font-weight: 700; color: {ZOMATO_RED}; }}
    [data-testid="stSidebar"] {{ border-right: 3px solid {ZOMATO_RED}; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        color: {ZOMATO_RED}; border-bottom: 3px solid {ZOMATO_RED};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def header():
    if os.path.exists(LOGO_PATH):
        import base64

        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        brand = f'<img src="data:image/png;base64,{b64}">'
    else:
        brand = '<div class="zomato-wordmark">zomato</div>'
    st.markdown(
        f"""
        <div class="zomato-header">
            {brand}
            <div>
                <div style="font-size:1.4rem;font-weight:700;">Restaurant Analytics Dashboard</div>
                <div class="zomato-sub">Ratings, cuisines, cities, pricing and votes at a glance</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi(col, label, value):
    col.markdown(
        f'<div class="kpi"><div class="label">{label}</div>'
        f'<div class="value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def style(fig, height=420):
    fig.update_layout(
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#1C1C1C"),
        margin=dict(l=10, r=10, t=50, b=10),
        title_font=dict(size=16, color=DARK_RED),
    )
    return fig


def hbar(series, title, xlabel, height=420):
    d = series.sort_values().reset_index()
    d.columns = ["label", "value"]
    fig = px.bar(d, x="value", y="label", orientation="h", title=title,
                 labels={"value": xlabel, "label": ""},
                 color="value", color_continuous_scale=RED_SCALE)
    fig.update_coloraxes(showscale=False)
    return style(fig, height)


# ----------------------------------------------------------------------------
# Data loading + cleaning (same steps as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data...")
def load_data(source):
    df = pd.read_csv(source, on_bad_lines="skip")
    df.columns = df.columns.str.strip()
    df = df.drop(columns=["Best Seller"], errors="ignore")
    for col in ["Dining Rating", "Delivery Rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())
    for col in ["Dining Votes", "Delivery Votes", "Votes", "Prices"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


header()

with st.sidebar:
    if os.path.exists(ICON_PATH):
        st.image(ICON_PATH, width=70)
    st.markdown("### Filters")
    uploaded = st.file_uploader("Upload zomato_dataset.csv", type="csv")

source = uploaded if uploaded is not None else (DATA_PATH if os.path.exists(DATA_PATH) else None)
if source is None:
    st.info("Place **zomato_dataset.csv** next to `app.py`, or upload it from the sidebar.")
    st.stop()

df = load_data(source)

required = ["Restaurant Name", "City", "Cuisine", "Item Name", "Dining Rating",
            "Delivery Rating", "Dining Votes", "Delivery Votes", "Votes", "Prices"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"These columns are missing from the dataset: {missing}")
    st.stop()

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
with st.sidebar:
    cities = sorted(df["City"].dropna().unique())
    sel_cities = st.multiselect("City", cities)
    cuisines = sorted(df["Cuisine"].dropna().unique())
    sel_cuisines = st.multiselect("Cuisine", cuisines)

    r_min, r_max = float(df["Dining Rating"].min()), float(df["Dining Rating"].max())
    rating_rng = st.slider("Dining rating", r_min, r_max, (r_min, r_max), step=0.1)

    p_min, p_max = float(df["Prices"].min(skipna=True)), float(df["Prices"].max(skipna=True))
    price_rng = st.slider("Price", p_min, p_max, (p_min, p_max))

f = df.copy()
if sel_cities:
    f = f[f["City"].isin(sel_cities)]
if sel_cuisines:
    f = f[f["Cuisine"].isin(sel_cuisines)]
f = f[f["Dining Rating"].between(*rating_rng)]
f = f[f["Prices"].isna() | f["Prices"].between(*price_rng)]

if f.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
r1 = st.columns(4)
kpi(r1[0], "Total Restaurants", f"{f['Restaurant Name'].nunique():,}")
kpi(r1[1], "Cities", f"{f['City'].nunique():,}")
kpi(r1[2], "Cuisines", f"{f['Cuisine'].nunique():,}")
kpi(r1[3], "Food Items", f"{f['Item Name'].nunique():,}")

r2 = st.columns(4)
kpi(r2[0], "Avg Dining Rating", f"{f['Dining Rating'].mean():.2f} ⭐")
kpi(r2[1], "Avg Delivery Rating", f"{f['Delivery Rating'].mean():.2f} ⭐")
kpi(r2[2], "Avg Food Price", f"₹{f['Prices'].mean():,.0f}")
kpi(r2[3], "Highest Food Price", f"₹{f['Prices'].max():,.0f}")

r3 = st.columns(3)
kpi(r3[0], "Total Dining Votes", f"{f['Dining Votes'].sum():,.0f}")
kpi(r3[1], "Total Delivery Votes", f"{f['Delivery Votes'].sum():,.0f}")
kpi(r3[2], "Total Food Votes", f"{f['Votes'].sum():,.0f}")

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Restaurants & Cities", "Food & Pricing", "Ratings & Votes", "Data"]
)

with tab1:
    c1, c2 = st.columns(2)
    cuisine_cnt = f["Cuisine"].value_counts().head(10)
    c1.plotly_chart(hbar(cuisine_cnt, "Top 10 Popular Cuisines", "Number of Records"),
                    use_container_width=True)
    c2.plotly_chart(
        style(px.histogram(f, x="Prices", nbins=30, title="Food Price Distribution",
                           color_discrete_sequence=[ZOMATO_RED])),
        use_container_width=True)
    c3, c4 = st.columns(2)
    c3.plotly_chart(
        style(px.histogram(f, x="Dining Rating", nbins=15, title="Dining Rating Distribution",
                           color_discrete_sequence=[ZOMATO_RED])),
        use_container_width=True)
    c4.plotly_chart(
        style(px.histogram(f, x="Delivery Rating", nbins=15, title="Delivery Rating Distribution",
                           color_discrete_sequence=[DARK_RED])),
        use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)
    top_rest = (f.groupby("Restaurant Name")["Dining Rating"].mean()
                .sort_values(ascending=False).head(10))
    c1.plotly_chart(hbar(top_rest.round(2), "Top 10 Restaurants by Dining Rating",
                         "Average Dining Rating"), use_container_width=True)
    city_cnt = (f.groupby("City")["Restaurant Name"].nunique()
                .sort_values(ascending=False).head(10))
    d = city_cnt.reset_index()
    d.columns = ["City", "Restaurants"]
    fig = px.bar(d, x="City", y="Restaurants", title="Top 10 Cities by Restaurant Count",
                 color="Restaurants", color_continuous_scale=RED_SCALE)
    fig.update_coloraxes(showscale=False)
    c2.plotly_chart(style(fig), use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)
    items = f.groupby("Item Name")["Votes"].sum().sort_values(ascending=False).head(10)
    c1.plotly_chart(hbar(items, "Top 10 Food Items by Votes", "Total Votes"),
                    use_container_width=True)
    cp = f.groupby("Cuisine")["Prices"].mean().sort_values(ascending=False).head(10)
    c2.plotly_chart(hbar(cp.round(1), "Top 10 Cuisines by Average Food Price", "Average Price"),
                    use_container_width=True)

with tab4:
    c1, c2 = st.columns(2)
    cr = f.groupby("Cuisine")["Dining Rating"].mean().sort_values(ascending=False).head(10)
    c1.plotly_chart(hbar(cr.round(2), "Top 10 Cuisines by Average Rating",
                         "Average Dining Rating"), use_container_width=True)
    corr = f[["Dining Rating", "Delivery Rating", "Dining Votes",
              "Delivery Votes", "Votes", "Prices"]].corr()
    c2.plotly_chart(
        style(px.imshow(corr, text_auto=".2f", title="Correlation Heatmap",
                        color_continuous_scale=RED_SCALE, aspect="auto")),
        use_container_width=True)

    sample = f.sample(min(len(f), 5000), random_state=1)
    c3, c4 = st.columns(2)
    c3.plotly_chart(
        style(px.scatter(sample, x="Dining Rating", y="Dining Votes", opacity=0.6,
                         title="Dining Rating vs Dining Votes",
                         color_discrete_sequence=[ZOMATO_RED])),
        use_container_width=True)
    c4.plotly_chart(
        style(px.scatter(sample, x="Dining Rating", y="Delivery Rating", opacity=0.6,
                         title="Dining Rating vs Delivery Rating",
                         color_discrete_sequence=[DARK_RED])),
        use_container_width=True)
    if len(f) > 5000:
        st.caption("Scatter plots show a random sample of 5,000 rows for speed.")

with tab5:
    st.dataframe(f, use_container_width=True, height=500)
    st.download_button("Download filtered data (CSV)",
                       f.to_csv(index=False).encode("utf-8"),
                       "zomato_filtered.csv", "text/csv")
