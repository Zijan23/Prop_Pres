# app.py - CPP Dashboard (updated robust overdue detection + clean layout)
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
import datetime
import dateutil.parser  # ✅ added for flexible date parsing

# ----------------------------------------------------------------------

# --- Streamlit Page Config ---
st.set_page_config(page_title="Property Preservation Live Report", layout="wide")

st.title("🏠 CPP Dashboard")
st.subheader("🔍 Zoom in/out and click on any property to see its details")

# --------------------------
# Helper functions
# --------------------------
def normalize_cols(df):
    """Normalize and map lowercase columns."""
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
    df = pd.read_csv(url)
    return df

try:
    df = load_property_sheet(CSV_URL)
    st.success("✅ Live property data loaded from Google Sheets")
except Exception as e:
    st.error(f"❌ Failed to load property sheet: {e}")
    df = pd.DataFrame(columns=["W/O Number", "address", "latitude", "longitude", "status", "vendor"])

# Normalize and clean coordinates
df, prop_col_map = normalize_cols(df)
if "latitude" in df.columns and "longitude" in df.columns:
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

# --------------------------
# Load updates (status sheet)
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
# Page layout: Left panel (status) + Right panel (map)
# --------------------------
left_col, right_col = st.columns([4, 6])

# ---------- LEFT PANEL ----------
with left_col:
    st.markdown(
        "<h2 style='margin:0 0 8px 0;'>🏠 Property Preservation Status Board</h2>",
        unsafe_allow_html=True
    )
    st.caption("🔴 Live from updates tab (gid=160282702) • Refreshes ~every 3 min")

    if df_updates.empty:
        st.warning("No status data loaded yet. Check sheet permissions/export link.")
    else:
        df_left = df_updates.copy()
        today = pd.Timestamp.today().normalize()

        # ---- Date Parsing ----
        if "Due date" in df_left.columns:
            def parse_date(x):
                if pd.isna(x):
                    return pd.NaT
                s = str(x).strip()
                if s == "" or s.lower() in ["none", "nan", "n/a", "na"]:
                    return pd.NaT
                for fmt in ["%d/%m/%Y", "%m/%d/%y", "%m/%d/%Y", "%d-%m-%y", "%d-%m-%Y", "%b %d, %Y", "%Y-%m-%d"]:
                    try:
                        return pd.to_datetime(s, format=fmt, errors="raise")
                    except Exception:
                        pass
                try:
                    dt = dateutil.parser.parse(s, dayfirst=False, fuzzy=True)
                    return pd.to_datetime(dt).normalize()
                except Exception:
                    return pd.to_datetime(s, errors="coerce", dayfirst=True)

            df_left["Due date"] = df_left["Due date"].apply(parse_date)

        # ---- Categorize ----
        def categorize(row):
            s = str(row.get("Status 1", "")).lower().strip()
            due = row.get("Due date")

            # Explicit overdue markers in text
            if any(word in s for word in ["overdue", "late"]):
                return "❌ Overdue"

            if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received"]):
                return "✅ Completed"

            # Date-based overdue detection
            if pd.notna(due) and isinstance(due, (pd.Timestamp, datetime.datetime)):
                if due.normalize() < today:
                    return "❌ Overdue"

            if any(word in s for word in ["ongoing", "progress", "will be", "try to", "today", "tomorrow", "friday", "monday"]):
                return "🔄 In Progress"

            if any(word in s for word in ["waiting", "pending", "bid", "pricing", "activation"]):
                return "⏳ Pending / Bid"

            return "📌 Other"

        df_left["Category"] = df_left.apply(categorize, axis=1)

        # Debug expander for problem addresses
        with st.expander("🔎 Debug: show TX/ID overdue check", expanded=False):
            suspects = df_left[
                df_left["Property"].astype(str).str.lower().str.contains("eagles nest", na=False) |
                df_left["Property"].astype(str).str.lower().str.contains("nebraska st", na=False)
            ].copy()
            if suspects.empty:
                st.write("No rows found matching those substrings.")
            else:
                st.dataframe(
                    suspects[["Property", "CREW NAME", "Due date", "Status 1", "Category"]],
                    use_container_width=True
                )

        # ---- KPIs ----
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

        # ---- Status Breakdown Chart ----
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

        st.markdown("---")

        # ====================== SMART INSIGHTS ======================
        st.markdown("### 💡 Executive Insights")

        overdue_df = df_left[df_left["Category"] == "❌ Overdue"].copy()
        pending_df = df_left[df_left["Category"] == "⏳ Pending / Bid"].copy()
        due_soon_df = df_left[
            (pd.notna(df_left["Due date"])) &
            (df_left["Due date"] <= today + pd.Timedelta(days=7)) &
            (df_left["Category"] != "✅ Completed")
        ].copy()

        def show_filtered_table(title, filtered_df, key_prefix):
            if filtered_df.empty:
                st.caption("No matching properties.")
                return
            if "Due date" in filtered_df.columns:
                filtered_df["Due date"] = filtered_df["Due date"].dt.strftime("%b %d, %Y")
            st.dataframe(
                filtered_df[["Property", "CREW NAME", "Due date", "Status 1"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Property": "🏠 Property / Address",
                    "CREW NAME": "👷 Crew",
                    "Due date": "📅 Due",
                    "Status 1": "Status"
                },
                key=f"{key_prefix}_table"
            )

        with st.expander(f"🚨 {len(overdue_df)} properties are overdue — immediate action needed", expanded=len(overdue_df) > 0):
            show_filtered_table("Overdue Properties", overdue_df, "overdue")

        with st.expander(f"⏳ {len(pending_df)} bids/activations pending — follow up today", expanded=len(pending_df) >= 2):
            show_filtered_table("Pending / Bid Properties", pending_df, "pending")

        top_crew = df_left["CREW NAME"].value_counts().idxmax() if not df_left["CREW NAME"].dropna().empty else "N/A"
        top_count = df_left["CREW NAME"].value_counts().max() if not df_left["CREW NAME"].dropna().empty else 0
        st.info(f"🏆 **{top_crew}** is leading with **{top_count}** assignments.")

        with st.expander(f"📅 {len(due_soon_df)} properties due within 7 days", expanded=len(due_soon_df) > 0):
            show_filtered_table("Due Soon Properties", due_soon_df, "due_soon")

        # ---- Urgent Items ----
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

# ---------- RIGHT PANEL ----------
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

    if not df.empty:
        try:
            gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])], crs="EPSG:4326")
        except Exception:
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
# 📋 Detailed Property Updates Section (below the map)
# --------------------------
st.markdown("---")
st.markdown("## 🧾 Latest Property Updates")

if not df_updates.empty:
    df_updates.columns = [c.strip() for c in df_updates.columns]
    if "Due date" in df_updates.columns:
        try:
            df_updates["Due date"] = pd.to_datetime(df_updates["Due date"], errors="coerce")
            df_updates = df_updates.sort_values("Due date", ascending=True)
        except Exception:
            pass

    with st.container():
        st.markdown(
            """
            <div style="max-height:500px; overflow-y:auto; padding-right:10px;">
            """,
            unsafe_allow_html=True
        )

        for _, row in df_updates.iterrows():
            prop = row.get("Property", "")
            details = row.get("Details", "")
            crew = row.get("CREW NAME", "")
            due = row.get("Due date", "")
            status = row.get("Status 1", "")
            reason = row.get("Reason", "")

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
                <div style="background-color:{color}15; border-left:4px solid {color};
                            padding:10px; border-radius:6px; margin-bottom:8px;">
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

