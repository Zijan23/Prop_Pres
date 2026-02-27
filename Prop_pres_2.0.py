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
                for fmt in [
                    "%d/%m/%Y",
                    "%m/%d/%y",
                    "%m/%d/%Y",
                    "%d-%m-%y",
                    "%d-%m-%Y",
                    "%b %d, %Y",
                    "%Y-%m-%d",
                ]:
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
            today_dt = pd.Timestamp.today().normalize()

            # If status text shows completed
            if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received"]):
                return "✅ Completed"

            # ✅ Force mark overdue if due date is before today
            if pd.notna(due) and isinstance(due, (pd.Timestamp, datetime.datetime)):
                if due.normalize() < today_dt:
                    return "❌ Overdue"

            # Other progress / pending checks
            if any(word in s for word in ["ongoing", "progress", "will be", "try to", "today", "tomorrow", "friday", "monday"]):
                return "🔄 In Progress"

            if any(word in s for word in ["waiting", "pending", "bid", "pricing", "activation"]):
                return "⏳ Pending / Bid"

            return "📌 Other"

        df_left["Category"] = df_left.apply(categorize, axis=1)

        # Debug expander for problem addresses
        with st.expander("🔎 Debug: show TX/ID overdue check", expanded=False):
            suspects = df_left[
                df_left["Property"].astype(str).str.lower().str.contains("eagles nest", na=False)
                | df_left["Property"].astype(str).str.lower().str.contains("nebraska st", na=False)
            ].copy()

            if suspects.empty:
                st.write("No rows found matching those substrings.")
            else:
                st.dataframe(
                    suspects[["Property", "CREW NAME", "Due date", "Status 1", "Category"]],
                    use_container_width=True,
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
