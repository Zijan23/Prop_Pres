enhanced_code = '''# app.py - Property Preservation Pro Dashboard with AI Agent
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
import sqlite3
import json
from pathlib import Path
import time
import requests
import re

# =============================================================================
# AI AGENT CONFIGURATION - FREE TIER OPTIONS
# =============================================================================
# Option 1: Groq (Recommended - $5 free credit, no CC required)
# Get key at: https://console.groq.com/keys
# Default key below is placeholder - replace with your actual key
# Option 2: OpenRouter (Free tier available)
# Get key at: https://openrouter.ai/keys
# Option 3: Google AI Studio (Gemini - completely free)
# Get key at: https://aistudio.google.com/app/apikey
AI_CONFIG = {
    "provider": "groq", # Change to "openrouter" or "gemini" as needed
    "groq_api_key": os.getenv("GROQ_API_KEY", "gsk_your_free_groq_key_here"),
    "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-your-openrouter-key"),
    "gemini_api_key": os.getenv("GEMINI_API_KEY", "your-gemini-key"),
    "model": "llama-3.1-8b-instant", # Fast and capable (Groq)
    # "model": "google/gemma-2-9b-it", # Alternative for OpenRouter
    "temperature": 0.7,
    "max_tokens": 1024
}

# =============================================================================
# AI AGENT CLASS
# =============================================================================
class PropertyAIAgent:
    """AI Agent for Property Preservation Dashboard"""
    
    def __init__(self, config):
        self.config = config
        self.provider = config.get("provider", "groq")
        self.conversation_history = []
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self):
        return """You are "Preservation Pal" 🤖🏠, an AI assistant for a Property Preservation Dashboard.
        
Your personality is friendly, helpful, and slightly playful - you love helping property managers stay organized!
CAPABILITIES:
1. 🔍 FIND PROPERTIES - Search through property database by name, address, crew, or status
2. 📊 CHECK STATUS - Report on property statuses (Overdue, In Progress, Completed, Pending)
3. 💡 GENERATE INSIGHTS - Analyze data and provide actionable recommendations
4. ⏰ SET REMINDERS - Help track due dates and flag urgent items
5. ❓ ANSWER QUESTIONS - Explain the dashboard, data, or property management concepts
RULES:
- Always respond in a warm, professional tone with occasional relevant emojis
- When asked about properties, reference the actual data provided in context
- If you don't have access to live data, explain what you can do instead
- For overdue properties, show urgency but remain solution-oriented
- Keep responses concise but informative (2-4 paragraphs max)
- If asked to perform actions beyond your capabilities (like modifying data), explain that you can guide the user on how to do it manually
CURRENT CONTEXT:
You are analyzing a property preservation database with work orders, crew assignments, due dates, and status tracking. The dashboard integrates with Google Sheets for live data."""

    def query(self, user_message, context_data=None):
        """Send query to AI provider and return response"""
        
        # Build messages
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add context if provided (property data summary)
        if context_data:
            context_msg = self._format_context(context_data)
            messages.append({"role": "system", "content": f"CURRENT DATA CONTEXT:\\n{context_msg}"})
        
        # Add conversation history (last 5 exchanges)
        for exchange in self.conversation_history[-5:]:
            messages.append(exchange)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            if self.provider == "groq":
                response = self._query_groq(messages)
            elif self.provider == "openrouter":
                response = self._query_openrouter(messages)
            elif self.provider == "gemini":
                response = self._query_gemini(messages)
            else:
                response = "⚠️ AI provider not configured. Please check settings."
                
            # Store in history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            return f"😅 Oops! I had a little hiccup: {str(e)}\\n\\nPlease check your API key or try again in a moment!"

    def _query_groq(self, messages):
        """Query Groq API (Free tier: $5 credit, fast inference)"""
        headers = {
            "Authorization": f"Bearer {self.config['groq_api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            if "invalid api key" in error_msg.lower():
                return "🔑 Hmm, my brain key seems to be invalid! Please check your GROQ_API_KEY configuration."
            raise Exception(f"API Error: {error_msg}")

    def _query_openrouter(self, messages):
        """Query OpenRouter API (Free tier available)"""
        headers = {
            "Authorization": f"Bearer {self.config['openrouter_api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cppprop.streamlit.app/",
            "X-Title": "Property Preservation Dashboard"
        }
        
        data = {
            "model": "google/gemma-2-9b-it", # Free tier model
            "messages": messages,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter Error: {response.text}")

    def _query_gemini(self, messages):
        """Query Google Gemini API (Completely free tier)"""
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "model" or msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
        
        data = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": self.config["temperature"],
                "maxOutputTokens": self.config["max_tokens"]
            }
        }
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.config['gemini_api_key']}",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return "🤔 I couldn't generate a response. Try rephrasing your question!"
        else:
            raise Exception(f"Gemini Error: {response.text}")

    def _format_context(self, data):
        """Format property data for AI context"""
        if data is None or data.empty:
            return "No property data currently loaded."
        
        total = len(data)
        completed = (data["Category"] == "✅ Completed").sum() if "Category" in data.columns else 0
        overdue = (data["Category"] == "❌ Overdue").sum() if "Category" in data.columns else 0
        in_progress = (data["Category"] == "🔄 In Progress").sum() if "Category" in data.columns else 0
        pending = (data["Category"] == "⏳ Pending / Bid").sum() if "Category" in data.columns else 0
        
        # Get top overdue properties
        overdue_props = ""
        if "Category" in data.columns and overdue > 0:
            od = data[data["Category"] == "❌ Overdue"].head(3)
            for _, row in od.iterrows():
                overdue_props += f"\\n- {row.get('Property', 'Unknown')} (Due: {row.get('Due date', 'N/A')})"
        
        context = f"""
TOTAL PROPERTIES: {total}
STATUS BREAKDOWN:
- ✅ Completed: {completed}
- ❌ Overdue: {overdue}
- 🔄 In Progress: {in_progress}
- ⏳ Pending/Bid: {pending}
TOP OVERDUE PROPERTIES:{overdue_props if overdue_props else " None currently"}
CREWS ACTIVE: {data['CREW NAME'].nunique() if 'CREW NAME' in data.columns else 0}
        """
        return context

# Initialize AI Agent
@st.cache_resource
def get_ai_agent():
    return PropertyAIAgent(AI_CONFIG)

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="CPP Pro | Property Preservation AI Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS - INCLUDING AI ASSISTANT STYLING
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 100%) !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em !important;
    }
    
    p, span, div {
        color: #e0e0e0 !important;
        font-weight: 400 !important;
    }
    
    /* KPI Cards */
    .kpi-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .kpi-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(102, 126, 234, 0.4);
    }
    
    .kpi-value {
        font-size: 2.5em;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .kpi-label {
        font-size: 0.9em;
        opacity: 0.9;
        margin-top: 8px;
        font-weight: 500;
    }
    
    .kpi-completed {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .kpi-overdue {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        animation: pulse-red 2s infinite;
    }
    
    .kpi-progress {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .kpi-pending {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 10px 40px rgba(235, 51, 73, 0.4); }
        50% { box-shadow: 0 10px 60px rgba(235, 51, 73, 0.6); }
    }
    
    /* Property Cards */
    .property-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        border-left: 4px solid;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .property-card:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(8px);
    }
    
    .property-card.overdue { border-left-color: #e74c3c; }
    .property-card.completed { border-left-color: #27ae60; }
    .property-card.in-progress { border-left-color: #f39c12; }
    .property-card.pending { border-left-color: #3498db; }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge.overdue {
        background: rgba(231, 76, 60, 0.2);
        color: #ff6b6b;
        border: 1px solid rgba(231, 76, 60, 0.3);
    }
    
    .status-badge.completed {
        background: rgba(39, 174, 96, 0.2);
        color: #51cf66;
        border: 1px solid rgba(39, 174, 96, 0.3);
    }
    
    .status-badge.in-progress {
        background: rgba(243, 156, 18, 0.2);
        color: #ffd43b;
        border: 1px solid rgba(243, 156, 18, 0.3);
    }
    
    .status-badge.pending {
        background: rgba(52, 152, 219, 0.2);
        color: #74c0fc;
        border: 1px solid rgba(52, 152, 219, 0.3);
    }
    
    /* Insight Cards */
    .insight-box {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .insight-box:hover {
        background: rgba(102, 126, 234, 0.2);
        transform: scale(1.02);
    }
    
    /* Dashboard Header */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }
    
    .dashboard-header h1 {
        font-size: 3em !important;
        margin: 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    /* Form Styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* DataFrames */
    .dataframe {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background: rgba(102, 126, 234, 0.3) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        color: #e0e0e0 !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px 10px 0 0 !important;
        color: #e0e0e0 !important;
        font-weight: 500 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(102, 126, 234, 0.3) !important;
        color: white !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
    
    /* Alert boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2em !important;
        font-weight: 700 !important;
        color: white !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
        font-weight: 500 !important;
    }
    
    /* Crew cards */
    .crew-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .crew-card:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateY(-5px);
    }
    
    .crew-avatar {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 700;
        margin: 0 auto 16px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Date indicator */
    .date-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .date-indicator.overdue {
        background: rgba(231, 76, 60, 0.2);
        color: #ff6b6b;
    }
    
    .date-indicator.due-soon {
        background: rgba(243, 156, 18, 0.2);
        color: #ffd43b;
    }
    
    .date-indicator.on-track {
        background: rgba(39, 174, 96, 0.2);
        color: #51cf66;
    }
    
    /* ================================================================= */
    /* AI ASSISTANT STYLING - CUTE FLOATING BOT */
    /* ================================================================= */
    
    /* Main AI Container - Fixed at bottom */
    .ai-assistant-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 380px;
        max-height: 600px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        border: 2px solid rgba(102, 126, 234, 0.5);
        z-index: 9999;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        transition: all 0.3s ease;
    }
    
    .ai-assistant-container.minimized {
        height: 70px;
        max-height: 70px;
        width: 280px;
        cursor: pointer;
    }
    
    /* AI Header with Cute Avatar */
    .ai-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .ai-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .ai-title {
        flex: 1;
    }
    
    .ai-title h4 {
        margin: 0;
        font-size: 16px;
        color: white !important;
    }
    
    .ai-title span {
        font-size: 12px;
        color: rgba(255,255,255,0.7) !important;
    }
    
    .ai-toggle {
        color: white;
        font-size: 20px;
        transition: transform 0.3s ease;
    }
    
    .ai-toggle.collapsed {
        transform: rotate(180deg);
    }
    
    /* Chat Messages Area */
    .ai-messages {
        flex: 1;
        overflow-y: auto;
        padding: 15px;
        max-height: 400px;
        background: rgba(0,0,0,0.2);
    }
    
    .ai-message {
        margin-bottom: 12px;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 85%;
        font-size: 13px;
        line-height: 1.5;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .ai-message.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .ai-message.assistant {
        background: rgba(255,255,255,0.1);
        color: #e0e0e0 !important;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .ai-message.assistant strong {
        color: #f093fb !important;
    }
    
    /* Input Area */
    .ai-input-area {
        padding: 15px;
        background: rgba(0,0,0,0.3);
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    .ai-quick-actions {
        display: flex;
        gap: 8px;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    
    .ai-chip {
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.5);
        color: #a0c4ff !important;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 11px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .ai-chip:hover {
        background: rgba(102, 126, 234, 0.4);
        color: white !important;
    }
    
    /* Typing Indicator */
    .ai-typing {
        display: flex;
        gap: 4px;
        padding: 10px 14px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        width: fit-content;
        margin-bottom: 12px;
    }
    
    .ai-typing-dot {
        width: 8px;
        height: 8px;
        background: #f093fb;
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    
    .ai-typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .ai-typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    /* Welcome message styling */
    .ai-welcome {
        text-align: center;
        padding: 20px;
        color: rgba(255,255,255,0.6) !important;
        font-size: 13px;
    }
    
    .ai-welcome-icon {
        font-size: 40px;
        margin-bottom: 10px;
    }
    
    /* Ensure main content doesn't get hidden behind AI assistant */
    .main .block-container {
        padding-bottom: 100px !important;
    }
    
    /* Mobile responsiveness for AI assistant */
    @media (max-width: 768px) {
        .ai-assistant-container {
            width: calc(100% - 40px);
            right: 20px;
            left: 20px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Database Setup for Historical Data
# ----------------------------------------------------------------------
import sqlite3

DB_PATH = "property_preservation.db"

def init_database():
    """Initialize SQLite database for historical data."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Historical properties table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historical_properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_name TEXT,
        wo_number TEXT,
        address TEXT,
        crew_name TEXT,
        due_date TEXT,
        status TEXT,
        category TEXT,
        reason TEXT,
        details TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_completed TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    """)

    # Crew performance history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crew_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crew_name TEXT,
        property_name TEXT,
        action TEXT,
        status TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Daily snapshots for trends
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date DATE,
        total_properties INTEGER,
        completed INTEGER,
        overdue INTEGER,
        in_progress INTEGER,
        pending INTEGER,
        active_crews INTEGER
    )
    """)

    # User inputs / updates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_name TEXT,
        crew_name TEXT,
        status TEXT,
        due_date TEXT,
        details TEXT,
        reason TEXT,
        updated_by TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_to_history(df_updates):
    """Save current data to historical database."""
    conn = sqlite3.connect(DB_PATH)
    
    for _, row in df_updates.iterrows():
        # Check if property already exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM historical_properties WHERE property_name = ? AND is_active = 1",
            (row.get("Property", ""),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE historical_properties
                SET status = ?, category = ?, crew_name = ?, due_date = ?,
                    reason = ?, details = ?
                WHERE id = ?
            ''', (
                row.get("Status 1", ""),
                row.get("Category", ""),
                row.get("CREW NAME", ""),
                str(row.get("Due date", "")) if pd.notna(row.get("Due date")) else None,
                row.get("Reason", ""),
                row.get("Details", ""),
                existing[0]
            ))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO historical_properties
                (property_name, wo_number, address, crew_name, due_date, status, category, reason, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get("Property", ""),
                row.get("W/O Number", ""),
                row.get("Address", ""),
                row.get("CREW NAME", ""),
                str(row.get("Due date", "")) if pd.notna(row.get("Due date")) else None,
                row.get("Status 1", ""),
                row.get("Category", ""),
                row.get("Reason", ""),
                row.get("Details", "")
            ))
    
    conn.commit()
    conn.close()

def save_daily_snapshot(df_updates):
    """Save daily snapshot for trend analysis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    # Check if snapshot already exists for today
    cursor.execute("SELECT id FROM daily_snapshots WHERE snapshot_date = ?", (today,))
    if cursor.fetchone():
        conn.close()
        return
    
    total = len(df_updates)
    completed = (df_updates["Category"] == "✅ Completed").sum() if "Category" in df_updates.columns else 0
    overdue = (df_updates["Category"] == "❌ Overdue").sum() if "Category" in df_updates.columns else 0
    in_progress = (df_updates["Category"] == "🔄 In Progress").sum() if "Category" in df_updates.columns else 0
    pending = (df_updates["Category"] == "⏳ Pending / Bid").sum() if "Category" in df_updates.columns else 0
    active_crews = df_updates["CREW NAME"].dropna().nunique() if "CREW NAME" in df_updates.columns else 0
    
    cursor.execute('''
        INSERT INTO daily_snapshots
        (snapshot_date, total_properties, completed, overdue, in_progress, pending, active_crews)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (today, total, completed, overdue, in_progress, pending, active_crews))
    
    conn.commit()
    conn.close()

def get_historical_data(days=30):
    """Get historical data for trend analysis."""
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT * FROM daily_snapshots
        WHERE snapshot_date >= date('now', '-{days} days')
        ORDER BY snapshot_date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_all_historical_properties():
    """Get all historical properties."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM historical_properties ORDER BY date_added DESC", conn)
    conn.close()
    return df

def add_user_update(property_name, crew_name, status, due_date, details, reason, updated_by="System"):
    """Add a user update to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_updates (property_name, crew_name, status, due_date, details, reason, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (property_name, crew_name, status, due_date, details, reason, updated_by))
    conn.commit()
    conn.close()

# Initialize database
init_database()

# ----------------------------------------------------------------------
# Custom CSS with Better Fonts
# ----------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 100%) !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em !important;
    }
    
    p, span, div {
        color: #e0e0e0 !important;
        font-weight: 400 !important;
    }
    
    /* KPI Cards */
    .kpi-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .kpi-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(102, 126, 234, 0.4);
    }
    
    .kpi-value {
        font-size: 2.5em;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .kpi-label {
        font-size: 0.9em;
        opacity: 0.9;
        margin-top: 8px;
        font-weight: 500;
    }
    
    .kpi-completed {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .kpi-overdue {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        animation: pulse-red 2s infinite;
    }
    
    .kpi-progress {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .kpi-pending {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 10px 40px rgba(235, 51, 73, 0.4); }
        50% { box-shadow: 0 10px 60px rgba(235, 51, 73, 0.6); }
    }
    
    /* Property Cards */
    .property-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        border-left: 4px solid;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .property-card:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(8px);
    }
    
    .property-card.overdue { border-left-color: #e74c3c; }
    .property-card.completed { border-left-color: #27ae60; }
    .property-card.in-progress { border-left-color: #f39c12; }
    .property-card.pending { border-left-color: #3498db; }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge.overdue {
        background: rgba(231, 76, 60, 0.2);
        color: #ff6b6b;
        border: 1px solid rgba(231, 76, 60, 0.3);
    }
    
    .status-badge.completed {
        background: rgba(39, 174, 96, 0.2);
        color: #51cf66;
        border: 1px solid rgba(39, 174, 96, 0.3);
    }
    
    .status-badge.in-progress {
        background: rgba(243, 156, 18, 0.2);
        color: #ffd43b;
        border: 1px solid rgba(243, 156, 18, 0.3);
    }
    
    .status-badge.pending {
        background: rgba(52, 152, 219, 0.2);
        color: #74c0fc;
        border: 1px solid rgba(52, 152, 219, 0.3);
    }
    
    /* Insight Cards */
    .insight-box {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .insight-box:hover {
        background: rgba(102, 126, 234, 0.2);
        transform: scale(1.02);
    }
    
    /* Dashboard Header */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }
    
    .dashboard-header h1 {
        font-size: 3em !important;
        margin: 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    /* Form Styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* DataFrames */
    .dataframe {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background: rgba(102, 126, 234, 0.3) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        color: #e0e0e0 !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px 10px 0 0 !important;
        color: #e0e0e0 !important;
        font-weight: 500 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(102, 126, 234, 0.3) !important;
        color: white !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
    
    /* Alert boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2em !important;
        font-weight: 700 !important;
        color: white !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
        font-weight: 500 !important;
    }
    
    /* Crew cards */
    .crew-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .crew-card:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateY(-5px);
    }
    
    .crew-avatar {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 700;
        margin: 0 auto 16px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Date indicator */
    .date-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .date-indicator.overdue {
        background: rgba(231, 76, 60, 0.2);
        color: #ff6b6b;
    }
    
    .date-indicator.due-soon {
        background: rgba(243, 156, 18, 0.2);
        color: #ffd43b;
    }
    
    .date-indicator.on-track {
        background: rgba(39, 174, 96, 0.2);
        color: #51cf66;
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
if 'show_input_form' not in st.session_state:
    st.session_state.show_input_form = False
if 'data_refresh' not in st.session_state:
    st.session_state.data_refresh = 0

# ----------------------------------------------------------------------
# Helper Functions - FIXED DATE PARSING
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

def parse_date_american_first(x):
    """
    Parse date with AMERICAN FORMAT PRIORITY (MM-DD-YYYY).
    This fixes the issue where 02-12-2026 was parsed as Dec 2 instead of Feb 12.
    """
    if pd.isna(x) or str(x).strip() == "":
        return pd.NaT
    
    x_str = str(x).strip()
    
    # American formats FIRST (MM/DD/YYYY or MM-DD-YYYY)
    american_formats = [
        "%m/%d/%Y", # 02/12/2026 -> Feb 12, 2026
        "%m-%d-%Y", # 02-12-2026 -> Feb 12, 2026
        "%m/%d/%y", # 02/12/26 -> Feb 12, 2026
        "%m-%d-%y", # 02-12-26 -> Feb 12, 2026
    ]
    
    # Try American formats first
    for fmt in american_formats:
        try:
            return pd.to_datetime(x_str, format=fmt, errors="raise")
        except:
            pass
    
    # Then try international formats
    intl_formats = [
        "%d/%m/%Y", # 12/02/2026 -> Feb 12, 2026 (intl)
        "%d-%m-%Y", # 12-02-2026 -> Feb 12, 2026 (intl)
        "%Y-%m-%d", # 2026-02-12
        "%d/%m/%y",
        "%d-%m-%y",
        "%Y/%m/%d",
    ]
    
    for fmt in intl_formats:
        try:
            return pd.to_datetime(x_str, format=fmt, errors="raise")
        except:
            pass
    
    # Last resort - let pandas infer (may be wrong for ambiguous dates)
    return pd.to_datetime(x_str, errors="coerce")

def categorize_status(row):
    """Categorize property status with enhanced logic."""
    s = str(row.get("Status 1", "")).lower().strip()
    due = row.get("Due date")
    
    # Completed status
    if any(word in s for word in ["complete", "submitted", "payment", "finished", "done", "received", "approved", "paid"]):
        return "✅ Completed"
    
    # Check due date for overdue - compare dates properly
    if pd.notna(due) and isinstance(due, (pd.Timestamp, datetime)):
        today_dt = pd.Timestamp.today().normalize()
        due_normalized = pd.Timestamp(due).normalize()
        if due_normalized < today_dt:
            return "❌ Overdue"
    
    # In Progress status
    progress_keywords = [
        "ongoing", "progress", "will be", "try to", "today", "tomorrow",
        "friday", "monday", "tuesday", "wednesday", "thursday", "saturday",
        "sunday", "working", "scheduled", "assigned", "in progress", "started",
        "crew on site", "crew assigned", "in route", "en route"
    ]
    if any(word in s for word in progress_keywords):
        return "🔄 In Progress"
    
    # Pending status
    pending_keywords = [
        "waiting", "pending", "bid", "pricing", "activation", "quote",
        "estimate", "review", "approval needed", "client approval",
        "need bid", "bid requested", "awaiting"
    ]
    if any(word in s for word in pending_keywords):
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

def format_date_display(date_val):
    """Format date for display."""
    if pd.isna(date_val):
        return "N/A"
    try:
        return pd.Timestamp(date_val).strftime("%b %d, %Y")
    except:
        return str(date_val)

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
        <h1 style="color: white; margin: 0; font-size: 2em; font-weight: 800;">🏠 CPP</h1>
        <p style="color: rgba(255,255,255,0.6); margin: 5px 0; font-size: 0.85em;">Property Preservation Pro</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Properties", "Add New", "Crew Analytics", "Calendar", "Map View", "Reports", "History"],
        icons=["speedometer2", "houses", "plus-circle", "people", "calendar3", "geo-alt", "file-earmark-text", "clock-history"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "white", "font-size": "16px"},
            "nav-link": {
                "font-size": "13px",
                "text-align": "left",
                "padding": "14px 18px",
                "margin": "4px 8px",
                "border-radius": "10px",
                "color": "rgba(255,255,255,0.7)",
                "font-weight": "500",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white",
                "font-weight": "600",
            },
        }
    )
    
    st.session_state.active_tab = selected
    
    st.markdown("---")
    
    # Quick Filters
    st.markdown("<p style='color: rgba(255,255,255,0.8); font-weight: 600; font-size: 14px;'>🔍 Quick Filters</p>", unsafe_allow_html=True)
    filter_options = ["All", "Overdue", "In Progress", "Pending", "Completed"]
    selected_filter = st.selectbox("Status", filter_options,
                                   index=filter_options.index(st.session_state.filter_status),
                                   label_visibility="collapsed")
    st.session_state.filter_status = selected_filter
    
    # Search
    search = st.text_input("🔎 Search", st.session_state.search_query,
                          placeholder="Property, crew, address...",
                          label_visibility="collapsed")
    st.session_state.search_query = search
    
    st.markdown("---")
    
    # Live indicator
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(46, 204, 113, 0.2) 0%, rgba(39, 174, 96, 0.1) 100%);
                padding: 12px; border-radius: 10px; text-align: center;
                border: 1px solid rgba(46, 204, 113, 0.3);">
        <span style="color: #2ecc71; font-weight: 700; font-size: 14px;">● LIVE</span>
        <span style="color: rgba(255,255,255,0.6); font-size: 11px; display: block; margin-top: 4px;">
            Auto-refresh every 3 min
        </span>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Load Data
# ----------------------------------------------------------------------
with st.spinner("🔄 Loading live data from Google Sheets..."):
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

# Process updates data with FIXED date parsing
df_updates.columns = [c.strip() for c in df_updates.columns]
if "Due date" in df_updates.columns:
    df_updates["Due date"] = df_updates["Due date"].apply(parse_date_american_first)

# Categorize and add computed columns
df_updates["Category"] = df_updates.apply(categorize_status, axis=1)
df_updates["Days Until Due"] = df_updates["Due date"].apply(get_days_until_due)

# Save to historical database
if updates_loaded and not df_updates.empty:
    save_to_history(df_updates)
    save_daily_snapshot(df_updates)

# ----------------------------------------------------------------------
# DASHBOARD VIEW
# ----------------------------------------------------------------------
if st.session_state.active_tab == "Dashboard":
    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="margin: 0; font-size: 3em; font-weight: 800;">🏠 Property Preservation</h1>
        <p style="margin: 15px 0 0 0; font-size: 1.3em; opacity: 0.9; font-weight: 400;">
            Real-time Command Center for Property Management
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
        st.markdown("<h3 style='margin-bottom: 20px;'>📊 Key Performance Indicators</h3>", unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-container">
                <p class="kpi-value">{total}</p>
                <p class="kpi-label">📋 Total Properties</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-container kpi-completed">
                <p class="kpi-value">{completion_rate}%</p>
                <p class="kpi-label">✅ Completion Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-container kpi-overdue">
                <p class="kpi-value">{overdue}</p>
                <p class="kpi-label">⚠️ Overdue</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-container kpi-progress">
                <p class="kpi-value">{in_progress}</p>
                <p class="kpi-label">🔄 In Progress</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="kpi-container kpi-pending">
                <p class="kpi-value">{active_crews}</p>
                <p class="kpi-label">👷 Active Crews</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Main Content Area
        left_col, right_col = st.columns([6, 4])
        
        with left_col:
            # Status Breakdown Chart
            st.markdown("<h3 style='margin-bottom: 15px;'>📈 Status Distribution</h3>", unsafe_allow_html=True)
            
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
                hole=0.5
            )
            fig.update_traces(
                textinfo="percent+label",
                textfont_size=13,
                textfont_color="white",
                pull=[0.08 if s == "❌ Overdue" else 0 for s in status_counts["Status"]]
            )
            fig.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color="white")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Enhanced Weekly Workload with better insights
            st.markdown("<h3 style='margin: 25px 0 15px 0;'>📅 Weekly Workload Forecast</h3>", unsafe_allow_html=True)
            
            today = pd.Timestamp.today().normalize()
            week_data = []
            for i in range(7):
                day = today + timedelta(days=i)
                day_due = df_updates[
                    (df_updates["Due date"].dt.normalize() == day) &
                    (df_updates["Category"] != "✅ Completed")
                ]
                
                # Calculate workload score (overdue weighted more heavily)
                overdue_count = len(day_due[day_due["Category"] == "❌ Overdue"])
                due_count = len(day_due)
                workload_score = overdue_count * 2 + due_count
                
                week_data.append({
                    "Day": day.strftime("%a %d"),
                    "Full Date": day,
                    "Due": due_count,
                    "Overdue": overdue_count,
                    "Workload Score": workload_score,
                    "Is Today": i == 0
                })
            
            week_df = pd.DataFrame(week_data)
            
            # Create enhanced bar chart
            fig2 = go.Figure()
            
            # Background bars for workload score
            fig2.add_trace(go.Bar(
                x=week_df["Day"],
                y=week_df["Workload Score"],
                name="Workload Intensity",
                marker_color=["rgba(102, 126, 234, 0.3)" if not is_today else "rgba(102, 126, 234, 0.5)"
                             for is_today in week_df["Is Today"]],
                width=0.8,
                showlegend=False
            ))
            
            # Due properties
            fig2.add_trace(go.Bar(
                x=week_df["Day"],
                y=week_df["Due"],
                name="Due",
                marker_color="#3498db",
                width=0.5
            ))
            
            # Overdue properties
            fig2.add_trace(go.Bar(
                x=week_df["Day"],
                y=week_df["Overdue"],
                name="Overdue",
                marker_color="#e74c3c",
                width=0.3
            ))
            
            fig2.update_layout(
                barmode="overlay",
                height=280,
                margin=dict(t=20, b=40, l=40, r=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.05)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)", title="Properties")
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Workload insights
            max_workload_day = week_df.loc[week_df["Workload Score"].idxmax()]
            total_overdue_week = week_df["Overdue"].sum()
            total_due_week = week_df["Due"].sum()
            
            insight_cols = st.columns(3)
            with insight_cols[0]:
                st.info(f"📊 **{total_due_week}** properties due this week")
            with insight_cols[1]:
                if total_overdue_week > 0:
                    st.error(f"⚠️ **{total_overdue_week}** overdue properties need attention")
                else:
                    st.success("✅ No overdue properties this week!")
            with insight_cols[2]:
                st.warning(f"🔥 Busiest day: **{max_workload_day['Day']}** ({max_workload_day['Due']} properties)")
        
        with right_col:
            # Enhanced Clickable Insights
            st.markdown("<h3 style='margin-bottom: 15px;'>💡 Actionable Insights</h3>", unsafe_allow_html=True)
            
            today = pd.Timestamp.today()
            
            # Critical Overdue Insight
            if overdue > 0:
                overdue_props = df_updates[df_updates["Category"] == "❌ Overdue"].copy()
                overdue_props["Days Overdue"] = overdue_props["Due date"].apply(
                    lambda x: (today - x).days if pd.notna(x) else 0
                )
                
                with st.expander(f"🚨 {overdue} CRITICAL: Overdue Properties", expanded=True):
                    st.markdown("<p style='color: #ff6b6b; font-size: 12px; margin-bottom: 10px;'>Click property to view details</p>", unsafe_allow_html=True)
                    
                    for _, row in overdue_props.head(5).iterrows():
                        days_past = row["Days Overdue"]
                        urgency = "🔴" if days_past > 7 else "🟠"
                        
                        st.markdown(f"""
                        <div class="property-card overdue" style="padding: 12px; cursor: pointer;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <b style="font-size: 14px;">{row['Property']}</b><br>
                                    <small style="color: #aaa;">👷 {row['CREW NAME']}</small>
                                </div>
                                <div style="text-align: right;">
                                    <span class="date-indicator overdue">{urgency} {days_past} days</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if len(overdue_props) > 5:
                        st.caption(f"... and {len(overdue_props) - 5} more overdue properties")
            
            # Due Soon Insight
            due_soon = df_updates[
                (pd.notna(df_updates["Due date"])) &
                (df_updates["Due date"] <= today + pd.Timedelta(days=3)) &
                (df_updates["Category"] != "✅ Completed") &
                (df_updates["Category"] != "❌ Overdue")
            ].sort_values("Due date")
            
            if len(due_soon) > 0:
                with st.expander(f"⏰ {len(due_soon)} Due Within 3 Days", expanded=True):
                    for _, row in due_soon.head(5).iterrows():
                        days_left = get_days_until_due(row["Due date"])
                        urgency = "🔴" if days_left == 0 else "🟡"
                        
                        st.markdown(f"""
                        <div class="property-card in-progress" style="padding: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <b style="font-size: 14px;">{row['Property']}</b><br>
                                    <small style="color: #aaa;">👷 {row['CREW NAME']}</small>
                                </div>
                                <div>
                                    <span class="date-indicator due-soon">{urgency} {days_left} days left</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Enhanced Top Crews with historical comparison
            if not df_updates["CREW NAME"].dropna().empty:
                st.markdown("---")
                st.markdown("<h4 style='margin-bottom: 15px;'>🏆 Top Performing Crews</h4>", unsafe_allow_html=True)
                
                # Calculate crew performance with more metrics
                crew_performance = []
                for crew in df_updates["CREW NAME"].dropna().unique():
                    crew_data = df_updates[df_updates["CREW NAME"] == crew]
                    total_jobs = len(crew_data)
                    completed_jobs = len(crew_data[crew_data["Category"] == "✅ Completed"])
                    overdue_jobs = len(crew_data[crew_data["Category"] == "❌ Overdue"])
                    in_progress_jobs = len(crew_data[crew_data["Category"] == "🔄 In Progress"])
                    completion_rate = round((completed_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0
                    
                    # Efficiency score: completion rate - overdue penalty
                    efficiency = completion_rate - (overdue_jobs * 5)
                    
                    crew_performance.append({
                        "Crew": crew,
                        "Total": total_jobs,
                        "Completed": completed_jobs,
                        "Overdue": overdue_jobs,
                        "In Progress": in_progress_jobs,
                        "Completion Rate": completion_rate,
                        "Efficiency Score": efficiency
                    })
                
                # Sort by efficiency score
                crew_df = pd.DataFrame(crew_performance).sort_values("Efficiency Score", ascending=False)
                
                # Display top 3 crews
                for idx, (_, crew_row) in enumerate(crew_df.head(3).iterrows()):
                    rank_emoji = ["🥇", "🥈", "🥉"][idx]
                    
                    st.markdown(f"""
                    <div class="crew-card" style="margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div class="crew-avatar" style="width: 50px; height: 50px; font-size: 20px;">
                                {crew_row['Crew'][:2].upper()}
                            </div>
                            <div style="text-align: left; flex: 1;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 20px;">{rank_emoji}</span>
                                    <b style="font-size: 16px;">{crew_row['Crew']}</b>
                                </div>
                                <div style="margin-top: 6px; display: flex; gap: 12px; font-size: 12px;">
                                    <span style="color: #51cf66;">✅ {crew_row['Completed']}/{crew_row['Total']}</span>
                                    <span style="color: #ff6b6b;">⚠️ {crew_row['Overdue']} overdue</span>
                                    <span style="color: #74c0fc;">🔄 {crew_row['In Progress']} active</span>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 24px; font-weight: 800; color: #667eea;">{crew_row['Completion Rate']}%</div>
                                <div style="font-size: 10px; color: #888;">completion</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Pending Bids Alert
            if pending > 0:
                st.markdown("---")
                with st.expander(f"💰 {pending} Pending Bids/Activations"):
                    st.info(f"{pending} properties awaiting bid approval or activation. Follow up with clients to keep workflow moving.")

# ----------------------------------------------------------------------
# PROPERTIES VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Properties":
    st.markdown("<h2 style='margin-bottom: 20px;'>🏠 Property Management</h2>", unsafe_allow_html=True)
    
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
    
    # Stats bar
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 10px; margin-bottom: 20px;">
        <span style="font-size: 14px; color: #aaa;">Showing <b style="color: white;">{len(filtered_df)}</b> of <b style="color: white;">{len(df_updates)}</b> properties</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display properties as cards
    for idx, row in filtered_df.iterrows():
        status_class = {
            "✅ Completed": "completed",
            "❌ Overdue": "overdue",
            "🔄 In Progress": "in-progress",
            "⏳ Pending / Bid": "pending",
            "📌 Other": "pending"
        }.get(row["Category"], "pending")
        
        status_badge_class = {
            "✅ Completed": "completed",
            "❌ Overdue": "overdue",
            "🔄 In Progress": "in-progress",
            "⏳ Pending / Bid": "pending",
            "📌 Other": "pending"
        }.get(row["Category"], "pending")
        
        # Date display
        days = get_days_until_due(row["Due date"])
        if days is not None:
            if days < 0:
                date_display = f"<span class='date-indicator overdue'>⚠️ {abs(days)} days overdue</span>"
            elif days == 0:
                date_display = "<span class='date-indicator due-soon'>📅 Due TODAY</span>"
            elif days <= 3:
                date_display = f"<span class='date-indicator due-soon'>⏰ {days} days left</span>"
            else:
                date_display = f"<span class='date-indicator on-track'>📅 {days} days left</span>"
        else:
            date_display = "<span style='color: #888;'>No due date</span>"
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            st.markdown(f"""
            <div class="property-card {status_class}">
                <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 10px 0; font-size: 16px;">{row['Property']}</h4>
                        <p style="margin: 0; color: #aaa; font-size: 13px; line-height: 1.5;">{row.get('Details', 'No details available')}</p>
                        <div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                            <span class="status-badge {status_badge_class}">{row['Category']}</span>
                            <span style="font-size: 13px; color: #bbb;">👷 {row.get('CREW NAME', 'Unassigned')}</span>
                            {date_display}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📋 Details", key=f"view_{idx}", use_container_width=True):
                st.session_state.selected_property = row.to_dict()
                st.rerun()
        
        # Show details if selected
        if st.session_state.selected_property and st.session_state.selected_property.get("Property") == row["Property"]:
            with st.expander("📋 Property Details", expanded=True):
                detail_col1, detail_col2, detail_col3 = st.columns(3)
                with detail_col1:
                    st.write("**Property:**", row["Property"])
                    st.write("**Details:**", row.get("Details", "N/A"))
                with detail_col2:
                    st.write("**Crew:**", row.get("CREW NAME", "Unassigned"))
                    st.write("**Status:**", row["Category"])
                with detail_col3:
                    st.write("**Due Date:**", format_date_display(row["Due date"]))
                    st.write("**Reason:**", row.get("Reason", "N/A"))

# ----------------------------------------------------------------------
# ADD NEW PROPERTY VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Add New":
    st.markdown("<h2 style='margin-bottom: 20px;'>➕ Add New Property / Update</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 12px; padding: 20px; margin-bottom: 25px;">
        <p style="margin: 0; color: #aaa; font-size: 14px;">
            💡 <b>Tip:</b> Use this form to add new properties or update existing ones.
            Changes will be saved to the local database and can be synced to Google Sheets later.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🆕 New Property", "📝 Quick Update"])
    
    with tab1:
        with st.form("new_property_form"):
            st.markdown("<h4 style='margin-bottom: 20px;'>Property Information</h4>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                property_name = st.text_input("🏠 Property Name *", placeholder="e.g., 1227 EAGLES NEST TRL")
                wo_number = st.text_input("📋 W/O Number", placeholder="e.g., WO-2024-001")
                address = st.text_area("📍 Full Address", placeholder="e.g., 1227 EAGLES NEST TRL, KRUM, TX 76249")
            
            with col2:
                crew_name = st.selectbox(
                    "👷 Assign Crew *",
                    options=[""] + list(df_updates["CREW NAME"].dropna().unique()) if not df_updates.empty else [""],
                    format_func=lambda x: x if x else "-- Select Crew --"
                )
                
                status = st.selectbox(
                    "📊 Status *",
                    options=["", "Pending / Bid", "In Progress", "Completed", "Overdue"],
                    format_func=lambda x: x if x else "-- Select Status --"
                )
                
                due_date = st.date_input("📅 Due Date", value=None)
            
            details = st.text_area("📝 Work Details", placeholder="Describe the work needed...")
            reason = st.text_area("💬 Notes/Reason", placeholder="Any additional notes...")
            
            submitted = st.form_submit_button("💾 Save Property", use_container_width=True)
            
            if submitted:
                if not property_name or not crew_name or not status:
                    st.error("❌ Please fill in all required fields (marked with *)")
                else:
                    # Save to database
                    due_date_str = due_date.strftime("%Y-%m-%d") if due_date else None
                    add_user_update(
                        property_name=property_name,
                        crew_name=crew_name,
                        status=status,
                        due_date=due_date_str,
                        details=details,
                        reason=reason,
                        updated_by="User"
                    )
                    
                    st.success(f"✅ Property '{property_name}' saved successfully!")
                    st.balloons()
                    
                    # Show confirmation
                    st.markdown(f"""
                    <div style="background: rgba(39, 174, 96, 0.1); border: 1px solid rgba(39, 174, 96, 0.3);
                                border-radius: 10px; padding: 15px; margin-top: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: #51cf66;">✅ Property Added</h4>
                        <p style="margin: 0; color: #aaa; font-size: 13px;">
                            <b>Property:</b> {property_name}<br>
                            <b>Crew:</b> {crew_name}<br>
                            <b>Status:</b> {status}<br>
                            <b>Due Date:</b> {due_date_str or 'Not set'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.markdown("<h4 style='margin-bottom: 20px;'>Quick Status Update</h4>", unsafe_allow_html=True)
        
        # Get existing properties for quick update
        existing_properties = df_updates["Property"].tolist() if not df_updates.empty else []
        
        if existing_properties:
            with st.form("quick_update_form"):
                selected_prop = st.selectbox(
                    "🏠 Select Property *",
                    options=[""] + existing_properties,
                    format_func=lambda x: x if x else "-- Select Property --"
                )
                
                update_col1, update_col2 = st.columns(2)
                
                with update_col1:
                    new_status = st.selectbox(
                        "📊 New Status *",
                        options=["", "Pending / Bid", "In Progress", "Completed", "Overdue"],
                        format_func=lambda x: x if x else "-- Select Status --"
                    )
                
                with update_col2:
                    new_due_date = st.date_input("📅 Update Due Date (optional)", value=None)
                
                update_notes = st.text_area("💬 Update Notes", placeholder="What changed?")
                
                update_submitted = st.form_submit_button("🔄 Update Property", use_container_width=True)
                
                if update_submitted:
                    if not selected_prop or not new_status:
                        st.error("❌ Please select a property and status")
                    else:
                        # Get current property info
                        prop_data = df_updates[df_updates["Property"] == selected_prop].iloc[0]
                        
                        due_date_str = new_due_date.strftime("%Y-%m-%d") if new_due_date else str(prop_data.get("Due date", ""))
                        
                        add_user_update(
                            property_name=selected_prop,
                            crew_name=prop_data.get("CREW NAME", ""),
                            status=new_status,
                            due_date=due_date_str,
                            details=prop_data.get("Details", ""),
                            reason=update_notes,
                            updated_by="User"
                        )
                        
                        st.success(f"✅ '{selected_prop}' updated to '{new_status}'!")
        else:
            st.info("ℹ️ No existing properties found. Add a new property first.")

# ----------------------------------------------------------------------
# CREW ANALYTICS VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Crew Analytics":
    st.markdown("<h2 style='margin-bottom: 20px;'>👷 Crew Performance Analytics</h2>", unsafe_allow_html=True)
    
    if not df_updates["CREW NAME"].dropna().empty:
        # Calculate comprehensive crew stats
        crew_stats = []
        for crew in df_updates["CREW NAME"].dropna().unique():
            crew_data = df_updates[df_updates["CREW NAME"] == crew]
            total = len(crew_data)
            completed = len(crew_data[crew_data["Category"] == "✅ Completed"])
            overdue = len(crew_data[crew_data["Category"] == "❌ Overdue"])
            in_progress = len(crew_data[crew_data["Category"] == "🔄 In Progress"])
            pending = len(crew_data[crew_data["Category"] == "⏳ Pending / Bid"])
            completion_rate = round((completed / total * 100), 1) if total > 0 else 0
            
            # Calculate average completion time (if we had start dates)
            # For now, use efficiency score
            efficiency = completion_rate - (overdue * 3)
            
            crew_stats.append({
                "Crew": crew,
                "Total": total,
                "Completed": completed,
                "Overdue": overdue,
                "In Progress": in_progress,
                "Pending": pending,
                "Completion Rate": completion_rate,
                "Efficiency": efficiency
            })
        
        crew_df = pd.DataFrame(crew_stats).sort_values("Efficiency", ascending=False)
        
        # Top performers row
        st.markdown("<h4 style='margin-bottom: 15px;'>🏆 Top Performers</h4>", unsafe_allow_html=True)
        
        top_cols = st.columns(min(len(crew_df), 4))
        for idx, (_, crew_row) in enumerate(crew_df.head(4).iterrows()):
            with top_cols[idx]:
                st.markdown(f"""
                <div class="crew-card">
                    <div class="crew-avatar">{crew_row['Crew'][:2].upper()}</div>
                    <h4 style="margin: 0; font-size: 16px;">{crew_row['Crew']}</h4>
                    <p style="margin: 10px 0; font-size: 32px; font-weight: 800; color: #667eea;">{crew_row['Completion Rate']}%</p>
                    <p style="margin: 0; font-size: 12px; color: #888;">{crew_row['Completed']}/{crew_row['Total']} completed</p>
                    <div style="margin-top: 15px; display: flex; justify-content: center; gap: 15px; font-size: 11px;">
                        <span style="color: #ff6b6b;">● {crew_row['Overdue']} overdue</span>
                        <span style="color: #ffd43b;">● {crew_row['In Progress']} active</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("<h4 style='margin-bottom: 15px;'>📊 Completion Rate Comparison</h4>", unsafe_allow_html=True)
            
            fig = px.bar(
                crew_df,
                x="Crew",
                y="Completion Rate",
                color="Completion Rate",
                color_continuous_scale=["#e74c3c", "#f39c12", "#27ae60"],
                text="Completion Rate"
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(
                height=350,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.05)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)", range=[0, 105])
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            st.markdown("<h4 style='margin-bottom: 15px;'>📈 Workload Distribution</h4>", unsafe_allow_html=True)
            
            # Stacked bar chart
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Completed", x=crew_df["Crew"], y=crew_df["Completed"], marker_color="#27ae60"))
            fig2.add_trace(go.Bar(name="In Progress", x=crew_df["Crew"], y=crew_df["In Progress"], marker_color="#f39c12"))
            fig2.add_trace(go.Bar(name="Overdue", x=crew_df["Crew"], y=crew_df["Overdue"], marker_color="#e74c3c"))
            fig2.add_trace(go.Bar(name="Pending", x=crew_df["Crew"], y=crew_df["Pending"], marker_color="#3498db"))
            
            fig2.update_layout(
                barmode="stack",
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.05)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed crew table
        st.markdown("---")
        st.markdown("<h4 style='margin-bottom: 15px;'>📋 Detailed Crew Statistics</h4>", unsafe_allow_html=True)
        
        st.dataframe(
            crew_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Crew": st.column_config.TextColumn("👷 Crew Name"),
                "Total": st.column_config.NumberColumn("📋 Total", width="small"),
                "Completed": st.column_config.NumberColumn("✅ Done", width="small"),
                "Overdue": st.column_config.NumberColumn("❌ Late", width="small"),
                "In Progress": st.column_config.NumberColumn("🔄 Active", width="small"),
                "Pending": st.column_config.NumberColumn("⏳ Pending", width="small"),
                "Completion Rate": st.column_config.ProgressColumn("📊 Rate", min_value=0, max_value=100, format="%d%%", width="medium"),
                "Efficiency": st.column_config.NumberColumn("⚡ Score", width="small")
            }
        )

# ----------------------------------------------------------------------
# CALENDAR VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Calendar":
    st.markdown("<h2 style='margin-bottom: 20px;'>📅 Calendar View</h2>", unsafe_allow_html=True)
    
    today = pd.Timestamp.today().normalize()
    
    # Calendar filters
    cal_col1, cal_col2, cal_col3 = st.columns([1, 1, 2])
    with cal_col1:
        view_range = st.selectbox("View Range", ["Next 7 Days", "Next 14 Days", "Next 30 Days", "This Month"])
    with cal_col2:
        filter_by_crew = st.selectbox(
            "Filter by Crew",
            options=["All Crews"] + list(df_updates["CREW NAME"].dropna().unique()) if not df_updates.empty else ["All Crews"]
        )
    
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
    
    # Apply crew filter
    if filter_by_crew != "All Crews":
        calendar_props = calendar_props[calendar_props["CREW NAME"] == filter_by_crew]
    
    # Summary stats
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 10px; margin-bottom: 20px;">
        <span style="font-size: 14px; color: #aaa;">
            📊 <b style="color: white;">{len(calendar_props)}</b> properties due in selected period
            {f" | 👷 Filtered by: <b style='color: white;'>{filter_by_crew}</b>" if filter_by_crew != "All Crews" else ""}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Group by date
    if not calendar_props.empty:
        for date in pd.date_range(today, end_date, freq='D'):
            day_props = calendar_props[calendar_props["Due date"].dt.normalize() == date]
            if not day_props.empty:
                is_today = date == today
                date_label = "📅 TODAY" if is_today else date.strftime("%A, %B %d, %Y")
                border_color = "#f39c12" if is_today else "#3498db"
                
                st.markdown(f"""
                <div style="background: {'rgba(243, 156, 18, 0.1)' if is_today else 'rgba(255,255,255,0.03)'};
                            padding: 15px 20px; border-radius: 12px; margin: 15px 0;
                            border-left: 4px solid {border_color};">
                    <h4 style="margin: 0; font-size: 16px;">{date_label} ({len(day_props)} properties)</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for _, prop in day_props.iterrows():
                    status_class = {
                        "✅ Completed": "completed",
                        "❌ Overdue": "overdue",
                        "🔄 In Progress": "in-progress",
                        "⏳ Pending / Bid": "pending"
                    }.get(prop["Category"], "pending")
                    
                    days_left = get_days_until_due(prop["Due date"])
                    urgency = "🔴" if days_left == 0 else "⏰"
                    
                    st.markdown(f"""
                    <div class="property-card {status_class}" style="margin-left: 20px; padding: 12px 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <b style="font-size: 14px;">{prop['Property']}</b>
                                <span style="margin-left: 10px; font-size: 12px; color: #888;">👷 {prop.get('CREW NAME', 'Unassigned')}</span>
                            </div>
                            <div>
                                <span class="status-badge {status_class}" style="font-size: 10px;">{prop['Category']}</span>
                                <span style="margin-left: 8px; font-size: 12px;">{urgency} {days_left} days</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.success("🎉 No properties due in this period!")

# ----------------------------------------------------------------------
# MAP VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Map View":
    st.markdown("<h2 style='margin-bottom: 20px;'>🗺️ Interactive Property Map</h2>", unsafe_allow_html=True)
    
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
                    <div style='font-family: Inter, sans-serif; font-size:13px; min-width: 220px; padding: 10px;'>
                        <h4 style='margin: 0 0 12px 0; color: {color}; font-weight: 700;'>🏠 Property</h4>
                        <p style='margin: 6px 0;'><b>W/O:</b> {wo}</p>
                        <p style='margin: 6px 0;'><b>Address:</b> {address}</p>
                        <p style='margin: 6px 0;'><b>Status:</b> <span style='color: {color}; font-weight: 600;'>{status}</span></p>
                        <p style='margin: 6px 0;'><b>Vendor:</b> {vendor}</p>
                    </div>
                """
                iframe = IFrame(popup_html, width=280, height=180)
                
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
        background: rgba(30, 30, 50, 0.95);
        border: 1px solid rgba(255,255,255,0.1);
        z-index: 9999;
        font-size: 14px;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        font-family: Inter, sans-serif;
        color: white;
    ">
    <b style="font-size:16px; margin-bottom: 12px; display: block;">📍 Status Legend</b>
    <div style="margin: 10px 0;"><span style="color:#e74c3c; font-size:18px;">●</span> Overdue</div>
    <div style="margin: 10px 0;"><span style="color:#f39c12; font-size:18px;">●</span> In Progress</div>
    <div style="margin: 10px 0;"><span style="color:#3498db; font-size:18px;">●</span> Pending/Bid</div>
    <div style="margin: 10px 0;"><span style="color:#27ae60; font-size:18px;">●</span> Completed</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width=1200, height=700)

# ----------------------------------------------------------------------
# REPORTS VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "Reports":
    st.markdown("<h2 style='margin-bottom: 20px;'>📊 Reports & Analytics</h2>", unsafe_allow_html=True)
    
    report_type = st.selectbox("Select Report Type", [
        "Executive Summary",
        "Overdue Properties Report",
        "Crew Performance Report",
        "Weekly Status Report",
        "Historical Trends"
    ])
    
    if report_type == "Executive Summary":
        st.markdown("<h4 style='margin-bottom: 20px;'>Executive Summary</h4>", unsafe_allow_html=True)
        
        total = len(df_updates)
        completed = (df_updates["Category"] == "✅ Completed").sum()
        overdue = (df_updates["Category"] == "❌ Overdue").sum()
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        
        summary_cols = st.columns(4)
        summary_cols[0].metric("Total Properties", total)
        summary_cols[1].metric("Completion Rate", f"{completion_rate}%")
        summary_cols[2].metric("Overdue Properties", overdue, delta=f"-{overdue}" if overdue > 0 else None, delta_color="inverse")
        summary_cols[3].metric("Active Crews", df_updates["CREW NAME"].dropna().nunique())
        
        # Status breakdown
        st.markdown("---")
        st.markdown("<h4 style='margin-bottom: 15px;'>Status Breakdown</h4>", unsafe_allow_html=True)
        status_df = df_updates["Category"].value_counts().reset_index()
        status_df.columns = ["Status", "Count"]
        
        fig = px.bar(status_df, x="Status", y="Count", color="Status",
                     color_discrete_map={
                         "✅ Completed": "#27ae60",
                         "❌ Overdue": "#e74c3c",
                         "🔄 In Progress": "#f39c12",
                         "⏳ Pending / Bid": "#3498db"
                     })
        fig.update_layout(
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.05)",
            font=dict(color="white"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Export
        st.markdown("---")
        csv = df_updates.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Report (CSV)",
            data=csv,
            file_name=f"executive_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    elif report_type == "Overdue Properties Report":
        st.markdown("<h4 style='margin-bottom: 20px;'>Overdue Properties Report</h4>", unsafe_allow_html=True)
        
        overdue_df = df_updates[df_updates["Category"] == "❌ Overdue"].copy()
        
        if not overdue_df.empty:
            today = pd.Timestamp.today()
            overdue_df["Days Overdue"] = overdue_df["Due date"].apply(
                lambda x: (today - x).days if pd.notna(x) else 0
            )
            
            st.error(f"⚠️ {len(overdue_df)} properties are overdue and need immediate attention")
            
            st.dataframe(
                overdue_df[["Property", "CREW NAME", "Due date", "Days Overdue", "Status 1", "Reason", "Details"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Days Overdue": st.column_config.NumberColumn("Days Late", help="Number of days past due date")
                }
            )
            
            # Export
            csv = overdue_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Overdue Report",
                data=csv,
                file_name=f"overdue_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.success("🎉 No overdue properties! Great job!")
    
    elif report_type == "Crew Performance Report":
        st.markdown("<h4 style='margin-bottom: 20px;'>Crew Performance Report</h4>", unsafe_allow_html=True)
        
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
            
            crew_perf_df = pd.DataFrame(crew_performance).sort_values("Completion Rate (%)", ascending=False)
            st.dataframe(crew_perf_df, use_container_width=True, hide_index=True)
            
            # Export
            csv = crew_perf_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Crew Report",
                data=csv,
                file_name=f"crew_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    elif report_type == "Historical Trends":
        st.markdown("<h4 style='margin-bottom: 20px;'>📈 Historical Trends (30 Days)</h4>", unsafe_allow_html=True)
        
        hist_data = get_historical_data(days=30)
        
        if not hist_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_data["snapshot_date"], y=hist_data["total_properties"],
                                     name="Total", mode="lines+markers", line=dict(color="#667eea")))
            fig.add_trace(go.Scatter(x=hist_data["snapshot_date"], y=hist_data["completed"],
                                     name="Completed", mode="lines+markers", line=dict(color="#27ae60")))
            fig.add_trace(go.Scatter(x=hist_data["snapshot_date"], y=hist_data["overdue"],
                                     name="Overdue", mode="lines+markers", line=dict(color="#e74c3c")))
            
            fig.update_layout(
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.05)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)", title="Date"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)", title="Count"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Not enough historical data yet. Data will accumulate over time.")

# ----------------------------------------------------------------------
# HISTORY VIEW
# ----------------------------------------------------------------------
elif st.session_state.active_tab == "History":
    st.markdown("<h2 style='margin-bottom: 20px;'>🕐 Historical Data</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 12px; padding: 20px; margin-bottom: 25px;">
        <p style="margin: 0; color: #aaa; font-size: 14px;">
            📊 <b>Historical Tracking:</b> This dashboard automatically saves daily snapshots and property updates
            to a local database. Even if data is deleted from Google Sheets, you'll have a record here.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    hist_tab1, hist_tab2 = st.tabs(["📋 All Historical Properties", "👤 Recent User Updates"])
    
    with hist_tab1:
        hist_props = get_all_historical_properties()
        
        if not hist_props.empty:
            st.markdown(f"<p style='color: #aaa; margin-bottom: 15px;'>Showing {len(hist_props)} historical property records</p>", unsafe_allow_html=True)
            
            st.dataframe(
                hist_props[["property_name", "crew_name", "status", "category", "due_date", "date_added"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "property_name": st.column_config.TextColumn("Property"),
                    "crew_name": st.column_config.TextColumn("Crew"),
                    "status": st.column_config.TextColumn("Status"),
                    "category": st.column_config.TextColumn("Category"),
                    "due_date": st.column_config.TextColumn("Due Date"),
                    "date_added": st.column_config.DatetimeColumn("Recorded", format="MMM DD, YYYY")
                }
            )
        else:
            st.info("ℹ️ No historical data yet. Data will be saved automatically as you use the dashboard.")
    
    with hist_tab2:
        conn = sqlite3.connect(DB_PATH)
        user_updates = pd.read_sql_query(
            "SELECT * FROM user_updates ORDER BY timestamp DESC LIMIT 50",
            conn
        )
        conn.close()
        
        if not user_updates.empty:
            st.markdown(f"<p style='color: #aaa; margin-bottom: 15px;'>Showing {len(user_updates)} recent user updates</p>", unsafe_allow_html=True)
            
            st.dataframe(
                user_updates[["property_name", "crew_name", "status", "due_date", "updated_by", "timestamp"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "property_name": st.column_config.TextColumn("Property"),
                    "crew_name": st.column_config.TextColumn("Crew"),
                    "status": st.column_config.TextColumn("New Status"),
                    "due_date": st.column_config.TextColumn("Due Date"),
                    "updated_by": st.column_config.TextColumn("Updated By"),
                    "timestamp": st.column_config.DatetimeColumn("When", format="MMM DD, HH:mm")
                }
            )
        else:
            st.info("ℹ️ No user updates yet. Updates will appear here when you add or modify properties.")

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 30px 20px; color: #666;">
    <p style="font-size: 14px; margin: 0;">🏠 <b style="color: #888;">Property Preservation Pro Dashboard</b></p>
    <p style="font-size: 12px; margin: 8px 0 0 0; color: #555;">
        Live Data from Google Sheets | Historical Tracking Enabled
    </p>
    <p style="font-size: 11px; margin: 5px 0 0 0; color: #444;">
        Last updated: {}
    </p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
