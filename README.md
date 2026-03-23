# SleepSense-Upschool
# 🌙 SleepSense Pro

## 🎯 Problem
Günümüzde pek çok kişi kalitesiz uyku sorunu çekiyor ancak bunun gün içindeki aktiviteleriyle (yedikleri, duygu durumları) veya çevresel faktörlerle (hava sıcaklığı, gürültü) bağlantısını kuramıyor.

## 💡 Çözüm
SleepSense, kullanıcının günlük verilerini ve konum bazlı çevresel faktörleri analiz ederek yapay zeka destekli, kişiselleştirilmiş uyku tavsiyeleri sunan akıllı bir uyku takip asistanıdır.

## 🚀 Canlı Demo
* **Yayın Linki:**## 🚀 Canlı Demo
* **Yayın Linki:** https://sleepsense-upschool-drzuzykz6fh7cpwg8zmc7n.streamlit.app/
* **Demo Video:** [6. Adımda eklenecek]

## 📸 Uygulama Görüntüleri
*(Görüntüler assets klasörüne daha sonra eklenecek)*

## 🛠️ Kullanılan Teknolojiler
* **Frontend:** Streamlit
* **Backend:** Python, SQLite
* **Yapay Zeka:** Groq API (Ultra Hızlı Çıkarım / Açık Kaynak LLM)
* **API'ler:** OpenStreetMap (Konum), OpenWeather (Hava Durumu), Overpass (Gürültü Analizi)

## 💻 Nasıl Çalıştırılır?
1. Proje dosyalarını bilgisayarınıza indirin.
2. Gerekli kütüphaneleri terminalden yükleyin (`pip install streamlit pandas requests python-dotenv groq`).
3. Ana dizinde bir `.env` dosyası oluşturup içine `GROQ_API_KEY` ve `OPENWEATHER_API_KEY` bilgilerinizi ekleyin.
4. Terminalde şu komutu çalıştırarak uygulamayı başlatın: `streamlit run features/app.py`
