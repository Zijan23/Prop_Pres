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
# ---------- LEFT: Premium Status Board ----------
with left_col:
    st.markdown(
        "<h2 style='margin:0 0 8px 0;'>🏠 Property Preservation Status Board</h2>",
        unsafe_allow_html=True
    )
    st.caption("🔴 Live from Google Sheet • Auto-refreshes every 3 minutes")

    # Use the CLEAN tab (this fixes the "not updating" issue)
    df_left = df_updates.copy()

    if df_left.empty:
        st.warning("No status data available yet.")
    else:
        # ====================== DATA CLEANING ======================
        df_left.columns = [c.strip() for c in df_left.columns]
        
        # Proper date parsing (02-12-26 format)
        df_left["Due date"] = pd.to_datetime(
            df_left["Due date"], format="%m-%d-%y", errors="coerce"
        )
        today = pd.Timestamp.now().normalize()

        # Smart status categorization (handles real free-text entries)
        def categorize(row):
            s = str(row.get("Status 1", "")).lower()
            due = row.get("Due date")
            
            if any(x in s for x in ["complete", "submitted", "payment", "finished", "done", "received"]):
                return "✅ Completed"
            elif due and due < today and "complete" not in s:
                return "❌ Overdue"
            elif any(x in s for x in ["ongoing", "progress", "will be", "try to", "today", "tomorrow", "friday", "monday"]):
                return "🔄 In Progress"
            elif any(x in s for x in ["waiting", "pending", "bid", "pricing", "activation"]):
                return "⏳ Pending / Bid"
            else:
                return "📌 Other"

        df_left["Category"] = df_left.apply(categorize, axis=1)

        # ====================== CALCULATIONS ======================
        total = len(df_left)
        completed = (df_left["Category"] == "✅ Completed").sum()
        overdue = (df_left["Category"] == "❌ Overdue").sum()
        in_progress = (df_left["Category"] == "🔄 In Progress").sum()
        pending = (df_left["Category"] == "⏳ Pending / Bid").sum()
        
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        active_crews = df_left["CREW NAME"].dropna().nunique()

        # ====================== PREMIUM KPI CARDS ======================
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📋 Total Properties", total)
        c2.metric("✅ Completion Rate", f"{completion_rate}%", 
                  delta=f"{completed} completed")
        c3.metric("❌ Overdue", overdue, 
                  help="Past due date & not marked complete")
        c4.metric("👷 Active Crews", active_crews)

        st.markdown("---")

        # ====================== INTERACTIVE PIE CHART ======================
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

        # ====================== SMART INSIGHTS ======================
        st.markdown("### 💡 Executive Insights")
        
        insight_list = []
        if overdue > 0:
            insight_list.append(f"🚨 **{overdue} properties are overdue** — immediate action needed.")
        if pending >= 2:
            insight_list.append(f"⏳ **{pending} bids/activations pending** — follow up today.")
        
        top_crew = df_left["CREW NAME"].value_counts().idxmax() if not df_left["CREW NAME"].dropna().empty else "N/A"
        top_count = df_left["CREW NAME"].value_counts().max()
        insight_list.append(f"🏆 **{top_crew}** is leading with **{top_count}** assignments.")

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

        # ====================== URGENT TABLE ======================
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
