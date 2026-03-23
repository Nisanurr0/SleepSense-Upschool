import streamlit as st
import sqlite3
import os
import requests
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

st.set_page_config(page_title="SleepSense", page_icon="🌙", layout="wide")

tema = st.sidebar.selectbox("Tema Seç", ["Yeşil", "Mor", "Mavi"], index=0)

if tema == "Yeşil":
    bg_color = "rgba(0,100,0,0.9)"
    accent   = "rgba(0,255,0,0.1)"
    avatar   = "🐢"
elif tema == "Mor":
    bg_color = "rgba(75,0,130,0.9)"
    accent   = "rgba(255,0,255,0.1)"
    avatar   = "🐻"
else:
    bg_color = "rgba(0,0,139,0.9)"
    accent   = "rgba(0,191,255,0.1)"
    avatar   = "🐠"

css = f"""
<style>
.stApp {{
    background:
        radial-gradient(circle at 30% 40%, {accent} 0%, transparent 30%),
        radial-gradient(circle at 70% 60%, {accent} 0%, transparent 30%),
        linear-gradient(135deg, {bg_color} 0%, rgba(0,0,0,0.95) 100%) !important;
}}
.avatar {{
    position: fixed;
    bottom: 30px;
    right: 30px;
    font-size: 60px;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

GROQ_KEY        = os.environ.get("GROQ_API_KEY", "")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

client = None
try:
    from groq import Groq
    if GROQ_KEY:
        client = Groq(api_key=GROQ_KEY)
except:
    client = None

# =========================
# 🔥 FIXED FUNCTIONS
# =========================

def get_coordinates(address):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        headers = {"User-Agent": "SleepSense/1.0"}

        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()

        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            st.sidebar.write("📍 Koordinat:", lat, lon)

            return lat, lon, data[0].get("display_name", address)

    except Exception as e:
        st.sidebar.error(f"Koordinat hatası: {e}")

    # FALLBACK
    st.sidebar.warning("Adres bulunamadı → Ankara kullanılıyor")
    return 39.9334, 32.8597, "Ankara"


def get_weather(lat, lon):
    if not OPENWEATHER_KEY:
        st.sidebar.error("API key yok")
        return None

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_KEY,
            "units": "metric",
            "lang": "tr"
        }

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        st.sidebar.write("🌤 Weather:", data)

        if r.status_code == 200:
            return {
                "desc": data["weather"][0]["description"],
                "temp": round(data["main"]["temp"]),
                "feels": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind": round(data["wind"]["speed"] * 3.6, 1),
            }

    except Exception as e:
        st.sidebar.error(f"Hava hatası: {e}")

    return None


def get_noise_sources(lat, lon, radius=1500):
    found = []

    try:
        query = f"""
        [out:json];
        node(around:{radius},{lat},{lon})["amenity"];
        out;
        """

        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": query}, timeout=10)

        data = r.json()
        st.sidebar.write("🔊 Noise:", data)

        for el in data.get("elements", []):
            name = el.get("tags", {}).get("amenity")
            if name:
                found.append(name)

    except Exception as e:
        st.sidebar.error(f"Gürültü hatası: {e}")

    return list(set(found))


# =========================

st.title("🌙 SleepSense")

address = st.sidebar.text_input("Adres")

if st.sidebar.button("🔄 Konumu Yenile"):
    st.session_state["location_info"] = None

if address:
    with st.sidebar:
        lat, lon, _ = get_coordinates(address)
        weather = get_weather(lat, lon)
        noise = get_noise_sources(lat, lon)

        if weather:
            st.write(f"🌤 {weather['desc']} {weather['temp']}°C")
        else:
            st.write("Hava alınamadı")

        if noise:
            st.write("🔊 Gürültü:", ", ".join(noise[:5]))
        else:
            st.write("Sessiz bölge")

st.write("Uygulama çalışıyor 🎉")