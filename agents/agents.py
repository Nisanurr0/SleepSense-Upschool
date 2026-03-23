import sqlite3
import os
import pandas as pd
from dotenv import load_dotenv

# Yapay zeka kurulumu (Groq)
load_dotenv()
GROQ_KEY = os.environ.get("GROQ_API_KEY")

try:
    from groq import Groq
    client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except ImportError:
    client = None

def haftalik_analizi_calistir():
    print("🤖 SleepSense Agent: Haftalık verileriniz toplanıyor...")
    
    # Ana dizindeki veritabanına bağlan
    db_path = os.path.join(os.path.dirname(__file__), '..', 'sleep_sense_final.db')
    
    if not os.path.exists(db_path):
        print("❌ Hata: Veritabanı bulunamadı. Lütfen önce uygulamadan birkaç günlük veri girin.")
        return

    conn = sqlite3.connect(db_path)
    # Son 7 günün verilerini çek
    df = pd.read_sql_query("SELECT date, mood, food_evening, sleep_quality FROM daily_entries ORDER BY date DESC LIMIT 7", conn)
    conn.close()

    if df.empty or len(df) < 3:
        print("⚠️ Agent Uyarısı: Sağlıklı bir haftalık analiz için veritabanında en az 3 günlük kayıt olmalıdır.")
        return

    print(f"✅ {len(df)} günlük veri bulundu. Groq AI'a gönderiliyor...\n")

    # Verileri metne çevir
    veri_metni = df.to_string(index=False)

    prompt = f"""
    [SİSTEM MESAJI]
    Sen SleepSense uygulamasının arka planda çalışan "Haftalık Analiz Ajanı"sın (Agent).
    Görevin, kullanıcının son 1 haftalık verilerine bakarak genel bir trend analizi yapmak.

    [KULLANICI VERİLERİ (Son Günler)]
    {veri_metni}

    [GÖREV]
    Bu verilere bakarak:
    1. Kullanıcının genel uyku kalitesi trendini yorumla (Düşüyor mu, artıyor mu?).
    2. Akşam yediği yemekler ile uyku kalitesi arasında bir bağlantı görüyor musun? (Kısaca belirt).
    3. Gelecek hafta için motive edici tek bir tavsiye ver.
    Yanıtın kısa, profesyonel ve rapor formatında olsun.
    """

    try:
        # Groq API çağrısı (Llama3 modelini kullanıyoruz, inanılmaz hızlıdır)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        print("========================================")
        print(" 🌙 HAFTALIK SLEEPSENSE AI RAPORU ")
        print("========================================\n")
        print(response.choices[0].message.content)
        print("\n========================================")
    except Exception as e:
        print(f"❌ Groq AI Analizi sırasında hata oluştu: {e}")

if __name__ == "__main__":
    haftalik_analizi_calistir()