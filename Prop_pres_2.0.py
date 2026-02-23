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
    df = pd.DataFrame(columns=["W/O Number","address","latitude","longitude","status","vendor"])

# Normalize columns for safety
df, prop_col_map = normalize_cols(df)

# Ensure numeric lat/lon
if "latitude" in df.columns and "longitude" in df.columns:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
else:
    # leave df as-is but will produce empty map
    pass

# --------------------------
# Load status sheet (the new left-panel data)
# --------------------------
SHEET_ID_STATS = "1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY"
CSV_URL_STATS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_STATS}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=180)
def load_status_sheet(url):
    df = pd.read_csv(url)
    return df

try:
    df_status = load_status_sheet(CSV_URL_STATS)
    # normalize
    df_status, status_col_map = normalize_cols(df_status)
    st.success("✅ Live status data loaded")
except Exception as e:
    st.error(f"❌ Failed to load status sheet: {e}")
    df_status = pd.DataFrame(columns=["Property","Details","CREW NAME","Due date","Status 1","Reason"])
    df_status, status_col_map = normalize_cols(df_status)

# --------------------------
# Page layout: left status panel + right map
# --------------------------
left_col, right_col = st.columns([3, 9])  # adjust widths: left smaller, right larger

# ---------- LEFT: Status Board ----------
with left_col:
    st.markdown("## 📊 Property Preservation Status Board")
    st.markdown("Live updates from your status sheet")

    if df_status.empty:
        st.info("No status data available.")
    else:
        # Use safe_get to find required columns even if names vary
        prop_series = safe_get(df_status, status_col_map, "Property", "")
        crew_series = safe_get(df_status, status_col_map, "CREW NAME", "")
        due_series = safe_get(df_status, status_col_map, "Due date", "")
        status_series = safe_get(df_status, status_col_map, "Status 1", "")
        reason_series = safe_get(df_status, status_col_map, "Reason", "")

        # Simple classification counts (case-insensitive)
        completed_mask = status_series.str.contains("complete|submitted|finished", case=False, na=False)
        pending_mask = status_series.str.contains("pending|in progress|assigned|no crew", case=False, na=False)
        overdue_mask = status_series.str.contains("overdue|late", case=False, na=False)

        completed_count = int(completed_mask.sum())
        pending_count = int(pending_mask.sum())
        overdue_count = int(overdue_mask.sum())
        crews_count = int(crew_series.dropna().nunique())

        # KPI cards
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("✅ Completed", completed_count)
        k2.metric("🕓 Pending", pending_count)
        k3.metric("❌ Overdue", overdue_count)
        k4.metric("👷 Crews", crews_count)

        st.markdown("---")

        # Status distribution bar chart (counts)
        st.markdown("### 📈 Status Distribution")
        chart_counts = status_series.fillna("unknown").value_counts()
        # st.bar_chart accepts a series or dataframe with numeric values
        st.bar_chart(chart_counts)

        st.markdown("---")

        # --- Latest Property Updates (only from specific tab gid=160282702) ---

st.markdown("### 📰 Latest Property Updates")

# Define the direct URL to that tab
CSV_URL_UPDATES = "https://docs.google.com/spreadsheets/d/1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY/gviz/tq?tqx=out:csv&gid=160282702"

@st.cache_data(ttl=300)
def load_latest_updates():
    return pd.read_csv(CSV_URL_UPDATES)

try:
    df_updates = load_latest_updates()
    st.success("📡 Live updates loaded successfully")
except Exception as e:
    st.error(f"❌ Failed to load updates sheet: {e}")
    df_updates = pd.DataFrame(columns=["Property", "Details", "CREW NAME", "Due date", "Status 1", "Reason"])

# Show updates if data exists
if not df_updates.empty:
    # Normalize column names
    df_updates.columns = [c.strip() for c in df_updates.columns]

    # Sort by due date (if possible)
    if "Due date" in df_updates.columns:
        try:
            df_updates["Due date"] = pd.to_datetime(df_updates["Due date"], errors="coerce")
            df_updates = df_updates.sort_values("Due date", ascending=True)
        except Exception:
            pass

    # Create a scrollable container
    with st.container():
        st.markdown(
            """
            <div style="max-height:450px; overflow-y:auto; padding-right:10px;">
            """,
            unsafe_allow_html=True
        )

        # Loop through rows
        for _, row in df_updates.iterrows():
            prop = row.get("Property", "")
            details = row.get("Details", "")
            crew = row.get("CREW NAME", "")
            due = row.get("Due date", "")
            status = row.get("Status 1", "")
            reason = row.get("Reason", "")

            # Color code by status
            s = str(status).lower()
            if "complete" in s:
                color = "#2ecc71"
            elif "overdue" in s or "late" in s:
                color = "#e74c3c"
            elif "pending" in s or "in progress" in s:
                color = "#f39c12"
            else:
                color = "#3498db"

            st.markdown(
                f"""
                <div style="background-color:{color}15; border-left:4px solid {color}; padding:10px; border-radius:6px; margin-bottom:8px;">
                    <b>🏠 Property:</b> {prop}<br>
                    <b>🧾 Details:</b> {details}<br>
                    <b>👷 Crew:</b> {crew}<br>
                    <b>📅 Due:</b> {due}<br>
                    <b>📊 Status:</b> {status}<br>
                    <b>💬 Reason:</b> {reason}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No recent property updates available.")
# ---------- RIGHT: Map ----------
with right_col:
    # create map center
    if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
        map_center = [df["latitude"].mean(), df["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=12, tiles=None)
    else:
        # fallback
        map_center = [24.0, 90.0]
        m = folium.Map(location=map_center, zoom_start=5, tiles=None)

    # Basemaps
    folium.TileLayer("CartoDB positron", name="Light Map").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)

    # optional overlays (keep, but note: some tile URLs require https and API keys in secrets)
    # Marker cluster
    marker_cluster = MarkerCluster().add_to(m)

    # If df has lat/lon, add markers
    if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
        # create GeoDataFrame for searching layer as well
        try:
            gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])], crs="EPSG:4326")
        except Exception:
            gdf = None

        # Add markers with popup
        if gdf is not None:
            for _, row in gdf.iterrows():
                # build popup using safe access to columns that may exist
                wo = row.get(prop_col_map.get("w/o number", "W/O Number"), row.get("W/O Number", ""))
                address = row.get(prop_col_map.get("address", "address"), row.get("address", ""))
                status = row.get(prop_col_map.get("status", "status"), row.get("status", ""))
                vendor = row.get(prop_col_map.get("vendor", "vendor"), row.get("vendor", ""))

                # simple popup HTML
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

            # Add searchable GeoJson layer for Search plugin
            geojson_layer = folium.GeoJson(
                gdf,
                name="Searchable Properties",
                tooltip=folium.features.GeoJsonTooltip(fields=["address"], aliases=["Address:"])
            ).add_to(m)

            Search(layer=geojson_layer, search_label="address", placeholder="🔍 Search address or W/O", collapsed=False, search_zoom=16).add_to(m)

    # Legend (kept simple)
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

    # Render map
    st_folium(m, width=1100, height=700)
