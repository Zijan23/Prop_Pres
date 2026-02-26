# app.py - CPP Dashboard (updated left-panel status board + map)
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster, Search
from streamlit_folium import st_folium
from shapely.geometry import Point
from folium import IFrame
import os
import plotly.express as px
from datetime import datetime

# --- Streamlit Page Config ---
st.set_page_config(page_title="Property Preservation Live Report", layout="wide")

st.title("🏠 CPP Dashboard")
st.subheader("🔍 Zoom in/out and click on any property to see its details")

# --------------------------
# Helper functions
# --------------------------
def normalize_cols(df):
    """Make a mapping of lower-trimmed column names to original and rename a copy for easy lookups."""
    df = df.copy()
    col_map = {c.strip().lower(): c for c in df.columns}
    df.columns = [c.strip() for c in df.columns]
    return df, col_map


def safe_get(df, col_map, want_name, default=""):
    """Return series df[col] if present using a case-insensitive match, else default."""
    key = want_name.strip().lower()
    if key in col_map:
        return df[col_map[key]]
    # not found, return a series of defaults
    return pd.Series([default] * len(df), index=df.index)


# --------------------------
# Load property map data (existing Google Sheet)
# --------------------------
SHEET_ID = "1AxNmdkDGxYhi0-3-bZGdng-hT1KzxHqpgn_82eqglYg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"


@st.cache_data(ttl=180)
def load_property_sheet(url):
    df = pd.read_csv(url)
    return df


try:
    df = load_property_sheet(CSV_URL)
    st.success("✅ Live property data loaded from Google Sheets")
except Exception as e:
    st.error(f"❌ Failed to load property sheet: {e}")
    df = pd.DataFrame(columns=["W/O Number", "address", "latitude", "longitude", "status", "vendor"])

# Normalize columns for safety
df, prop_col_map = normalize_cols(df)

# Ensure numeric lat/lon
if "latitude" in df.columns and "longitude" in df.columns:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
else:
    pass

# --------------------------
# Load status sheet (left-panel data)
# --------------------------
CSV_URL_UPDATES = "https://docs.google.com/spreadsheets/d/1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY/gviz/tq?tqx=out:csv&gid=160282702"


@st.cache_data(ttl=180)
def load_updates():
    return pd.read_csv(CSV_URL_UPDATES)


df_updates = None
try:
    df_updates = load_updates()
    st.caption(f"✅ Loaded {len(df_updates)} rows from updates tab")
except Exception as e:
    st.error(f"❌ Failed to load updates tab: {e}")
    df_updates = pd.DataFrame(columns=["Property", "Details", "CREW NAME", "Due date", "Status 1", "Reason"])

# Normalize once here
if df_updates is not None and not df_updates.empty:
    df_updates.columns = [c.strip() for c in df_updates.columns]

# --------------------------
# Page layout: left status panel + right map
# --------------------------
left_col, right_col = st.columns([3, 9])

# ---------- LEFT: Status Board ----------
with left_col:
    st.markdown(
        "<h2 style='margin:0 0 8px 0;'>🏠 Property Preservation Status Board</h2>",
        unsafe_allow_html=True
    )
    st.caption("🔴 Live from updates tab (gid=160282702) • Refreshes ~every 3 min")

    if df_updates is None or df_updates.empty:
        st.warning("No status data loaded yet. Check sheet permissions/export link.")
    else:
        df_left = df_updates.copy()

        # Date parsing
        if "Due date" in df_left.columns:

            def parse_date(x):
                if pd.isna(x) or str(x).strip() == "":
                    return pd.NaT
                x_str = str(x).strip()
                for fmt in ["%d/%m/%Y", "%m/%d/%y", "%m/%d/%Y", "%d-%m-%y", "%d-%m-%Y"]:
                    try:
                        return pd.to_datetime(x_str, format=fmt, errors="raise")
                    except:
                        pass
                return pd.to_datetime(x_str, errors="coerce", dayfirst=True)

            df_left["Due date"] = df_left["Due date"].apply(parse_date)

        # Categorize function
        def categorize(row):
            s = str(row.get("Status 1", "")).lower().strip()
            due = row.get("Due date")

            if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received"]):
                return "✅ Completed"

            if pd.notna(due) and isinstance(due, (pd.Timestamp, datetime.date, datetime.datetime)):
                today_dt = pd.Timestamp.today().normalize()
                if due < today_dt:
                    return "❌ Overdue"

            if any(word in s for word in ["ongoing", "progress", "will be", "try to", "today", "tomorrow", "friday", "monday"]):
                return "🔄 In Progress"

            if any(word in s for word in ["waiting", "pending", "bid", "pricing", "activation"]):
                return "⏳ Pending / Bid"

            return "📌 Other"

        df_left["Category"] = df_left.apply(categorize, axis=1)

        # Metrics
        total = len(df_left)
        completed = (df_left["Category"] == "✅ Completed").sum()
        overdue = (df_left["Category"] == "❌ Overdue").sum()
        in_progress = (df_left["Category"] == "🔄 In Progress").sum()
        pending = (df_left["Category"] == "⏳ Pending / Bid").sum()
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        active_crews = df_left["CREW NAME"].dropna().nunique()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📋 Total Properties", total)
        c2.metric("✅ Completion Rate", f"{completion_rate}%", delta=f"{completed} completed")
        c3.metric("❌ Overdue", overdue, help="Past due date & not marked complete")
        c4.metric("👷 Active Crews", active_crews)

        st.markdown("---")

        # Pie Chart
        st.markdown("### 📊 Status Breakdown")
        fig = px.pie(
            df_left["Category"].value_counts().reset_index(),
            names="Category",
            values="count",
            color="Category",
            color_discrete_map={
                "✅ Completed": "#2ecc71",
                "❌ Overdue": "#e74c3c",
                "🔄 In Progress": "#f39c12",
                "⏳ Pending / Bid": "#3498db",
                "📌 Other": "#7f8c8d"
            }
        )
        fig.update_traces(textinfo="percent+label", textfont_size=14)
        fig.update_layout(height=320, margin=dict(t=30, b=10, l=0, r=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Executive Insights
        st.markdown("### 💡 Executive Insights")

        insight_list = []
        if overdue > 0:
            insight_list.append(f"🚨 **{overdue} properties are overdue** — immediate action needed.")
        if pending >= 2:
            insight_list.append(f"⏳ **{pending} bids/activations pending** — follow up today.")

        top_crew = df_left["CREW NAME"].value_counts().idxmax() if not df_left["CREW NAME"].dropna().empty else "N/A"
        top_count = df_left["CREW NAME"].value_counts().max()
        insight_list.append(f"🏆 **{top_crew}** is leading with **{top_count}** assignments.")

        today = pd.Timestamp.today()
        due_soon = df_left[
            (pd.notna(df_left["Due date"])) &
            (df_left["Due date"] <= today + pd.Timedelta(days=7)) &
            (df_left["Category"] != "✅ Completed")
        ]
        if len(due_soon) > 0:
            insight_list.append(f"📅 **{len(due_soon)} properties due within 7 days**.")

        for ins in insight_list:
            st.info(ins)

        st.markdown("---")

        # Urgent Items
        st.markdown("### ⚠️ Urgent Items (Overdue or Due Soon)")
        urgent = df_left[
            (df_left["Category"] == "❌ Overdue") |
            ((pd.notna(df_left["Due date"])) &
             (df_left["Due date"] <= today + pd.Timedelta(days=7)) &
             (df_left["Category"] != "✅ Completed"))
        ].copy()

        if not urgent.empty:
            urgent = urgent[["Property", "CREW NAME", "Due date", "Status 1"]].sort_values("Due date")
            urgent["Due date"] = urgent["Due date"].dt.strftime("%b %d, %Y")
            st.dataframe(
                urgent,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Property": st.column_config.TextColumn("🏠 Property"),
                    "CREW NAME": st.column_config.TextColumn("👷 Crew"),
                    "Due date": st.column_config.TextColumn("📅 Due"),
                    "Status 1": st.column_config.TextColumn("Status")
                }
            )
        else:
            st.success("🎉 All properties are on track!")

        st.markdown("---")

# ---------- RIGHT: Map ----------
with right_col:
    if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
        map_center = [df["latitude"].mean(), df["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=12, tiles=None)
    else:
        map_center = [24.0, 90.0]
        m = folium.Map(location=map_center, zoom_start=5, tiles=None)

    folium.TileLayer("CartoDB positron", name="Light Map").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
        try:
            gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])], crs="EPSG:4326")
        except Exception:
            gdf = None

        if gdf is not None:
            for _, row in gdf.iterrows():
                wo = row.get(prop_col_map.get("w/o number", "W/O Number"), row.get("W/O Number", ""))
                address = row.get(prop_col_map.get("address", "address"), row.get("address", ""))
                status = row.get(prop_col_map.get("status", "status"), row.get("status", ""))
                vendor = row.get(prop_col_map.get("vendor", "vendor"), row.get("vendor", ""))

                popup_html = f"""
                    <div style='font-size:13px;'>
                        <b>W/O:</b> {wo}<br>
                        <b>Address:</b> {address}<br>
                        <b>Status:</b> {status}<br>
                        <b>Vendor:</b> {vendor}
                    </div>
                """
                iframe = IFrame(popup_html, width=280, height=140)
                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=6,
                    color="blue",
                    fill=True,
                    fill_color="blue",
                    fill_opacity=0.9,
                    popup=folium.Popup(iframe, max_width=300),
                ).add_to(marker_cluster)

            geojson_layer = folium.GeoJson(
                gdf,
                name="Searchable Properties",
                tooltip=folium.features.GeoJsonTooltip(fields=["address"], aliases=["Address:"])
            ).add_to(m)

            Search(layer=geojson_layer, search_label="address", placeholder="🔍 Search address or W/O", collapsed=False, search_zoom=16).add_to(m)

    legend_html = """
    <div style="
        position: fixed; 
        bottom: 40px; left: 40px; width: 180px; height: 100px; 
        background-color: white; 
        border:2px solid grey; 
        z-index:9999; 
        font-size:14px; 
        border-radius:8px;
        padding:10px;
        box-shadow:2px 2px 5px rgba(0,0,0,0.3);
    ">
        <b>Status Legend</b><br>
        <span style="color:#e74c3c;">&#9679;</span> Overdue<br>
        <span style="color:#f39c12;">&#9679;</span> Pending<br>
        <span style="color:#2ecc71;">&#9679;</span> Complete
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width=1100, height=700)
