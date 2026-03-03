# app.py - Enhanced Property Preservation Dashboard
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
import plotly.graph_objects as go
from datetime import datetime, timedelta
import datetime as dt_module
from streamlit_option_menu import option_menu
from streamlit_card import card

# ----------------------------------------------------------------------
# Page Configuration - MUST BE FIRST STREAMLIT COMMAND
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Property Preservation Pro Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------
# Custom CSS for Enhanced Styling
# ----------------------------------------------------------------------
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    
    .kpi-card.completed {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .kpi-card.overdue {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    }
    
    .kpi-card.pending {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .kpi-card.progress {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* Property card styling */
    .property-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid;
        transition: all 0.3s ease;
    }
    
    .property-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .property-card.overdue {
        border-left-color: #e74c3c;
        background: linear-gradient(90deg, #fff5f5 0%, #ffffff 100%);
    }
    
    .property-card.completed {
        border-left-color: #27ae60;
        background: linear-gradient(90deg, #f0fff4 0%, #ffffff 100%);
    }
    
    .property-card.in-progress {
        border-left-color: #f39c12;
        background: linear-gradient(90deg, #fffbeb 0%, #ffffff 100%);
    }
    
    .property-card.pending {
        border-left-color: #3498db;
        background: linear-gradient(90deg, #ebf8ff 0%, #ffffff 100%);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .status-badge.overdue {
        background: #fee;
        color: #c33;
    }
    
    .status-badge.completed {
        background: #efe;
        color: #3c3;
    }
    
    .status-badge.in-progress {
        background: #ffeaa7;
        color: #d68910;
    }
    
    .status-badge.pending {
        background: #d6eaf8;
        color: #2874a6;
    }
    
    /* Insight cards */
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 15px;
        color: white;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .insight-card:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Filter chips */
    .filter-chip {
        display: inline-block;
        padding: 8px 16px;
        margin: 5px;
        border-radius: 25px;
        background: #f0f0f0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .filter-chip:hover, .filter-chip.active {
        background: #667eea;
        color: white;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
    
    /* Animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Crew card */
    .crew-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .crew-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto 10px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Session State Initialization
# ----------------------------------------------------------------------
if 'selected_property' not in st.session_state:
    st.session_state.selected_property = None
if 'filter_status' not in st.session_state:
    st.session_state.filter_status = 'All'
if 'search_query' not in st.session_state:
    st.session_state.search_query = ''
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Dashboard'

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
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

def parse_date(x):
    """Parse date with multiple formats."""
    if pd.isna(x) or str(x).strip() == "":
        return pd.NaT
    x_str = str(x).strip()
    formats = ["%m/%d/%y", "%m/%d/%Y", "%d-%m-%y", "%d-%m-%Y", 
               "%Y-%m-%d", "%d/%m/%y", "%m-%d-%Y", "%m-%d-%y"]
    for fmt in formats:
        try:
            return pd.to_datetime(x_str, format=fmt, errors="raise")
        except:
            pass
    return pd.to_datetime(x_str, errors="coerce", dayfirst=True)

def categorize_status(row):
    """Categorize property status with enhanced logic."""
    s = str(row.get("Status 1", "")).lower().strip()
    due = row.get("Due date")
    
    # Completed status
    if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received", "approved"]):
        return "✅ Completed"
    
    # Check due date for overdue
    if pd.notna(due) and isinstance(due, (pd.Timestamp, datetime)):
        today_dt = pd.Timestamp.today().normalize()
        if due < today_dt:
            return "❌ Overdue"
    
    # In Progress status
    if any(word in s for word in ["ongoing", "progress", "will be", "try to", "today", "tomorrow", 
                                   "friday", "monday", "tuesday", "wednesday", "thursday", "saturday", 
                                   "sunday", "working", "scheduled", "assigned", "in progress"]):
        return "🔄 In Progress"
    
    # Pending status
    if any(word in s for word in ["waiting", "pending", "bid", "pricing", "activation", "quote", 
                                   "estimate", "review", "approval needed"]):
        return "⏳ Pending / Bid"
    
    return "📌 Other"

def get_status_color(status):
    """Get color for status."""
    colors = {
        "✅ Completed": "#27ae60",
        "❌ Overdue": "#e74c3c",
        "🔄 In Progress": "#f39c12",
        "⏳ Pending / Bid": "#3498db",
        "📌 Other": "#7f8c8d"
    }
    return colors.get(status, "#7f8c8d")

def get_days_until_due(due_date):
    """Calculate days until due date."""
    if pd.isna(due_date):
        return None
    today = pd.Timestamp.today().normalize()
    due = pd.Timestamp(due_date).normalize()
    return (due - today).days

# ----------------------------------------------------------------------
# Data Loading Functions
# ----------------------------------------------------------------------
SHEET_ID = "1AxNmdkDGxYhi0-3-bZGdng-hT1KzxHqpgn_82eqglYg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
CSV_URL_UPDATES = "https://docs.google.com/spreadsheets/d/1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY/gviz/tq?tqx=out:csv&gid=160282702"

@st.cache_data(ttl=180)
def load_property_sheet(url):
    df = pd.read_csv(url)
    return df

@st.cache_data(ttl=180)
def load_updates():
    return pd.read_csv(CSV_URL_UPDATES)

# ----------------------------------------------------------------------
# Sidebar Navigation
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: white; margin: 0;">🏠 CPP Pro</h2>
        <p style="color: rgba(255,255,255,0.7); margin: 5px 0;">Property Preservation</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Properties", "Crew Analytics", "Calendar", "Map View", "Reports"],
        icons=["speedometer2", "houses", "people", "calendar3", "geo-alt", "file-earmark-text"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "white", "font-size": "18px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "padding": "15px 20px",
                "margin": "5px 10px",
                "border-radius": "10px",
                "color": "rgba(255,255,255,0.8)",
            },
            "nav-link-selected": {
                "background-color": "rgba(255,255,255,0.2)",
                "color": "white",
                "font-weight": "bold",
            },
        }
    )
    
    st.session_state.active_tab = selected
    
    st.markdown("---")
    
    # Quick Filters
    st.markdown("### 🔍 Quick Filters")
    filter_options = ["All", "Overdue", "In Progress", "Pending", "Completed"]
    selected_filter = st.selectbox("Status Filter", filter_options, 
                                   index=filter_options.index(st.session_state.filter_status))
    st.session_state.filter_status = selected_filter
    
    # Search
    search = st.text_input("🔎 Search Property", st.session_state.search_query)
    st.session_state.search_query = search
    
    st.markdown("---")
    
    # Live indicator
    st.markdown("""
    <div style="background: rgba(46, 204, 113, 0.2); padding: 10px; border-radius: 8px; text-align: center;">
        <span style="color: #2ecc71; font-weight: bold;">● Live</span>
        <span style="color: rgba(255,255,255,0.7); font-size: 12px;"><br>Auto-refresh every 3 min</span>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Load Data
# ----------------------------------------------------------------------
try:
    df_properties = load_property_sheet(CSV_URL)
    data_loaded = True
except Exception as e:
    st.error(f"❌ Failed to load property data: {e}")
    df_properties = pd.DataFrame(columns=["W/O Number", "address", "latitude", "longitude", "status", "vendor"])
    data_loaded = False

try:
    df_updates = load_updates()
    updates_loaded = True
except Exception as e:
    st.error(f"❌ Failed to load updates: {e}")
    df_updates = pd.DataFrame(columns=["Property", "Details", "CREW NAME", "Due date", "Status 1", "Reason"])
    updates_loaded = False

# Process property data
df_properties, prop_col_map = normalize_cols(df_properties)
if "latitude" in df_properties.columns and "longitude" in df_properties.columns:
    df_properties["latitude"] = pd.to_numeric(df_properties["latitude"], errors="coerce")
    df_properties["longitude"] = pd.to_numeric(df_properties["longitude"], errors="coerce")
    df_properties = df_properties.dropna(subset=["latitude", "longitude"])

# Process updates data
df_updates.columns = [c.strip() for c in df_updates.columns]
if "Due date" in df_updates.columns:
    df_updates["Due date"] = df_updates["Due date"].apply(parse_date)

# Categorize and add computed columns
df_updates["Category"] = df_updates.apply(categorize_status, axis=1)
df_updates["Days Until Due"] = df_updates["Due date"].apply(get_days_until_due)

# ----------------------------------------------------------------------
# DASHBOARD VIEW
# ----------------------------------------------------------------------
if st.session_state.active_tab == "Dashboard":
    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="margin: 0; font-size: 2.5em;">🏠 Property Preservation Dashboard</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">
            Real-time insights and property management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not updates_loaded:
        st.warning("⚠️ Unable to load data. Please check your connection and sheet permissions.")
    else:
        # Calculate KPIs
        total = len(df_updates)
        completed = (df_updates["Category"] == "✅ Completed").sum()
        overdue = (df_updates["Category"] == "❌ Overdue").sum()
        in_progress = (df_updates["Category"] == "🔄 In Progress").sum()
        pending = (df_updates["Category"] == "⏳ Pending / Bid").sum()
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        active_crews = df_updates["CREW NAME"].dropna().nunique()
        
        # KPI Cards Row
        st.markdown("### 📊 Key Performance Indicators")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card" onclick="window.location.href='?filter=All'">
                <h3 style="margin: 0; font-size: 2em;">{total}</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Total Properties</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card completed">
                <h3 style="margin: 0; font-size: 2em;">{completed}</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Completed ({completion_rate}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-card overdue pulse">
                <h3 style="margin: 0; font-size: 2em;">{overdue}</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">⚠️ Overdue</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-card progress">
                <h3 style="margin: 0; font-size: 2em;">{in_progress}</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">In Progress</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="kpi-card pending">
                <h3 style="margin: 0; font-size: 2em;">{active_crews}</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Active Crews</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Main Content Area
        left_col, right_col = st.columns([6, 4])
        
        with left_col:
            # Status Breakdown Chart
            st.markdown("### 📈 Status Distribution")
            
            status_counts = df_updates["Category"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig = px.pie(
                status_counts,
                names="Status",
                values="Count",
                color="Status",
                color_discrete_map={
                    "✅ Completed": "#27ae60",
                    "❌ Overdue": "#e74c3c",
                    "🔄 In Progress": "#f39c12",
                    "⏳ Pending / Bid": "#3498db",
                    "📌 Other": "#7f8c8d"
                },
                hole=0.4
            )
            fig.update_traces(
                textinfo="percent+label",
                textfont_size=12,
                pull=[0.05 if s == "❌ Overdue" else 0 for s in status_counts["Status"]]
            )
            fig.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Weekly Trend (simulated based on due dates)
            st.markdown("### 📅 Weekly Workload")
            today = pd.Timestamp.today().normalize()
            week_data = []
            for i in range(7):
                day = today + timedelta(days=i)
                day_due = df_updates[
                    (df_updates["Due date"].dt.normalize() == day) &
                    (df_updates["Category"] != "✅ Completed")
                ]
                week_data.append({
                    "Day": day.strftime("%a %d"),
                    "Due": len(day_due),
                    "Overdue": len(day_due[day_due["Category"] == "❌ Overdue"])
                })
            
            week_df = pd.DataFrame(week_data)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=week_df["Day"],
                y=week_df["Due"],
                name="Due",
                marker_color="#3498db"
            ))
            fig2.add_trace(go.Bar(
                x=week_df["Day"],
                y=week_df["Overdue"],
                name="Overdue",
                marker_color="#e74c3c"
            ))
            fig2.update_layout(
                barmode="stack",
                height=250,
                margin=dict(t=20, b=40, l=40, r=20),
                showlegend=True
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        with right_col:
            # Clickable Insights
            st.markdown("### 💡 Clickable Insights")
            
            today = pd.Timestamp.today()
            
            # Overdue Insight
            if overdue > 0:
                with st.expander(f"🚨 {overdue} Properties Overdue", expanded=True):
                    overdue_props = df_updates[df_updates["Category"] == "❌ Overdue"][["Property", "CREW NAME", "Due date"]].head(5)
                    for _, row in overdue_props.iterrows():
                        days_past = (today - row["Due date"]).days if pd.notna(row["Due date"]) else "N/A"
                        st.markdown(f"""
                        <div class="property-card overdue" style="padding: 8px; font-size: 12px;">
                            <b>{row['Property']}</b><br>
                            <small>👷 {row['CREW NAME']} | 📅 {days_past} days past due</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Due Soon Insight
            due_soon = df_updates[
                (pd.notna(df_updates["Due date"])) &
                (df_updates["Due date"] <= today + pd.Timedelta(days=3)) &
                (df_updates["Category"] != "✅ Completed") &
                (df_updates["Category"] != "❌ Overdue")
            ]
            if len(due_soon) > 0:
                with st.expander(f"⏰ {len(due_soon)} Due Within 3 Days", expanded=True):
                    for _, row in due_soon.head(5).iterrows():
                        days_left = get_days_until_due(row["Due date"])
                        st.markdown(f"""
                        <div class="property-card in-progress" style="padding: 8px; font-size: 12px;">
                            <b>{row['Property']}</b><br>
                            <small>👷 {row['CREW NAME']} | ⏰ {days_left} days left</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Top Crew Insight
            if not df_updates["CREW NAME"].dropna().empty:
                top_crew = df_updates["CREW NAME"].value_counts()
                if len(top_crew) > 0:
                    with st.expander("🏆 Top Performing Crews", expanded=True):
                        for crew, count in top_crew.head(3).items():
                            completed_by_crew = len(df_updates[
                                (df_updates["CREW NAME"] == crew) &
                                (df_updates["Category"] == "✅ Completed")
                            ])
                            st.markdown(f"""
                            <div class="crew-card" style="padding: 10px;">
                                <div class="crew-avatar" style="width: 40px; height: 40px; font-size: 16px;">
                                    {crew[:2].upper() if pd.notna(crew) else '??'}
                                </div>
                                <b>{crew}</b><br>
                                <small>{count} assignments | {completed_by_crew} completed</small>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Pending Bids Insight
            if pending > 0:
                with st.expander(f"💰 {pending} Pending Bids/Activations"):
                    st.info(f"{pending} properties awaiting bid approval or activation. Follow up with clients.")

# ----------------------------------------------------------------------
# PROPERTIES VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Properties":
    st.markdown("### 🏠 Property Management")
    
    # Filter logic
    filtered_df = df_updates.copy()
    
    if st.session_state.filter_status != "All":
        status_map = {
            "Overdue": "❌ Overdue",
            "In Progress": "🔄 In Progress",
            "Pending": "⏳ Pending / Bid",
            "Completed": "✅ Completed"
        }
        filtered_df = filtered_df[filtered_df["Category"] == status_map.get(st.session_state.filter_status, "")]
    
    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        filtered_df = filtered_df[
            filtered_df["Property"].str.lower().str.contains(query, na=False) |
            filtered_df["CREW NAME"].str.lower().str.contains(query, na=False) |
            filtered_df["Details"].str.lower().str.contains(query, na=False)
        ]
    
    # Property count
    st.markdown(f"**Showing {len(filtered_df)} properties**")
    
    # Display properties as cards
    for idx, row in filtered_df.iterrows():
        status_class = {
            "✅ Completed": "completed",
            "❌ Overdue": "overdue",
            "🔄 In Progress": "in-progress",
            "⏳ Pending / Bid": "pending",
            "📌 Other": "pending"
        }.get(row["Category"], "pending")
        
        status_badge = {
            "✅ Completed": "completed",
            "❌ Overdue": "overdue",
            "🔄 In Progress": "in-progress",
            "⏳ Pending / Bid": "pending",
            "📌 Other": "pending"
        }.get(row["Category"], "pending")
        
        days_info = ""
        if pd.notna(row["Due date"]):
            days = get_days_until_due(row["Due date"])
            if days is not None:
                if days < 0:
                    days_info = f"<span style='color: #e74c3c; font-weight: bold;'>⚠️ {abs(days)} days overdue</span>"
                elif days == 0:
                    days_info = "<span style='color: #f39c12; font-weight: bold;'>📅 Due today</span>"
                elif days <= 3:
                    days_info = f"<span style='color: #f39c12; font-weight: bold;'>⏰ {days} days left</span>"
                else:
                    days_info = f"📅 {days} days left"
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="property-card {status_class}">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h4 style="margin: 0 0 8px 0;">{row['Property']}</h4>
                        <p style="margin: 0; color: #666; font-size: 14px;">{row.get('Details', 'No details')}</p>
                        <div style="margin-top: 10px;">
                            <span class="status-badge {status_badge}">{row['Category']}</span>
                            <span style="margin-left: 10px; font-size: 13px;">👷 {row.get('CREW NAME', 'Unassigned')}</span>
                            <span style="margin-left: 10px; font-size: 13px;">{days_info}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📋 View", key=f"view_{idx}"):
                st.session_state.selected_property = row.to_dict()
                st.rerun()
        
        # Show details if selected
        if st.session_state.selected_property and st.session_state.selected_property.get("Property") == row["Property"]:
            with st.expander("📋 Property Details", expanded=True):
                detail_col1, detail_col2 = st.columns(2)
                with detail_col1:
                    st.write("**Property:**", row["Property"])
                    st.write("**Details:**", row.get("Details", "N/A"))
                    st.write("**Crew:**", row.get("CREW NAME", "Unassigned"))
                with detail_col2:
                    st.write("**Status:**", row["Category"])
                    st.write("**Due Date:**", row["Due date"].strftime("%b %d, %Y") if pd.notna(row["Due date"]) else "N/A")
                    st.write("**Reason:**", row.get("Reason", "N/A"))

# ----------------------------------------------------------------------
# CREW ANALYTICS VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Crew Analytics":
    st.markdown("### 👷 Crew Performance Analytics")
    
    if not df_updates["CREW NAME"].dropna().empty:
        crew_stats = []
        for crew in df_updates["CREW NAME"].dropna().unique():
            crew_data = df_updates[df_updates["CREW NAME"] == crew]
            total = len(crew_data)
            completed = len(crew_data[crew_data["Category"] == "✅ Completed"])
            overdue = len(crew_data[crew_data["Category"] == "❌ Overdue"])
            in_progress = len(crew_data[crew_data["Category"] == "🔄 In Progress"])
            completion_rate = round((completed / total * 100), 1) if total > 0 else 0
            
            crew_stats.append({
                "Crew": crew,
                "Total": total,
                "Completed": completed,
                "Overdue": overdue,
                "In Progress": in_progress,
                "Completion Rate": completion_rate
            })
        
        crew_df = pd.DataFrame(crew_stats).sort_values("Completion Rate", ascending=False)
        
        # Crew cards
        st.markdown("#### Crew Overview")
        crew_cols = st.columns(min(len(crew_df), 4))
        for idx, (_, crew_row) in enumerate(crew_df.head(4).iterrows()):
            with crew_cols[idx]:
                st.markdown(f"""
                <div class="crew-card">
                    <div class="crew-avatar">{crew_row['Crew'][:2].upper()}</div>
                    <h4 style="margin: 0;">{crew_row['Crew']}</h4>
                    <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #667eea;">{crew_row['Completion Rate']}%</p>
                    <p style="margin: 0; font-size: 12px; color: #666;">{crew_row['Completed']}/{crew_row['Total']} completed</p>
                    <div style="margin-top: 10px;">
                        <span style="color: #e74c3c; font-size: 12px;">● {crew_row['Overdue']} overdue</span>
                        <span style="margin-left: 10px; color: #f39c12; font-size: 12px;">● {crew_row['In Progress']} in progress</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Performance chart
        st.markdown("---")
        st.markdown("#### Completion Rate by Crew")
        
        fig = px.bar(
            crew_df,
            x="Crew",
            y="Completion Rate",
            color="Completion Rate",
            color_continuous_scale=["#e74c3c", "#f39c12", "#27ae60"],
            text="Completion Rate"
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed crew table
        st.markdown("#### Detailed Crew Statistics")
        st.dataframe(
            crew_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Crew": st.column_config.TextColumn("👷 Crew Name"),
                "Total": st.column_config.NumberColumn("📋 Total Jobs"),
                "Completed": st.column_config.NumberColumn("✅ Completed"),
                "Overdue": st.column_config.NumberColumn("❌ Overdue"),
                "In Progress": st.column_config.NumberColumn("🔄 In Progress"),
                "Completion Rate": st.column_config.ProgressColumn("📊 Completion %", min_value=0, max_value=100, format="%d%%")
            }
        )

# ----------------------------------------------------------------------
# CALENDAR VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Calendar":
    st.markdown("### 📅 Calendar View")
    
    today = pd.Timestamp.today().normalize()
    
    # Calendar filters
    cal_col1, cal_col2 = st.columns([1, 3])
    with cal_col1:
        view_range = st.selectbox("View Range", ["Next 7 Days", "Next 14 Days", "Next 30 Days", "This Month"])
    
    # Calculate date range
    if view_range == "Next 7 Days":
        end_date = today + timedelta(days=7)
    elif view_range == "Next 14 Days":
        end_date = today + timedelta(days=14)
    elif view_range == "Next 30 Days":
        end_date = today + timedelta(days=30)
    else:
        end_date = today + timedelta(days=30)
    
    # Get properties in date range
    calendar_props = df_updates[
        (pd.notna(df_updates["Due date"])) &
        (df_updates["Due date"] >= today) &
        (df_updates["Due date"] <= end_date) &
        (df_updates["Category"] != "✅ Completed")
    ].sort_values("Due date")
    
    st.markdown(f"**{len(calendar_props)} properties due in selected period**")
    
    # Group by date
    if not calendar_props.empty:
        for date in pd.date_range(today, end_date, freq='D'):
            day_props = calendar_props[calendar_props["Due date"].dt.normalize() == date]
            if not day_props.empty:
                is_today = date == today
                date_label = "📅 TODAY" if is_today else date.strftime("%A, %B %d")
                bg_color = "#fff3cd" if is_today else "white"
                
                st.markdown(f"""
                <div style="background: {bg_color}; padding: 10px 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid {'#f39c12' if is_today else '#3498db'};">
                    <h4 style="margin: 0;">{date_label}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for _, prop in day_props.iterrows():
                    status_class = {
                        "✅ Completed": "completed",
                        "❌ Overdue": "overdue",
                        "🔄 In Progress": "in-progress",
                        "⏳ Pending / Bid": "pending"
                    }.get(prop["Category"], "pending")
                    
                    st.markdown(f"""
                    <div class="property-card {status_class}" style="margin-left: 20px;">
                        <b>{prop['Property']}</b> | 👷 {prop.get('CREW NAME', 'Unassigned')} | {prop['Category']}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.success("🎉 No properties due in this period!")

# ----------------------------------------------------------------------
# MAP VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Map View":
    st.markdown("### 🗺️ Interactive Property Map")
    
    if not df_properties.empty and "latitude" in df_properties.columns:
        map_center = [df_properties["latitude"].mean(), df_properties["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=12, tiles=None)
    else:
        map_center = [24.0, 90.0]
        m = folium.Map(location=map_center, zoom_start=5, tiles=None)
    
    # Add tile layers
    folium.TileLayer("CartoDB positron", name="Light Map").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark Map").add_to(m)
    
    # Create marker clusters by status
    overdue_cluster = MarkerCluster(name="❌ Overdue").add_to(m)
    in_progress_cluster = MarkerCluster(name="🔄 In Progress").add_to(m)
    pending_cluster = MarkerCluster(name="⏳ Pending").add_to(m)
    completed_cluster = MarkerCluster(name="✅ Completed").add_to(m)
    
    # Color mapping
    status_colors = {
        "❌ Overdue": "#e74c3c",
        "🔄 In Progress": "#f39c12",
        "⏳ Pending / Bid": "#3498db",
        "✅ Completed": "#27ae60",
        "📌 Other": "#7f8c8d"
    }
    
    if not df_properties.empty:
        try:
            gdf = gpd.GeoDataFrame(
                df_properties,
                geometry=[Point(xy) for xy in zip(df_properties["longitude"], df_properties["latitude"])],
                crs="EPSG:4326"
            )
        except Exception:
            gdf = None
        
        if gdf is not None:
            for _, row in gdf.iterrows():
                wo = row.get(prop_col_map.get("w/o number", "W/O Number"), "")
                address = row.get(prop_col_map.get("address", "address"), "N/A")
                status = row.get(prop_col_map.get("status", "status"), "")
                vendor = row.get(prop_col_map.get("vendor", "vendor"), "N/A")
                
                # Determine color based on status
                color = "#3498db"
                for status_key, col in status_colors.items():
                    if status_key.lower() in str(status).lower():
                        color = col
                        break
                
                popup_html = f"""
                    <div style='font-size:13px; min-width: 200px;'>
                        <h4 style='margin: 0 0 10px 0; color: {color};'>🏠 Property</h4>
                        <b>W/O:</b> {wo}<br>
                        <b>Address:</b> {address}<br>
                        <b>Status:</b> <span style='color: {color};'>{status}</span><br>
                        <b>Vendor:</b> {vendor}
                    </div>
                """
                iframe = IFrame(popup_html, width=280, height=160)
                
                marker = folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    popup=folium.Popup(iframe, max_width=300),
                    weight=2
                )
                
                # Add to appropriate cluster
                if "overdue" in str(status).lower():
                    marker.add_to(overdue_cluster)
                elif "complete" in str(status).lower():
                    marker.add_to(completed_cluster)
                elif "progress" in str(status).lower():
                    marker.add_to(in_progress_cluster)
                else:
                    marker.add_to(pending_cluster)
            
            # Add search
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
        bottom: 40px; left: 40px; width: 200px; 
        background-color: rgba(255, 255, 255, 0.95); 
        border: 2px solid #ddd; 
        z-index: 9999; 
        font-size: 14px; 
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        font-family: Arial, sans-serif;
    ">
    <b style="font-size:16px; margin-bottom: 10px; display: block;">📍 Status Legend</b>
    <div style="margin: 8px 0;"><span style="color:#e74c3c; font-size:18px;">●</span> Overdue</div>
    <div style="margin: 8px 0;"><span style="color:#f39c12; font-size:18px;">●</span> In Progress</div>
    <div style="margin: 8px 0;"><span style="color:#3498db; font-size:18px;">●</span> Pending/Bid</div>
    <div style="margin: 8px 0;"><span style="color:#27ae60; font-size:18px;">●</span> Completed</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width=1200, height=700)

# ----------------------------------------------------------------------
# REPORTS VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Reports":
    st.markdown("### 📊 Reports & Analytics")
    
    report_type = st.selectbox("Select Report", [
        "Summary Report",
        "Overdue Properties Report",
        "Crew Performance Report",
        "Weekly Status Report"
    ])
    
    if report_type == "Summary Report":
        st.markdown("#### Executive Summary")
        
        total = len(df_updates)
        completed = (df_updates["Category"] == "✅ Completed").sum()
        overdue = (df_updates["Category"] == "❌ Overdue").sum()
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        summary_col1.metric("Total Properties", total)
        summary_col2.metric("Completion Rate", f"{completion_rate}%")
        summary_col3.metric("Overdue Properties", overdue, delta=f"-{overdue}" if overdue > 0 else None, delta_color="inverse")
        
        # Status breakdown
        st.markdown("---")
        st.markdown("#### Status Breakdown")
        status_df = df_updates["Category"].value_counts().reset_index()
        status_df.columns = ["Status", "Count"]
        st.bar_chart(status_df.set_index("Status"))
        
        # Export option
        st.markdown("---")
        csv = df_updates.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Report (CSV)",
            data=csv,
            file_name=f"property_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    elif report_type == "Overdue Properties Report":
        st.markdown("#### Overdue Properties")
        overdue_df = df_updates[df_updates["Category"] == "❌ Overdue"]
        
        if not overdue_df.empty:
            st.warning(f"⚠️ {len(overdue_df)} properties are overdue")
            
            # Add days overdue
            today = pd.Timestamp.today()
            overdue_df = overdue_df.copy()
            overdue_df["Days Overdue"] = overdue_df["Due date"].apply(
                lambda x: (today - x).days if pd.notna(x) else None
            )
            
            st.dataframe(
                overdue_df[["Property", "CREW NAME", "Due date", "Days Overdue", "Status 1", "Reason"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Export
            csv = overdue_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Overdue Report",
                data=csv,
                file_name=f"overdue_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.success("🎉 No overdue properties!")
    
    elif report_type == "Crew Performance Report":
        st.markdown("#### Crew Performance")
        
        if not df_updates["CREW NAME"].dropna().empty:
            crew_performance = []
            for crew in df_updates["CREW NAME"].dropna().unique():
                crew_data = df_updates[df_updates["CREW NAME"] == crew]
                total = len(crew_data)
                completed = len(crew_data[crew_data["Category"] == "✅ Completed"])
                overdue = len(crew_data[crew_data["Category"] == "❌ Overdue"])
                completion_rate = round((completed / total * 100), 1) if total > 0 else 0
                
                crew_performance.append({
                    "Crew": crew,
                    "Total Assignments": total,
                    "Completed": completed,
                    "Overdue": overdue,
                    "Completion Rate (%)": completion_rate
                })
            
            crew_perf_df = pd.DataFrame(crew_performance)
            st.dataframe(crew_perf_df, use_container_width=True, hide_index=True)
            
            # Export
            csv = crew_perf_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Crew Report",
                data=csv,
                file_name=f"crew_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666;">
    <p>🏠 Property Preservation Pro Dashboard | Live Data from Google Sheets</p>
    <p style="font-size: 12px;">Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
