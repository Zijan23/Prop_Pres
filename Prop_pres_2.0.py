# -*- coding: utf-8 -*-
"""app_1 - Property Preservation Dashboard"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from shapely.geometry import Point
from folium import IFrame
import os

# --- Streamlit Page Config ---
st.set_page_config(page_title="Property Preservation Live Report", layout="wide")

st.title("🏠 CPP Dashboard")
st.subheader("🔍 Zoom in/out and click on any property to see its details")

# --- Google Sheets live data source ---
SHEET_ID = "1AxNmdkDGxYhi0-3-bZGdng-hT1KzxHqpgn_82eqglYg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)  # cache for 5 minutes
def load_data():
    return pd.read_csv(CSV_URL)

try:
    df = load_data()
    st.success("✅ Live property data loaded from Google Sheets")
except Exception as e:
    st.error(f"❌ Failed to load Google Sheet: {e}")
    df = pd.DataFrame(columns=["W/O Number","address","latitude","longitude","status","vendor","W/O Type","Due Date","Complete Date", "notes", "Detailed Services", "Attach Photos"])

# --- Sidebar: Admin Controls & Resources ---
st.sidebar.header("Admin Controls")
st.sidebar.title("📂 Resources")

sections = ["VRM", "Cyprex", "Pricing", "Other"]
selected_section = st.sidebar.selectbox("Select Section", sections)

# Admin file upload
st.sidebar.markdown("### Upload a file")
uploaded_resource = st.sidebar.file_uploader(
    f"Upload file to {selected_section}", 
    type=["pdf", "docx", "xlsx", "csv", "txt"]
)

if uploaded_resource:
    os.makedirs("resources", exist_ok=True)
    save_path = f"resources/{selected_section}_{uploaded_resource.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_resource.getbuffer())
    st.sidebar.success(f"✅ File uploaded to {selected_section} section!")

# --- Convert to GeoDataFrame ---
if not df.empty and {"latitude", "longitude"}.issubset(df.columns):
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
        crs="EPSG:4326"
    )
else:
    st.warning("⚠️ No valid geographic data found. Check your Google Sheet columns.")
    gdf = gpd.GeoDataFrame(columns=["geometry"])

# --- Create Map ---
if not gdf.empty:
    map_center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()]
else:
    map_center = [24.0, 90.0]  # Fallback: Bangladesh center

# Your OpenWeatherMap API key (sign up at openweathermap.org for free)
OWM_API_KEY = "9ab014df3ac7ed08dc86c07d88a7941b"  # Replace!

# Your TomTom API key (optional, for traffic; sign up at developer.tomtom.com)
TOMTOM_API_KEY = "kx2GxCYzq5RP8TEsePw7OXVpwF5VYv2f"  # Replace or remove if not using

m = folium.Map(location=map_center, zoom_start=13, tiles=None)  # Start with no base tiles (we'll add them below)

# --- Add Basemaps (mutually exclusive; radio buttons in control) ---
# Current default: CartoDB Positron (clean, light)
folium.TileLayer(
    tiles="CartoDB positron",
    name="Light Map (Default)",
    attr="CartoDB"
).add_to(m)

# Route/Navigation: OpenStreetMap (emphasizes roads, good for routing)
folium.TileLayer(
    tiles="OpenStreetMap",
    name="Routes & Navigation (OSM)",
    attr="OpenStreetMap contributors"
).add_to(m)

# Alternative terrain basemap (for visual variety, e.g., hilly routes)
folium.TileLayer(
    tiles="Stamen Terrain",
    name="Terrain Map",
    attr="Stamen Design"
).add_to(m)

# --- Add Overlays (toggle on/off; checkboxes in control) ---
# Weather: Clouds (from OpenWeatherMap)
folium.TileLayer(
    tiles=f"http://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}",
    attr="OpenWeatherMap",
    name="Weather: Clouds",
    overlay=True,
    control=True,
    opacity=0.6  # Semi-transparent so markers show through
).add_to(m)

# Weather: Precipitation (from OpenWeatherMap)
folium.TileLayer(
    tiles=f"http://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}",
    attr="OpenWeatherMap",
    name="Weather: Precipitation",
    overlay=True,
    control=True,
    opacity=0.6
).add_to(m)

# Traffic: Real-time flow (from TomTom; optional)
if TOMTOM_API_KEY:  # Only add if you have a key
    folium.TileLayer(
        tiles=f"https://api.tomtom.com/traffic/map/4/tile/flow/relative/{{z}}/{{x}}/{{y}}.png?key={TOMTOM_API_KEY}",
        attr="TomTom",
        name="Traffic Flow",
        overlay=True,
        control=True,
        opacity=0.7
    ).add_to(m)

# Cyclones: Add as GeoJSON overlay (example historical tracks; fetch real-time if needed)
# Sample public GeoJSON URL (NOAA Atlantic hurricanes; replace with Bangladesh/Indian Ocean data, e.g., from IMD or GDACS)
cyclone_geojson_url = "https://www.nhc.noaa.gov/gis/best_track/al2023_best_track.zip"  # This is a ZIP—use a direct GeoJSON if possible
# For simplicity, assume you have a GeoJSON file or URL; here's how to add it
cyclone_geojson_url = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/cyclone_tracks.geojson"
folium.GeoJson(
    cyclone_geojson_url,
    name="Cyclones/Hurricanes",
    style_function=lambda feature: {'color': 'red', 'weight': 2},
    overlay=True,
    control=True
).add_to(m)


#status colors

status_colors = {
    "Overdue": "red",
    "Bid request": "orange",
    "Biweekly": "green"
}
#marker cluster
marker_cluster = MarkerCluster().add_to(m)

# Clean and validate numeric coordinates
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"])

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    df,
    geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
    crs="EPSG:4326"
)

# --- Draw map markers ---
for _, row in gdf.iterrows():
    
# ── New version ──
    detailed_url = row.get("Detailed Services URL", row.get("Detailed Services", ""))  # fallback to old column if needed

    if pd.notna(detailed_url) and str(detailed_url).strip().startswith(("http://", "https://")):
        detailed_services_html = (
            '<a href="{url}" target="_blank" style="color:#1E90FF; text-decoration:underline; font-weight:bold;">'
            'Click here'
            '</a>'
        ).format(url=detailed_url.strip())
    else:
        detailed_services_html = "No link available"

# --- Draw map markers ---
for _, row in gdf.iterrows():
    detailed_services_link = row.get("Detailed Services", "")
    if pd.notna(detailed_services_link) and str(detailed_services_link).startswith("http"):
        detailed_services_html = f'<a href="{detailed_services_link}" target="_blank" style="color:#1E90FF;">Open Details</a>'
    else:
        detailed_services_html = str(detailed_services_link)
    attach_photos_link = row.get("Attach Photos", "")

    if pd.notna(attach_photos_link) and "drive.google.com/drive/folders/" in str(attach_photos_link):
        photos_html = (
            '<b>Attach Photos:</b> '
            '<a href="{url}" target="_blank" '
            'style="color:#1E90FF; text-decoration:underline; font-weight:bold;">'
            'Upload photos here →'
            '</a>'
        ).format(url=attach_photos_link.strip())
    else:
        photos_html = '<br><b>Attach Photos:</b> No upload link available'
    

    html = f"""
    <div style='font-size:14px;'>
        <b>W/O Number:</b> {row.get('W/O Number', '')}<br>
        <b>Address:</b> {row.get('address', '')}<br>
        <b>Latitude:</b> {row.get('latitude', '')}<br>
        <b>Longitude:</b> {row.get('longitude', '')}<br>
        <b>Status:</b> {row.get('status', '')}<br>
        <b>Vendor:</b> {row.get('vendor', '')}<br>
        <b>W/O Type:</b> {row.get('W/O Type', '')}<br>
        <b>Due Date:</b> {row.get('Due Date', '')}<br>
        <b>Complete Date:</b> {row.get('Complete Date', '')}<br>
        <b>Notes:</b> {row.get('notes', '')}<br>
        <b>Detailed Services:</b> {detailed_services_html}<br>
        {photos_html}
    </div>
    """

    iframe = IFrame(html=html, width=300, height=200)
    popup = folium.Popup(iframe, max_width=300)

    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=6,
        color=status_colors.get(row.get("status", ""), "gray"),
        fill=True,
        fill_color=status_colors.get(row.get("status", ""), "gray"),
        fill_opacity=0.9,
        popup=popup,
    ).add_to(marker_cluster)


# --- Add Legend ---
legend_html = """
<div style="
    position: fixed; 
    bottom: 40px; left: 40px; width: 180px; height: 130px; 
    background-color: white; 
    border:2px solid grey; 
    z-index:9999; 
    font-size:14px; 
    border-radius:8px;
    padding:10px;
    box-shadow:2px 2px 5px rgba(0,0,0,0.3);
">
<b>Status Legend</b><br>
<span style="color:red;">&#9679;</span> Overdue<br>
<span style="color:orange;">&#9679;</span> Bid request<br>
<span style="color:green;">&#9679;</span> Biweekly
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# --- Add Layer Control (clickable options in top-right corner) ---
folium.LayerControl(collapsed=False).add_to(m)  # collapsed=False keeps it open by default

# --- Render Map ---
st_folium(m, width=1300, height=650)
