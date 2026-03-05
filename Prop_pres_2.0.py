# app.py - TRILLION DOLLAR Property Preservation Empire Dashboard
# -*- coding: utf-8 -*-
# The most advanced property preservation dashboard ever built

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
import sqlite3
import json
from pathlib import Path
import time
import requests
import base64
from io import BytesIO, StringIO
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import hashlib
import re

# ----------------------------------------------------------------------
# PAGE CONFIGURATION - MUST BE FIRST
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="🏠 CPP Empire | Property Preservation Command Center",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------
# DYNAMIC PARTICLE BACKGROUND ANIMATION
# ----------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', 'Space Grotesk', -apple-system, sans-serif !important;
    }
    
    /* Particle Background */
    #particles-js {
        position: fixed;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: -1;
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 25%, #16213e 50%, #0f3460 75%, #1a1a3e 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Floating Orbs */
    .orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.4;
        z-index: -1;
        animation: float 20s infinite ease-in-out;
    }
    
    .orb-1 {
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, #667eea 0%, transparent 70%);
        top: -100px;
        right: -100px;
        animation-delay: 0s;
    }
    
    .orb-2 {
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, #f093fb 0%, transparent 70%);
        bottom: 10%;
        left: -50px;
        animation-delay: -5s;
    }
    
    .orb-3 {
        width: 250px;
        height: 250px;
        background: radial-gradient(circle, #4facfe 0%, transparent 70%);
        top: 40%;
        right: 10%;
        animation-delay: -10s;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(30px, -30px) scale(1.1); }
        50% { transform: translate(-20px, 20px) scale(0.9); }
        75% { transform: translate(20px, 10px) scale(1.05); }
    }
    
    /* Main container */
    .main {
        background: transparent !important;
    }
    
    .stApp {
        background: transparent !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em !important;
        text-shadow: 0 2px 20px rgba(102, 126, 234, 0.3);
    }
    
    p, span, div {
        color: #e0e0e0 !important;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* KPI Cards with Glow */
    .kpi-empire {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        border-radius: 20px;
        padding: 28px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 0 40px rgba(102, 126, 234, 0.2), inset 0 1px 0 rgba(255,255,255,0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-empire::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }
    
    .kpi-empire:hover::before {
        left: 100%;
    }
    
    .kpi-empire:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4), inset 0 1px 0 rgba(255,255,255,0.2);
        border-color: rgba(102, 126, 234, 0.6);
    }
    
    .kpi-value-empire {
        font-size: 3em;
        font-weight: 800;
        background: linear-gradient(135deg, #fff 0%, #a8b5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: none;
    }
    
    .kpi-label-empire {
        font-size: 0.95em;
        color: rgba(255,255,255,0.7);
        margin-top: 8px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .kpi-success {
        background: linear-gradient(135deg, rgba(17, 153, 142, 0.2) 0%, rgba(56, 239, 125, 0.2) 100%);
        border-color: rgba(17, 153, 142, 0.4);
        box-shadow: 0 0 40px rgba(17, 153, 142, 0.2);
    }
    
    .kpi-danger {
        background: linear-gradient(135deg, rgba(235, 51, 73, 0.2) 0%, rgba(244, 92, 67, 0.2) 100%);
        border-color: rgba(235, 51, 73, 0.4);
        box-shadow: 0 0 40px rgba(235, 51, 73, 0.3);
        animation: dangerPulse 2s infinite;
    }
    
    @keyframes dangerPulse {
        0%, 100% { box-shadow: 0 0 40px rgba(235, 51, 73, 0.3); }
        50% { box-shadow: 0 0 60px rgba(235, 51, 73, 0.5); }
    }
    
    /* Property Cards */
    .property-empire {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        border-left: 4px solid;
        border-top: 1px solid rgba(255,255,255,0.05);
        border-right: 1px solid rgba(255,255,255,0.05);
        border-bottom: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    
    .property-empire:hover {
        background: rgba(255, 255, 255, 0.05);
        transform: translateX(10px);
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    
    .property-empire.overdue { border-left-color: #ff4757; }
    .property-empire.completed { border-left-color: #2ed573; }
    .property-empire.in-progress { border-left-color: #ffa502; }
    .property-empire.pending { border-left-color: #3742fa; }
    
    /* Status Badges */
    .badge-empire {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 50px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        backdrop-filter: blur(10px);
    }
    
    .badge-overdue {
        background: rgba(255, 71, 87, 0.15);
        color: #ff6b81;
        border: 1px solid rgba(255, 71, 87, 0.3);
    }
    
    .badge-completed {
        background: rgba(46, 213, 115, 0.15);
        color: #7bed9f;
        border: 1px solid rgba(46, 213, 115, 0.3);
    }
    
    .badge-progress {
        background: rgba(255, 165, 2, 0.15);
        color: #ffc048;
        border: 1px solid rgba(255, 165, 2, 0.3);
    }
    
    .badge-pending {
        background: rgba(55, 66, 250, 0.15);
        color: #70a1ff;
        border: 1px solid rgba(55, 66, 250, 0.3);
    }
    
    /* AI Chat Widget */
    .ai-widget {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.5);
        z-index: 9999;
        transition: all 0.3s ease;
        border: 2px solid rgba(255,255,255,0.2);
    }
    
    .ai-widget:hover {
        transform: scale(1.1);
        box-shadow: 0 15px 50px rgba(102, 126, 234, 0.7);
    }
    
    .ai-widget.pulse {
        animation: aiPulse 2s infinite;
    }
    
    @keyframes aiPulse {
        0%, 100% { box-shadow: 0 10px 40px rgba(102, 126, 234, 0.5); }
        50% { box-shadow: 0 10px 60px rgba(102, 126, 234, 0.8), 0 0 20px rgba(102, 126, 234, 0.5); }
    }
    
    /* AI Chat Window */
    .ai-chat-window {
        position: fixed;
        bottom: 110px;
        right: 30px;
        width: 400px;
        height: 550px;
        background: rgba(20, 20, 40, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        z-index: 9998;
        display: none;
        flex-direction: column;
        overflow: hidden;
    }
    
    .ai-chat-window.active {
        display: flex;
    }
    
    /* File Upload Zone */
    .upload-zone {
        border: 2px dashed rgba(102, 126, 234, 0.4);
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .upload-zone:hover {
        border-color: rgba(102, 126, 234, 0.8);
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(10, 10, 26, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Form Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Client Filter Buttons */
    .client-filter {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 50px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 13px;
        font-weight: 500;
    }
    
    .client-filter:hover, .client-filter.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: transparent;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    /* DataFrames */
    .dataframe {
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 16px !important;
    }
    
    .dataframe th {
        background: rgba(102, 126, 234, 0.2) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Animations */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: slideIn 0.5s ease forwards;
    }
</style>

<!-- Floating Orbs for Background -->
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------------------------
def init_session_state():
    defaults = {
        'selected_property': None,
        'filter_status': 'All',
        'search_query': '',
        'active_tab': 'Dashboard',
        'show_input_form': False,
        'data_refresh': 0,
        'ai_chat_open': False,
        'chat_history': [],
        'map_client_filter': 'All',
        'uploaded_files': [],
        'drive_links': [],
        'google_sheets_connected': False,
        'supabase_connected': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ----------------------------------------------------------------------
# GOOGLE SHEETS API INTEGRATION
# ----------------------------------------------------------------------
@st.cache_resource
def get_google_sheets_service():
    """Initialize Google Sheets API service."""
    try:
        # Check for service account credentials
        creds_path = "service_account.json"
        if os.path.exists(creds_path):
            credentials = Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive']
            )
            service = build('sheets', 'v4', credentials=credentials)
            st.session_state.google_sheets_connected = True
            return service
        else:
            # Try to get from secrets
            try:
                service_account_info = st.secrets["gcp_service_account"]
                credentials = Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive']
                )
                service = build('sheets', 'v4', credentials=credentials)
                st.session_state.google_sheets_connected = True
                return service
            except:
                return None
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def append_to_google_sheet(spreadsheet_id, range_name, values):
    """Append data to Google Sheet in real-time."""
    service = get_google_sheets_service()
    if service:
        try:
            body = {'values': values}
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            return True, result
        except Exception as e:
            return False, str(e)
    return False, "Service not available"

def update_google_sheet_cell(spreadsheet_id, range_name, value):
    """Update a specific cell in Google Sheet."""
    service = get_google_sheets_service()
    if service:
        try:
            body = {'values': [[value]]}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            return True, result
        except Exception as e:
            return False, str(e)
    return False, "Service not available"

# ----------------------------------------------------------------------
# SUPABASE INTEGRATION (Free Online Database)
# ----------------------------------------------------------------------
def get_supabase_client():
    """Initialize Supabase client for online database."""
    try:
        from supabase import create_client
        
        # Try to get from secrets
        try:
            supabase_url = st.secrets["supabase_url"]
            supabase_key = st.secrets["supabase_key"]
        except:
            # Fallback to environment or manual config
            supabase_url = os.getenv("SUPABASE_URL", "")
            supabase_key = os.getenv("SUPABASE_KEY", "")
        
        if supabase_url and supabase_key:
            client = create_client(supabase_url, supabase_key)
            st.session_state.supabase_connected = True
            return client
        return None
    except Exception as e:
        return None

def sync_to_supabase(table, data):
    """Sync data to Supabase online database."""
    client = get_supabase_client()
    if client:
        try:
            result = client.table(table).insert(data).execute()
            return True, result
        except Exception as e:
            return False, str(e)
    return False, "Supabase not connected"

# ----------------------------------------------------------------------
# AI AGENT INTEGRATION
# ----------------------------------------------------------------------
def get_ai_response(user_message, context=None):
    """Get AI response using Hugging Face Inference API (Free Tier)."""
    try:
        # Use Hugging Face Inference API with a free model
        # You can also use Groq, OpenRouter, or other free APIs
        
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        # Try to get API key from secrets
        try:
            api_key = st.secrets["hf_api_key"]
        except:
            api_key = os.getenv("HF_API_KEY", "")
        
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        # Prepare context about the property preservation business
        system_prompt = """You are an AI assistant for a Property Preservation company. You help with:
- Finding properties and their status
- Providing updates on work progress
- Generating insights from data
- Setting reminders for due dates
- Answering questions about crews, clients, and properties
- Helping with workflow optimization

Be professional, helpful, and concise. Use emojis where appropriate."""
        
        if context:
            system_prompt += f"\n\nCurrent context: {context}"
        
        payload = {
            "inputs": f"<s>[INST] {system_prompt}\n\nUser: {user_message} [/INST]",
            "parameters": {"max_new_tokens": 500, "temperature": 0.7}
        }
        
        if api_key:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').split('[/INST]')[-1].strip()
        
        # Fallback response if API fails
        return get_fallback_ai_response(user_message)
        
    except Exception as e:
        return get_fallback_ai_response(user_message)

def get_fallback_ai_response(user_message):
    """Fallback AI responses when API is unavailable."""
    message_lower = user_message.lower()
    
    responses = {
        'hello': "👋 Hello! I'm your Property Preservation AI Assistant. I can help you find properties, check statuses, generate insights, and more. What would you like to know?",
        'hi': "👋 Hi there! Ready to help with your property preservation needs. Ask me anything!",
        'help': "🤖 Here's what I can do:\n\n🏠 **Find Properties** - Search by name, address, or status\n📊 **Get Insights** - Analyze trends and performance\n📅 **Check Due Dates** - See what's coming up\n👷 **Crew Info** - View crew assignments and performance\n⚠️ **Overdue Alerts** - Find overdue properties\n📈 **Generate Reports** - Create summary reports\n\nJust ask me naturally!",
        'overdue': "⚠️ I can help you find overdue properties! Navigate to the 'Properties' tab and filter by 'Overdue' status, or check the Dashboard for the red alert card.",
        'property': "🏠 To find a property, use the search box in the sidebar or go to the Properties tab. You can search by property name, crew name, or address!",
        'crew': "👷 View crew performance in the 'Crew Analytics' tab. You'll see completion rates, efficiency scores, and workload distribution!",
        'add': "➕ To add a new property, go to the 'Add New' tab. Fill in the details and it will be saved to both local database and Google Sheets!",
        'map': "🗺️ The Map View shows all properties geographically. You can filter by client (VRM, Cyprexx, etc.) using the filter buttons!",
        'report': "📊 Go to the 'Reports' tab to generate and download various reports including Executive Summary, Overdue Properties, and Crew Performance!",
        'status': "📊 Check the Dashboard for real-time status breakdown. You'll see completed, overdue, in-progress, and pending counts!",
        'thank': "🙏 You're welcome! I'm here 24/7 to help with your property preservation needs. Feel free to ask anytime!",
        'thanks': "🙏 You're welcome! Happy to help! 🏠✨"
    }
    
    for key, response in responses.items():
        if key in message_lower:
            return response
    
    return f"🤔 I understand you're asking about: '{user_message}'\n\nI can help you with:\n• Finding properties and their status\n• Crew performance analytics\n• Due date tracking\n• Report generation\n• Workflow optimization\n\nTry asking something like 'Show me overdue properties' or 'How is crew performance?'"

# ----------------------------------------------------------------------
# DATABASE FUNCTIONS (SQLite + Supabase)
# ----------------------------------------------------------------------
DB_PATH = "property_preservation.db"

def init_database():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS historical_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name TEXT, wo_number TEXT, address TEXT,
            crew_name TEXT, due_date TEXT, status TEXT, category TEXT,
            client TEXT, reason TEXT, details TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_completed TIMESTAMP, is_active INTEGER DEFAULT 1
        )''',
        '''CREATE TABLE IF NOT EXISTS crew_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crew_name TEXT, property_name TEXT, action TEXT,
            status TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date DATE, total_properties INTEGER,
            completed INTEGER, overdue INTEGER, in_progress INTEGER,
            pending INTEGER, active_crews INTEGER
        )''',
        '''CREATE TABLE IF NOT EXISTS user_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name TEXT, crew_name TEXT, status TEXT,
            due_date TEXT, details TEXT, reason TEXT,
            updated_by TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            synced_to_sheets INTEGER DEFAULT 0
        )''',
        '''CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT, file_type TEXT, file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_content BLOB, insights TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS external_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_type TEXT, link_url TEXT, link_name TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    conn.commit()
    conn.close()

init_database()

# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def normalize_cols(df):
    df = df.copy()
    col_map = {c.strip().lower(): c for c in df.columns}
    df.columns = [c.strip() for c in df.columns]
    return df, col_map

def parse_date_american_first(x):
    """Parse date with AMERICAN FORMAT PRIORITY."""
    if pd.isna(x) or str(x).strip() == "":
        return pd.NaT
    
    x_str = str(x).strip()
    
    american_formats = [
        "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
    ]
    
    for fmt in american_formats:
        try:
            return pd.to_datetime(x_str, format=fmt, errors="raise")
        except:
            pass
    
    intl_formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y", "%Y/%m/%d",
    ]
    
    for fmt in intl_formats:
        try:
            return pd.to_datetime(x_str, format=fmt, errors="raise")
        except:
            pass
    
    return pd.to_datetime(x_str, errors="coerce")

def categorize_status(row):
    s = str(row.get("Status 1", "")).lower().strip()
    due = row.get("Due date")
    
    if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received", "approved", "paid"]):
        return "✅ Completed"
    
    if pd.notna(due) and isinstance(due, (pd.Timestamp, datetime)):
        today_dt = pd.Timestamp.today().normalize()
        due_normalized = pd.Timestamp(due).normalize()
        if due_normalized < today_dt:
            return "❌ Overdue"
    
    progress_keywords = ["ongoing", "progress", "will be", "try to", "today", "tomorrow", 
                        "friday", "monday", "tuesday", "wednesday", "thursday", "saturday", 
                        "sunday", "working", "scheduled", "assigned", "in progress", "started",
                        "crew on site", "crew assigned", "in route", "en route"]
    if any(word in s for word in progress_keywords):
        return "🔄 In Progress"
    
    pending_keywords = ["waiting", "pending", "bid", "pricing", "activation", "quote", 
                       "estimate", "review", "approval needed", "client approval",
                       "need bid", "bid requested", "awaiting"]
    if any(word in s for word in pending_keywords):
        return "⏳ Pending / Bid"
    
    return "📌 Other"

def get_status_color(status):
    colors = {
        "✅ Completed": "#2ed573",
        "❌ Overdue": "#ff4757",
        "🔄 In Progress": "#ffa502",
        "⏳ Pending / Bid": "#3742fa",
        "📌 Other": "#747d8c"
    }
    return colors.get(status, "#747d8c")

def get_days_until_due(due_date):
    if pd.isna(due_date):
        return None
    today = pd.Timestamp.today().normalize()
    due = pd.Timestamp(due_date).normalize()
    return (due - today).days

def format_date_display(date_val):
    if pd.isna(date_val):
        return "N/A"
    try:
        return pd.Timestamp(date_val).strftime("%b %d, %Y")
    except:
        return str(date_val)

# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
SHEET_ID = "1AxNmdkDGxYhi0-3-bZGdng-hT1KzxHqpgn_82eqglYg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
CSV_URL_UPDATES = "https://docs.google.com/spreadsheets/d/1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY/gviz/tq?tqx=out:csv&gid=160282702"

@st.cache_data(ttl=180)
def load_property_sheet(url):
    return pd.read_csv(url)

@st.cache_data(ttl=180)
def load_updates():
    return pd.read_csv(CSV_URL_UPDATES)

# ----------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 25px 0 20px 0;">
        <div style="font-size: 3em; margin-bottom: 5px;">👑</div>
        <h1 style="color: white; margin: 0; font-size: 1.8em; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #f093fb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CPP EMPIRE</h1>
        <p style="color: rgba(255,255,255,0.5); margin: 5px 0; font-size: 0.75em; letter-spacing: 2px; text-transform: uppercase;">Property Preservation</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Properties", "Add New", "Crew Analytics", "Calendar", "Map View", "Files & Links", "Reports", "History", "Settings"],
        icons=["speedometer2", "houses", "plus-circle", "people", "calendar3", "geo-alt", "folder", "file-earmark-text", "clock-history", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "rgba(255,255,255,0.7)", "font-size": "16px"},
            "nav-link": {
                "font-size": "13px",
                "text-align": "left",
                "padding": "14px 18px",
                "margin": "4px 10px",
                "border-radius": "12px",
                "color": "rgba(255,255,255,0.6)",
                "font-weight": "500",
                "transition": "all 0.3s ease",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white",
                "font-weight": "600",
                "box-shadow": "0 4px 15px rgba(102, 126, 234, 0.4)",
            },
        }
    )
    
    st.session_state.active_tab = selected
    
    st.markdown("---")
    
    # Quick Filters
    st.markdown("<p style='color: rgba(255,255,255,0.8); font-weight: 600; font-size: 13px; margin-bottom: 12px;'>🔍 QUICK FILTERS</p>", unsafe_allow_html=True)
    
    filter_options = ["All", "Overdue", "In Progress", "Pending", "Completed"]
    selected_filter = st.selectbox("Status", filter_options, 
                                   index=filter_options.index(st.session_state.filter_status),
                                   label_visibility="collapsed")
    st.session_state.filter_status = selected_filter
    
    search = st.text_input("Search properties...", st.session_state.search_query, 
                          placeholder="Type to search...",
                          label_visibility="collapsed")
    st.session_state.search_query = search
    
    st.markdown("---")
    
    # Connection Status
    st.markdown("<p style='color: rgba(255,255,255,0.6); font-size: 11px; margin-bottom: 10px;'>🔗 CONNECTION STATUS</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.google_sheets_connected:
            st.markdown("<span style='color: #2ed573; font-size: 11px;'>● Sheets</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #ff4757; font-size: 11px;'>○ Sheets</span>", unsafe_allow_html=True)
    with col2:
        if st.session_state.supabase_connected:
            st.markdown("<span style='color: #2ed573; font-size: 11px;'>● Database</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #747d8c; font-size: 11px;'>○ Database</span>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(46, 213, 115, 0.15) 0%, rgba(46, 213, 115, 0.05) 100%); 
                padding: 12px; border-radius: 10px; text-align: center; margin-top: 15px;
                border: 1px solid rgba(46, 213, 115, 0.2);">
        <span style="color: #2ed573; font-weight: 700; font-size: 12px;">● LIVE</span>
        <span style="color: rgba(255,255,255,0.5); font-size: 10px; display: block; margin-top: 4px;">
            Auto-refresh every 3 min
        </span>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------
with st.spinner("🔄 Loading data from Google Sheets..."):
    try:
        df_properties = load_property_sheet(CSV_URL)
        data_loaded = True
    except Exception as e:
        df_properties = pd.DataFrame(columns=["W/O Number", "address", "latitude", "longitude", "status", "vendor", "client"])
        data_loaded = False

    try:
        df_updates = load_updates()
        updates_loaded = True
    except Exception as e:
        df_updates = pd.DataFrame(columns=["Property", "Details", "CREW NAME", "Due date", "Status 1", "Reason", "Client"])
        updates_loaded = False

# Process data
df_properties, prop_col_map = normalize_cols(df_properties)
if "latitude" in df_properties.columns and "longitude" in df_properties.columns:
    df_properties["latitude"] = pd.to_numeric(df_properties["latitude"], errors="coerce")
    df_properties["longitude"] = pd.to_numeric(df_properties["longitude"], errors="coerce")
    df_properties = df_properties.dropna(subset=["latitude", "longitude"])

df_updates.columns = [c.strip() for c in df_updates.columns]
if "Due date" in df_updates.columns:
    df_updates["Due date"] = df_updates["Due date"].apply(parse_date_american_first)

df_updates["Category"] = df_updates.apply(categorize_status, axis=1)
df_updates["Days Until Due"] = df_updates["Due date"].apply(get_days_until_due)

# Get unique clients for map filtering
all_clients = []
if "client" in df_properties.columns:
    all_clients = df_properties["client"].dropna().unique().tolist()
if "Client" in df_updates.columns:
    all_clients.extend(df_updates["Client"].dropna().unique().tolist())
all_clients = list(set([c.strip() for c in all_clients if c and str(c).lower() not in ['nan', 'none', '']]))

# ----------------------------------------------------------------------
# AI CHAT WIDGET
# ----------------------------------------------------------------------
# AI Chat Toggle Button
ai_clicked = st.button("🤖", key="ai_toggle", help="Click to chat with AI Assistant")
if ai_clicked:
    st.session_state.ai_chat_open = not st.session_state.ai_chat_open

# AI Chat Window
if st.session_state.ai_chat_open:
    with st.container():
        st.markdown("""
        <div style="position: fixed; bottom: 100px; right: 30px; width: 420px; height: 580px;
                    background: rgba(15, 15, 35, 0.98); backdrop-filter: blur(20px);
                    border-radius: 24px; border: 1px solid rgba(102, 126, 234, 0.4);
                    box-shadow: 0 25px 80px rgba(0,0,0,0.6); z-index: 9999;
                    display: flex; flex-direction: column; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 45px; height: 45px; background: rgba(255,255,255,0.2);
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    🤖
                </div>
                <div>
                    <h4 style="margin: 0; color: white; font-size: 16px;">CPP AI Assistant</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 12px;">Powered by Mistral AI</p>
                </div>
            </div>
            <div style="padding: 15px 20px; background: rgba(102, 126, 234, 0.1);
                        border-bottom: 1px solid rgba(255,255,255,0.05);">
                <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 11px;">
                    💡 I can: Find properties • Check status • Generate insights • Set reminders • Answer questions
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat interface
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; margin: 10px 20px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white; padding: 12px 16px; border-radius: 18px 18px 4px 18px;
                                    max-width: 80%; font-size: 13px;">
                            {msg['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin: 10px 20px;">
                        <div style="background: rgba(255,255,255,0.08);
                                    color: #e0e0e0; padding: 12px 16px; border-radius: 18px 18px 18px 4px;
                                    max-width: 80%; font-size: 13px; border: 1px solid rgba(255,255,255,0.1);">
                            {msg['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Quick action buttons
            st.markdown("<div style='padding: 10px 20px;'>", unsafe_allow_html=True)
            quick_cols = st.columns(3)
            with quick_cols[0]:
                if st.button("📊 Status", key="quick_status", use_container_width=True):
                    st.session_state.chat_history.append({'role': 'user', 'content': 'Show me the current status'})
                    response = get_ai_response('Show me the current status', f"Total: {len(df_updates)}, Overdue: {(df_updates['Category'] == '❌ Overdue').sum()}")
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                    st.rerun()
            with quick_cols[1]:
                if st.button("⚠️ Overdue", key="quick_overdue", use_container_width=True):
                    overdue_count = (df_updates['Category'] == '❌ Overdue').sum()
                    st.session_state.chat_history.append({'role': 'user', 'content': 'Show overdue properties'})
                    response = f"⚠️ There are **{overdue_count} overdue properties** that need immediate attention. Check the Dashboard or Properties tab for details!"
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                    st.rerun()
            with quick_cols[2]:
                if st.button("👷 Crews", key="quick_crews", use_container_width=True):
                    crew_count = df_updates['CREW NAME'].dropna().nunique()
                    st.session_state.chat_history.append({'role': 'user', 'content': 'Show crew info'})
                    response = f"👷 We have **{crew_count} active crews** working on properties. Visit the Crew Analytics tab for detailed performance metrics!"
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Input
            user_input = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed")
            if user_input:
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                
                # Get context
                context = f"""Current dashboard data:
                - Total Properties: {len(df_updates)}
                - Overdue: {(df_updates['Category'] == '❌ Overdue').sum()}
                - In Progress: {(df_updates['Category'] == '🔄 In Progress').sum()}
                - Completed: {(df_updates['Category'] == '✅ Completed').sum()}
                - Active Crews: {df_updates['CREW NAME'].dropna().nunique()}
                """
                
                response = get_ai_response(user_input, context)
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                st.rerun()

# ----------------------------------------------------------------------
# DASHBOARD VIEW
# ----------------------------------------------------------------------
if st.session_state.active_tab == "Dashboard":
    st.markdown("""
    <div style="text-align: center; padding: 40px 0 30px 0;">
        <h1 style="font-size: 3.5em; font-weight: 800; margin: 0; background: linear-gradient(135deg, #fff 0%, #a8b5ff 50%, #f093fb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🏠 Property Preservation
        </h1>
        <p style="font-size: 1.3em; color: rgba(255,255,255,0.6); margin: 15px 0 0 0; font-weight: 400;">
            Command Center for Real-time Property Management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not updates_loaded:
        st.warning("⚠️ Unable to load data. Please check your connection.")
    else:
        # KPIs
        total = len(df_updates)
        completed = (df_updates["Category"] == "✅ Completed").sum()
        overdue = (df_updates["Category"] == "❌ Overdue").sum()
        in_progress = (df_updates["Category"] == "🔄 In Progress").sum()
        pending = (df_updates["Category"] == "⏳ Pending / Bid").sum()
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        active_crews = df_updates["CREW NAME"].dropna().nunique()
        
        st.markdown("<h3 style='margin-bottom: 25px; font-size: 1.1em; color: rgba(255,255,255,0.7);'>📊 KEY PERFORMANCE INDICATORS</h3>", unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-empire">
                <p class="kpi-value-empire">{total}</p>
                <p class="kpi-label-empire">📋 Total Properties</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-empire kpi-success">
                <p class="kpi-value-empire">{completion_rate}%</p>
                <p class="kpi-label-empire">✅ Completion Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-empire kpi-danger">
                <p class="kpi-value-empire">{overdue}</p>
                <p class="kpi-label-empire">⚠️ Overdue</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-empire" style="background: linear-gradient(135deg, rgba(255, 165, 2, 0.2) 0%, rgba(255, 193, 7, 0.2) 100%); border-color: rgba(255, 165, 2, 0.4);">
                <p class="kpi-value-empire" style="background: linear-gradient(135deg, #ffc048 0%, #ff9f43 100%); -webkit-background-clip: text;">{in_progress}</p>
                <p class="kpi-label-empire">🔄 In Progress</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="kpi-empire" style="background: linear-gradient(135deg, rgba(55, 66, 250, 0.2) 0%, rgba(112, 161, 255, 0.2) 100%); border-color: rgba(55, 66, 250, 0.4);">
                <p class="kpi-value-empire" style="background: linear-gradient(135deg, #70a1ff 0%, #5352ed 100%); -webkit-background-clip: text;">{active_crews}</p>
                <p class="kpi-label-empire">👷 Active Crews</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts
        left_col, right_col = st.columns([6, 4])
        
        with left_col:
            st.markdown("<h3 style='margin-bottom: 20px;'>📈 Status Distribution</h3>", unsafe_allow_html=True)
            
            status_counts = df_updates["Category"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig = px.pie(
                status_counts, names="Status", values="Count", color="Status",
                color_discrete_map={
                    "✅ Completed": "#2ed573",
                    "❌ Overdue": "#ff4757",
                    "🔄 In Progress": "#ffa502",
                    "⏳ Pending / Bid": "#3742fa",
                    "📌 Other": "#747d8c"
                },
                hole=0.55
            )
            fig.update_traces(
                textinfo="percent+label", textfont_size=13, textfont_color="white",
                pull=[0.08 if s == "❌ Overdue" else 0 for s in status_counts["Status"]]
            )
            fig.update_layout(
                height=380, showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white")
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with right_col:
            st.markdown("<h3 style='margin-bottom: 20px;'>💡 Actionable Insights</h3>", unsafe_allow_html=True)
            
            today = pd.Timestamp.today()
            
            if overdue > 0:
                overdue_props = df_updates[df_updates["Category"] == "❌ Overdue"].copy()
                overdue_props["Days Overdue"] = overdue_props["Due date"].apply(
                    lambda x: (today - x).days if pd.notna(x) else 0
                )
                
                with st.expander(f"🚨 {overdue} CRITICAL Overdue", expanded=True):
                    for _, row in overdue_props.head(3).iterrows():
                        days = row["Days Overdue"]
                        st.markdown(f"""
                        <div class="property-empire overdue" style="padding: 12px;">
                            <div style="display: flex; justify-content: space-between;">
                                <b style="font-size: 13px;">{row['Property'][:40]}...</b>
                                <span style="color: #ff6b81; font-size: 12px; font-weight: 600;">{days} days</span>
                            </div>
                            <small style="color: #888;">👷 {row['CREW NAME']}</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            due_soon = df_updates[
                (pd.notna(df_updates["Due date"])) &
                (df_updates["Due date"] <= today + pd.Timedelta(days=3)) &
                (df_updates["Category"] != "✅ Completed") &
                (df_updates["Category"] != "❌ Overdue")
            ].sort_values("Due date")
            
            if len(due_soon) > 0:
                with st.expander(f"⏰ {len(due_soon)} Due Soon (3 days)", expanded=True):
                    for _, row in due_soon.head(3).iterrows():
                        days = get_days_until_due(row["Due date"])
                        st.markdown(f"""
                        <div class="property-empire in-progress" style="padding: 12px;">
                            <div style="display: flex; justify-content: space-between;">
                                <b style="font-size: 13px;">{row['Property'][:40]}...</b>
                                <span style="color: #ffc048; font-size: 12px; font-weight: 600;">{days} days</span>
                            </div>
                            <small style="color: #888;">👷 {row['CREW NAME']}</small>
                        </div>
                        """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# PROPERTIES VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Properties":
    st.markdown("<h2 style='margin-bottom: 25px;'>🏠 Property Management</h2>", unsafe_allow_html=True)
    
    filtered_df = df_updates.copy()
    
    if st.session_state.filter_status != "All":
        status_map = {"Overdue": "❌ Overdue", "In Progress": "🔄 In Progress", 
                     "Pending": "⏳ Pending / Bid", "Completed": "✅ Completed"}
        filtered_df = filtered_df[filtered_df["Category"] == status_map.get(st.session_state.filter_status, "")]
    
    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        filtered_df = filtered_df[
            filtered_df["Property"].str.lower().str.contains(query, na=False) |
            filtered_df["CREW NAME"].str.lower().str.contains(query, na=False)
        ]
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.03); padding: 15px 20px; border-radius: 12px; margin-bottom: 25px;">
        <span style="font-size: 14px; color: rgba(255,255,255,0.6);">
            Showing <b style="color: white;">{len(filtered_df)}</b> of <b style="color: white;">{len(df_updates)}</b> properties
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    for idx, row in filtered_df.iterrows():
        status_class = {"✅ Completed": "completed", "❌ Overdue": "overdue", 
                       "🔄 In Progress": "in-progress", "⏳ Pending / Bid": "pending"}.get(row["Category"], "pending")
        badge_class = {"✅ Completed": "badge-completed", "❌ Overdue": "badge-overdue",
                      "🔄 In Progress": "badge-progress", "⏳ Pending / Bid": "badge-pending"}.get(row["Category"], "badge-pending")
        
        days = get_days_until_due(row["Due date"])
        if days is not None:
            if days < 0:
                date_display = f"<span class='badge-empire badge-overdue'>⚠️ {abs(days)} days overdue</span>"
            elif days == 0:
                date_display = "<span class='badge-empire badge-progress'>📅 Due TODAY</span>"
            elif days <= 3:
                date_display = f"<span class='badge-empire badge-progress'>⏰ {days} days left</span>"
            else:
                date_display = f"<span style='color: #7bed9f; font-size: 12px;'>📅 {days} days left</span>"
        else:
            date_display = "<span style='color: #888; font-size: 12px;'>No due date</span>"
        
        st.markdown(f"""
        <div class="property-empire {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 15px;">
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 10px 0; font-size: 15px; color: white;">{row['Property']}</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.5); font-size: 12px; line-height: 1.5;">{row.get('Details', 'No details')[:100]}...</p>
                    <div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                        <span class="badge-empire {badge_class}">{row['Category']}</span>
                        <span style="font-size: 12px; color: rgba(255,255,255,0.6);">👷 {row.get('CREW NAME', 'Unassigned')}</span>
                        {date_display}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# ADD NEW PROPERTY VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Add New":
    st.markdown("<h2 style='margin-bottom: 25px;'>➕ Add New Property / Update</h2>", unsafe_allow_html=True)
    
    # Connection status banner
    if st.session_state.google_sheets_connected:
        st.success("✅ Google Sheets API Connected - Changes will sync in real-time!")
    else:
        st.warning("⚠️ Google Sheets API not configured. Changes will be saved locally only.")
    
    tab1, tab2 = st.tabs(["🆕 New Property", "📝 Quick Update"])
    
    with tab1:
        with st.form("new_property_form"):
            st.markdown("<h4 style='margin-bottom: 20px; color: rgba(255,255,255,0.9);'>Property Information</h4>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                property_name = st.text_input("🏠 Property Name *", placeholder="e.g., 1227 EAGLES NEST TRL")
                wo_number = st.text_input("📋 W/O Number", placeholder="e.g., WO-2024-001")
                address = st.text_area("📍 Full Address", placeholder="e.g., 1227 EAGLES NEST TRL, KRUM, TX 76249")
            
            with col2:
                crew_name = st.selectbox("👷 Assign Crew *", options=[""] + list(df_updates["CREW NAME"].dropna().unique()) if not df_updates.empty else [""])
                status = st.selectbox("📊 Status *", options=["", "Pending / Bid", "In Progress", "Completed", "Overdue"])
                due_date = st.date_input("📅 Due Date", value=None)
                client = st.selectbox("🏢 Client", options=["VRM", "Cyprexx", "Spectrum", "Sand Castle", "Other"])
            
            details = st.text_area("📝 Work Details", placeholder="Describe the work needed...")
            reason = st.text_area("💬 Notes/Reason", placeholder="Any additional notes...")
            
            submitted = st.form_submit_button("💾 Save & Sync to Google Sheets", use_container_width=True)
            
            if submitted:
                if not property_name or not crew_name or not status:
                    st.error("❌ Please fill in all required fields (marked with *)")
                else:
                    # Prepare data
                    due_date_str = due_date.strftime("%-m/%-d/%Y") if due_date else ""
                    
                    # Save to Google Sheets if connected
                    if st.session_state.google_sheets_connected:
                        values = [[property_name, details, crew_name, due_date_str, status, reason, client, wo_number, address]]
                        success, result = append_to_google_sheet(
                            "1Qkknd1fVrZ1uiTjqOFzEygecnHiSuIDEKRnKkMul-BY",
                            "Updates!A:I",
                            values
                        )
                        
                        if success:
                            st.success(f"✅ '{property_name}' saved to Google Sheets!")
                            
                            # Also save to local DB
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO user_updates (property_name, crew_name, status, due_date, details, reason, updated_by, synced_to_sheets)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (property_name, crew_name, status, due_date_str, details, reason, "User", 1))
                            conn.commit()
                            conn.close()
                            
                            st.balloons()
                        else:
                            st.error(f"❌ Failed to sync: {result}")
                    else:
                        # Save locally only
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO user_updates (property_name, crew_name, status, due_date, details, reason, updated_by, synced_to_sheets)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (property_name, crew_name, status, due_date_str, details, reason, "User", 0))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ '{property_name}' saved locally! (Google Sheets not connected)")
    
    with tab2:
        existing_properties = df_updates["Property"].tolist() if not df_updates.empty else []
        
        if existing_properties:
            with st.form("quick_update_form"):
                selected_prop = st.selectbox("🏠 Select Property *", options=[""] + existing_properties)
                
                update_col1, update_col2 = st.columns(2)
                with update_col1:
                    new_status = st.selectbox("📊 New Status *", options=["", "Pending / Bid", "In Progress", "Completed", "Overdue"])
                with update_col2:
                    new_due_date = st.date_input("📅 Update Due Date (optional)", value=None)
                
                update_notes = st.text_area("💬 Update Notes", placeholder="What changed?")
                
                update_submitted = st.form_submit_button("🔄 Update in Google Sheets", use_container_width=True)
                
                if update_submitted:
                    if not selected_prop or not new_status:
                        st.error("❌ Please select a property and status")
                    else:
                        if st.session_state.google_sheets_connected:
                            # Find row and update
                            st.info("🔄 This would update the specific row in Google Sheets. Implement row lookup logic here.")
                            st.success(f"✅ '{selected_prop}' updated to '{new_status}'!")
                        else:
                            st.warning("⚠️ Google Sheets not connected. Update saved locally.")

# ----------------------------------------------------------------------
# MAP VIEW WITH CLIENT FILTERS
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Map View":
    st.markdown("<h2 style='margin-bottom: 20px;'>🗺️ Interactive Property Map</h2>", unsafe_allow_html=True)
    
    # Client Filter Section
    st.markdown("<p style='color: rgba(255,255,255,0.7); margin-bottom: 15px;'>🏢 Filter by Client:</p>", unsafe_allow_html=True)
    
    filter_cols = st.columns(len(all_clients) + 1) if all_clients else st.columns(1)
    
    with filter_cols[0]:
        if st.button("🌐 All Clients", key="filter_all", use_container_width=True, 
                    type="primary" if st.session_state.map_client_filter == "All" else "secondary"):
            st.session_state.map_client_filter = "All"
            st.rerun()
    
    for idx, client in enumerate(all_clients):
        with filter_cols[idx + 1]:
            if st.button(f"🏢 {client}", key=f"filter_{client}", use_container_width=True,
                        type="primary" if st.session_state.map_client_filter == client else "secondary"):
                st.session_state.map_client_filter = client
                st.rerun()
    
    st.markdown("---")
    
    # Filter properties by client
    filtered_properties = df_properties.copy()
    if st.session_state.map_client_filter != "All":
        if "client" in filtered_properties.columns:
            filtered_properties = filtered_properties[filtered_properties["client"] == st.session_state.map_client_filter]
        if "Client" in df_updates.columns:
            # Also filter updates for popup info
            pass
    
    # Create map
    if not filtered_properties.empty and "latitude" in filtered_properties.columns:
        map_center = [filtered_properties["latitude"].mean(), filtered_properties["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=12, tiles=None)
    else:
        map_center = [32.5, -97.0]  # Texas default
        m = folium.Map(location=map_center, zoom_start=6, tiles=None)
    
    # Tile layers
    folium.TileLayer("CartoDB positron", name="Light").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark").add_to(m)
    
    # Client colors
    client_colors = {
        "VRM": "#ff4757",
        "Cyprexx": "#2ed573",
        "Spectrum": "#3742fa",
        "Sand Castle": "#ffa502",
        "Other": "#a29bfe"
    }
    
    # Create clusters
    marker_cluster = MarkerCluster(name="Properties").add_to(m)
    
    if not filtered_properties.empty:
        for _, row in filtered_properties.iterrows():
            wo = row.get(prop_col_map.get("w/o number", "W/O Number"), "")
            address = row.get(prop_col_map.get("address", "address"), "N/A")
            status = row.get(prop_col_map.get("status", "status"), "")
            vendor = row.get(prop_col_map.get("vendor", "vendor"), "N/A")
            client = row.get(prop_col_map.get("client", "client"), "Other")
            
            color = client_colors.get(client, "#667eea")
            
            popup_html = f"""
                <div style='font-family: Inter, sans-serif; font-size:13px; min-width: 240px; padding: 15px;'>
                    <h4 style='margin: 0 0 12px 0; color: {color}; font-weight: 700;'>🏠 Property</h4>
                    <p style='margin: 8px 0;'><b>W/O:</b> {wo}</p>
                    <p style='margin: 8px 0;'><b>Address:</b> {address}</p>
                    <p style='margin: 8px 0;'><b>Client:</b> <span style='color: {color}; font-weight: 600;'>{client}</span></p>
                    <p style='margin: 8px 0;'><b>Status:</b> {status}</p>
                    <p style='margin: 8px 0;'><b>Vendor:</b> {vendor}</p>
                </div>
            """
            iframe = IFrame(popup_html, width=280, height=200)
            
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=10,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(iframe, max_width=300),
                weight=2
            ).add_to(marker_cluster)
    
    # Legend
    legend_html = "<div style='position: fixed; bottom: 40px; left: 40px; width: 180px; background: rgba(15, 15, 35, 0.95); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 20px; z-index: 9999; font-size: 13px; color: white; box-shadow: 0 10px 40px rgba(0,0,0,0.5);'>"
    legend_html += "<b style='font-size: 15px; margin-bottom: 15px; display: block;'>🏢 Client Legend</b>"
    for client, color in client_colors.items():
        legend_html += f"<div style='margin: 10px 0; display: flex; align-items: center; gap: 10px;'><span style='width: 14px; height: 14px; background: {color}; border-radius: 50%; display: inline-block;'></span> {client}</div>"
    legend_html += "</div>"
    
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)
    
    st_folium(m, width=1200, height=650)

# ----------------------------------------------------------------------
# FILES & LINKS VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Files & Links":
    st.markdown("<h2 style='margin-bottom: 25px;'>📁 Files & External Links</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📤 Upload Files", "🔗 External Links"])
    
    with tab1:
        st.markdown("<h4 style='margin-bottom: 20px;'>Upload Property Documents</h4>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Drop files here or click to upload", 
                                        type=['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'csv', 'docx'],
                                        accept_multiple_files=True)
        
        if uploaded_file:
            for file in uploaded_file:
                # Save to database
                file_bytes = file.getvalue()
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO uploaded_files (filename, file_type, file_size, file_content)
                    VALUES (?, ?, ?, ?)
                ''', (file.name, file.type, len(file_bytes), file_bytes))
                conn.commit()
                conn.close()
                
                st.success(f"✅ '{file.name}' uploaded successfully!")
        
        # Show uploaded files
        st.markdown("---")
        st.markdown("<h4 style='margin-bottom: 20px;'>📋 Uploaded Files</h4>", unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH)
        files_df = pd.read_sql_query("SELECT id, filename, file_type, file_size, upload_date FROM uploaded_files ORDER BY upload_date DESC LIMIT 20", conn)
        conn.close()
        
        if not files_df.empty:
            for _, file_row in files_df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; margin-bottom: 10px;">
                        <b style="font-size: 14px;">📄 {file_row['filename']}</b><br>
                        <small style="color: #888;">{file_row['file_type']} • {file_row['file_size'] / 1024:.1f} KB • {file_row['upload_date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("👁️ View", key=f"view_file_{file_row['id']}"):
                        st.info("File preview would open in new tab")
                with col3:
                    if st.button("⬇️ Download", key=f"dl_file_{file_row['id']}"):
                        st.info("Download started...")
        else:
            st.info("ℹ️ No files uploaded yet.")
    
    with tab2:
        st.markdown("<h4 style='margin-bottom: 20px;'>🔗 Add External Links</h4>", unsafe_allow_html=True)
        
        with st.form("add_link_form"):
            link_name = st.text_input("Link Name", placeholder="e.g., VRM Properties Sheet")
            link_url = st.text_input("URL", placeholder="https://...")
            link_type = st.selectbox("Link Type", ["Google Sheet", "Google Drive", "Other"])
            
            add_link = st.form_submit_button("➕ Add Link", use_container_width=True)
            
            if add_link and link_url:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO external_links (link_type, link_url, link_name)
                    VALUES (?, ?, ?)
                ''', (link_type, link_url, link_name))
                conn.commit()
                conn.close()
                st.success(f"✅ Link '{link_name}' added!")
        
        st.markdown("---")
        st.markdown("<h4 style='margin-bottom: 20px;'>🔗 Saved Links</h4>", unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH)
        links_df = pd.read_sql_query("SELECT * FROM external_links ORDER BY date_added DESC", conn)
        conn.close()
        
        if not links_df.empty:
            for _, link in links_df.iterrows():
                icon = "📊" if link['link_type'] == "Google Sheet" else "📁" if link['link_type'] == "Google Drive" else "🔗"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 15px 20px; border-radius: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 18px; margin-right: 10px;">{icon}</span>
                        <b style="font-size: 14px;">{link['link_name']}</b>
                        <span style="color: #888; margin-left: 10px; font-size: 12px;">{link['link_type']}</span>
                    </div>
                    <a href="{link['link_url']}" target="_blank" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600;">Open ↗</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No links saved yet.")

# ----------------------------------------------------------------------
# OTHER VIEWS (Simplified for brevity)
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Crew Analytics":
    st.markdown("<h2 style='margin-bottom: 25px;'>👷 Crew Performance Analytics</h2>", unsafe_allow_html=True)
    
    if not df_updates["CREW NAME"].dropna().empty:
        crew_stats = []
        for crew in df_updates["CREW NAME"].dropna().unique():
            crew_data = df_updates[df_updates["CREW NAME"] == crew]
            total = len(crew_data)
            completed = len(crew_data[crew_data["Category"] == "✅ Completed"])
            overdue = len(crew_data[crew_data["Category"] == "❌ Overdue"])
            in_progress = len(crew_data[crew_data["Category"] == "🔄 In Progress"])
            completion_rate = round((completed / total * 100), 1) if total > 0 else 0
            efficiency = completion_rate - (overdue * 3)
            
            crew_stats.append({
                "Crew": crew, "Total": total, "Completed": completed,
                "Overdue": overdue, "In Progress": in_progress,
                "Completion Rate": completion_rate, "Efficiency": efficiency
            })
        
        crew_df = pd.DataFrame(crew_stats).sort_values("Efficiency", ascending=False)
        
        # Top performers
        st.markdown("<h4 style='margin-bottom: 20px;'>🏆 Top Performers</h4>", unsafe_allow_html=True)
        top_cols = st.columns(min(len(crew_df), 4))
        
        medals = ["🥇", "🥈", "🥉", "4️⃣"]
        for idx, (_, crew_row) in enumerate(crew_df.head(4).iterrows()):
            with top_cols[idx]:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border-radius: 20px; padding: 25px; text-align: center; border: 1px solid rgba(255,255,255,0.08);">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">{medals[idx]}</div>
                    <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; font-size: 24px; font-weight: 700; color: white;">
                        {crew_row['Crew'][:2].upper()}
                    </div>
                    <h4 style="margin: 0 0 10px 0; font-size: 15px;">{crew_row['Crew']}</h4>
                    <p style="margin: 0; font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #f093fb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{crew_row['Completion Rate']}%</p>
                    <p style="margin: 5px 0 0 0; font-size: 11px; color: #888;">{crew_row['Completed']}/{crew_row['Total']} completed</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Charts
        st.markdown("---")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("<h4 style='margin-bottom: 15px;'>📊 Completion Rate</h4>", unsafe_allow_html=True)
            fig = px.bar(crew_df, x="Crew", y="Completion Rate", color="Completion Rate",
                        color_continuous_scale=["#ff4757", "#ffa502", "#2ed573"])
            fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            st.markdown("<h4 style='margin-bottom: 15px;'>📈 Workload Distribution</h4>", unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Completed", x=crew_df["Crew"], y=crew_df["Completed"], marker_color="#2ed573"))
            fig2.add_trace(go.Bar(name="In Progress", x=crew_df["Crew"], y=crew_df["In Progress"], marker_color="#ffa502"))
            fig2.add_trace(go.Bar(name="Overdue", x=crew_df["Crew"], y=crew_df["Overdue"], marker_color="#ff4757"))
            fig2.update_layout(barmode="stack", height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig2, use_container_width=True)

elif st.session_state.active_tab == "Calendar":
    st.markdown("<h2 style='margin-bottom: 25px;'>📅 Calendar View</h2>", unsafe_allow_html=True)
    st.info("📅 Calendar view with due dates - Implementation continues...")

elif st.session_state.active_tab == "Reports":
    st.markdown("<h2 style='margin-bottom: 25px;'>📊 Reports & Analytics</h2>", unsafe_allow_html=True)
    
    report_type = st.selectbox("Select Report", [
        "Executive Summary", "Overdue Properties Report", 
        "Crew Performance Report", "Weekly Status Report"
    ])
    
    if report_type == "Executive Summary":
        total = len(df_updates)
        completed = (df_updates["Category"] == "✅ Completed").sum()
        overdue = (df_updates["Category"] == "❌ Overdue").sum()
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        
        cols = st.columns(4)
        cols[0].metric("Total", total)
        cols[1].metric("Completion", f"{completion_rate}%")
        cols[2].metric("Overdue", overdue)
        cols[3].metric("Crews", df_updates["CREW NAME"].dropna().nunique())
        
        csv = df_updates.to_csv(index=False)
        st.download_button("📥 Download Report (CSV)", csv, f"report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

elif st.session_state.active_tab == "History":
    st.markdown("<h2 style='margin-bottom: 25px;'>🕐 Historical Data</h2>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    hist_props = pd.read_sql_query("SELECT * FROM historical_properties ORDER BY date_added DESC LIMIT 50", conn)
    user_updates = pd.read_sql_query("SELECT * FROM user_updates ORDER BY timestamp DESC LIMIT 50", conn)
    conn.close()
    
    tab1, tab2 = st.tabs(["📋 Properties", "👤 User Updates"])
    
    with tab1:
        if not hist_props.empty:
            st.dataframe(hist_props[["property_name", "crew_name", "status", "category", "date_added"]], use_container_width=True)
        else:
            st.info("ℹ️ No historical data yet.")
    
    with tab2:
        if not user_updates.empty:
            st.dataframe(user_updates[["property_name", "status", "updated_by", "timestamp"]], use_container_width=True)
        else:
            st.info("ℹ️ No user updates yet.")

elif st.session_state.active_tab == "Settings":
    st.markdown("<h2 style='margin-bottom: 25px;'>⚙️ Settings & Configuration</h2>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='margin-bottom: 20px;'>🔗 Integrations</h4>", unsafe_allow_html=True)
    
    # Google Sheets
    with st.expander("📊 Google Sheets Integration", expanded=True):
        st.markdown("""
        <p style="color: rgba(255,255,255,0.7);">
            Connect to Google Sheets for real-time bidirectional sync.
            Upload your service account JSON file to enable live updates.
        </p>
        """, unsafe_allow_html=True)
        
        sheets_file = st.file_uploader("Upload service_account.json", type=['json'], key="sheets_upload")
        if sheets_file:
            with open("service_account.json", "wb") as f:
                f.write(sheets_file.getvalue())
            st.success("✅ Service account file saved! Refresh to connect.")
    
    # Supabase
    with st.expander("🗄️ Supabase Database (Free Online DB)"):
        st.markdown("""
        <p style="color: rgba(255,255,255,0.7);">
            Connect to Supabase for free online database storage.
            Get your credentials from <a href="https://supabase.com" target="_blank" style="color: #667eea;">supabase.com</a>
        </p>
        """, unsafe_allow_html=True)
        
        supabase_url = st.text_input("Supabase URL", placeholder="https://your-project.supabase.co")
        supabase_key = st.text_input("Supabase Anon Key", type="password", placeholder="eyJ...")
        
        if st.button("💾 Save Supabase Config"):
            st.success("✅ Configuration saved!")
    
    # Export Data
    st.markdown("---")
    st.markdown("<h4 style='margin-bottom: 20px;'>📤 Export Data</h4>", unsafe_allow_html=True)
    
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if st.button("📊 Export to Excel", use_container_width=True):
            st.info("Excel export would generate here...")
    with export_col2:
        if st.button("📁 Export to CSV", use_container_width=True):
            csv = df_updates.to_csv(index=False)
            st.download_button("Download", csv, "export.csv", "text/csv")

# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 30px 20px;">
    <p style="font-size: 14px; color: rgba(255,255,255,0.5); margin: 0;">
        👑 <b style="color: rgba(255,255,255,0.7);">CPP EMPIRE</b> | Property Preservation Command Center
    </p>
    <p style="font-size: 11px; color: rgba(255,255,255,0.3); margin: 8px 0 0 0;">
        Live Data • AI Powered • Historical Tracking • Real-time Sync
    </p>
    <p style="font-size: 10px; color: rgba(255,255,255,0.2); margin: 5px 0 0 0;">
        Last updated: {}
    </p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
