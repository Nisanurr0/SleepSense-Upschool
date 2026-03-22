📄 PRD: "SleepSense" 

1. Ürünün Amacı (Neden Buradayız?)

İnsanların uyku sorunlarını yüzeysel tavsiyelerle değil; kullanıcının biyolojisini, gün içindeki davranışlarını ve bulunduğu ortamın (mekan) fiziksel şartlarını birleştirerek çözen yapay zeka destekli bir web uygulaması yaratmak. Uygulamanın kalbinde, tüm bu verileri harmanlayan bir Bütüncül Karar Motoru yer alır.

2. Hedef Kitle (Kimin İçin Yapıyoruz?)

Kronik uyku problemi (insomnia) çekenler.

Vardiyalı çalışanlar veya sık seyahat edip jet-lag yaşayanlar.

Uyku kalitesini artırarak gün içi performansını yükseltmek isteyen herkes.

3. Çekirdek Sistem: 3'lü Sacayağı

Uygulamamız problemi 3 ana başlıkta toplar:

Mekan (Çevresel Veriler): Uygulama hem kullanıcının sabit ev konumunu (otoban, eğlence mekanı vb.) hem de o anki hava durumu, sıcaklık, hava kalitesi gibi dinamik verileri analiz eder.

Davranış (Günlük Alışkanlıklar): Kullanıcının gün içindeki hareketleri, yediği/içtiği şeyler ve duygu durumu (modu).

Biyoloji (Fiziksel Durum): Kullanıcının yaşı, cinsiyeti, mevcut stres seviyesi, kronik rahatsızlıkları ve birikmiş "uyku borcu".

4. Kullanıcı Deneyimi (Bir Kullanıcı Uygulamayı Nasıl Kullanır?)

İlk Tanışma (Onboarding): Kullanıcı siteye girer. Uygulama ona yaşını, genel uyku düzenini ve kronik bir sorunu olup olmadığını sorar (Biyoloji profilini oluşturur). Ayrıca kullanıcıdan ev adresini veya konumunu girmesini ister. Böylece evin çevresel faktörlerini (otobana veya eğlence mekanlarına yakınlık, gürültü potansiyeli vb.) baştan analiz eder.

Günlük Veri Girişi (Check-in): Sadece akşamları siteye girmek yerine, kullanıcı gün içinde yediklerini, içtiklerini ve anlık duygu durumunu (modunu) sisteme girer. Sistem sadece tek bir anı değil, kullanıcının o günkü tüm yaşantısını bir bütün olarak toplar.

Yapay Zeka Motorunun Çalışması: Bütüncül Karar Motoru devreye girer. Kullanıcının gün boyu girdiği beslenme ve mod verilerini (Davranış), profilini (Biyoloji), evinin çevresel dezavantajlarını ve o anki hava durumunu (Mekan) tek bir potada birleştirerek analiz eder.

Somut Aksiyon Önerisi: Kullanıcıya ezbere bilgi yerine, o geceye ve o kişiye özel direktifler verir.

Örnek Çıktı: "Bugün akşam yemeğinde ağır yemişsin ve gün boyu stresliymişsin (Davranış/Mod). Üstelik evinin yanındaki otobandan dolayı bu gece gürültü olabilir ve hava normalden 5 derece daha sıcak (Mekan). Vücut ısını düşürmek için uyumadan önce ılık bir duş al, sindirimi rahatlatmak için nane çayı iç ve otoban gürültüsünü bastırmak için beyaz gürültü (white noise) aç."

5. Temel Özellikler (MVP - Minimum Çalışan Ürün)

Uygulamayı ilk canlıya aldığımızda içinde olması gereken en temel özellikler:

Kullanıcı Kayıt Sistemi: Herkesin kendi profilinin, ev konumunun ve geçmiş uyku verilerinin tutulması.

Günlük Mini Form: Kullanıcının yediklerini ve gün içindeki modunu girebileceği basit, yorucu olmayan bir arayüz.

Çevresel API Entegrasyonu: Konum izni ve harita analizi ile o bölgenin risklerini (gürültü, mekanlar) ve hava durumunu otomatik çeken sistem.

Yapay Zeka Prompt Motoru: Elde edilen verileri yapay zekaya gönderip, anlamlı ve insansı tavsiyelere dönüştüren arka plan sistemi.

İlerleme Grafiği: Kullanıcının son 1 haftadaki uyku puanını ve gelişimini gösteren basit bir pano.

6. Teknik Altyapı Özeti (Mimari)

Ön Yüz (Kullanıcının Gördüğü Kısım): React.js veya Next.js (Hızlı, modern ve mobil cihazlarda uygulama gibi çalışır).

Arka Yüz (Beyin): Python (Verileri işlemek, dış çevresel API'ler ile haberleşmek ve yapay zeka motorunu en verimli şekilde çalıştırmak için en doğru tercih).

Veritabanı (Hafıza): PostgreSQL veya Firebase.

Dış Kaynaklar (Sensörler): Google Maps/Places API (Mekan analizi için), OpenWeatherMap API (Hava durumu için), AI API (Karar motoru için).