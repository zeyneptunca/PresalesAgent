# EFOR TAHMİN REFERANS DOKÜMANI
# Versiyon: 12
# Son Güncelleme: 2026-03
# Önceki: v11


Bu doküman, Efor Tahmin Agentı tarafından kullanılan karar ağacı, kategori tanımları ve referans bilgilerini içerir.


================================================================================
BÖLÜM 1: DELİVERABLE KATEGORİ KARAR AĞACI
================================================================================

Her deliverable için aşağıdaki adımları SIRAYLA kontrol et.
İLK eşleşen kategoriyi kullan ve sonraki adımlara GEÇME.
Kontrol alanları: deliverable adı, WP description, frontend_requirements, backend_requirements

ÖNEMLİ: Keyword eşleşmesi tek başına yeterli DEĞİL.
"DEĞİL Koşulları" ve "Bağlam Kontrolü" de değerlendirilmeli.

!!! KRİTİK PRENSİP: "KATEGORİ ŞÜPHEDE KÜÇÜĞE YUVARLA" !!!
VibeCoding ve Copilot+Claude profillerinde, bir deliverable'ın hangi kategoriye
girdiği konusunda tereddüt varsa DAHA DÜŞÜK EFORLu kategoriyi seç.
  → "Bu COMPLEX_UI mı SIMPLE_UI mı?" → SIMPLE_UI seç
  → "Bu RULE_ENGINE mı yoksa basit iş mantığı mı?" → SIMPLE_UI seç
  → "Bu INTEGRATION mı yoksa sadece API call mı?" → SIMPLE_UI seç
Gerekçe: AI araçları karmaşıklığı absorbe eder. Geleneksel geliştirmede
"karmaşık" olan pattern'ler AI ile "basit" hale gelir.


─────────────────────────────────────────────────────────────────────────────
ADIM A - ARKA PLAN İŞLEMİ Mİ? → BACKGROUND_JOB
─────────────────────────────────────────────────────────────────────────────
Keywordler: "Job", "Scheduler", "Sync", "Arka plan", "Background", "Queue",
            "Async", "Batch işlem", "Scheduled", "Periyodik", "Zamanlanmış",
            "Cron", "Worker", "Message queue"

DEĞİL Koşulları (bu varsa BACKGROUND_JOB değil):
  ✗ "Async button click" → UI interaction, SIMPLE_UI
  ✗ "Background color" → Styling, SIMPLE_UI
  ✗ Sadece "senkronizasyon" kelimesi → Bağlama bak, veri sync mi UI sync mi?
  ✗ "Auto-save" → Periyodik gibi görünür ama standart frontend timer, SIMPLE_UI
  ✗ "Countdown timer" → UI timer, SIMPLE_UI
  ✗ "Retry logic" → Eğer basit try-catch + retry ise SIMPLE_UI

Bağlam Kontrolü:
  → İşlem KULLANICI ETKİLEŞİMİ DIŞINDA mı çalışıyor? (Evet → BACKGROUND_JOB)
  → Sunucu tarafında zamanlanan bağımsız bir süreç mi? (Evet → BACKGROUND_JOB)
  → Kullanıcı tetikliyor ama sonucu beklemiyor mu? (Evet → BACKGROUND_JOB)

VibeCoding İndirgeme Kuralı:
  → Basit event listener + e-posta tetikleme → SIMPLE_UI (AI trivial üretir)
  → Basit queue (Redis/DB tabanlı) → SIMPLE_UI (standart pattern, AI bilir)
  → SADECE karmaşık scheduling, cron ifadeleri, dead-letter queue → BACKGROUND_JOB

Örnek EVET: "Günlük rapor oluşturma job'ı", "Periyodik veri senkronizasyonu"
Örnek HAYIR: "Async form submit", "Auto-save draft", "E-posta gönderim trigger"

Referans Efor (VibeCoding):
  Basit scheduled job: ~2 saat (0.25 AG)
  Karmaşık queue + retry + dead-letter: ~4 saat (0.5 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM B - ENTEGRASYON MU? → INTEGRATION
─────────────────────────────────────────────────────────────────────────────
Keywordler: "SSO", "Integration", "Entegrasyon", "Dış sistem", "3rd party",
            "Üçüncü parti", "API client", "Servis entegrasyon", "SAP", "ERP",
            "CRM", "Provider", "Adaptör", "Web service", "SOAP", "REST client"

DEĞİL Koşulları (bu varsa INTEGRATION değil):
  ✗ "YouTube embed/iframe/link" → Sadece URL gömme, SIMPLE_UI
  ✗ "Video oynatma", "Video izleme" → Media player component, SIMPLE_UI
  ✗ "Google Maps gösterimi" → Embed, SIMPLE_UI (API key ile veri çekme yoksa)
  ✗ "Sosyal medya paylaş butonu" → Share link + meta tag, SIMPLE_UI
  ✗ "iframe içinde göster" → Embed, SIMPLE_UI
  ✗ integration_points[] dizisi BOŞ → Gerçek entegrasyon yok
  ✗ "CDN upload/download" → Standart SDK call, SIMPLE_UI (Azure Blob gibi)
  ✗ "SMTP e-posta gönderimi" → Standart library call, SIMPLE_UI
  ✗ "LLM API call (OpenAI/Claude)" → Tek endpoint call + prompt, SIMPLE_UI
  ✗ "Webhook alıcı" → Basit endpoint, SIMPLE_UI

Bağlam Kontrolü:
  → "Entegrasyon" kelimesi geçse bile integration_points[] boşsa → SIMPLE_UI
  → Dış sistemden veri ÇEKİLİYOR mu yoksa sadece link/embed mi?
  → API anahtarı, authentication, veri dönüşümü var mı?
  → Karmaşık veri mapping veya protocol dönüşümü var mı?

VibeCoding İndirgeme Kuralı:
  → Standart REST API call (SDK mevcut) → SIMPLE_UI (AI SDK wrapper yazar)
  → OAuth/API key ile basit veri çekme → SIMPLE_UI (boilerplate, AI üretir)
  → SADECE karmaşık protocol (SOAP, custom binary), çift yönlü sync,
    veya dokümantasyonu yetersiz proprietary API → INTEGRATION

Örnek EVET: "Koç Gönüllüleri Portal çift yönlü sync", "BKD Portal veri eşleme",
            "SAP entegrasyonu (BAPI)", "Proprietary API veri dönüşümü"
Örnek HAYIR: "YouTube video embed", "CDN dosya upload", "SMTP mail gönder",
            "LLM API call", "Sosyal medya share", "SMS API", "Webhook endpoint"

Referans Efor (VibeCoding):
  Basit API entegrasyonu (SDK var): ~2 saat → SIMPLE_UI olarak eforla
  Orta (REST+OAuth, veri mapping): ~6 saat (0.75 AG)
  Karmaşık (bidirectional sync, protocol): ~6 saat (0.75 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM C - KURAL MOTORU / KOMPLEKS MANTIK MI? → RULE_ENGINE
─────────────────────────────────────────────────────────────────────────────
Keywordler: "Rule engine", "Kural motoru", "Validasyon motoru", "Algoritma",
            "Hesaplama motoru", "Puanlama", "Scoring", "Ön eleme",
            "Filtreleme motoru", "İş kuralı engine", "Decision engine",
            "Calculation engine", "Dinamik kural"

DEĞİL Koşulları (bu varsa RULE_ENGINE değil):
  ✗ "Form validasyon" → Standart input validation, SIMPLE_UI
  ✗ "Basit hesaplama" (toplam, ortalama, yüzde) → SIMPLE_UI
  ✗ "if-else iş mantığı" → Normal backend logic, SIMPLE_UI
  ✗ "Filtreleme" (liste filtreleme) → UI filter, SIMPLE_UI
  ✗ "Puan ortalaması hesaplama" → SQL AVG, SIMPLE_UI
  ✗ "Sıralama algoritması" → SQL ORDER BY + basit kural, SIMPLE_UI
  ✗ "Eşik kontrolü" (puan farkı > 1 ise uyar) → Basit if, SIMPLE_UI
  ✗ "Atama algoritması" (her takıma 2 jüri) → Basit loop + dağıtım, SIMPLE_UI
  ✗ "Son tarih kontrolü" → Date comparison, SIMPLE_UI
  ✗ "Yaş validasyonu" → Basit tarih farkı, SIMPLE_UI

Bağlam Kontrolü:
  → Kurallar RUNTIME'da DEĞİŞTİRİLEBİLİR mi? (Evet → RULE_ENGINE)
  → Kural sayısı > 10 ve KARMAŞIK MI? (Evet → RULE_ENGINE)
  → Kurallar arası BAĞIMLILIK ve ÖNCELİK sırası var mı? (Evet → RULE_ENGINE)
  → Sadece hardcoded iş mantığı mı? (Evet → SIMPLE_UI)
  → "Algoritma" kelimesi geçse bile SQL query + basit mantık mı? (Evet → SIMPLE_UI)

VibeCoding İndirgeme Kuralı:
  → Puan hesaplama (ortalama, toplam, ağırlıklı) → SIMPLE_UI
  → Basit atama/dağıtım mantığı (round-robin, rastgele, constraint) → SIMPLE_UI
  → Sıralama + tiebreaker kuralları → SIMPLE_UI
  → SADECE dinamik konfigürasyon, karmaşık karar ağacı, ML modeli → RULE_ENGINE

Örnek EVET: "Dinamik fiyat hesaplama motoru (20+ kural)",
            "Kredi skorlama (configurable parametre)", "Admin tarafından düzenlenebilir iş kuralları"
Örnek HAYIR: "Puan ortalaması hesapla", "Takım sıralama", "Yaş kontrolü",
            "Jüri atama (min 2 jüri/takım)", "Puan farkı uyarısı", "Son tarih kilidi"

Referans Efor (VibeCoding):
  Puan hesaplama/sıralama: ~1-2 saat → SIMPLE_UI olarak eforla
  Atama algoritması (constraint): ~3 saat → SIMPLE_UI olarak eforla
  Gerçek configurable rule engine: ~6 saat (0.75 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM D - EXPORT / RAPOR MU? → EXPORT_REPORT
─────────────────────────────────────────────────────────────────────────────
Keywordler: "Export", "PDF oluştur", "PDF export", "JPEG export", "PNG export",
            "CSV export", "Excel export", "Rapor oluştur", "Report generate",
            "Dışa aktar", "Yazdır", "Print"

DEĞİL Koşulları (bu varsa EXPORT_REPORT değil):
  ✗ "PDF görüntüle/aç" → Viewer, SIMPLE_UI
  ✗ "Dosya indir" (mevcut dosya) → Download link, SIMPLE_UI
  ✗ "Print CSS" → Styling, SIMPLE_UI
  ✗ "Rapor ekranı" (sadece data table gösterimi) → SIMPLE_UI
  ✗ "İstatistik kartları" (count/sum gösterimi) → SIMPLE_UI
  ✗ "Dashboard grafikleri" → Chart.js/Recharts, ayrı değerlendir (COMPLEX_UI veya SIMPLE_UI)

Bağlam Kontrolü:
  → Sistem yeni dosya OLUŞTURUYOR mu yoksa mevcut dosyayı mı gösteriyor?
  → Veri dönüşümü ve formatting var mı?
  → Library (PDFKit, ClosedXML, Puppeteer) ile template bazlı üretim mi?

VibeCoding İndirgeme Kuralı:
  → Basit CSV/Excel export (veri dump) → SIMPLE_UI (AI library call yazar)
  → Template bazlı PDF (sertifika, fatura) → EXPORT_REPORT (ama düşük efor)
  → Karmaşık rapor (multi-sheet Excel, grafik + tablo + header/footer) → EXPORT_REPORT

Örnek EVET: "Sertifika PDF oluştur", "Turnuva sonuç raporu Excel export",
            "Karmaşık fatura PDF (header+detay+footer)"
Örnek HAYIR: "Veri tablosunu CSV indir", "Dashboard istatistik kartları",
            "PDF dosyasını görüntüle"

Referans Efor (VibeCoding):
  Basit CSV/Excel dump: ~1 saat → SIMPLE_UI olarak eforla
  Template PDF (sertifika): ~2 saat (0.25 AG)
  Karmaşık rapor: ~2 saat (0.25 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM E - DOSYA İŞLEME Mİ? → FILE_PROCESS
─────────────────────────────────────────────────────────────────────────────
Keywordler: "Upload", "Yükle", "Import", "İçe aktar", "Parse", "Dosya yükleme",
            "Şablon indirme", "Template download", "Belge yükleme", "Attachment",
            "Ek dosya", "Bulk import", "Toplu yükleme"

DEĞİL Koşulları (bu varsa FILE_PROCESS değil):
  ✗ "Dosya linki göster" → SIMPLE_UI
  ✗ "Dosya adı listele" → SIMPLE_UI
  ✗ "İndirme butonu" → Mevcut dosya download, SIMPLE_UI
  ✗ "Tek dosya upload (profil fotoğrafı)" → Framework upload widget, SIMPLE_UI
  ✗ "CDN'den dosya indir" → Link, SIMPLE_UI

Bağlam Kontrolü:
  → Dosya içeriği PARSE ediliyor mu? (Evet → FILE_PROCESS)
  → Dosya format/boyut DOĞRULAMASI karmaşık mı? (Karmaşık → FILE_PROCESS)
  → Toplu (bulk) veri import mu? (Evet → FILE_PROCESS)
  → Basit upload + CDN'e kaydet mi? (Basit → SIMPLE_UI)

VibeCoding İndirgeme Kuralı:
  → Tek/çoklu dosya upload (boyut/tip validasyonlu) → SIMPLE_UI (AI widget üretir)
  → CDN'e upload + metadata kaydet → SIMPLE_UI
  → SADECE Excel/CSV parse + veri dönüştürme + bulk insert → FILE_PROCESS

Örnek EVET: "CSV'den toplu öğrenci veri yükle", "Excel template import + mapping",
            "PDF parse + metin çıkarma"
Örnek HAYIR: "Profil fotoğrafı upload", "Sunum dosyası yükleme", "CDN upload"

Referans Efor (VibeCoding):
  Dosya upload + CDN: ~1-2 saat → SIMPLE_UI olarak eforla
  Excel/CSV parse + bulk import: ~2 saat (0.25 AG)
  Karmaşık parse + mapping: ~3 saat (0.375 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM F - KOMPLEKS UI Mİ? → COMPLEX_UI
─────────────────────────────────────────────────────────────────────────────
Keywordler: "Dashboard", "Wizard", "Şema", "Ağaç", "Tree", "Hiyerarşi", "Chart",
            "Grafik", "Timeline", "Kırpma", "Crop", "Zoom", "Drag", "Drop",
            "Kanban", "Calendar", "Takvim", "Gantt", "Flow", "Akış", "Multi-step",
            "Çok adımlı", "Stepper", "Org chart", "Interactive map"

DEĞİL Koşulları (bu varsa COMPLEX_UI değil):
  ✗ "Basit dropdown tree" → SIMPLE_UI
  ✗ "Statik grafik görseli" → Image, SIMPLE_UI
  ✗ "Accordion/collapse" → SIMPLE_UI
  ✗ "Tab navigasyonu" → Standart tab component, SIMPLE_UI
  ✗ "Özet kartlar (summary cards)" → Basit card layout, SIMPLE_UI
  ✗ "Basit chart" (tek pie/bar chart, Chart.js ile) → SIMPLE_UI
  ✗ "Multi-step form" (adım 1-2-3 wizard, basit) → SIMPLE_UI
  ✗ "Status badge/indicator" → Basit component, SIMPLE_UI
  ✗ "Rating/scoring component" (1-4 yıldız) → Basit input, SIMPLE_UI
  ✗ "Countdown timer" → Basit JS timer, SIMPLE_UI
  ✗ "Multi-select tablo" (checkbox + select) → SIMPLE_UI

Bağlam Kontrolü:
  → GERÇEK drag-drop etkileşimi var mı? (Evet → COMPLEX_UI)
  → Canvas/SVG manipülasyonu var mı? (Evet → COMPLEX_UI)
  → Özel 3rd party library'nin DETAYLI konfigürasyonu gerekiyor mu?
  → "Dashboard" kelimesi geçse bile sadece kartlar + tablolar mı? (Evet → SIMPLE_UI)

VibeCoding İndirgeme Kuralı:
  → "Dashboard" = tab menü + kartlar + tablo → SIMPLE_UI (çoğu dashboard budur!)
  → "Multi-step form" = birkaç adımlı form → SIMPLE_UI (AI stepper üretir)
  → "Chart" = Chart.js/Recharts ile 1-3 grafik → SIMPLE_UI
  → "Scoring form" = rating component + form → SIMPLE_UI
  → SADECE interaktif drag-drop, real-time collaboration, canvas/SVG editor,
    karmaşık veri görselleştirme (10+ chart, drill-down) → COMPLEX_UI

!!! ÖNEMLİ: "Dashboard" kelimesi COMPLEX_UI DEMEKTİR diye düşünME !!!
Gerçek dünya projelerinin %80'inde "dashboard" basit kartlar + tablo + sekmedir.
Bu SIMPLE_UI'dır. COMPLEX_UI yalnızca gerçek interaktif/görsel karmaşıklık
olduğunda kullanılır.

Örnek EVET: "Gerçek zamanlı veri akış görselleştirme", "Drag-drop jüri-takım
            atama paneli", "Interaktif organizasyon şeması"
Örnek HAYIR: "Admin dashboard (sekmeler + kartlar)", "Jüri dashboard (takım
            listesi + butonlar)", "Turnuva dashboard (9 sekme, her biri basit liste/form)"

Referans Efor (VibeCoding):
  "Dashboard" (kartlar+tab+tablo): ~2-5 saat → SIMPLE_UI olarak eforla
  "Multi-step form": ~2 saat → SIMPLE_UI olarak eforla
  Gerçek interactive chart/drag-drop: ~5 saat (0.625 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM G - MASKELEME / YETKİ KOMPONENTİ Mİ? → AUTH_COMPONENT
─────────────────────────────────────────────────────────────────────────────
Keywordler: "Maskeleme", "Gizleme", "Göster butonu", "Göster/Gizle toggle",
            "Yetki kontrol", "Permission check", "RBAC", "Rol bazlı görünürlük",
            "Erişim kontrol", "field-level security"

DEĞİL Koşulları (bu varsa AUTH_COMPONENT değil):
  ✗ "Password gizle/göster" → Standart input, SIMPLE_UI
  ✗ "Collapse/expand section" → UI toggle, SIMPLE_UI
  ✗ "Menu görünürlük" (role göre) → Routing/menu logic, SIMPLE_UI
  ✗ "RBAC tanımlama ekranı" → CRUD form, SIMPLE_UI (OF-AUTHZ eşleşir)
  ✗ "Rol atama dropdown" → Basit select, SIMPLE_UI
  ✗ "Admin permissions" → Framework RBAC config, SIMPLE_UI (OF-AUTHZ eşleşir)

Bağlam Kontrolü:
  → Hassas veri maskeleme mi? (ücret, TC kimlik, kredi kartı)
  → Field seviyesinde ÖZEL yetki kontrolü mü?
  → Backend'de KAYIT BAZLI veri filtreleme gerekiyor mu?

VibeCoding İndirgeme Kuralı:
  → Rol bazlı menu/sayfa görünürlüğü → SIMPLE_UI (framework middleware)
  → Standart RBAC (5-10 rol, sayfa bazlı yetki) → SIMPLE_UI (OneFrame hazır)
  → SADECE field-level maskeleme (ücret gizle/göster), kayıt bazlı
    veri filtreleme (kendi takımını görme kuralı) → AUTH_COMPONENT

Örnek EVET: "Maaş bilgisi maskeleme", "TC kimlik göster/gizle butonu"
Örnek HAYIR: "Rol atama ekranı", "Admin yetki matrisi", "Sayfa bazlı erişim"

Referans Efor (VibeCoding):
  RBAC ekranı: ~1 saat → SIMPLE_UI olarak eforla
  Field-level maskeleme: ~2 saat (0.25 AG)

─────────────────────────────────────────────────────────────────────────────
ADIM H - HİÇBİRİ DEĞİL → SIMPLE_UI
─────────────────────────────────────────────────────────────────────────────
Yukarıdaki hiçbir kategoriye uymayan her şey SIMPLE_UI'dır.

!!! SIMPLE_UI GENIŞ BIR KATEGORİDİR !!!
VibeCoding modunda görevlerin büyük çoğunluğu (%65-75) SIMPLE_UI olarak
sınıflandırılmalıdır. Bu beklenen ve doğru bir durumdur.

Tipik SIMPLE_UI örnekleri:
  • Form ekranları (kayıt, düzenleme, başvuru)
  • Liste/tablo ekranları (data table, sayfalama)
  • Detay görüntüleme ekranları
  • Modal/popup/dialog
  • Arama ve filtreleme ekranları
  • Basit CRUD operasyonları (ekleme, silme, güncelleme)
  • Tab/accordion yapıları
  • Dropdown/select/cascading komponentleri
  • Button/link aksiyonları
  • Basit dashboard'lar (kartlar + tablo + sekmeler)
  • Multi-step form (wizard yapıları)
  • Rating/scoring komponentleri (1-5 yıldız, 1-4 skala)
  • Status badge/indicator
  • Countdown timer
  • Profil sayfaları
  • Ayar/konfigürasyon ekranları
  • Onay mekanizmaları (KVKK, şartname checkbox)
  • Şifre oluşturma/sıfırlama ekranları
  • Login/logout ekranları
  • E-posta template yönetim ekranları
  • Basit puan hesaplama (ortalama, toplam)
  • Basit sıralama (SQL ORDER BY + tiebreaker)
  • Basit atama mantığı (round-robin, constraint)
  • Eşik kontrol uyarıları (fark > N ise bildir)
  • Son tarih kilitleme (date comparison)
  • CDN dosya upload/download
  • Sosyal medya paylaşım butonları
  • Basit API çağrıları (LLM, SMTP, SMS, CDN)
  • UUID üretimi + doğrulama endpoint
  • Audit log görüntüleme tablosu
  • Basit chart/grafik (tek grafik, Chart.js ile)


─────────────────────────────────────────────────────────────────────────────
1.2 VİBECODİNG KATEGORİ İNDİRGEME MATRİSİ
─────────────────────────────────────────────────────────────────────────────

VibeCoding ve Copilot+Claude profillerinde, AI araçlarının üretkenlik avantajı
nedeniyle birçok deliverable geleneksel kategorisinden DAHA DÜŞÜK kategoriye
indirgenir. Bu matris, karar ağacından SONRA uygulanır.

GELENEKSEL KATEGORİ    | KOŞUL                                          | VibeCoding KATEGORİSİ
-----------------------|------------------------------------------------|---------------------
BACKGROUND_JOB         | Basit event trigger + API call                  | → SIMPLE_UI
BACKGROUND_JOB         | Basit queue (Redis/DB)                          | → SIMPLE_UI
BACKGROUND_JOB         | Karmaşık scheduling/cron + dead-letter          | → BACKGROUND_JOB (kalır)
INTEGRATION            | Standart SDK mevcut (CDN, SMTP, LLM)            | → SIMPLE_UI
INTEGRATION            | REST API + OAuth (iyi dokümante)                | → SIMPLE_UI
INTEGRATION            | Bidirectional sync, proprietary protocol        | → INTEGRATION (kalır)
RULE_ENGINE            | Puan ortalama/toplam hesaplama                  | → SIMPLE_UI
RULE_ENGINE            | Basit sıralama + tiebreaker                     | → SIMPLE_UI
RULE_ENGINE            | Basit atama/dağıtım (constraint var)            | → SIMPLE_UI
RULE_ENGINE            | Dinamik configurable kural motoru               | → RULE_ENGINE (kalır)
EXPORT_REPORT          | Basit veri dump (CSV/Excel)                     | → SIMPLE_UI
EXPORT_REPORT          | Template bazlı PDF/Excel                        | → EXPORT_REPORT (kalır)
FILE_PROCESS           | Tekli/çoklu upload + CDN kaydet                 | → SIMPLE_UI
FILE_PROCESS           | Bulk import + parse + mapping                   | → FILE_PROCESS (kalır)
COMPLEX_UI             | Dashboard (kartlar + tab + tablo)               | → SIMPLE_UI
COMPLEX_UI             | Multi-step form (basit wizard)                  | → SIMPLE_UI
COMPLEX_UI             | Basit chart (1-3 grafik, Chart.js)              | → SIMPLE_UI
COMPLEX_UI             | Scoring/rating form                             | → SIMPLE_UI
COMPLEX_UI             | Drag-drop, canvas, real-time vizüalizasyon      | → COMPLEX_UI (kalır)
AUTH_COMPONENT         | Standart RBAC (rol-sayfa bazlı)                 | → SIMPLE_UI
AUTH_COMPONENT         | Field-level maskeleme                           | → AUTH_COMPONENT (kalır)

İndirgeme Uygulama Kuralı:
  1. Karar ağacında (ADIM A-H) ilk eşleşen kategori belirlenir
  2. VibeCoding veya Copilot+Claude profili seçiliyse bu matris uygulanır
  3. Matristeki koşul sağlanıyorsa kategori indirgenir
  4. İndirgenen kategori hesaplama notunda belirtilir:
     "Orijinal: COMPLEX_UI → VibeCoding indirgeme: SIMPLE_UI (kartlar+tab dashboard)"

!!! İNDİRGEME İSTİSNALARI (v11) !!!
Aşağıdaki koşullardan BİRİ bile sağlanıyorsa indirgeme UYGULANMAZ,
orijinal kategori korunur:

  1. ENTEGRASYON İSTİSNASI: Deliverable'ın ait olduğu WP'de
     integration_points > 0 ise, o deliverable indirgenmez.
     Gerekçe: Dış sistem entegrasyonu AI'ın kontrol edemediği karmaşıklık
     getirir — API davranışı, timeout, hata yönetimi, güvenlik.

  2. ÇOKLU KAYNAK İSTİSNASI: WP description'da 3+ farklı veri kaynağı
     veya sistem referansı varsa, o WP'deki deliverable'lar indirgenmez.
     Gerekçe: Normalize etme, mapping, farklı format yönetimi AI ile
     üretilse bile test ve doğrulama süresi yüksektir.

  3. REAL-TIME İSTİSNASI: Deliverable'da "real-time", "WebSocket", "SSE",
     "SignalR", "live update" keyword'leri varsa COMPLEX_UI indirgenmez.
     Gerekçe: Real-time veri akışı connection yönetimi, reconnect, state
     sync gibi edge case'ler gerektirir.

  4. GÜVENLİK KRİTİK İSTİSNASI: Deliverable'da "SSO", "OAuth", "SAML",
     "token", "encryption", "güvenlik" varsa AUTH_COMPONENT indirgenmez.
     Gerekçe: Güvenlik bileşenlerinde hata toleransı sıfırdır, review
     ve test süresi AI hızından bağımsızdır.


─────────────────────────────────────────────────────────────────────────────
1.3 GERÇEK PROJE KATEGORİ DAĞILIM REHBERİ
─────────────────────────────────────────────────────────────────────────────

VibeCoding modunda beklenen kategori dağılımı (tipik web uygulaması bazlı):

BEKLENEN VibeCoding DAĞILIMI (tipik web uygulaması):
  SIMPLE_UI:        %65-75 (görevlerin büyük çoğunluğu)
  INTEGRATION:      %5-10  (sadece gerçek dış sistem entegrasyonları)
  EXPORT_REPORT:    %3-5   (sadece template bazlı dosya üretimi)
  FILE_PROCESS:     %2-4   (sadece parse + bulk import)
  COMPLEX_UI:       %3-5   (sadece gerçek interaktif UI)
  BACKGROUND_JOB:   %2-4   (sadece karmaşık scheduling)
  RULE_ENGINE:      %1-3   (sadece dinamik configurable kurallar)
  AUTH_COMPONENT:   %1-3   (sadece field-level maskeleme)

!!! UYARI: Eğer SIMPLE_UI oranı %50'nin altındaysa !!!
Kategorizasyonu gözden geçirin. VibeCoding modunda SIMPLE_UI baskın kategori
olmalıdır. Düşük SIMPLE_UI oranı muhtemelen şu hatalardan birine işaret eder:
  - "Dashboard" kelimesine bakarak COMPLEX_UI etiketlemek
  - Basit hesaplamaları RULE_ENGINE saymak
  - SDK tabanlı API çağrılarını INTEGRATION saymak
  - Basit upload'ları FILE_PROCESS saymak

─────────────────────────────────────────────────────────────────────────────
1.4 SIK YAPILAN KATEGORİZASYON HATALARI
─────────────────────────────────────────────────────────────────────────────

Aşağıdaki hatalar tahminlerin şişmesine neden olur.
Bu hataları TEKRARLAMA:

HATA 1: "Dashboard" = COMPLEX_UI sanmak
  ✗ YANLIŞ: "Turnuva Dashboard (9 sekme)" → COMPLEX_UI (FE:2.5, BE:2.0)
  ✓ DOĞRU:  "Turnuva Dashboard (9 sekme)" → SIMPLE_UI (her sekme basit liste/form)
  Neden: 9 sekme = 9 adet SIMPLE_UI'dır, tek bir COMPLEX_UI değil.
  AI her sekmeyi ayrı basit component olarak üretir.

HATA 2: "Puan hesaplama" = RULE_ENGINE sanmak
  ✗ YANLIŞ: "Puan Ortalaması Hesaplama Servisi" → RULE_ENGINE (BE:4.0)
  ✓ DOĞRU:  "Puan Ortalaması Hesaplama Servisi" → SIMPLE_UI (BE:0.20)
  Neden: SQL AVG() + GROUP BY + basit if-else. AI bunu 15 dakikada yazar.

HATA 3: "CDN Entegrasyonu" = INTEGRATION sanmak
  ✗ YANLIŞ: "CDN Dosya Upload/Download" → INTEGRATION (BE:3.0)
  ✓ DOĞRU:  "CDN Dosya Upload/Download" → SIMPLE_UI (BE:0.20)
  Neden: Azure Blob SDK 3 satır kod. AI bunu anında üretir.

HATA 4: "E-posta gönderim servisi" = INTEGRATION sanmak
  ✗ YANLIŞ: "E-posta Gönderim Servisi" → INTEGRATION (BE:3.0)
  ✓ DOĞRU:  "E-posta Gönderim Servisi" → SIMPLE_UI (BE:0.20)
  Neden: SMTP veya API SDK çağrısı. OneFrame notification modülü zaten var.

HATA 5: "Auto-save" = BACKGROUND_JOB sanmak
  ✗ YANLIŞ: "Taslak Kaydetme Mekanizması" → BACKGROUND_JOB (BE:3.0)
  ✓ DOĞRU:  "Taslak Kaydetme Mekanizması" → SIMPLE_UI (BE:0.20)
  Neden: Frontend setInterval + API POST. Arka plan job'ı değil.

HATA 6: "OTP/MFA" = COMPLEX_UI sanmak
  ✗ YANLIŞ: "OTP Mekanizması" → COMPLEX_UI (FE:2.5, BE:2.0)
  ✓ DOĞRU:  "OTP Mekanizması" → SIMPLE_UI (toplam:0.40)
  Neden: Mevcut OTP library + input + verify. AI pattern'i bilir.

HATA 7: "Atama algoritması" = RULE_ENGINE sanmak
  ✗ YANLIŞ: "Jüri Atama Algoritması" → RULE_ENGINE (BE:4.0)
  ✓ DOĞRU:  "Jüri Atama Algoritması" → SIMPLE_UI (BE:0.20)
  Neden: Min 2 jüri/takım, yük dengeleme = basit loop + constraint.
  AI bunu tek prompt ile yazar.

HATA 8: "Sosyal medya entegrasyonu" = INTEGRATION sanmak
  ✗ YANLIŞ: "Sosyal Medya Paylaşım Entegrasyonu" → INTEGRATION (BE:3.0)
  ✓ DOĞRU:  "Sosyal Medya Paylaşım Entegrasyonu" → SIMPLE_UI (toplam:0.40)
  Neden: Share URL + meta tag. Gerçek API entegrasyonu yok.

HATA 9: "AI destekli geri bildirim" = INTEGRATION sanmak
  ✗ YANLIŞ: "AI Destekli Geri Bildirim Düzenleme" → INTEGRATION (BE:3.0)
  ✓ DOĞRU:  "AI Destekli Geri Bildirim Düzenleme" → SIMPLE_UI (toplam:0.40)
  Neden: Tek bir LLM API call (OpenAI/Claude) + prompt template. SDK mevcut.

HATA 10: Her deliverable'ı AYRI görev saymak (çarpan şişirmesi)
  ✗ YANLIŞ: 5 deliverable olan WP'ye 5 ayrı baz değer + batch çarpanı
  ✓ DOĞRU:  WP'nin TEK BİR FONKSİYONEL BLOK olduğunu düşün, deliverable'ları
            mikro-görev olarak değil parçalar olarak değerlendir.
  Neden: VibeCoding'de AI tüm WP'yi tek seferde scaffold eder, sonra
  developer her deliverable'ı ince ayar yapar.


================================================================================
BÖLÜM 2: KATEGORİ BAZLI BAZ EFOR DEĞERLERİ (Adam-Gün)
================================================================================

ÖNEMLİ: Bu bölümde ÜÇ ayrı geliştirici profili tanımlanmıştır.
Proje metodolojisine göre DOĞRU profili seçin.

2.1 GELİŞTİRİCİ PROFİLLERİ
-----------------------------
Profil A: Geleneksel (Non-AI) Mid-Level Developer
  → AI araç desteği YOK, klasik yazılım geliştirme süreci
  → Tüm kod elle yazılır, araştırma/deneme süreci dahil

Profil B: Copilot+Claude Destekli Senior Developer
  → GitHub Copilot + Claude ile eşli programlama (pair programming)
  → Kod önerileri AI'dan gelir, developer yönlendirir ve düzeltir
  → Senior seviye: Framework ve domain bilgisi yüksek

Profil C: VibeCoding (Tam AI Destekli) Senior Developer
  → Visual Studio Copilot, Visual Studio Code Copilot, Antigravity, Cursor, Claude Code, Windsurf gibi AI IDE araçlarıyla geliştirme
  → Developer prompt verir, AI kodu üretir, developer review eder
  → Kod üretiminin %70-80'i AI tarafından yapılır
  → Senior seviye: OneFrame framework deneyimi yüksek


2.2 GELENEKSEL GELİŞTİRME BAZ DEĞERLERİ (Profil A)
-----------------------------------------------------
KATEGORİ              | FE    | BE    | TOPLAM | AÇIKLAMA
----------------------|-------|-------|--------|------------------------------------------
BACKGROUND_JOB        | 0.0   | 3.0   | 3.0    | Arka plan servisi, scheduler, queue
INTEGRATION           | 0.0   | 3.0   | 3.0    | 3. parti API entegrasyonu, adaptör
RULE_ENGINE           | 0.0   | 4.0   | 4.0    | İş kuralı motoru, puanlama algoritması
EXPORT_REPORT         | 1.2   | 1.5   | 2.7    | PDF/Excel export, rapor ekranı
FILE_PROCESS          | 0.5   | 2.0   | 2.5    | Dosya yükleme, parse, şablon işleme
COMPLEX_UI            | 2.5   | 2.0   | 4.5    | Wizard, dashboard, tree, chart
AUTH_COMPONENT        | 0.5   | 1.5   | 2.0    | Maskeleme, yetki kontrolü komponenti
SIMPLE_UI             | 0.8   | 0.8   | 1.6    | Standart form, liste, modal, CRUD


2.3 COPILOT+CLAUDE BAZ DEĞERLERİ (Profil B)
---------------------------------------------------------
Senior developer + AI pair programming. OneFrame framework avantajı dahil.

Profil Çarpanı: Geleneksel baz değer x 0.40

KATEGORİ              | FE    | BE    | TOPLAM | AÇIKLAMA
----------------------|-------|-------|--------|------------------------------------------
BACKGROUND_JOB        | 0.0   | 1.20  | 1.20   | AI job pattern'i hızlı üretir
INTEGRATION           | 0.0   | 1.20  | 1.20   | API client AI ile hızlı, review gerekli
RULE_ENGINE           | 0.0   | 1.60  | 1.60   | İş kuralı AI ile yazılır, doğrulama önemli
EXPORT_REPORT         | 0.48  | 0.60  | 1.08   | Template bazlı, AI verimli
FILE_PROCESS          | 0.20  | 0.80  | 1.00   | Upload/parse AI ile standart
COMPLEX_UI            | 1.00  | 0.80  | 1.80   | Dashboard/wizard AI ile oluşturulur
AUTH_COMPONENT        | 0.20  | 0.60  | 0.80   | Yetki pattern'i framework'te mevcut
SIMPLE_UI             | 0.32  | 0.32  | 0.64   | Form/liste AI çok iyi üretir


2.4 VIBE CODING BAZ DEĞERLERİ (Profil C)
--------------------------------------------------------------
Tam AI destekli geliştirme. Kod üretiminin büyük kısmı AI tarafından.

Vibe Coding Çarpanı: Copilot+Claude baz değer x ortalama 0.60
(v11: Review, test ve entegrasyon doğrulama süresi dahil gerçekçi oran)

KATEGORİ              | Vibe FE | Vibe BE | TOPLAM | Geleneksele Oran
----------------------|---------|---------|--------|-------------------
SIMPLE_UI             | 0.20    | 0.20    | 0.40   | x0.25 (AI üretir + review + test)
FILE_PROCESS          | 0.12    | 0.50    | 0.62   | x0.25 (parse+mapping review gerektirir)
EXPORT_REPORT         | 0.30    | 0.35    | 0.65   | x0.24 (template test+doğrulama dahil)
AUTH_COMPONENT        | 0.12    | 0.38    | 0.50   | x0.25 (güvenlik review kritik)
COMPLEX_UI            | 0.60    | 0.50    | 1.10   | x0.24 (AI üretir, UX review şart)
BACKGROUND_JOB        | 0.00    | 0.75    | 0.75   | x0.25 (edge case test dahil)
INTEGRATION           | 0.00    | 0.95    | 0.95   | x0.32 (API client riskli, dış bağımlılık)
RULE_ENGINE           | 0.00    | 1.10    | 1.10   | x0.28 (mantık doğrulama kritik)

Vibe Coding Çarpan Mantığı (Copilot+Claude değerine göre):
- x0.58-0.63: Düşük riskli kategoriler (SIMPLE_UI, FILE_PROCESS, EXPORT, AUTH_COMP, COMPLEX_UI, BG_JOB)
- x0.69-0.79: Yüksek riskli kategoriler (INTEGRATION x0.79, RULE_ENGINE x0.69)
- Proje toplam ortalaması: %60

VibeCoding Uygulama Kuralı:
  metodoloji="VibeCoding" ise:
    1. Doğrudan Profil C baz değerlerini kullan (yukarıdaki tablo)
    2. Sonraki adımlar (batch, entegrasyon, kompleksite) uygulanır
    3. Faz hesabı VibeCoding özel yüzdeleriyle yapılır (Bölüm 4)

  metodoloji="Copilot+Claude" ise:
    1. Doğrudan Profil B baz değerlerini kullan
    2. Sonraki adımlar normal uygulanır
    3. Faz hesabı Copilot+Claude özel yüzdeleriyle yapılır (Bölüm 4)

ÖNEMLİ: Deliverable listesinde her zaman kullanılan profilin BAZ DEĞERİNİ göster.
Batch indirimi ayrı satırda belirtilir, baz değer DEĞİŞTİRİLMEZ.


================================================================================
BÖLÜM 3: ÇARPAN KURALLARI
================================================================================

3.1 BATCH (TOPLU) ÇARPANI
--------------------------
Aynı kategoriden birden fazla deliverable varsa profil bazlı indirim uygulanır.

GELENEKSEL (Profil A):
  1. ve 2. deliverable: 1.0x (tam efor)
  3. ve 4. deliverable: 0.6x (reuse avantajı)
  5. ve sonrası: 0.4x (yüksek reuse)

COPILOT+CLAUDE (Profil B):
  1. deliverable: 1.0x (tam efor)
  2. deliverable: 0.8x (AI pattern tanır, hızlı reuse)
  3. deliverable: 0.5x (pattern oturmuş)
  4. deliverable: 0.35x (minimal düzeltme)
  5. ve sonrası: 0.25x (sadece fark review)

VIBE CODING (Profil C):
  1. deliverable: 1.0x (tam efor)
  2. deliverable: 0.8x (AI pattern'i tanır)
  3. deliverable: 0.6x (pattern oturmuş)
  4. deliverable: 0.5x (minimal fark)
  5. ve sonrası: 0.35x (sadece prompt + review)

Neden B/C'de daha agresif? AI araçları pattern tekrarını hızlı uygular.
Ancak her deliverable'da hâlâ review, test ve entegrasyon doğrulaması gerekir.
Bu nedenle çarpanlar makul seviyelerde tutulur.

Gösterim kuralı: Deliverable listesinde BAZ DEĞER yazılır.
Batch indirimi hesaplama notunda ayrıca gösterilir.


3.2 ENTEGRASYON ÇARPANI
------------------------
integration_points dizisinin uzunluğuna göre:

GELENEKSEL ve COPILOT+CLAUDE (Profil A, B):
(NOT: Entegrasyon riski AI desteğinden bağımsızdır - dış sistem davranışı
değişmez. Bu nedenle A ve B aynı çarpanı kullanır.)
  0 nokta: 1.0x
  1-2 nokta: 1.15x
  3+ nokta: 1.30x

VIBE CODING (Profil C):
  0 nokta: 1.0x
  1-2 nokta: 1.08x
  3+ nokta: 1.15x

Neden Vibe daha düşük? AI araçları API client kodunu hızlı üretir, boilerplate
entegrasyon kodu neredeyse tamamen AI tarafından yazılır. Ama risk hala mevcuttur.

ÖNEMLİ: Çıktıda hangi entegrasyon noktalarının tetiklediği isim olarak belirtilmelidir.


3.3 KOMPLEKSİTE ÇARPANI
------------------------
WP complexity.level değerine göre (WBS'den olduğu gibi al, DEĞİŞTİRME):

GELENEKSEL ve COPILOT+CLAUDE (Profil A, B):
(NOT: Kompleksite seviyesi projenin doğasından gelir, AI desteği bu riski
azaltmaz. Bu nedenle A ve B aynı çarpanı kullanır.)
  low: 0.8x
  medium: 1.0x
  high: 1.25x
  very_high: 1.50x

VIBE CODING (Profil C):
  low: 0.85x
  medium: 1.0x
  high: 1.15x
  very_high: 1.30x

Neden C'de fark korunuyor? Karmaşıklık projenin doğasından gelir.
AI kod üretimini hızlandırsa da, karmaşık iş mantığının review ve test süresi
lineer olarak azalmaz. high ve very_high arasındaki fark korunmalıdır.


3.4 REUSE (YENİDEN KULLANIM) ÇARPANI
-------------------------------------
Benzerlik Kriterleri (aşağıdakilerden EN AZ 2 tanesi eşleşmeli):
  Kriter 1: Aynı baskın deliverable kategorisi (en çok tekrar eden kategori aynı)
  Kriter 2: Aynı veya komşu complexity level (low-medium veya medium-high komşu sayılır)
  Kriter 3: Deliverable sayısı farkı <= 2
  Kriter 4: Aynı modül içinde veya benzer domain (aynı profil portleti ailesi vb.)

Reuse Çarpanları (WP toplam eforuna uygulanır):

GELENEKSEL (Profil A):
  1. (orijinal) WP: 1.0x
  2. benzer WP: 0.7x
  3. benzer WP: 0.5x
  4+ benzer WP: 0.4x

COPILOT+CLAUDE (Profil B):
  1. (orijinal) WP: 1.0x
  2. benzer WP: 0.6x
  3. benzer WP: 0.4x
  4+ benzer WP: 0.25x

VIBE CODING (Profil C):
  1. (orijinal) WP: 1.0x
  2. benzer WP: 0.6x
  3. benzer WP: 0.45x
  4+ benzer WP: 0.3x

Neden C'de makul seviyede? AI reuse'u hızlandırsa da, her benzer WP'de
hâlâ entegrasyon testi, veri modeli farkı review ve UAT doğrulaması gerekir.

ÖNEMLİ: Çıktıda reuse_neden alanında hangi kriterlerin eşleştiği belirtilmelidir.


3.5 ALTYAPI WP İLİŞKİSİ
--------------------------
Eğer bir WP "altyapı" veya "ortak bileşen" niteliğindeyse (örn: tarihçeli veri altyapısı),
bu altyapıyı KULLANAN diğer WP'lerde bu bilgi hesaplama notunda belirtilmelidir.

Kural: Altyapı WP'si tam efor alır. Kullanan WP'ler kendi eforlarını alır ama
hesaplama notunda "WP-019 altyapısını kullanır" şeklinde referans verilir.
Altyapı kullanan WP'lerin eforları ayrıca azaltılmaz (çünkü altyapı ayrı hesaplanmıştır),
ancak bu bağımlılık açıkça belirtilir.


================================================================================
BÖLÜM 4: FAZ HESAPLAMA FORMÜLLERİ
================================================================================

Adjusted_FE ve Adjusted_BE hesaplandıktan sonra:
DevTotal = Adjusted_FE + Adjusted_BE

!!! KRİTİK PRENSİP !!!
Faz yüzdeleri PROFİL BAZLI uygulanır. VibeCoding'de analiz, tasarım,
mimari ve test işleri kısmen geliştirme süreci İÇİNDE (inline) yapılır.
Ancak bu fazlar İNSAN AKTİVİTELERİDİR ve doğaları gereği belirli bir
olgunlaşma süresi gerektirir. Bu nedenle faz yüzdeleri geleneksel
seviyelere yakın tutulur — DevTotal'ın kendisinin düşmüş olması
zaten yeterli tasarrufu sağlar.


4.1 GELENEKSEL FAZ FORMÜLLERİ (Profil A)
------------------------------------------
FAZ                    | FORMÜL                              | AÇIKLAMA
-----------------------|-------------------------------------|------------------------------
Analiz                 | Complexity'ye bağlı (aşağıya bak)   | Gereksinim analizi
UI_UX_Tasarim          | %20 x Adjusted_FE                   | Arayüz tasarımı
                       | (Adjusted_FE = 0 ise 0)             |
Yazilim_Mimarisi       | %10 x DevTotal                      | Teknik tasarım, veri modeli
Frontend_Gelistirme    | Adjusted_FE                         | UI implementasyonu
Backend_Gelistirme     | Adjusted_BE                         | API, servis, veritabanı
Test                   | Kompleksiteye bağlı (aşağıya bak)   | Unit, integration, QA

ANALİZ EFORU TABLOSU (Profil A, complexity bazlı):
  low/medium:    %18 x DevTotal
  high:          %24 x DevTotal
  very_high:     %30 x DevTotal

TEST EFORU KOMPLEKSİTE TABLOSU (Profil A):
  low: %24 x DevTotal
  medium: %30 x DevTotal
  high: %36 x DevTotal
  very_high: %42 x DevTotal


4.2 COPILOT+CLAUDE FAZ FORMÜLLERİ (Profil B)
-----------------------------------------------------------
FAZ                    | FORMÜL                              | AÇIKLAMA
-----------------------|-------------------------------------|------------------------------
Analiz                 | Complexity'ye bağlı (aşağıya bak)   | AI hızlandırır ama hala gerekli
UI_UX_Tasarim          | %15 x Adjusted_FE                   | Tasarım kararları insan yargısı
                       | (Adjusted_FE = 0 ise 0)             |
Yazilim_Mimarisi       | %8 x DevTotal                       | Mimari review hâlâ kritik
Frontend_Gelistirme    | Adjusted_FE                         | AI ile pair programming
Backend_Gelistirme     | Adjusted_BE                         | AI ile pair programming
Test                   | Kompleksiteye bağlı (aşağıya bak)   | AI test yazımını hızlandırır

ANALİZ EFORU TABLOSU (Profil B, complexity bazlı):
  low/medium:    %12 x DevTotal
  high:          %16 x DevTotal
  very_high:     %20 x DevTotal

TEST EFORU KOMPLEKSİTE TABLOSU (Profil B):
  low: %16 x DevTotal
  medium: %20 x DevTotal
  high: %24 x DevTotal
  very_high: %30 x DevTotal


4.3 VIBE CODING FAZ FORMÜLLERİ (Profil C)
--------------------------------------------------------
TEMEL PRENSİP: AI geliştirmeyi hızlandırır ama analiz/test/UI/mimari gibi
fazlar doğaları gereği belirli bir OLGUNLAŞMA SÜRESİ gerektirir:
  - Analiz: Paydaş görüşmeleri, gereksinim netleştirme, kabul kriteri yazma
  - UI/UX: Tasarım kararları, kullanıcı deneyimi testi, revizyon döngüsü
  - Mimari: Teknoloji seçimi, güvenlik review, ölçeklenebilirlik değerlendirmesi
  - Test: Entegrasyon testi, regresyon, edge case keşfi, güvenlik taraması

VibeCoding'de analiz ve test İKİ BİLEŞENLİDİR:
  1. WP Seviyesi: Yüzde × DevTotal (her WP için ayrı hesaplanır)
  2. Proje Seviyesi: Sabit taban (BA_Base / Test_Base) proje toplamına eklenir
Bu yapı, küçük projelerde yüzdenin tek başına absürt küçük kalmasını önler.

FAZ                    | FORMÜL (WP Seviyesi)                | AÇIKLAMA
-----------------------|-------------------------------------|------------------------------
Analiz                 | %20 x DevTotal (sabit)              | Proje seviyesinde BA_Base eklenir
UI_UX_Tasarim          | %15 x Adjusted_FE                   | Tasarım kararları insan yargısı
                       | (Adjusted_FE = 0 ise 0)             |
Yazilim_Mimarisi       | %8 x DevTotal                       | Mimari review hâlâ gerekli
Frontend_Gelistirme    | Adjusted_FE                         | AI üretir, developer review
Backend_Gelistirme     | Adjusted_BE                         | AI üretir, developer review
Test                   | %20 x DevTotal (sabit)              | Proje seviyesinde Test_Base eklenir

NOT: VibeCoding'de complexity ayrımı faz hesabında UYGULANMAZ.
Sabit yüzdeler kullanılır. Analiz ve test tabanları (BA_Base, Test_Base)
Bölüm 5.3'te tanımlıdır ve proje seviyesinde toplama eklenir.


================================================================================
BÖLÜM 5: GLOBAL EFOR FORMÜLLERİ
================================================================================

Tüm WP'ler hesaplandıktan SONRA proje seviyesinde eklenir:

Technical_Total = Σ(Tüm WP Toplamları)
Total_Test = Σ(Tüm WP Test Eforları)
Modul_Sayisi = modules dizisinin uzunluğu


5.0 PROJE BÜYÜKLÜK BANTLARI VE SABİT TABANLAR
------------------------------------------------
B ve C profillerinde bazı kalemler (PM, Analiz, Test, UAT) "sabit taban + yüzde"
formülüyle hesaplanır. Bunun nedeni: AI destekli geliştirmede DevTotal çok
küçüldüğünde yüzde tek başına anlamsız kalır. Sabit taban, bu fazların
doğasında olan minimum olgunlaşma süresini garanti eder.

PROJE BÜYÜKLÜK BANTI (Technical_Total'a göre):
  S:  Technical_Total ≤ 20 AG
  M:  Technical_Total 21–60 AG
  L:  Technical_Total 61–120 AG
  XL: Technical_Total > 120 AG

SABİT TABAN DEĞERLERİ (AG):
KALEM      | S   | M   | L   | XL  | AÇIKLAMA
-----------|-----|-----|-----|-----|------------------------------------------
PM_Base    | 2   | 3   | 6   | 8   | Minimum PM koordinasyon süresi
BA_Base    | 2   | 3   | 6   | 8   | Minimum iş analizi olgunlaşma süresi
Test_Base  | 2   | 4   | 6   | 8   | Minimum test planlama ve regresyon süresi
UAT_Base   | 3   | 5   | 8   | 10  | Minimum kullanıcı kabul testi süresi

NOT: Bu tabanlar SADECE Profil B ve C'de kullanılır. Profil A'da yüzde
formülleri yeterli büyüklükte sonuç üretir.

UAT_Base Gerekçesi: UAT tamamen insan aktivitesidir. Kullanıcılar senaryoları
çalıştırır, hata bildirir, düzeltme bekler, tekrar test eder. Bu döngü proje
büyüklüğünden bağımsız minimum bir süre gerektirir. Küçük bir projede bile
(S bandı) UAT en az 3 AG (24 saat) sürer.

BA_Base ve Test_Base proje seviyesinde, WP faz toplamlarının ÜZERİNE eklenir:
  Toplam_Analiz = Σ(WP Analiz Eforları) + BA_Base
  Toplam_Test = Σ(WP Test Eforları) + Test_Base
  Toplam_UAT = UAT_Base + (%30 x Technical_Total)


5.1 GELENEKSEL GLOBAL EFORLAR (Profil A)
------------------------------------------
KALEM              | FORMÜL                                    | NOT
-------------------|-------------------------------------------|---------------------------
PM                 | %9 x Technical_Total                      | Proje yönetimi
Technical_Design   | %4 x Technical_Total                      | Teknik tasarım dokümanı
DevOps             | 5 + (1 x Modul_Sayisi)                    | CI/CD, ortam kurulumu
                   | Eğer architect_notes'da "müşteri tarafından",
                   | "mevcut altyapı", "OneFrame", "hazır edilecek"
                   | varsa MAX 8 ile sınırla
Deployment         | %3 x Technical_Total                      | Canlıya geçiş
UAT                | %30 x Technical_Total                     | Kullanıcı kabul testi


5.2 COPILOT+CLAUDE GLOBAL EFORLAR (Profil B)
-----------------------------------------------------------
KALEM              | FORMÜL                                    | NOT
-------------------|-------------------------------------------|---------------------------
PM                 | PM_Base + (%9 x Technical_Total)          | Sabit taban + oransal
Technical_Design   | %2 x Technical_Total                      | AI dokümantasyon hızlandırır
DevOps             | 3 + (0.5 x Modul_Sayisi)                  | Framework CI/CD hazır
                   | MAX 5 ile sınırla (OneFrame altyapısı)
Deployment         | %3 x Technical_Total                      | Deploy validasyonu gerekli
UAT                | UAT_Base + (%30 x Technical_Total)        | Sabit taban + oransal
BA_Base            | Bölüm 5.0 tablosundan                     | Analiz faz toplamına eklenir
Test_Base          | Bölüm 5.0 tablosundan                     | Test faz toplamına eklenir


5.3 VIBE CODING GLOBAL EFORLAR (Profil C)
--------------------------------------------------------
KALEM              | FORMÜL                                    | NOT
-------------------|-------------------------------------------|---------------------------
PM                 | PM_Base + (%9 x Technical_Total)          | Sabit taban + oransal
Technical_Design   | %2 x Technical_Total                      | Minimum dokümantasyon gerekli
DevOps             | 3 (sabit)                                 | OneFrame pipeline + AI script
Deployment         | %3 x Technical_Total                      | Deploy validasyonu gerekli
UAT                | UAT_Base + (%30 x Technical_Total)        | Sabit taban + oransal
BA_Base            | Bölüm 5.0 tablosundan                     | Analiz faz toplamına eklenir
Test_Base          | Bölüm 5.0 tablosundan                     | Test faz toplamına eklenir

Sabit Taban Gerekçesi (B ve C profilleri):
- PM_Base: Proje büyüklüğünden bağımsız minimum koordinasyon maliyeti.
  Küçük VibeCoding projesinde bile proje planı, sprint yönetimi, raporlama gerekir.
- BA_Base: İş analizi olgunlaşma süresini garanti eder.
  AI geliştirmeyi hızlandırsa da paydaş görüşmeleri, kabul kriteri yazma,
  gereksinim netleştirme sabit süre gerektirir.
- Test_Base: Test planlama, regresyon stratejisi, entegrasyon test ortamı
  kurulumu. Projenin küçüklüğü bu hazırlık süresini ortadan kaldırmaz.
- UAT_Base: Kullanıcı kabul testi tamamen insan aktivitesidir. Kullanıcılar
  senaryoları çalıştırır, hata bildirir, düzeltme bekler, tekrar test eder.
  Bu döngü minimum 3 AG (S bandı) sürer ve AI hızıyla ilgisi yoktur.


================================================================================
BÖLÜM 6: MİN-MAX ARALIĞI
================================================================================

WP complexity seviyesine göre doğrudan min-max aralığı belirlenir:

  low:
    Min = WP_Toplam x 0.90 | Max = WP_Toplam x 1.10
    Dar aralık, düşük belirsizlik

  medium:
    Min = WP_Toplam x 0.85 | Max = WP_Toplam x 1.15
    Makul aralık

  high:
    Min = WP_Toplam x 0.80 | Max = WP_Toplam x 1.25
    Geniş aralık, dikkatli takip

  very_high:
    Min = WP_Toplam x 0.70 | Max = WP_Toplam x 1.40
    Yüksek belirsizlik, risk planı önerilir

Proje genelinde:
  Proje Min = Σ(WP Min'ler) + Global Eforlar
  Proje Max = Σ(WP Max'lar) + Global Eforlar


================================================================================
BÖLÜM 7: HESAPLAMA NOTU YAZIM STANDARDI
================================================================================

Her WP'nin her fazı için hesaplama notu (hesaplama alanı) şu standardı takip eder.
Bu notları bir senior developer okuyacaktır. Tam izlenebilirlik sağlanmalıdır.

ADIM NUMARALAMA TANIMI:
  ADIM 0: Profil seçimi (A, B veya C)
  ADIM 1: Deliverable kategorizasyon (Bölüm 1 karar ağacı + indirgeme matrisi)
  ADIM 1.5: OneFrame eşleştirme (Bölüm 10 - ZORUNLU, atlanaMAZ)
  ADIM 2: Batch hesabı (profil bazlı çarpanlar)

  ADIM 3: Entegrasyon çarpanı
  ADIM 4: Kompleksite çarpanı
  ADIM 5: Faz hesabı (profil bazlı yüzdeler)
  ADIM 6: Reuse uygulaması (profil bazlı çarpanlar)

Format:
"Profil → Deliverables → OF → Batch → Ent → Kompl → Faz → Reuse"

Örnek - VibeCoding Frontend_Gelistirme fazı için:
"Profil C (VibeCoding) → Deliverables: 4xSIMPLE_UI(0.20) + 1xAUTH_COMP(0.12) → OneFrame: eşleşme yok → Batch: SIMPLE_UI 1x1.0 + 1x0.8 + 1x0.6 + 1x0.5 → Baz FE:0.70 → Entegrasyon: x1.08=0.864 → Kompleksite: x1.15(high)=0.994 → Adj_FE=1.0 → Reuse: 1.0x"

Örnek - VibeCoding Test fazı için:
"DevTotal:2.6 → Test: 2.6 x %20 = 0.52 → 0.5 (proje seviyesinde Test_Base eklenir)"

Örnek - VibeCoding Analiz fazı için:
"DevTotal:2.6 → Analiz: 2.6 x %20 = 0.52 → 0.5 (proje seviyesinde BA_Base eklenir)"

NOT: BA_Base, Test_Base ve UAT_Base WP hesaplama notunda gösterilmez. Proje toplam
çıktısında global eforlar altında gösterilir (Bölüm 5.0).

Kısa WP'ler için minimum:
"2xSIMPLE_UI(0.20) → OF: eşleşme yok → Baz:0.80 → Ent:1.0x → Kompl:0.85x(low) → DevTotal:0.68 → Test: 0.68 x %20 = 0.14 → Reuse: 1.0x"


================================================================================
BÖLÜM 8: ARCHITECT NOTES -> RİSK EŞLEMESİ
================================================================================

architect_notes içindeki keywordlere göre risk tanımla:

KEYWORD GRUBU                          | RİSK                    | ETKİ
---------------------------------------|-------------------------|-------
"kritik", "cascade", "geri alınamaz"   | Veri kaybı riski        | HIGH
"KVKK", "gizlilik", "güvenlik"        | Uyumluluk gereksinimleri | HIGH
"field-level", "maskeleme"             | Yetki karmaşıklığı      | HIGH
"performans", "test edilmeli"          | Performans darboğazı    | MEDIUM
"mevcut sistem", "legacy", "OneFrame"  | Legacy bağımlılık       | MEDIUM
"belirsiz", "netleştirilmeli"         | Kapsam belirsizliği     | MEDIUM
"müşteri tarafından", "temin"          | Dış bağımlılık          | MEDIUM
"third-party", "library"              | 3.parti kütüphane riski | LOW


================================================================================
BÖLÜM 9: ÖRNEK HESAPLAMA (TAM İZLENEBİLİR)
================================================================================

9.1 GELENEKSEL ÖRNEK (Profil A)
---------------------------------
WP-006: İstihdam Bilgileri Portleti
  Complexity: high
  Integration_points: 1 (Mevcut OneFrame yetki yönetimi)
  Deliverables: 5 adet

ADIM 0 - PROFİL SEÇİMİ:
  Başlangıç: 100
  high complexity: -10
  1 entegrasyon noktası: -5
  Final: 85 → HIGH (Analiz %15 uygulanacak, Test %30)

ADIM 1 - DELİVERABLE KATEGORİZASYON:
  1. Tarih Bilgileri Ekranı → SIMPLE_UI (FE:0.8, BE:0.8)
  2. Organizasyon Bilgileri Ekranı → SIMPLE_UI (FE:0.8, BE:0.8)
  3. İş Bilgileri Ekranı → SIMPLE_UI (FE:0.8, BE:0.8)
  4. İş Ortakları Ekranı → SIMPLE_UI (FE:0.8, BE:0.8)
  5. Kademe Maskeleme Komponenti → AUTH_COMPONENT (FE:0.5, BE:1.5)

ADIM 1.5 - ONEFRAME EŞLEŞTİRME:
  Taranan alanlar: deliverable adları, description, backend_req, frontend_req, integration_points
  integration_points: "Mevcut OneFrame yetki yönetimi" → OF-AUTHZ keyword eşleşmesi
  D5 "Kademe Maskeleme" → field-level maskeleme, OF-AUTHZ kapsamına girmez (field-level özel geliştirme)
  Sonuç: Bu WP'de OF eşleşmesi YOK (maskeleme = özel AUTH_COMPONENT, OF-AUTHZ residüel uygulanmaz)

ADIM 2 - BATCH HESABI:
  SIMPLE_UI (4 adet): 2x1.0 + 2x0.6 → FE=2.56, BE=2.56
  AUTH_COMPONENT (1 adet): 1x1.0 → FE=0.50, BE=1.50
  Baz toplam: FE=3.06, BE=4.06

ADIM 3 - ENTEGRASYON: x1.15 → FE:3.519, BE:4.669
ADIM 4 - KOMPLEKSİTE: x1.25 → Adj_FE:4.5, Adj_BE:6.0, DevTotal:10.5
ADIM 5 - FAZ: Analiz(15%x10.5=1.5) + UI(20%x4.5=1.0) + Mimari(10%x10.5=1.0) + FE:4.5 + BE:6.0 + Test(30%x10.5=3.0) = 17.5 AG
ADIM 6 - REUSE: Bu WP orijinal (ilk portlet) → 1.0x → 17.5 AG


9.2 VIBE CODING ÖRNEK (Profil C)
-----------------------------------------------
Aynı WP-006, VibeCoding ile:

ADIM 0 - High complexity → Analiz %24(A) %16(B) %20(C), Min-Max ×0.80-×1.25

ADIM 1 - DELİVERABLE KATEGORİZASYON (Profil C baz değerleri v11):
  1. Tarih Bilgileri Ekranı → SIMPLE_UI (FE:0.20, BE:0.20)
  2. Organizasyon Bilgileri Ekranı → SIMPLE_UI (FE:0.20, BE:0.20)
  3. İş Bilgileri Ekranı → SIMPLE_UI (FE:0.20, BE:0.20)
  4. İş Ortakları Ekranı → SIMPLE_UI (FE:0.20, BE:0.20)
  5. Kademe Maskeleme Komponenti → AUTH_COMPONENT (FE:0.12, BE:0.38)

ADIM 1.5 - ONEFRAME EŞLEŞTİRME:
  Profil A örneğiyle aynı tarama. Sonuç: OF eşleşmesi YOK.
  Tüm deliverable'lar profil baz değerleriyle devam eder.

ADIM 2 - BATCH HESABI (VibeCoding batch çarpanları: 1.0/0.8/0.6/0.5):
  SIMPLE_UI (4 adet): 1x1.0=0.40 + 1x0.8=0.32 + 1x0.6=0.24 + 1x0.5=0.20 = 1.16
    FE = 0.58, BE = 0.58
  AUTH_COMPONENT (1 adet): 1x1.0 → FE=0.12, BE=0.38
  Baz toplam: FE=0.70, BE=0.96

ADIM 3 - ENTEGRASYON (VibeCoding): x1.08 → FE:0.756, BE:1.037
ADIM 4 - KOMPLEKSİTE (VibeCoding): x1.15 (high) → Adj_FE:0.869→0.9, Adj_BE:1.193→1.2
  DevTotal: 0.9 + 1.2 = 2.1

ADIM 5 - FAZ HESABI (VibeCoding):
  Analiz: 2.1 x 0.20 = 0.42 → 0.4 (proje seviyesinde BA_Base eklenir)
  UI_UX: 0.9 x 0.15 = 0.135 → 0.1
  Mimari: 2.1 x 0.08 = 0.168 → 0.2
  FE: 0.9
  BE: 1.2
  Test: 2.1 x 0.20 = 0.42 → 0.4 (proje seviyesinde Test_Base eklenir)

WP TOPLAM (VibeCoding): 0.4 + 0.1 + 0.2 + 0.9 + 1.2 + 0.4 = 3.2 AG
ADIM 6 - REUSE: Bu WP orijinal (ilk portlet) → 1.0x → 3.2 AG

KARŞILAŞTIRMA (WP seviyesi, Base tabanları hariç):
  Geleneksel: 17.5 AG
  VibeCoding:  3.2 AG
  Tasarruf: %82 (14.3 AG)


9.3 COPILOT+CLAUDE ÖRNEK (Profil B)
----------------------------------------------------
Aynı WP-006, Copilot+Claude ile:

ADIM 0 - High complexity → Analiz %24(A) %16(B), Min-Max ×0.80-×1.25

ADIM 1 - DELİVERABLE KATEGORİZASYON (Profil B baz değerleri):
  1. Tarih Bilgileri Ekranı → SIMPLE_UI (FE:0.32, BE:0.32)
  2. Organizasyon Bilgileri Ekranı → SIMPLE_UI (FE:0.32, BE:0.32)
  3. İş Bilgileri Ekranı → SIMPLE_UI (FE:0.32, BE:0.32)
  4. İş Ortakları Ekranı → SIMPLE_UI (FE:0.32, BE:0.32)
  5. Kademe Maskeleme Komponenti → AUTH_COMPONENT (FE:0.20, BE:0.60)

ADIM 1.5 - ONEFRAME EŞLEŞTİRME:
  Profil A örneğiyle aynı tarama. Sonuç: OF eşleşmesi YOK.

ADIM 2 - BATCH HESABI (Profil B batch çarpanları: 1.0/0.8/0.5/0.35):
  SIMPLE_UI (4 adet): D1x1.0=0.64 + D2x0.8=0.512 + D3x0.5=0.32 + D4x0.35=0.224 = 1.696
    FE = 0.848, BE = 0.848
  AUTH_COMPONENT (1 adet): 1x1.0 → FE=0.20, BE=0.60
  Baz toplam: FE=1.048, BE=1.448

ADIM 3 - ENTEGRASYON: x1.15 → FE:1.205, BE:1.665
ADIM 4 - KOMPLEKSİTE: x1.25 → Adj_FE:1.507→1.5, Adj_BE:2.082→2.1
  DevTotal: 1.5 + 2.1 = 3.6

ADIM 5 - FAZ HESABI (Profil B):
  Analiz: 12% x 3.6 = 0.432 → 0.4 (proje seviyesinde BA_Base eklenir)
  UI_UX: 15% x 1.5 = 0.225 → 0.2
  Mimari: 8% x 3.6 = 0.288 → 0.3
  FE: 1.5
  BE: 2.1
  Test: 24% x 3.6 = 0.864 → 0.9 (proje seviyesinde Test_Base eklenir)

WP TOPLAM (Copilot+Claude): 0.4 + 0.2 + 0.3 + 1.5 + 2.1 + 0.9 = 5.4 AG
ADIM 6 - REUSE: Bu WP orijinal → 1.0x → 5.4 AG

KARŞILAŞTIRMA (WP seviyesi, Base tabanları hariç):
  Geleneksel:     17.5 AG
  Copilot+Claude:  5.4 AG (%69 tasarruf)
  VibeCoding:      3.2 AG (%82 tasarruf)


9.4 PROJE SEVİYESİ GLOBAL EFOR ÖRNEĞİ
----------------------------------------------------
Varsayım: Proje 3 modül, 10 WP, toplam eforlar:
  Technical_Total_A = 120 AG → Bant: L
  Technical_Total_B = 48 AG  → Bant: M
  Technical_Total_C = 18 AG  → Bant: S
  Total_Test_A = 30 AG, Total_Test_B = 12 AG, Total_Test_C = 5 AG

Profil A (Geleneksel):
  PM:         %9 x 120 = 10.8 AG
  TechDesign: %4 x 120 = 4.8 AG
  DevOps:     5 + (1x3) = 8 AG (MAX 8 sınırına ulaştı)
  Deployment: %3 x 120 = 3.6 AG
  UAT:        %30 x 120 = 36.0 AG

Profil B (Copilot+Claude, Bant M):
  PM:         PM_Base(3) + %9 x 48 = 3 + 4.32 = 7.3 AG
  TechDesign: %2 x 48 = 1.0 AG
  DevOps:     3 + (0.5x3) = 4.5 AG
  Deployment: %3 x 48 = 1.4 AG
  UAT:        UAT_Base(5) + %30 x 48 = 5 + 14.4 = 19.4 AG
  BA_Base:    3 AG (Analiz faz toplamına eklenir)
  Test_Base:  4 AG (Test faz toplamına eklenir)

Profil C (VibeCoding, Bant S):
  PM:         PM_Base(2) + %9 x 18 = 2 + 1.62 = 3.6 AG
  TechDesign: %2 x 18 = 0.4 AG
  DevOps:     3 AG (sabit)
  Deployment: %3 x 18 = 0.5 AG
  UAT:        UAT_Base(3) + %30 x 18 = 3 + 5.4 = 8.4 AG
  BA_Base:    2 AG (Analiz faz toplamına eklenir)
  Test_Base:  2 AG (Test faz toplamına eklenir)


================================================================================
BÖLÜM 10: ONEFRAME FRAMEWORK EŞLEŞTİRME VE EFOR İNDİRİMİ
================================================================================

10.1 GENEL PRENSİP
-------------------
OneFrame, hazır modülleri ve altyapı yetenekleri ile birçok teknik gereksinimi kutudan çıktığı
haliyle karşılar. Ancak "hazır" demek "sıfır efor" demek DEĞİLDİR.
Her müşterinin kurumsal ayarları, özelleştirmeleri ve entegrasyon parametreleri farklıdır.
Bu nedenle OneFrame'in karşıladığı deliverable'larda geliştirme eforu yerine
KONFIGÜRASYON + ENTEGRASYON + TEST eforu hesaplanır.

!!! KRİTİK KAVRAM AYRIMI - KAPSAM DIŞI vs ONEFRAME İNDİRİMİ !!!
Bu iki mekanizma birbirinden TAMAMEN BAĞIMSIZDIR:

  A) KAPSAM DIŞI (out_of_scope_items):
     → WBS'te WP olarak yer ALMAZ, hiç eforlanmaz.

  B) ONEFRAME EFOR İNDİRİMİ (Bu bölüm):
     → Kapsam İÇİNDEKİ WP'lerin deliverable'larına uygulanır.

  Kapsam dışı kalemler mevcut diye "OneFrame zaten halletti, indirim gerekmez" DEDİRME.
  Kapsam içindeki HER WP'de OneFrame eşleşmesi ayrıca kontrol edilmelidir.


10.2 ONEFRAME YETENEK HARİTASI
-----------------------------------------------------
Kaynak: https://oneframe.kocsistem.com.tr/features ve /overview
Aşağıdaki yetenekler OneFrame tarafından hazır sunulur:

─── KİMLİK DOĞRULAMA VE YETKİLENDİRME ─────────────────────────────────────

YETENEK_ID  | YETENEK ADI                         | EŞLEŞME KEYWORDLERİ
------------|-------------------------------------|----------------------------------------------
OF-AUTH     | Authentication, SSO & MFA           | "SSO", "Login", "Giriş", "Oturum",
            | (Identity & Access Management)      | "Authentication", "JWT", "Bearer", "SAML",
            | JWT, IdentityServer4, KeyCloak,     | "KeyCloak", "IdentityServer", "OpenID",
            | SAML 2.0, LDAP/AD, ReCaptcha,       | "OAuth", "Şifre", "Password", "Token",
            | 2FA (SMS, QR Code), Sosyal Login     | "OTP", "MFA", "2FA", "İki faktör",
            | (Google, Facebook, Twitter),         | "Çok faktörlü", "ReCaptcha", "LDAP",
            | Sign up, Forgot password,            | "Active Directory", "Kayıt ol", "Sign up",
            | Auto logout                          | "Şifremi unuttum", "Forgot password",
            |                                     | "Oturum yönetimi", "Session", "Auto logout"
OF-AUTHZ    | Authorization & RBAC                | "Yetkilendirme", "RBAC", "Rol bazlı",
            | Tenant/User/Role/Permission bazlı,  | "Permission", "Erişim kontrol", "Yetki",
            | User & Role claim management         | "Tenant", "Yetki yönetimi", "Rol atama",
            |                                     | "Claim", "Kullanıcı yetki", "Role operation"

─── VERİ KATMANI VE ALTYAPI ────────────────────────────────────────────────

OF-CRUD     | Generic CRUD Altyapısı              | "CRUD", "Ekleme", "Güncelleme", "Silme",
            | Repository pattern, UoW pattern,    | "Listeleme", "Görüntüleme", "Detay",
            | Base entity                          | "Generic repository", "Base entity",
            |                                     | "UoW pattern", "Kayıt", "Düzenleme"
OF-DATA     | Data Access Layer                   | "Repository pattern", "EF Core",
            | EF Core Code-First, scaffolding,    | "Code-First", "Migration", "UoW",
            | migrations, multi-DB desteği         | "Veritabanı", "Database", "SQL Server",
            | (SQL Server, PostgreSQL, Oracle,     | "PostgreSQL", "Oracle", "MySQL",
            | MySQL)                               | "Scaffolding", "Entity Framework"
OF-CACHE    | Caching Altyapısı       | "Cache", "Önbellek", "Redis",
            | In-Memory, Redis Distributed,        | "In-Memory", "Distributed cache",
            | SQL Server Cache                     | "Performans", "Hız"
OF-SEARCH   | Arama & Elasticsearch   | "Elasticsearch", "Arama", "Search",
            | Elasticsearch entegrasyon desteği     | "Full-text search", "Arama motoru"

─── AUDIT, LOG VE İZLEME ──────────────────────────────────────────────────

OF-AUDIT    | Audit Logging                       | "Audit", "Log kaydı", "İşlem geçmişi",
            | Otomatik DB audit, API Request/      | "Loglama", "Audit trail", "Değişiklik logu",
            | Response audit, çoklu provider       | "Request log", "Response log", "NLog",
            | (Redis, Elasticsearch, NLog, SQL,    | "İzleme", "Takip", "Log tablosu"
            | PostgreSQL, MongoDB)                 |

─── UI BİLEŞENLERİ VE ŞABLONLAR ───────────────────────────────────────────

OF-UI       | Metronic UI Component Kit| "Metronic", "UI component", "Bileşen",
            | React & Vue tam UI bileşen seti,     | "Bootstrap", "Material Design",
            | Bootstrap + Material Design,         | "Responsive", "Layout", "Tema", "Theme",
            | Responsive, Light/Dark mode,         | "Dark mode", "Light mode", "LTR", "RTL"
            | LTR/RTL desteği                      |
OF-FORM     | Form Builder Altyapısı              | "Form", "Kayıt formu", "Başvuru formu",
            | React/Vue form bileşenleri,          | "Input", "Multi-step form", "Wizard form",
            | validasyonlu input'lar               | "Checkbox", "Dropdown", "Select"
OF-TABLE    | Data Grid / Tablo Altyapısı         | "Tablo", "Liste", "Grid", "Data table",
            | Zengin data grid: sıralama,          | "Listeleme ekranı", "Sayfalama",
            | sayfalama, batch operasyonlar,       | "Sorting", "Pagination", "Batch",
            | özel fonksiyon desteği               | "Data grid", "Sıralama", "Filtreleme"
OF-MENU     | Dinamik Menü Ağacı      | "Menü", "Sidebar", "Navigasyon",
            | Dynamic sidebar menu tree             | "Menu tree", "Dinamik menü"
OF-DASH     | Dashboard & Chart       | "Dashboard", "Grafik", "Chart",
            | Hazır dashboard bileşenleri,          | "İstatistik", "Özet", "Summary",
            | çeşitli chart tipleri                 | "Kart", "Card", "Stats"
OF-PROFILE  | Profil Yönetimi         | "Profil", "Profile", "Kullanıcı bilgi",
            | Kullanıcı bilgi, şifre, fotoğraf     | "Profil fotoğrafı", "Hesap ayarları",
            | işlemleri hazır                       | "Kullanıcı güncelleme"
OF-REPORT   | Rapor Sayfaları         | "Rapor", "Report", "Raporlama",
            | Hazır rapor sayfa şablonları          | "Rapor sayfası", "Report page"

─── SERVİSLER VE ARKA PLAN ────────────────────────────────────────────────

OF-NOTIF    | Notification Servisi                | "Bildirim", "Notification", "E-posta",
            | Çoklu kanal: SMS, E-mail,            | "E-posta gönderim", "SMS", "Mail",
            | Push Notification, Slack              | "Template", "Şablon gönderim",
            |                                     | "Push notification", "Slack", "Bildirim kanal"
OF-HANGFIRE | Hangfire Background Jobs | "Hangfire", "Background job", "Arka plan job",
            | Hazır Hangfire template,              | "Scheduled task", "Windows service",
            | Windows Service desteği               | "Zamanlı görev", "Periyodik iş"
OF-RULE     | Rule Engine Servisi     | "Rule engine", "Kural motoru", "İş kuralı",
            | Hazır kural motoru servisi             | "Business rule", "Kural yönetimi",
            |                                     | "Dinamik kural"
OF-WORKFLOW | Workflow Engine          | "Workflow", "İş akışı", "Akış motoru",
            | Hazır iş akışı motoru                 | "Süreç yönetimi", "Process engine",
            |                                     | "Onay akışı", "Approval flow"

─── DOKÜMAN VE İÇERİK YÖNETİMİ ───────────────────────────────────────────

OF-DMS      | Document Management     | "Doküman yönetim", "DMS", "Document",
            | Hazır doküman yönetim sistemi          | "Belge yönetim", "Dosya yönetim",
            |                                     | "Klasör", "Folder", "Arşiv"
OF-FILE     | File Upload/Download Altyapısı      | "Dosya yükleme", "Upload", "Download",
            |                                     | "Attachment", "Storage service",
            |                                     | "Dosya indirme", "Ek dosya"
OF-UPLOAD   | Upload Widget                       | "Upload widget", "Yükleme widget",
            |                                     | "Dosya seçici", "Drag drop upload",
            |                                     | "Çoklu dosya"
OF-CMS      | CMS / İçerik Yönetimi               | "CMS", "İçerik yönetim", "Content",
            |                                     | "WYSIWYG", "Editör", "İçerik düzenleme"
OF-FAQ      | FAQ Sistemi             | "FAQ", "SSS", "Sıkça sorulan",
            | Hazır SSS yönetim sistemi              | "Soru-cevap", "Yardım", "Help"

─── DEVOPS VE ALTYAPI ─────────────────────────────────────────────────────

OF-CICD     | CI/CD & DevOps Pipeline             | "CI/CD", "Pipeline", "Deploy", "DevOps",
            | Otomatik CI/CD, Unit/Integration/    | "Automated deploy", "Test pipeline"
            | Load test pipeline'ları               |
OF-CLOUD    | Cloud & Container       | "Docker", "Kubernetes", "Container",
            | Docker, Kubernetes, Azure desteği     | "K8s", "Cloud", "Azure"
OF-MULTI    | Multi-Tenancy                       | "Tenant", "Multi-tenant", "Çoklu kiracı",
            |                                     | "Tenant bazlı", "Kiracı"
OF-VALID    | Validation Altyapısı                | "FluentValidation", "Validation",
            | FluentValidation, pipeline kayıt     | "Doğrulama", "Validasyon"
OF-I18N     | Multi-Language & Localization        | "Çok dil", "Multi-language", "Localization",
            |                           | "Dil desteği", "i18n", "Yerelleştirme",
            | Çoklu dil, LTR/RTL desteği           | "Türkçe", "İngilizce"
OF-ERR      | Error Handling & Middleware          | "Exception", "Hata yönetimi", "Error handling",
            |                           | "Middleware", "API middleware",
            | Exception handling, logging,          | "Hata yakalama"
            | API communication middleware          |

─── EK SERVİSLER ──────────────────────────────────────────────────────────

OF-CHATBOT  | Chatbot Servisi         | "Chatbot", "Bot", "Sohbet botu",
            | Hazır chatbot altyapısı               | "Canlı destek", "Chat"
OF-APIGW    | API Gateway             | "API Gateway", "Gateway", "API yönetim",
            | Hazır API gateway servisi              | "API management", "Rate limit"
OF-SIGNAL   | SignalR / Real-time     | "SignalR", "Real-time", "Gerçek zamanlı",
            | Gerçek zamanlı iletişim desteği        | "WebSocket", "Canlı güncelleme", "Live"


10.3 EŞLEŞME KURALLARI
------------------------
OneFrame eşleşme taraması aşağıdaki 5 WBS alanında yapılır (TAMAMI taranmalı):
  ✓ deliverable adı (deliverables[])
  ✓ WP description
  ✓ backend_requirements
  ✓ frontend_requirements
  ✓ integration_points[]    ← ÖNEMLİ: Bu alan sıklıkla OneFrame referansı içerir!

Tarama prosedürü:
  1. Her WP için yukarıdaki 5 alanı Bölüm 10.2'deki keyword tablosu ile karşılaştır.
  2. Keyword eşleşmesi case-insensitive yapılır.
  3. Eşleşen her deliverable için hangi OF yeteneğinin eşleştiğini tespit et.
  4. Eşleşen deliverable'ın baz eforu yerine residüel efor kullan (Bölüm 10.4).
  5. Bir WP birden fazla OF yeteneğiyle eşleşebilir.
  6. architect_notes içinde "OneFrame", "mevcut altyapı", "hazır", "framework desteği"
     ifadesi varsa ek onay sinyali olarak değerlendir.

!!! GENİŞLETİLMİŞ EŞLEŞME KURALI !!!
  → Keyword eşleşmesi için TAM EŞLEŞME gerekmez, KISMI EŞLEŞME de yeterlidir.
  → Örnek: "Kullanıcı Listesi" → OF-TABLE (içinde "Liste" var)
  → Örnek: "Kayıt Formu" → OF-FORM (içinde "Form" + "Kayıt" var)
  → Örnek: "E-posta Gönderim Servisi" → OF-NOTIF (içinde "E-posta gönderim" var)

!!! YAPILMAMASI GEREKEN HATALAR (ANTİ-PATTERN) !!!
  ✗ "out_of_scope_items'da OneFrame var, o yüzden OneFrame indirimi gerekmez" → YANLIŞ
  ✗ "Deliverable adında OF keyword yok, eşleşme yok" → EKSİK TARAMA
  ✗ "oneframe_analizi boş bırakılabilir" → YANLIŞ


10.4 ONEFRAME RESIDÜEL EFOR TABLOSU
---------------------------------------------------------
OneFrame'in karşıladığı deliverable'larda baz efor yerine aşağıdaki residüel eforlar kullanılır.

!!! PROFİL BAZLI RESİDÜEL DEĞERLER !!!

GELENEKSEL RESİDÜEL (Profil A):
YETENEK_ID  | RESİDÜEL FE | RESİDÜEL BE | TOPLAM | NE İÇİN HARCANIR
------------|-------------|-------------|--------|------------------------------------------
OF-AUTH     | 0.0         | 1.0         | 1.0    | SSO/SAML/2FA konfigürasyonu, provider ayarı
OF-AUTHZ    | 0.0         | 1.0         | 1.0    | Rol-permission tanımları, claim matris
OF-CRUD     | 0.0         | 0.5         | 0.5    | Entity tanımı, migration, mapping
OF-DATA     | 0.0         | 0.5         | 0.5    | Context config, connection string
OF-AUDIT    | 0.0         | 0.5         | 0.5    | Audit scope, provider seçimi
OF-CACHE    | 0.0         | 0.3         | 0.3    | Cache provider seçimi, TTL ayarları
OF-SEARCH   | 0.0         | 0.5         | 0.5    | Elasticsearch index tanımı
OF-MULTI    | 0.0         | 0.5         | 0.5    | Tenant konfigürasyonu
OF-CICD     | 0.0         | 0.0         | 0.0    | Mevcut pipeline (DevOps global eforda)
OF-CLOUD    | 0.0         | 0.0         | 0.0    | Docker/K8s mevcut (DevOps global eforda)
OF-UI       | 0.1         | 0.0         | 0.1    | Tema/layout seçimi
OF-FORM     | 0.1         | 0.1         | 0.2    | Form alan tanımları, validasyon kuralı
OF-TABLE    | 0.1         | 0.1         | 0.2    | Kolon tanımları, sıralama/sayfalama
OF-MENU     | 0.1         | 0.1         | 0.2    | Menü item tanımları, yetki eşleme
OF-DASH     | 0.2         | 0.2         | 0.4    | Chart verisi bağlama, kart düzeni
OF-PROFILE  | 0.1         | 0.2         | 0.3    | Profil alanları özelleştirme
OF-REPORT   | 0.2         | 0.3         | 0.5    | Rapor query + şablon bağlama
OF-NOTIF    | 0.0         | 0.5         | 0.5    | Kanal config, template tanımlama
OF-HANGFIRE | 0.0         | 0.3         | 0.3    | Job tanımı, schedule ayarı
OF-RULE     | 0.0         | 0.5         | 0.5    | Kural tanımı, parametre config
OF-WORKFLOW | 0.0         | 0.5         | 0.5    | Workflow tanımı, adım config
OF-DMS      | 0.1         | 0.3         | 0.4    | Klasör yapısı, metadata config
OF-FILE     | 0.0         | 0.3         | 0.3    | Storage provider konfigürasyonu
OF-UPLOAD   | 0.1         | 0.1         | 0.2    | Boyut/tip sınırları, widget config
OF-CMS      | 0.1         | 0.3         | 0.4    | İçerik tipi tanımları, şablon kurulumu
OF-FAQ      | 0.1         | 0.2         | 0.3    | Kategori/soru tanımları
OF-VALID    | 0.0         | 0.3         | 0.3    | Validasyon kuralı, pipeline kayıt
OF-I18N     | 0.1         | 0.2         | 0.3    | Dil dosyaları, çeviri
OF-ERR      | 0.0         | 0.2         | 0.2    | Error handler config, log seviyesi
OF-CHATBOT  | 0.1         | 0.3         | 0.4    | Bot senaryo, cevap tanımları
OF-APIGW    | 0.0         | 0.3         | 0.3    | Route tanımı, rate limit
OF-SIGNAL   | 0.1         | 0.3         | 0.4    | Hub tanımı, event bağlama

COPILOT+CLAUDE RESİDÜEL (Profil B):
AI pair programming konfigürasyon süresini kısaltır. Profil A değerlerinin x0.65'i.
YETENEK_ID  | RESİDÜEL FE | RESİDÜEL BE | TOPLAM | NE İÇİN HARCANIR
------------|-------------|-------------|--------|------------------------------------------
OF-AUTH     | 0.0         | 0.65        | 0.65   | AI ile SSO/2FA config hızlanır
OF-AUTHZ    | 0.0         | 0.65        | 0.65   | AI ile rol-permission config hızlanır
OF-CRUD     | 0.0         | 0.30        | 0.30   | AI entity + migration hızlı üretir
OF-DATA     | 0.0         | 0.30        | 0.30   | AI context config hızlı üretir
OF-AUDIT    | 0.0         | 0.30        | 0.30   | AI audit config hızlı üretir
OF-CACHE    | 0.0         | 0.20        | 0.20   | AI cache config hızlı üretir
OF-SEARCH   | 0.0         | 0.30        | 0.30   | AI index tanımı hızlı üretir
OF-MULTI    | 0.0         | 0.30        | 0.30   | AI tenant config hızlı üretir
OF-CICD     | 0.0         | 0.0         | 0.0    | Mevcut pipeline
OF-CLOUD    | 0.0         | 0.0         | 0.0    | Dockerfile/K8s mevcut
OF-UI       | 0.05        | 0.0         | 0.05   | Tema seçimi minimal
OF-FORM     | 0.05        | 0.05        | 0.10   | AI form config hızlı üretir
OF-TABLE    | 0.05        | 0.05        | 0.10   | AI tablo config hızlı üretir
OF-MENU     | 0.05        | 0.05        | 0.10   | AI menü config hızlı üretir
OF-DASH     | 0.10        | 0.10        | 0.20   | AI chart binding hızlı üretir
OF-PROFILE  | 0.05        | 0.10        | 0.15   | AI profil config hızlı üretir
OF-REPORT   | 0.10        | 0.20        | 0.30   | AI rapor query hızlı üretir
OF-NOTIF    | 0.0         | 0.30        | 0.30   | AI template config hızlı üretir
OF-HANGFIRE | 0.0         | 0.20        | 0.20   | AI job tanımı hızlı üretir
OF-RULE     | 0.0         | 0.30        | 0.30   | AI kural config hızlı üretir
OF-WORKFLOW | 0.0         | 0.30        | 0.30   | AI workflow config hızlı üretir
OF-DMS      | 0.05        | 0.20        | 0.25   | AI DMS config hızlı üretir
OF-FILE     | 0.0         | 0.20        | 0.20   | AI storage config hızlı üretir
OF-UPLOAD   | 0.05        | 0.05        | 0.10   | AI upload config hızlı üretir
OF-CMS      | 0.05        | 0.20        | 0.25   | AI CMS config hızlı üretir
OF-FAQ      | 0.05        | 0.10        | 0.15   | AI FAQ config hızlı üretir
OF-VALID    | 0.0         | 0.20        | 0.20   | AI validation config hızlı üretir
OF-I18N     | 0.05        | 0.10        | 0.15   | AI dil dosyası hızlı üretir
OF-ERR      | 0.0         | 0.10        | 0.10   | AI error config hızlı üretir
OF-CHATBOT  | 0.05        | 0.20        | 0.25   | AI bot senaryo hızlı üretir
OF-APIGW    | 0.0         | 0.20        | 0.20   | AI route config hızlı üretir
OF-SIGNAL   | 0.05        | 0.20        | 0.25   | AI hub config hızlı üretir

VIBE CODING RESİDÜEL (Profil C):
NOT: Profil C'de birçok OF yeteneğinin FE residüeli 0.0'dır çünkü AI aracı
frontend konfigürasyonunu (form tanımları, tablo ayarları, tema seçimi)
tamamen otomatik üretir. Residüel efor yalnızca backend konfigürasyonuna aittir.

YETENEK_ID  | RESİDÜEL FE | RESİDÜEL BE | TOPLAM | NE İÇİN HARCANIR
------------|-------------|-------------|--------|------------------------------------------
OF-AUTH     | 0.0         | 0.25        | 0.25   | AI ile provider config + 2FA setup
OF-AUTHZ    | 0.0         | 0.25        | 0.25   | AI ile rol-permission prompt
OF-CRUD     | 0.0         | 0.10        | 0.10   | AI entity + migration üretir
OF-DATA     | 0.0         | 0.10        | 0.10   | AI context config üretir
OF-AUDIT    | 0.0         | 0.10        | 0.10   | AI audit config üretir
OF-CACHE    | 0.0         | 0.05        | 0.05   | AI cache config üretir
OF-SEARCH   | 0.0         | 0.10        | 0.10   | AI index tanımı üretir
OF-MULTI    | 0.0         | 0.10        | 0.10   | AI tenant config üretir
OF-CICD     | 0.0         | 0.00        | 0.00   | Mevcut pipeline
OF-CLOUD    | 0.0         | 0.00        | 0.00   | Dockerfile/K8s mevcut
OF-UI       | 0.05        | 0.0         | 0.05   | Tema seçimi
OF-FORM     | 0.0         | 0.05        | 0.05   | AI form tanımı üretir
OF-TABLE    | 0.0         | 0.05        | 0.05   | AI tablo config üretir
OF-MENU     | 0.0         | 0.05        | 0.05   | AI menü item üretir
OF-DASH     | 0.05        | 0.05        | 0.10   | AI chart binding üretir
OF-PROFILE  | 0.0         | 0.05        | 0.05   | AI profil alanları config
OF-REPORT   | 0.05        | 0.10        | 0.15   | AI rapor query + şablon
OF-NOTIF    | 0.0         | 0.10        | 0.10   | AI template + kanal config
OF-HANGFIRE | 0.0         | 0.10        | 0.10   | AI job tanımı üretir
OF-RULE     | 0.0         | 0.15        | 0.15   | AI kural tanımı üretir
OF-WORKFLOW | 0.0         | 0.15        | 0.15   | AI workflow adım tanımı
OF-DMS      | 0.0         | 0.10        | 0.10   | AI klasör + metadata config
OF-FILE     | 0.0         | 0.05        | 0.05   | AI storage config üretir
OF-UPLOAD   | 0.0         | 0.05        | 0.05   | AI upload config üretir
OF-CMS      | 0.0         | 0.10        | 0.10   | AI CMS config üretir
OF-FAQ      | 0.0         | 0.05        | 0.05   | AI FAQ yapısı üretir
OF-VALID    | 0.0         | 0.05        | 0.05   | AI validation rule üretir
OF-I18N     | 0.0         | 0.05        | 0.05   | AI dil dosyası üretir
OF-ERR      | 0.0         | 0.05        | 0.05   | AI error handler config
OF-CHATBOT  | 0.0         | 0.10        | 0.10   | AI bot senaryo üretir
OF-APIGW    | 0.0         | 0.05        | 0.05   | AI route config üretir
OF-SIGNAL   | 0.0         | 0.10        | 0.10   | AI hub + event binding üretir


10.5 UYGULAMA SIRASI
---------------------
OneFrame indirimi, çarpan zincirinde BAZ DEĞER aşamasında uygulanır:
  1. Deliverable kategorize edilir (Bölüm 1 karar ağacı)
  2. Kullanılan profil belirlenir (A, B veya C)
  3. OneFrame eşleşmesi kontrol edilir
  4. Eşleşen deliverable'da profil baz değer yerine residüel değer KULLANILIR
  5. Batch, entegrasyon, kompleksite çarpanları profil bazlı uygulanır
  6. Faz hesaplamaları profil bazlı uygulanır

!!! OF RESİDÜEL BİRİKİM SINIRI !!!
Aynı OF yeteneği bir WP içinde birden fazla deliverable'da eşleştiğinde,
residüel değerler birikir ve efor şişebilir. Bunu önlemek için:

  KURAL: Aynı OF yetenek ID'si bir WP içinde EN FAZLA 2 KEZ tam residüel alır.
  3. ve sonraki eşleşmelerde residüel değer %50 uygulanır.

  Örnek (WP-009 gibi: 4 deliverable hepsi OF-AUTH eşleşmeli):
    D1 OF-AUTH: BE=0.25 (tam)
    D2 OF-AUTH: BE=0.25 (tam)
    D3 OF-AUTH: BE=0.25 x 0.50 = 0.125 (yarı)
    D4 OF-AUTH: BE=0.25 x 0.50 = 0.125 (yarı)
    Toplam: 0.75 AG (sınırsız olsaydı 1.0 AG olurdu)

  Neden: OneFrame bir yeteneği kutudan çıktığı haliyle sunar. İlk 1-2
  deliverable'da konfigürasyon yapılır, sonrakilerde sadece küçük farklar
  (farklı form alanları, farklı endpoint) eklenir. Her deliverable için tam
  konfigürasyon maliyeti tekrarlanmaz.


!!! OF RESİDÜEL + DIŞ ENTEGRASYON ÇARPANI (v11) !!!
OneFrame eşleşen bir deliverable'ın ait olduğu WP'de integration_points
dizisinde DIŞ SİSTEM referansı varsa, residüel değer x1.5 uygulanır.

Gerekçe: OneFrame'in hazır modülü kullanılsa bile, dış sistem entegrasyonu
ek konfigürasyon, güvenlik ayarı ve entegrasyon testi gerektirir. Örneğin
OF-AUTH SSO'su hazırdır ama Azure AD'ye özgü SAML konfigürasyonu, token
endpoint ayarı, kurumsal politika uyumu ayrıca zaman alır.

  Kural: OF residüel eşleşen deliverable'ın WP'sindeki
  integration_points[].length > 0 ise → residüel x 1.5

  Örnek:
    WP-001 integration_points: ["Azure AD", "Kurumsal kimlik sistemi"]
    D1: OF-AUTH eşleşti → Normal residüel BE: 0.25 → Dış ent. x1.5 → BE: 0.375
    
  İstisna: integration_points sadece iç sistemlere referans veriyorsa
  ("OneFrame API", "mevcut veritabanı" gibi) bu çarpan UYGULANMAZ.


10.6 GÖSTERIM KURALI
---------------------
Deliverable listesinde:
  {"adi":"SSO Login Entegrasyonu","kategori":"INTEGRATION",
   "baz_fe":0.0,"baz_be":0.63,  ← VibeCoding Profil C baz değeri
   "oneframe_eslesmesi":"OF-AUTH","residuel_fe":0.0,"residuel_be":0.25,
   "oneframe_notu":"SSO/SAML konfigürasyonu, AI ile hızlı kurulum"}


10.7 ONEFRAME GÖSTERİMİ - ÇIKTI JSON EKLEMESİ
-------------------------------------------------
Proje çıktısının sonuna eklenir:
  "oneframe_analizi": {
    "eslesen_yetenekler": ["OF-AUTH","OF-AUTHZ","OF-FORM","OF-TABLE"],
    "etkilenen_wp_listesi": ["WP-XXX","WP-YYY"],
    "toplam_orijinal_baz": 0,
    "toplam_residuel": 0,
    "toplam_tasarruf_adam_gun": 0,
    "aciklama": "OneFrame framework yetenekleri sayesinde sağlanan efor tasarrufu"
  }


================================================================================
BÖLÜM 11: BAĞLAM ÇARPANLARI (Context Multipliers)
================================================================================

Aynı teknik iş, farklı bağlamlarda farklı efor gerektirir.
Bu çarpanlar PROJE SEVİYESİNDE uygulanır (WP seviyesinde değil).
WBS'teki project_context alanından okunur.

!!! HIZLI ATLAMA KURALI !!!
WBS'te project_context alanı YOKSA veya BOŞSA → Bağlam_Faktörü = x1.0
Bu bölümün tamamı atlanır. Çoğu projede project_context tanımlı değildir.


11.1 ORGANİZASYON ÖLÇEĞİ ÇARPANI
----------------------------------
ÖLÇEK                  | ÇALIŞAN SAYISI  | Profil A,B | Profil C
-----------------------|-----------------|------------|----------
Küçük                  | < 500           | x0.85      | x0.90
Orta (BAZ)             | 500 - 5,000     | x1.00      | x1.00
Büyük                  | 5,000 - 50,000  | x1.20      | x1.05
Enterprise             | > 50,000        | x1.40      | x1.08


11.2 EKİP DENEYİM ÇARPANI
---------------------------
SEVİYE                 | TANIM                          | Profil A,B | Profil C
-----------------------|--------------------------------|------------|----------
Junior Ağırlıklı       | %60+ junior, mentoring gerekli | x1.30      | x1.10
Mid-Level (BAZ)        | Dengeli ekip                   | x1.00      | x1.00
Senior Ağırlıklı       | %60+ senior, otonom çalışır    | x0.85      | x0.95
Uzman Ekip             | Domain expert + senior mix     | x0.75      | x0.90


11.3 DOMAIN KARMAŞIKLIK ÇARPANI
---------------------------------
DOMAIN                 | Profil A,B | Profil C
-----------------------|------------|----------
Standart İş Uygulaması | x1.00      | x1.00
Finans / Muhasebe      | x1.15      | x1.03
Regülasyona Tabi       | x1.25      | x1.05
Sağlık / HIPAA         | x1.30      | x1.08
Kritik Altyapı         | x1.40      | x1.10


11.4 TEKNİK BORÇ ÇARPANI
--------------------------
DURUM                  | Profil A,B | Profil C
-----------------------|------------|----------
Greenfield (Sıfırdan)  | x1.00      | x1.00
Mevcut Sisteme Ekleme  | x1.10      | x1.03
Legacy Entegrasyon     | x1.25      | x1.05
Legacy Modernizasyon   | x1.40      | x1.08


11.5 ENTEGRASYON YOĞUNLUK ÇARPANI (v11)
------------------------------------------
Proje genelindeki FARKLI dış entegrasyon noktalarının toplam sayısına göre:

TOPLAM FARKLI ENT. NOKTASI | Profil A,B | Profil C
---------------------------|------------|----------
0-2 (düşük)                | x1.00      | x1.00
3-4 (orta)                 | x1.05      | x1.05
5-7 (yüksek)               | x1.10      | x1.10
8+ (çok yüksek)            | x1.15      | x1.15

SAYIM KURALI: Tüm WP'lerdeki integration_points[] birleştirilir,
tekrarlar teke düşürülür. Sadece DIŞ sistem referansları sayılır.
"Mevcut veritabanı", "OneFrame API" gibi iç referanslar hariçtir.


11.6 BAĞLAM ÇARPANI UYGULAMA FORMÜLÜ
--------------------------------------
Tüm bağlam çarpanları çarpılarak tek "Bağlam Faktörü" elde edilir:

Bağlam_Faktörü = Ölçek × Ekip × Domain × Teknik_Borç × Entegrasyon_Yoğunluk

Bu faktör PROJE TOPLAMI'na uygulanır (WP bazında değil).

!!! MAKSİMUM SINIR (Profil C VibeCoding) !!!
VibeCoding modunda Bağlam_Faktörü hiçbir durumda 1.20'yi AŞAMAZ.
Hesaplanan değer > 1.20 ise 1.20'ye sabitlenir.


================================================================================
BÖLÜM 12: STABİLİTE KURALLARI
================================================================================

1. Çarpan uygulama sırası (DEĞİŞTİRME):
   profil seç → base (profil bazlı) → (OneFrame residüel varsa: profil bazlı residüel
   değer ile değiştir) → batch (profil bazlı) → entegrasyon
   (profil bazlı) → kompleksite (profil bazlı) → (faz hesapla profil bazlı) → reuse
   (profil bazlı)

2. Yuvarlama ve Minimum Efor Koruması:

   GELENEKSEL (Profil A): 0.5 hassasiyetinde yuvarla (ROUND_HALF_UP)
   COPILOT+CLAUDE (Profil B): 0.1 hassasiyetinde yuvarla
   VIBE CODING (Profil C): 0.1 hassasiyetinde yuvarla

   MİNİMUM EFOR KORUMASI:
   ─────────────────────────────────────────────────────

   Seviye              | Profil A Min   | Profil B Min   | Profil C Min | Gerekçe
   --------------------|----------------|----------------|--------------|---------------------------
   Deliverable başına  | 0.5 AG         | 0.1 AG         | 0.10 AG      | C: 48 dk minimum
   WP başına           | 1.5 AG         | 0.5 AG         | 1.0 AG       | C: 8 saat min (analiz+dev+test)
   Faz kalemi başına   | 0.5 AG         | 0.1 AG         | 0.1 AG       | B,C: ~48 dk min

   Gerekçe:
   - Deliverable C≥0.10: En basit deliverable bile test+review gerektirir (48 dk)
   - WP C≥1.0: Bir WP'nin analiz+geliştirme+test+review döngüsü minimum 8 saat sürer.
     AI kodu anında üretse bile, gereksinim anlama, test senaryosu yazma, review ve
     entegrasyon kontrolü insan aktivitesidir. 4 saatlik eski minimum (0.5 AG)
     gerçek projelerde yetersiz kaldığı gözlemlenmiştir.

3. WP işlem sırası:
   module_id ASC → wp_id ASC

4. Reuse tespiti:
   İşlem sırasına göre, her WP önceki WP'lerle karşılaştırılır

5. Keyword eşleme:
   Büyük/küçük harf duyarsız (case-insensitive)

6. Çift hesaplama önleme:
   Her deliverable SADECE BİR kategoriye girer
   Karar ağacında İLK eşleşen kategori kullanılır

7. WBS'e sadakat:
   complexity.level WBS'den olduğu gibi alınır, DEĞİŞTİRİLMEZ
   Deliverable listesi WBS'den olduğu gibi alınır, eksik bırakılmaz

8. Baz değer gösterimi:
   Deliverable listesinde her zaman kullanılan PROFİLİN BAZ FE/BE değeri yazılır
   Batch indirimi deliverable değerine gömülmez, hesaplama notunda gösterilir

9. OneFrame eşleşme ZORUNLULUĞU:
   Her WP'de ADIM 1.5 (OneFrame eşleştirme, bkz. Bölüm 7 adım tanımı) mutlaka çalıştırılır.
   Taranacak alanlar: deliverable adı, description, backend_requirements,
   frontend_requirements VE integration_points (5 alan).
   Eşleşen deliverable'da profil baz değer yerine profil residüel değer kullanılır.
   Batch hesabı residüel değerler üzerinden yapılır.
   Hiç eşleşme yoksa oneframe_eslesmesi boş liste olarak gösterilir,
   ancak tarama yapıldığı oneframe_analizi.aciklama alanında belirtilir.
   "Kapsam dışı var, o yüzden OneFrame indirimi gerekmez" KABUL EDİLMEZ.

10. Profil tutarlılığı:
    Bir hesaplama boyunca TEK BİR profil kullanılır. Aynı çalışmada profil
    karıştırılmaz. Çıktıda kullanılan profil açıkça belirtilir:
    "metodoloji": "VibeCoding", "profil": "C"


================================================================================
DOKÜMAN SONU
================================================================================
