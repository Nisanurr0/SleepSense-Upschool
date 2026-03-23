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
    background-size: 300px 300px, 400px 400px, 100% 100% !important;
    background-repeat: no-repeat !important;
}}
.avatar {{
    position: fixed;
    bottom: 30px;
    right: 30px;
    font-size: 60px;
    z-index: 100;
    animation: floatbounce 3s ease-in-out infinite;
}}
@keyframes floatbounce {{
    0%   {{ transform: translateY(0px)   translateX(0px); }}
    25%  {{ transform: translateY(-10px) translateX(8px); }}
    50%  {{ transform: translateY(-20px) translateX(0px); }}
    75%  {{ transform: translateY(-10px) translateX(-8px); }}
    100% {{ transform: translateY(0px)   translateX(0px); }}
}}
.chat-bubble {{
    position: fixed;
    bottom: 110px;
    right: 20px;
    background: rgba(255,255,255,0.95);
    border: 2px solid rgba(100,200,255,0.6);
    border-radius: 15px;
    padding: 12px 15px;
    max-width: 250px;
    z-index: 99;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    font-size: 14px;
    color: #333;
    word-wrap: break-word;
}}
.chat-bubble::after {{
    content: '';
    position: absolute;
    bottom: -8px;
    right: 30px;
    width: 0; height: 0;
    border-left: 8px solid transparent;
    border-top: 8px solid rgba(255,255,255,0.95);
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
    else:
        st.sidebar.warning("⚠️ GROQ_API_KEY .env dosyasında bulunamadı.")
except Exception as e:
    st.sidebar.error(f"Groq yüklenemedi: {e}")
    client = None

def ask_ai(prompt):
    # Model ismi güncellendi: llama-3.3-70b-versatile
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return response.choices[0].message.content

def get_coordinates(address):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        headers = {"User-Agent": "SleepSense/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", address)
    except Exception:
        pass
    return None, None, None

def get_noise_sources(lat, lon, radius=500):
    noise_tags = {
        "highway": {"motorway": "Otoyol", "trunk": "Ana yol", "primary": "Ana cadde"},
        "amenity":  {"nightclub": "Gece kulübü", "bar": "Bar", "pub": "Pub",
                     "restaurant": "Restoran", "fast_food": "Fast food"},
        "landuse":  {"industrial": "Sanayi bölgesi", "commercial": "Ticaret bölgesi"},
        "railway":  {"rail": "Demiryolu", "subway": "Metro hattı"},
        "aeroway":  {"aerodrome": "Havalimanı"},
    }
    found = []
    try:
        query_parts = []
        for tag, values in noise_tags.items():
            for val in values:
                query_parts.append(f'node["{tag}"="{val}"](around:{radius},{lat},{lon});')
                query_parts.append(f'way["{tag}"="{val}"](around:{radius},{lat},{lon});')
        overpass_query = f"[out:json][timeout:10];( {''.join(query_parts)} );out tags;"
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": overpass_query}, timeout=15)
        elements = r.json().get("elements", [])
        seen = set()
        for el in elements:
            tags = el.get("tags", {})
            for tag, values in noise_tags.items():
                val = tags.get(tag)
                if val and val in values:
                    label = values[val]
                    if label not in seen:
                        seen.add(label)
                        name = tags.get("name", "")
                        found.append(label + (f" ({name})" if name else ""))
    except Exception:
        pass
    return found

def get_weather(lat, lon):
    if not OPENWEATHER_KEY:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric", "lang": "tr"}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if r.status_code == 200:
            return {
                "desc":     data["weather"][0]["description"].capitalize(),
                "temp":     round(data["main"]["temp"]),
                "feels":    round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind":     round(data["wind"]["speed"] * 3.6, 1),
            }
    except Exception:
        pass
    return None

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        age INTEGER, gender TEXT,
        chronic_issues TEXT, sleep_pattern TEXT, address TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, food_morning TEXT, food_noon TEXT, food_evening TEXT,
        drink_morning TEXT, drink_noon TEXT, drink_evening TEXT,
        mood TEXT, sleep_time TEXT, wake_time TEXT, nap_time TEXT,
        night_awake_duration TEXT, sleep_quality INTEGER, dream TEXT
    )""")
    for col, coltype in [("sleep_quality", "INTEGER"), ("dream", "TEXT"), ("activity_level", "TEXT")]:
        try:
            c.execute(f"ALTER TABLE daily_entries ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

init_db()

st.title("🌙 SleepSense: Uyku Pusulası")
st.markdown(f'<div class="avatar">{avatar}</div>', unsafe_allow_html=True)

for key in ["food_morning","food_noon","food_evening", "drink_morning","drink_noon","drink_evening"]:
    st.session_state.setdefault(key, [""])
st.session_state.setdefault("last_chat_response", "")
st.session_state.setdefault("address", "")
st.session_state.setdefault("location_info", None)
st.session_state.setdefault("show_chat", False)

# ─────────────────────────────────────────────
# AI Sohbet Kutusu (Hafızalı Orta Seviye Entegrasyon)
# ─────────────────────────────────────────────
with st.container():
    col_left, col_chat = st.columns([0.6, 0.4])
    with col_chat:
        st.markdown("### 💬 AI ile Sohbet (Hafızalı)")
        
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = [
                {"role": "system", "content": "Sen samimi bir uyku koçusun. Kısa ve net cevaplar ver."}
            ]

        user_question = st.text_input("Uyku ile ilgili bir soru sor...", key="ai_question_input")

        if st.button("💭 Sor", key="ask_button"):
            if not user_question:
                st.warning("Lütfen bir soru yazın.")
            elif not client:
                st.error("Groq bağlantısı kurulamadı — GROQ_API_KEY .env dosyasına eklendi mi?")
            else:
                with st.spinner("Düşünüyor..."):
                    try:
                        st.session_state.chat_memory.append({"role": "user", "content": user_question})
                        
                        # Model ismi güncellendi: llama-3.3-70b-versatile
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=st.session_state.chat_memory,
                            max_tokens=150
                        )
                        
                        ai_reply = response.choices[0].message.content
                        st.session_state.chat_memory.append({"role": "assistant", "content": ai_reply})
                        st.session_state.show_chat = True 
                        
                    except Exception as e:
                        st.error(f"Sistem meşgul: {e}")

        # 5. Sohbet Geçmişini Ekranda Göster (Koşullu)
        if st.session_state.show_chat and len(st.session_state.chat_memory) > 1:
            st.markdown("<div style='height: 250px; overflow-y: auto; padding: 10px; border: 1px solid rgba(255,255,255,0.2); border-radius: 10px;'>", unsafe_allow_html=True)
            for msg in st.session_state.chat_memory[1:]:
                if msg["role"] == "user":
                    st.markdown(f"<div style='text-align: right; color: #a8d5ff; margin-bottom: 5px;'><b>Sen:</b> {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-bubble' style='position: relative; bottom: 0; right: 0; margin-bottom: 15px;'><b>🤖 AI:</b> {msg['content']}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # İstediğin buton: Kapatma / Gizleme
            if st.button("✅ Tamam, Anladım", key="close_chat_btn"):
                st.session_state.show_chat = False
                st.rerun()

            if st.button("Sohbeti Temizle", key="clear_chat"):
                st.session_state.chat_memory = [{"role": "system", "content": "Sen samimi bir uyku koçusun. Kısa ve net cevaplar ver."}]
                st.session_state.show_chat = False
                st.rerun()

st.sidebar.header("Kullanıcı Profili")
age     = st.sidebar.number_input("Yaş", min_value=1, max_value=120, value=25)
gender  = st.sidebar.selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"])
chronic = st.sidebar.text_area("Kronik Rahatsızlıklar (varsa)")
address = st.sidebar.text_input(
    "Adres (şehir, ilçe, sokak)",
    value=st.session_state["address"],
    key="address_input"
)
st.session_state["address"] = address

if st.sidebar.button("Profili Kaydet"):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users LIMIT 1")
    row = c.fetchone()
    if row:
        c.execute("UPDATE users SET age=?, gender=?, chronic_issues=?, address=? WHERE id=?",
                  (age, gender, chronic, address, row[0]))
    else:
        c.execute("INSERT INTO users (age, gender, chronic_issues, sleep_pattern, address) VALUES (?, ?, ?, ?, ?)",
                  (age, gender, chronic, "", address))
    conn.commit()
    conn.close()
    st.session_state["location_info"] = None
    st.sidebar.success("Profil kaydedildi!")

if address:
    info = st.session_state.get("location_info")
    if info is None or info.get("address") != address:
        with st.sidebar:
            with st.spinner("Konum analiz ediliyor..."):
                _lat, _lon, _display = get_coordinates(address)
                if _lat:
                    _weather = get_weather(_lat, _lon)
                    _noise   = get_noise_sources(_lat, _lon, radius=500)
                    st.session_state["location_info"] = {
                        "address": address, "lat": _lat, "lon": _lon,
                        "display": _display, "weather": _weather, "noise": _noise,
                    }
                else:
                    st.session_state["location_info"] = {"address": address}

    info = st.session_state["location_info"]
    w    = info.get("weather")
    if w:
        st.sidebar.write(
            f"🌤 **Hava:** {w['desc']}, {w['temp']}°C "
            f"(hissedilen {w['feels']}°C), Nem: %{w['humidity']}, Rüzgar: {w['wind']} km/h"
        )
    else:
        st.sidebar.write("🌤 Hava durumu alınamadı.")

    noise_list = info.get("noise", [])
    if noise_list:
        st.sidebar.write(f"🔊 **Yakın Gürültü:** {', '.join(noise_list[:8])}")
    else:
        st.sidebar.write("🔇 Kayda değer gürültü kaynağı bulunamadı.")

st.sidebar.header("Bugünün Uyku Bilgisi")
sleep_time           = st.sidebar.time_input("Kaçta yatağa girdiniz?", value=None)
wake_time            = st.sidebar.time_input("Kaçta uyandınız?", value=None)
nap_duration         = st.sidebar.number_input("Gündüz uykusu (dakika)", min_value=0, value=0)
night_awake_duration = st.sidebar.number_input("Gece uyanık kalma (dakika)", min_value=0, value=0)
sleep_quality        = st.sidebar.radio("Uyku Kaliteniz", [0, 1, 2, 3, 4, 5], key="sleep_quality_radio")
dream                = st.sidebar.text_area("Rüyalar (varsa)", height=100)

st.write("### Bugünün nasıl geçti?")
st.write("#### Günlük Veri Girişi")

col1, col2, col3 = st.columns(3)

def meal_drink_section(col, label, food_key, drink_key):
    with col:
        st.subheader(label)
        st.write("**Yemekler**")
        for i in range(len(st.session_state[food_key])):
            st.session_state[food_key][i] = st.text_input(
                f"Yemek {i+1}", value=st.session_state[food_key][i], key=f"{food_key}_{i}"
            )
        if st.button("➕ Ekle", key=f"add_{food_key}"):
            st.session_state[food_key].append("")
            st.rerun()
        st.write("**İçecekler**")
        for i in range(len(st.session_state[drink_key])):
            st.session_state[drink_key][i] = st.text_input(
                f"İçecek {i+1}", value=st.session_state[drink_key][i], key=f"{drink_key}_{i}"
            )
        if st.button("➕ Ekle", key=f"add_{drink_key}"):
            st.session_state[drink_key].append("")
            st.rerun()

meal_drink_section(col1, "Sabah", "food_morning", "drink_morning")
meal_drink_section(col2, "Öğlen", "food_noon",    "drink_noon")
meal_drink_section(col3, "Akşam", "food_evening", "drink_evening")

mood = st.radio(
    "Duygu durumunuz",
    ["Mutlu 😊", "Stresli 😫", "Yorgun 😴", "Enerjik ⚡", "Üzgün 😢"],
    key="daily_mood"
)

st.write("#### 🏃 Bugünkü Hareket Durumu")
activity_level = st.radio(
    "Bugün ne kadar hareket ettiniz?",
    ["Az 🐢", "Orta 🚶", "Çok 🏃"],
    horizontal=True,
    key="activity_level_radio"
)

st.write("#### 🕐 Toplam Uyku Süresi")
if sleep_time and wake_time:
    sleep_dt = datetime.combine(date.today(), sleep_time)
    wake_dt  = datetime.combine(date.today(), wake_time)
    if wake_dt <= sleep_dt:
        wake_dt += timedelta(days=1)
    total_minutes = int((wake_dt - sleep_dt).total_seconds() / 60) - night_awake_duration
    total_minutes = max(0, total_minutes)
    hours   = total_minutes // 60
    minutes = total_minutes % 60
    st.info(f"🌙 Toplam uyku süreniz: **{hours} saat {minutes} dakika**"
            + (f" *(gece {night_awake_duration} dk uyanık kalma düşüldü)*" if night_awake_duration > 0 else ""))
    if total_minutes < 360:
        st.warning("⚠️ 6 saatten az uyudunuz. Daha fazla uyku önerilir!")
    elif total_minutes > 540:
        st.warning("⚠️ 9 saatten fazla uyudunuz. Çok fazla uyku da yorucu olabilir.")
    else:
        st.success("✅ Uyku süreniz ideal aralıkta (6-9 saat)!")
else:
    st.info("💤 Uyku süresini görmek için sidebar'dan yatış ve uyanış saatlerini girin.")

def join_list(lst):
    return ", ".join(x for x in lst if x)

if st.button("Günlük Veriyi Kaydet"):
    today = str(date.today())
    conn  = sqlite3.connect("users.db")
    c     = conn.cursor()
    c.execute("SELECT id FROM daily_entries WHERE date=? LIMIT 1", (today,))
    existing = c.fetchone()
    params = (
        join_list(st.session_state.food_morning), join_list(st.session_state.food_noon), join_list(st.session_state.food_evening),
        join_list(st.session_state.drink_morning), join_list(st.session_state.drink_noon), join_list(st.session_state.drink_evening),
        mood, str(sleep_time) if sleep_time else "", str(wake_time) if wake_time else "",
        str(nap_duration), str(night_awake_duration), sleep_quality, dream or "", activity_level
    )
    if existing:
        c.execute("""UPDATE daily_entries SET
            food_morning=?, food_noon=?, food_evening=?, drink_morning=?, drink_noon=?, drink_evening=?,
            mood=?, sleep_time=?, wake_time=?, nap_time=?, night_awake_duration=?, sleep_quality=?, dream=?, activity_level=?
            WHERE date=?""", (*params, today))
        st.success("Bugünün verisi güncellendi!")
    else:
        c.execute("""INSERT INTO daily_entries
            (date, food_morning, food_noon, food_evening, drink_morning, drink_noon, drink_evening,
             mood, sleep_time, wake_time, nap_time, night_awake_duration, sleep_quality, dream, activity_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (today, *params))
        st.success("Günlük veri kaydedildi!")
    conn.commit()
    conn.close()

if st.button("AI Uyku Tavsiyesi Al"):
    if not client:
        st.error("Groq bağlantısı kurulamadı — GROQ_API_KEY .env dosyasına eklendi mi?")
    else:
        with st.spinner("Yapay zeka uyku reçeteni hazırlıyor..."):
            try:
                info        = st.session_state.get("location_info") or {}
                w           = info.get("weather")
                noise_list  = info.get("noise", [])
                hava_str    = (f"{w['desc']}, {w['temp']}°C, nem %{w['humidity']}, rüzgar {w['wind']} km/h" if w else "bilinmiyor")
                gurultu_str = ", ".join(noise_list) if noise_list else "tespit edilmedi"

                prompt = f"""
Kullanıcı profili:
- Duygu durumu: {mood}
- Hareket durumu: {activity_level}
- Sabah yedikleri: {join_list(st.session_state.food_morning)}
- Akşam yedikleri: {join_list(st.session_state.food_evening)}
- Yatış saati: {str(sleep_time) if sleep_time else 'belirtilmemiş'}
- Uyanış saati: {str(wake_time) if wake_time else 'belirtilmemiş'}
- Uyku kalitesi (0-5): {sleep_quality}
- Gerçek hava durumu: {hava_str}
- Çevresindeki gürültü: {gurultu_str}

Yukarıdaki bilgilere göre 3 maddelik kısa uyku tavsiyesi ver. Her madde 1-2 cümle olsun. Türkçe yaz.
"""
                cevap = ask_ai(prompt)
                st.success("✨ İşte Uyku Reçeten:")
                st.write(cevap)
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")

st.write("")
st.markdown("---")
st.markdown("## 🌙 Uyku Kalitesi Takip Çizelgesi")

conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute("SELECT date, sleep_quality FROM daily_entries WHERE sleep_quality IS NOT NULL ORDER BY date DESC LIMIT 7")
data = c.fetchall()
conn.close()

if data:
    dates  = [row[0] for row in reversed(data)]
    scores = [row[1] for row in reversed(data)]
    df = pd.DataFrame({"Tarih": dates, "Uyku Kalitesi": scores})
    st.markdown("### 📊 Son 7 Günün Uyku Kalitesi")
    st.line_chart(df.set_index("Tarih"), height=300)

    c1, c2, c3 = st.columns(3)
    avg = sum(scores) / len(scores)
    with c1: st.metric("Ortalama Puan", f"{avg:.1f}/5", "⭐")
    with c2: st.metric("En İyi Gün",    f"{max(scores)}/5", "🌟")
    with c3: st.metric("En Kötü Gün",   f"{min(scores)}/5", "😴")

    emoji_map = {0:"😴 (Hiç uyumadım)",1:"😪 (Çok kötü)",2:"😐 (Kötü)",3:"😊 (Orta)",4:"😄 (İyi)",5:"🌟 (Mükemmel)"}
    st.markdown("### 📅 Günlük Puanlar")
    for d, s in zip(dates, scores):
        st.write(f"**{d}**: {emoji_map.get(s,'❓')}")
else:
    st.write("📊 Henüz uyku kalitesi verisi yok. Lütfen günlük veri kaydetmeye başlayın.")

st.markdown("---")
st.markdown("## 💭 Rüya Haritası")

conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute("SELECT date, dream FROM daily_entries WHERE dream IS NOT NULL AND dream != '' ORDER BY date DESC LIMIT 10")
dream_data = c.fetchall()
conn.close()

if dream_data:
    st.markdown("### 🌟 Son Rüyalar")
    for d, dream_text in dream_data:
        with st.expander(f"📅 {d}"):
            st.write(dream_text)
else:
    st.write("💭 Henüz rüya kaydınız yok. Gördüğünüz rüyaları sidebar'dan kaydedebilirsiniz!")