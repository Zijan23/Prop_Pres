# app.py - CPP Dashboard (robust overdue detection + synced updates section)
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster, Search
from streamlit_folium import st_folium
from shapely.geometry import Point
from folium import IFrame
import plotly.express as px
import datetime
import dateutil.parser

# --------------------------
# --- Streamlit Page Config ---
st.set_page_config(page_title="Property Preservation Live Report", layout="wide")

st.title("🏠 CPP Dashboard")
st.subheader("🔍 Zoom in/out and click on any property to see its details")

# --------------------------
# Helper Functions
# --------------------------
def normalize_cols(df):
    """Normalize column names to lowercase and strip."""
    df = df.copy()
    col_map = {c.strip().lower(): c for c in df.columns}
    df.columns = [c.strip() for c in df.columns]
    return df, col_map

def safe_get(df, col_map, want_name, default=""):
    """Return series by case-insensitive column name."""
    key = want_name.strip().lower()
    if key in col_map:
        return df[col_map[key]]
    return pd.Series([default] * len(df), index=df.index)

# --------------------------
# Load property map data
# --------------------------
SHEET_ID = "1AxNmdkDGxYhi0-3-bZGdng-hT1KzxHqpgn_82eqglYg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=180)
def load_property_sheet(url):
    return pd.read_csv(url)

try:
    df = load_property_sheet(CSV_URL)
    st.success("✅ Live property data loaded from Google Sheets")
except Exception as e:
    st.error(f"❌ Failed to load property sheet: {e}")
    df = pd.DataFrame(columns=["W/O Number", "address", "latitude", "longitude", "status", "vendor"])

df, prop_col_map = normalize_cols(df)
if "latitude" in df.columns and "longitude" in df.columns:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

# --------------------------
# Load updates data
# --------------------------
CSV_URL_UPDATES = "https://docs.google.com/spreadsheets/d/1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY/gviz/tq?tqx=out:csv&gid=160282702"

@st.cache_data(ttl=180)
def load_updates():
    return pd.read_csv(CSV_URL_UPDATES)

try:
    df_updates = load_updates()
    st.caption(f"✅ Loaded {len(df_updates)} rows from updates tab")
except Exception as e:
    st.error(f"❌ Failed to load updates tab: {e}")
    df_updates = pd.DataFrame(columns=["Property", "Details", "CREW NAME", "Due date", "Status 1", "Reason"])

df_updates.columns = [c.strip() for c in df_updates.columns]

# --------------------------
# Left panel (status board)
# --------------------------
left_col, right_col = st.columns([4, 6])
with left_col:
    st.markdown("<h2 style='margin:0 0 8px 0;'>🏠 Property Preservation Status Board</h2>", unsafe_allow_html=True)
    st.caption("🔴 Live from updates tab (gid=160282702) • Refreshes ~every 3 min")

    if df_updates.empty:
        st.warning("No status data loaded yet. Check sheet permissions/export link.")
    else:
        df_left = df_updates.copy()
        today = pd.Timestamp.today().normalize()

        # --- Parse Due Date ---
        def parse_date(x):
            if pd.isna(x) or str(x).strip().lower() in ["", "none", "nan", "n/a", "na"]:
                return pd.NaT
            try:
                return pd.to_datetime(x, errors="coerce", dayfirst=True)
            except:
                try:
                    return pd.to_datetime(dateutil.parser.parse(str(x), fuzzy=True))
                except:
                    return pd.NaT

        if "Due date" in df_left.columns:
            df_left["Due date"] = df_left["Due date"].apply(parse_date)

        # --- Categorize ---
        def categorize(row):
            s = str(row.get("Status 1", "")).lower().strip()
            due = row.get("Due date")
            today_dt = pd.Timestamp.today().normalize()

            if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received"]):
                return "✅ Completed"
            if pd.notna(due) and due < today_dt:
                return "❌ Overdue"
            if any(word in s for word in ["ongoing", "progress", "will be", "try to", "today", "tomorrow", "friday", "monday"]):
                return "🔄 In Progress"
            if any(word in s for word in ["waiting", "pending", "bid", "pricing", "activation"]):
                return "⏳ Pending / Bid"
            return "📌 Other"

        df_left["Category"] = df_left.apply(categorize, axis=1)

        # --- Debug check for TX / Nebraska ---
        with st.expander("🔎 Debug: show TX/ID overdue check", expanded=False):
            suspects = df_left[
                df_left["Property"].astype(str).str.lower().str.contains("eagles nest|nebraska st", regex=True, na=False)
            ].copy()
            if suspects.empty:
                st.write("No rows found matching those substrings.")
            else:
                st.dataframe(suspects[["Property", "CREW NAME", "Due date", "Status 1", "Category"]], use_container_width=True)

        # --- KPIs ---
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

        # --- Status Pie Chart ---
        st.markdown("### 📊 Status Breakdown")
        fig = px.pie(
            df_left["Category"].value_counts().reset_index(name="count"),
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

# --------------------------
# Right panel (Map)
# --------------------------
with right_col:
    if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
        map_center = [df["latitude"].mean(), df["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=12, tiles=None)
    else:
        m = folium.Map(location=[24.0, 90.0], zoom_start=5, tiles=None)

    folium.TileLayer("CartoDB positron", name="Light Map").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    if not df.empty:
        try:
            gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])], crs="EPSG:4326")
        except:
            gdf = None

        if gdf is not None:
            for _, row in gdf.iterrows():
                wo = row.get(prop_col_map.get("w/o number", "W/O Number"), "")
                address = row.get(prop_col_map.get("address", "address"), "")
                status = row.get(prop_col_map.get("status", "status"), "")
                vendor = row.get(prop_col_map.get("vendor", "vendor"), "")

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

            Search(
                layer=geojson_layer,
                search_label="address",
                placeholder="🔍 Search address or W/O",
                collapsed=False,
                search_zoom=16
            ).add_to(m)

    # Legend
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
    st_folium(m, width=800, height=700)

# --------------------------
# 🧾 Detailed Property Updates (below map)
# --------------------------
st.markdown("---")
st.markdown("## 🧾 Latest Property Updates")

if not df_updates.empty:
    df_bottom = df_updates.merge(df_left[["Property", "Category"]], on="Property", how="left")
    df_bottom["Due date"] = pd.to_datetime(df_bottom["Due date"], errors="coerce")

    with st.container():
        st.markdown('<div style="max-height:500px; overflow-y:auto; padding-right:10px;">', unsafe_allow_html=True)

        color_map = {
            "✅ Completed": "#2ecc71",
            "❌ Overdue": "#e74c3c",
            "🔄 In Progress": "#f39c12",
            "⏳ Pending / Bid": "#3498db",
            "📌 Other": "#7f8c8d"
        }

        for _, row in df_bottom.iterrows():
            prop = row.get("Property", "")
            details = row.get("Details", "")
            crew = row.get("CREW NAME", "")
            due = row.get("Due date", "")
            status = row.get("Status 1", "")
            category = row.get("Category", "📌 Other")
            reason = row.get("Reason", "")
            color = color_map.get(category, "#3498db")
            due_str = due.strftime("%b %d, %Y") if pd.notna(due) else "N/A"

            st.markdown(f"""
                <div style="background-color:{color}15; border-left:4px solid {color};
                            padding:10px; border-radius:6px; margin-bottom:8px;">
                    <b>🏠 Property:</b> {prop}<br>
                    <b>🧾 Details:</b> {details}<br>
                    <b>👷 Crew:</b> {crew}<br>
                    <b>📅 Due:</b> {due_str}<br>
                    <b>📊 Status:</b> {status}<br>
                    <b>💬 Reason:</b> {reason}
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No recent property updates available.")
