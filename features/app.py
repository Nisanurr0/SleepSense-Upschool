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

        if st.session_state.show_chat and len(st.session_state.chat_memory) > 1:
            st.markdown("<div style='height: 250px; overflow-y: auto; padding: 10px; border: 1px solid rgba(255,255,255,0.2); border-radius: 10px;'>", unsafe_allow_html=True)
            for msg in st.session_state.chat_memory[1:]:
                if msg["role"] == "user":
                    st.markdown(f"<div style='text-align: right; color: #a8d5ff; margin-bottom: 5px;'><b>Sen:</b> {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-bubble' style='position: relative; bottom: 0; right: 0; margin-bottom: 15px;'><b>🤖 AI:</b> {msg['content']}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
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


# ════════════════════════════════════════════════════════════════
# YENİ BLOK 1 — 💯 UYKU SKORU (0-100)
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 💯 Uyku Skoru")

def hesapla_uyku_skoru(sleep_time, wake_time, night_awake_duration, sleep_quality, nap_duration, mood, activity_level, noise_list):
    skor = 0

    # 1. Süre puanı (max 30)
    if sleep_time and wake_time:
        sleep_dt = datetime.combine(date.today(), sleep_time)
        wake_dt  = datetime.combine(date.today(), wake_time)
        if wake_dt <= sleep_dt:
            wake_dt += timedelta(days=1)
        net_min = int((wake_dt - sleep_dt).total_seconds() / 60) - night_awake_duration
        net_min = max(0, net_min)
        if 420 <= net_min <= 480:
            skor += 30
        elif 360 <= net_min < 420 or 480 < net_min <= 540:
            skor += 20
        elif 300 <= net_min < 360 or 540 < net_min <= 600:
            skor += 10
        else:
            skor += 0
    else:
        skor += 15  # veri yok, nötr

    # 2. Kalite puanı (max 30)
    skor += int(sleep_quality / 5 * 30)

    # 3. Ruh hali (max 15)
    mood_puan = {"Enerjik ⚡": 15, "Mutlu 😊": 12, "Yorgun 😴": 6, "Stresli 😫": 4, "Üzgün 😢": 3}
    skor += mood_puan.get(mood, 8)

    # 4. Hareket (max 10)
    aktivite_puan = {"Çok 🏃": 10, "Orta 🚶": 7, "Az 🐢": 3}
    skor += aktivite_puan.get(activity_level, 5)

    # 5. Gürültü etkisi (max 10)
    ciddi_gurultu = ["Otoyol", "Demiryolu", "Metro hattı", "Havalimanı", "Gece kulübü"]
    gurultu_puani = 10
    for g in noise_list:
        for cg in ciddi_gurultu:
            if cg in g:
                gurultu_puani -= 3
    skor += max(0, gurultu_puani)

    # 6. Gündüz uykusu bonusu/cezası (max 5)
    if nap_duration == 0:
        skor += 5
    elif nap_duration <= 30:
        skor += 3
    else:
        skor += 0

    return min(100, max(0, skor))

info_loc     = st.session_state.get("location_info") or {}
noise_list_s = info_loc.get("noise", [])

uyku_skoru = hesapla_uyku_skoru(
    sleep_time, wake_time, night_awake_duration,
    sleep_quality, nap_duration, mood, activity_level, noise_list_s
)

renk = "#ff4b4b" if uyku_skoru < 40 else ("#ffa500" if uyku_skoru < 70 else "#00cc66")
yorum = (
    "😴 Çok kötü — bu geceyi telafi etmeye çalış." if uyku_skoru < 40 else
    "😐 Orta — birkaç alışkanlık değişikliği büyük fark yaratır." if uyku_skoru < 60 else
    "😊 İyi — doğru yoldasın, devam et!" if uyku_skoru < 80 else
    "🌟 Mükemmel — bu alışkanlıkları koru!"
)

st.markdown(
    f"""
    <div style="text-align:center; padding: 20px;">
        <div style="font-size: 80px; font-weight: bold; color: {renk};">{uyku_skoru}</div>
        <div style="font-size: 20px; color: #ccc;">/ 100</div>
        <div style="font-size: 18px; margin-top: 10px;">{yorum}</div>
    </div>
    """,
    unsafe_allow_html=True
)

sc1, sc2, sc3, sc4 = st.columns(4)
with sc1: st.metric("Süre", "30 puan maks")
with sc2: st.metric("Kalite", "30 puan maks")
with sc3: st.metric("Ruh Hali + Aktivite", "25 puan maks")
with sc4: st.metric("Çevre (gürültü/nap)", "15 puan maks")


# ════════════════════════════════════════════════════════════════
# YENİ BLOK 2 — 📅 HAFTALIK AI RAPORU
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📅 Haftalık AI Raporu")

if st.button("🔍 Haftalık Rapor Oluştur", key="weekly_report_btn"):
    if not client:
        st.error("Groq bağlantısı kurulamadı.")
    else:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("""SELECT date, food_morning, food_noon, food_evening,
                            drink_morning, drink_noon, drink_evening,
                            mood, sleep_time, wake_time, sleep_quality, activity_level
                     FROM daily_entries ORDER BY date DESC LIMIT 7""")
        rows = c.fetchall()
        conn.close()

        if not rows:
            st.warning("Henüz yeterli veri yok. Birkaç gün veri girdikten sonra tekrar dene.")
        else:
            with st.spinner("AI haftalık raporunu hazırlıyor..."):
                try:
                    ozet = ""
                    for r in reversed(rows):
                        ozet += (
                            f"\nTarih: {r[0]} | Sabah: {r[1]} | Öğlen: {r[2]} | Akşam: {r[3]} | "
                            f"İçecekler: {r[4]}, {r[5]}, {r[6]} | Ruh hali: {r[7]} | "
                            f"Yatış: {r[8]} | Uyanış: {r[9]} | Kalite: {r[10]}/5 | Aktivite: {r[11]}"
                        )

                    prompt = f"""
Aşağıda bir kullanıcının son {len(rows)} günlük uyku ve beslenme verisi var:
{ozet}

Bu verilere bakarak:
1. Uyku kalitesini etkileyen 2 önemli pattern bul (örn: "Akşam kahve içtiğinde kalite düşüyor")
2. Beslenme açısından 1 dikkat çekici nokta belirt
3. Genel bir öneri ver

Türkçe, madde madde, kısa ve net yaz. Toplam 5-6 cümleyi geçme.
"""
                    rapor = ask_ai(prompt)
                    st.success("📊 Haftalık Analiz:")
                    st.write(rapor)
                except Exception as e:
                    st.error(f"Hata: {e}")


# ════════════════════════════════════════════════════════════════
# YENİ BLOK 3 — 🌙 RÜYA ANALİZİ (AI)
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🌙 Rüya Analizi")

if st.button("🔮 Rüyalarımı AI ile Analiz Et", key="dream_analysis_btn"):
    if not client:
        st.error("Groq bağlantısı kurulamadı.")
    else:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT date, dream FROM daily_entries WHERE dream IS NOT NULL AND dream != '' ORDER BY date DESC LIMIT 7")
        dream_rows = c.fetchall()
        conn.close()

        if not dream_rows:
            st.warning("Henüz rüya kaydın yok. Sidebar'dan rüyalarını ekleyebilirsin.")
        else:
            with st.spinner("AI rüyalarını analiz ediyor..."):
                try:
                    ruya_metni = "\n".join([f"{r[0]}: {r[1]}" for r in dream_rows])
                    prompt = f"""
Aşağıda bir kullanıcının son günlerde gördüğü rüyalar var:
{ruya_metni}

Bu rüyaları analiz ederek:
1. Genel tema veya tekrar eden motifler neler?
2. Bu rüyalar duygusal durum hakkında ne söylüyor?
3. Uyku kalitesiyle bir bağlantısı olabilir mi?

Türkçe, samimi, 4-5 cümle yaz. Kesinlikle söyle tarzında değil, "olabilir, gösteriyor olabilir" gibi yumuşak bir dille yaz.
"""
                    analiz = ask_ai(prompt)
                    st.info("🔮 Rüya Analizi:")
                    st.write(analiz)
                except Exception as e:
                    st.error(f"Hata: {e}")


# ════════════════════════════════════════════════════════════════
# YENİ BLOK 4 — 📸 YEMEK FOTOĞRAFI ANALİZİ (AI Vision)
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📸 Yemek Fotoğrafı Analizi")
st.caption("Fotoğraf çek veya yükle — AI yediğin yemekleri ve uyku üzerindeki etkisini analiz etsin.")

import base64

ogün_secim = st.selectbox(
    "Hangi öğün?",
    ["Sabah", "Öğlen", "Akşam"],
    key="foto_ogun"
)

foto_kaynak = st.radio(
    "Fotoğraf kaynağı",
    ["Dosyadan Yükle 📁", "Kamera ile Çek 📷"],
    horizontal=True,
    key="foto_kaynak"
)

uploaded_foto = None
if foto_kaynak == "Dosyadan Yükle 📁":
    uploaded_foto = st.file_uploader(
        "Yemek fotoğrafı yükle",
        type=["jpg", "jpeg", "png", "webp"],
        key="foto_uploader"
    )
else:
    uploaded_foto = st.camera_input("Yemeğinin fotoğrafını çek", key="foto_kamera")

if uploaded_foto is not None:
    st.image(uploaded_foto, caption=f"{ogün_secim} yemeği", use_container_width=True)

    if st.button("🍽️ Yemeği AI ile Analiz Et", key="foto_analiz_btn"):
        if not client:
            st.error("Groq bağlantısı kurulamadı.")
        else:
            with st.spinner("AI yemeğini inceliyor..."):
                try:
                    # Base64'e çevir
                    img_bytes = uploaded_foto.read()
                    img_b64   = base64.b64encode(img_bytes).decode("utf-8")
                    mime_type = uploaded_foto.type or "image/jpeg"

                    # Groq vision modeli: llama-4-scout-17b-16e-instruct
                    vision_response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{img_b64}"
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": f"""Bu fotoğraftaki yemeği analiz et. {ogün_secim} öğünü olarak yenmiş.

Şunları söyle:
1. Fotoğrafta ne var? (yemekleri listele)
2. Bu yemekler uyku kalitesini nasıl etkiler? (olumlu/olumsuz)
3. Varsa 1 öneri ver (örn: "akşam bu kadar ağır yemek yerine...")

Türkçe, kısa ve samimi yaz. 4-5 cümle yeterli."""
                                    }
                                ]
                            }
                        ],
                        max_tokens=400,
                    )

                    analiz_sonuc = vision_response.choices[0].message.content
                    st.success("🍽️ Yemek Analizi:")
                    st.write(analiz_sonuc)

                    # Analiz sonucunu ilgili öğünün yemek listesine otomatik ekle (opsiyonel ipucu)
                    st.caption("💡 İpucu: Analiz sonucuna göre yukarıdaki yemek alanlarını güncelleyebilirsin.")

                except Exception as e:
                    st.error(f"Görüntü analizi başarısız: {e}")
                    st.info("Not: Groq vision için 'meta-llama/llama-4-scout-17b-16e-instruct' modeli gereklidir. Groq hesabında bu modelin aktif olduğundan emin ol.")


# ════════════════════════════════════════════════════════════════
# YENİ BLOK 5 — 🎵 UYKU SESLERİ ÇALAR
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🎵 Uyku Sesleri")
st.caption("Uyumadan önce dinlemek için doğa sesleri — süre ve ses seviyesi ayarlanabilir.")

import streamlit.components.v1 as components

ses_col1, ses_col2 = st.columns(2)

with ses_col1:
    secilen_ses = st.selectbox(
        "Ses seç",
        ["🌧️ Yağmur", "🧠 Beyaz Gürültü", "🌊 Okyanus Dalgaları"],
        key="ses_secim"
    )

with ses_col2:
    sure_dk = st.select_slider(
        "Süre (dakika)",
        options=[5, 10, 15, 20, 30, 45, 60],
        value=15,
        key="ses_sure"
    )

ses_seviyesi = st.slider("🔊 Ses Seviyesi", min_value=0, max_value=100, value=60, key="ses_seviye")

ses_tipi_map = {
    "🌧️ Yağmur": "rain",
    "🧠 Beyaz Gürültü": "white",
    "🌊 Okyanus Dalgaları": "ocean",
}
ses_tipi = ses_tipi_map[secilen_ses]
sure_ms   = sure_dk * 60 * 1000

components.html(
    f"""
    <div style="font-family: sans-serif; padding: 10px;">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <button onclick="startSound()" id="startBtn"
                style="background:#00cc66; color:white; border:none; padding:10px 22px;
                       border-radius:8px; font-size:15px; cursor:pointer;">
                ▶ Başlat
            </button>
            <button onclick="stopSound()" id="stopBtn"
                style="background:#ff4b4b; color:white; border:none; padding:10px 22px;
                       border-radius:8px; font-size:15px; cursor:pointer; display:none;">
                ⏹ Durdur
            </button>
            <span id="timerDisplay"
                style="font-size:22px; font-weight:bold; color:#00cc66; min-width:80px;">
                {sure_dk:02d}:00
            </span>
            <span id="statusText" style="color:#aaa; font-size:13px;">Hazır</span>
        </div>
        <div style="margin-top:10px; background:#222; border-radius:8px; height:8px; overflow:hidden;">
            <div id="progressBar"
                style="height:100%; width:0%; background:linear-gradient(90deg,#00cc66,#00aaff);
                       transition: width 1s linear;">
            </div>
        </div>
    </div>

    <script>
        const SES_TIPI  = "{ses_tipi}";
        const VOLUME    = {ses_seviyesi} / 100;
        const TOTAL_SEC = {sure_ms} / 1000;

        let actx      = null;
        let gainNode  = null;
        let nodes     = [];
        let interval  = null;
        let remaining = TOTAL_SEC;

        const startBtn  = document.getElementById('startBtn');
        const stopBtn   = document.getElementById('stopBtn');
        const timerDisp = document.getElementById('timerDisplay');
        const statusTxt = document.getElementById('statusText');
        const progBar   = document.getElementById('progressBar');

        function formatTime(sec) {{
            const m = Math.floor(sec / 60);
            const s = Math.floor(sec % 60);
            return String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
        }}

        function createWhiteNoise(ctx, gain) {{
            const bufSize = ctx.sampleRate * 2;
            const buf     = ctx.createBuffer(1, bufSize, ctx.sampleRate);
            const data    = buf.getChannelData(0);
            for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;
            const src = ctx.createBufferSource();
            src.buffer = buf;
            src.loop   = true;
            src.connect(gain);
            src.start();
            return src;
        }}

        function createRain(ctx, gain) {{
            // Birden fazla katmanlı filtreli gürültü = yağmur efekti
            const srcs = [];
            const layers = [
                {{ freq: 800,  q: 0.8, g: 0.6 }},
                {{ freq: 3000, q: 1.2, g: 0.3 }},
                {{ freq: 200,  q: 0.5, g: 0.2 }},
            ];
            layers.forEach(l => {{
                const bufSize = ctx.sampleRate * 2;
                const buf     = ctx.createBuffer(1, bufSize, ctx.sampleRate);
                const data    = buf.getChannelData(0);
                for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;
                const src = ctx.createBufferSource();
                src.buffer = buf;
                src.loop   = true;
                const filt = ctx.createBiquadFilter();
                filt.type            = 'bandpass';
                filt.frequency.value = l.freq;
                filt.Q.value         = l.q;
                const layerGain = ctx.createGain();
                layerGain.gain.value = l.g;
                src.connect(filt);
                filt.connect(layerGain);
                layerGain.connect(gain);
                src.start();
                srcs.push(src);
            }});
            return srcs;
        }}

        function createOcean(ctx, gain) {{
            const srcs = [];
            // Dalga efekti: düşük frekanslı gürültü + yavaş LFO
            const bufSize = ctx.sampleRate * 4;
            const buf     = ctx.createBuffer(1, bufSize, ctx.sampleRate);
            const data    = buf.getChannelData(0);
            for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;

            const src = ctx.createBufferSource();
            src.buffer = buf;
            src.loop   = true;

            const filt = ctx.createBiquadFilter();
            filt.type            = 'lowpass';
            filt.frequency.value = 600;
            filt.Q.value         = 0.5;

            // LFO dalga modülasyonu
            const lfo      = ctx.createOscillator();
            const lfoGain  = ctx.createGain();
            lfo.frequency.value  = 0.15;
            lfoGain.gain.value   = 0.4;
            lfo.connect(lfoGain);
            lfoGain.connect(gain.gain);
            lfo.start();

            src.connect(filt);
            filt.connect(gain);
            src.start();
            srcs.push(src, lfo);
            return srcs;
        }}

        function startSound() {{
            actx     = new (window.AudioContext || window.webkitAudioContext)();
            gainNode = actx.createGain();
            gainNode.gain.value = VOLUME;
            gainNode.connect(actx.destination);

            if      (SES_TIPI === 'white') nodes = [createWhiteNoise(actx, gainNode)];
            else if (SES_TIPI === 'rain')  nodes = createRain(actx, gainNode);
            else                           nodes = createOcean(actx, gainNode);

            startBtn.style.display = 'none';
            stopBtn.style.display  = 'inline-block';
            statusTxt.textContent  = '🎵 Çalıyor...';
            remaining = TOTAL_SEC;

            interval = setInterval(() => {{
                remaining -= 1;
                timerDisp.textContent = formatTime(remaining);
                const pct = ((TOTAL_SEC - remaining) / TOTAL_SEC) * 100;
                progBar.style.width = pct + '%';
                if (remaining <= 0) {{
                    stopSound();
                    statusTxt.textContent = '✅ Süre doldu, iyi geceler!';
                }}
            }}, 1000);
        }}

        function stopSound() {{
            if (actx) {{ actx.close(); actx = null; }}
            clearInterval(interval);
            nodes = [];
            startBtn.style.display = 'inline-block';
            stopBtn.style.display  = 'none';
            timerDisp.textContent  = formatTime(TOTAL_SEC);
            progBar.style.width    = '0%';
            if (remaining > 0) statusTxt.textContent = 'Durduruldu';
        }}
    </script>
    """,
    height=160,
)


# ════════════════════════════════════════════════════════════════
# YENİ BLOK 6 — 🔥 GÜNLÜK STREAK (Seri Takibi)
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🔥 Günlük Seri")
st.caption("Her gün veri girersen serin büyür. Bir gün atlarsan sıfırlanır!")

def hesapla_streak():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT date FROM daily_entries ORDER BY date DESC")
    tarihler = [row[0] for row in c.fetchall()]
    conn.close()

    if not tarihler:
        return 0, 0, False

    bugun           = str(date.today())
    streak          = 0
    en_uzun         = 0
    temp_streak     = 0

    # Mevcut streak hesapla (bugünden geriye doğru)
    kontrol_tarihi = date.today()
    for t in tarihler:
        if t == str(kontrol_tarihi):
            streak += 1
            kontrol_tarihi -= timedelta(days=1)
        else:
            break

    # Bugün giriş yapılmış mı?
    bugun_giris = bugun in tarihler

    # En uzun streak hesapla
    if tarihler:
        sorted_dates = sorted(tarihler)
        temp_streak  = 1
        for i in range(1, len(sorted_dates)):
            d1 = datetime.strptime(sorted_dates[i-1], "%Y-%m-%d").date()
            d2 = datetime.strptime(sorted_dates[i],   "%Y-%m-%d").date()
            if (d2 - d1).days == 1:
                temp_streak += 1
                en_uzun = max(en_uzun, temp_streak)
            else:
                temp_streak = 1
        en_uzun = max(en_uzun, temp_streak)

    return streak, en_uzun, bugun_giris

streak, en_uzun_streak, bugun_giris = hesapla_streak()

# Ateş büyüklüğü ve rengi streak'e göre değişir
if streak == 0:
    ates_emoji  = "💤"
    streak_renk = "#888888"
    mesaj       = "yok yok yok."
elif streak < 3:
    ates_emoji  = "🔥"
    streak_renk = "#ffa500"
    mesaj       = "bakalım ne kadar 👀"
elif streak < 7:
    ates_emoji  = "🔥🔥"
    streak_renk = "#ff6600"
    mesaj       = "hâlâ buradasın?"
elif streak < 14:
    ates_emoji  = "🔥🔥🔥"
    streak_renk = "#ff3300"
    mesaj       = "tamam ciddi misin"
else:
    ates_emoji  = "🔥🔥🔥🔥"
    streak_renk = "#ff0000"
    mesaj       = "bu anormal. tebrikler."

# Görsel gösterim
st.markdown(
    f"""
    <div style="text-align:center; padding: 25px; background: rgba(255,100,0,0.08);
                border-radius: 16px; border: 1px solid rgba(255,100,0,0.2);">
        <div style="font-size: 60px;">{ates_emoji}</div>
        <div style="font-size: 64px; font-weight: bold; color: {streak_renk};
                    text-shadow: 0 0 20px {streak_renk};">
            {streak}
        </div>
        <div style="font-size: 16px; color: #ccc; margin-top: 4px;">günlük seri</div>
        <div style="font-size: 15px; color: #aaa; margin-top: 8px;">{mesaj}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# Metrikler
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("🔥 Mevcut Seri",  f"{streak} gün")
with m2:
    st.metric("🏆 En Uzun Seri", f"{en_uzun_streak} gün")
with m3:
    st.metric("📅 Bugün Giriş",  "✅ Yapıldı" if bugun_giris else "❌ Yapılmadı")

# Son 7 günün görsel takvimi
st.markdown("### 📆 Son 7 Gün")
conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute("SELECT DISTINCT date FROM daily_entries")
tum_tarihler = set(row[0] for row in c.fetchall())
conn.close()

takvim_cols = st.columns(7)
for i, col in enumerate(takvim_cols):
    gun     = date.today() - timedelta(days=6 - i)
    gun_str = str(gun)
    gun_adi = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"][gun.weekday()]
    giris_var = gun_str in tum_tarihler
    with col:
        st.markdown(
            f"""
            <div style="text-align:center; padding:8px; border-radius:10px;
                        background: {'rgba(0,200,100,0.2)' if giris_var else 'rgba(255,255,255,0.05)'};
                        border: 1px solid {'#00cc66' if giris_var else 'rgba(255,255,255,0.1)'};">
                <div style="font-size:20px;">{'✅' if giris_var else '⬜'}</div>
                <div style="font-size:11px; color:#aaa;">{gun_adi}</div>
                <div style="font-size:10px; color:#666;">{gun.day}</div>
            </div>
            """,
            unsafe_allow_html=True
        )