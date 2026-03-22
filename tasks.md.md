# Görev Listesi: SleepSense Uygulaması Geliştirme

Bu görev listesi, `prd.md` dosyasında tanımlanan gereksinimlere dayanarak "Uyku Pusulası" web uygulamasını adım adım geliştirmek için oluşturulmuştur. Görevler, MVP (Minimum Çalışan Ürün) özelliklerine odaklanarak mantıklı bir sırayla düzenlenmiştir.

## 1. Proje Kurulumu ve Temel Altyapı
- [ ] Proje klasör yapısını oluştur (frontend, backend, database).
- [ ] Git repository'sini başlat ve temel .gitignore dosyasını ekle.
- [ ] Ön yüz için Next.js projesini başlat (React tabanlı).
- [ ] Arka yüz için Python Flask/Django projesini başlat.
- [ ] Veritabanı olarak PostgreSQL'i kur ve bağlantıyı yapılandır (alternatif: Firebase).
- [ ] Temel bağımlılıkları yükle (frontend: React, backend: Python kütüphaneleri).

## 2. Kullanıcı Kayıt Sistemi
- [ ] Kullanıcı modeli oluştur (yaş, cinsiyet, kronik rahatsızlıklar, uyku düzeni).
- [ ] Kayıt ve giriş sayfalarını tasarla (frontend).
- [ ] Backend'de kullanıcı kimlik doğrulama API'sini geliştir (JWT token ile).
- [ ] Veritabanında kullanıcı tablolarını oluştur ve CRUD operasyonlarını ekle.
- [ ] Güvenlik önlemleri ekle (şifre hashleme, input validasyonu).

## 3. Onboarding Süreci
- [ ] İlk girişte kullanıcı profilini toplama formu oluştur (yaş, uyku düzeni, kronik sorunlar).
- [ ] Konum girişi için harita entegrasyonu (Google Maps API).
- [ ] Ev konumunun çevresel analizini başlat (otoban yakınlığı, gürültü potansiyeli).
- [ ] Profil verilerini veritabanına kaydetme işlevi ekle.

## 4. Günlük Veri Girişi (Mini Form)
- [ ] Günlük beslenme girişi formu oluştur (yedikleri/içtikleri).
- [ ] Duygu durumu (mod) girişi için basit arayüz geliştir.
- [ ] Form verilerini backend'e gönderme ve veritabanına kaydetme.
- [ ] Kullanıcı dostu, hızlı giriş için mobil uyumlu tasarım.

## 5. Çevresel API Entegrasyonları
- [ ] Google Maps/Places API ile mekan analizi (gürültü, eğlence mekanları).
- [ ] OpenWeatherMap API ile hava durumu verilerini çekme (sıcaklık, hava kalitesi).
- [ ] Konum bazlı dinamik verileri işleme ve saklama.
- [ ] API anahtarlarını güvenli şekilde yönetme.

## 6. Yapay Zeka Karar Motoru
- [ ] AI API entegrasyonu (örneğin, OpenAI GPT) için backend modülü oluştur.
- [ ] Kullanıcı verilerini (biyoloji, davranış, mekan) birleştiren prompt motoru geliştir.
- [ ] Kişiselleştirilmiş uyku tavsiyelerini üreten algoritma yaz.
- [ ] Örnek çıktılar: "Bugün akşam yemeğinde ağır yemişsin... ılık bir duş al, nane çayı iç."

## 7. İlerleme Grafiği ve Pano
- [ ] Uyku puanını hesaplayan algoritma geliştir (verilere dayanarak).
- [ ] Son 1 haftalık uyku verilerini gösteren grafik bileşeni oluştur (frontend).
- [ ] Kullanıcı panosunda ilerleme takibi ekle.
- [ ] Grafik kütüphanesi (örneğin, Chart.js) entegrasyonu.

## 8. Kullanıcı Arayüzü ve Deneyimi (UI/UX)
- [ ] Responsive tasarım için CSS framework'ü (Tailwind CSS) ekle.
- [ ] Navigasyon ve sayfa geçişlerini optimize et.
- [ ] Hata yönetimi ve kullanıcı geri bildirimleri ekle.
- [ ] Mobil cihazlarda test et ve uyumluluk sağla.

## 9. Test ve Kalite Güvence
- [ ] Birim testleri yaz (frontend ve backend için).
- [ ] Entegrasyon testleri gerçekleştir.
- [ ] Güvenlik testleri (SQL injection, XSS vb.) yap.
- [ ] Kullanıcı kabul testleri (UAT) için demo sürümü hazırla.

## 10. Dağıtım ve Lansman
- [ ] Uygulamayı canlı sunucuya dağıt (Vercel/Netlify for frontend, Heroku/AWS for backend).
- [ ] CI/CD pipeline kur.
- [ ] İlk kullanıcı geri bildirimlerini topla ve iyileştirmeler yap.
- [ ] MVP'yi yayınla ve izleme araçları ekle (analytics).

Bu görev listesi, PRD'deki çekirdek sistem (Mekan, Davranış, Biyoloji) ve kullanıcı deneyimini kapsar. Her görev tamamlandıktan sonra işaretleyin ve gerekirse alt görevler ekleyin.