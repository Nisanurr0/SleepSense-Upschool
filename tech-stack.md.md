 SleepSense (Uyku Pusulası) - Teknoloji Yığını ve Kurulum Rehberi

Başlangıç seviyesinde bir geliştirici için en uygun, en hızlı sonuç veren ve doğrudan yapay zekaya odaklanmanı sağlayacak teknoloji yığını (Tech Stack) aşağıdadır.

1. Önerilen Teknoloji Yığını

Arayüz ve Arka Plan (Full Stack): Streamlit (Python tabanlı)

Yapay Zeka: Google Gemini API (Google AI Studio)

Veritabanı: SQLite

2. Neden Bu Teknolojileri Seçiyoruz?

Neden Streamlit? Normalde bir web sitesi için HTML (iskelet), CSS (tasarım), JavaScript (etkileşim) ve bunları yönetecek bir backend (sunucu) yazman gerekir. Streamlit, sadece Python yazarak dakikalar içinde butonlar, formlar ve harika görünen web ekranları oluşturmanı sağlar.

Neden SQLite? PostgreSQL veya Firebase gibi sistemler başlangıçta karmaşık kurulumlar gerektirir. SQLite, Python'un içinde hazır gelir. Kurulum yapmana gerek yoktur, verileri bilgisayarında basit bir dosya (veritabanı.db) içinde tutar.

Neden Gemini API? Şu an en hızlı, Türkçe dilini en iyi anlayan ve entegrasyonu en kolay modellerden biri. Bütüncül Karar Motoru'muzun kalbi olacak.

3. Adım Adım Kurulum Rehberi

Projeni ayağa kaldırmak için bilgisayarının terminalinde (veya VS Code terminalinde) şu adımları izlemen yeterli:

Adım 1: Python'un Kurulu Olduğundan Emin Ol

Bilgisayarında Python yüklü değilse python.org adresinden indirip kur (Kurulum sırasında "Add Python to PATH" seçeneğini işaretlemeyi unutma).

Adım 2: Proje Klasörünü Oluştur

VS Code'da sleepsense adında boş bir klasör oluştur ve VS Code içinde terminali aç.

Adım 3: Sanal Ortam (Virtual Environment) Kurulumu

Projendeki kütüphanelerin bilgisayarındaki diğer projelerle karışmaması için izole bir ortam oluştururuz. Terminale şunları yaz:

python -m venv venv


Windows için aktif etme: venv\Scripts\activate

Mac/Linux için aktif etme: source venv/bin/activate

(Aktif ettiğinde terminal satırının başında (venv) yazısını görmelisin.)

Adım 4: Gerekli Kütüphaneleri Yükle

Aktif ettiğin sanal ortamda Streamlit ve Gemini API kütüphanelerini indirelim:

pip install streamlit google-generativeai


Adım 5: İlk Kodunu Yaz ve Test Et

Proje klasörünün içine app.py adında bir dosya oluştur ve içine şu basit kodu yapıştır:

import streamlit as st
import google.generativeai as genai

# Gemini API Ayarları (Buraya kendi API anahtarını yazmalısın)
API_KEY = "BURAYA_GOOGLE_AI_STUDIO_ANAHTARINI_YAZ"
genai.configure(api_key=API_KEY)

# Arayüz (Canvas'taki Adım 1 ve Adım 2)
st.title("🌙 SleepSense: Uyku Pusulası")
st.write("Bugünün nasıl geçti?")

# Basit bir buton ve aksiyon
if st.button("😫 Stresli ve Yorgun"):
    st.info("Yapay zeka verilerini analiz ediyor...") # Bekleme simülasyonu
    
    # Gemini'ye istek atma
    model = genai.GenerativeModel('gemini-1.5-flash')
    cevap = model.generate_content("Kullanıcı bugün çok stresli ve yorgun. Ona bu gece daha iyi uyuması için 2 maddelik çok kısa bir tavsiye ver.")
    
    st.success("İşte Uyku Reçeten:") # Sonuç ekranı
    st.write(cevap.text)


Adım 6: Uygulamayı Çalıştır!

Terminaline şu komutu yazıp Enter'a bas:

streamlit run app.py


Bu komut tarayıcında anında yeni bir sekme açacak ve hazırladığımız basit akışın çalışan bir web sitesi olarak karşına çıktığını göreceksin!