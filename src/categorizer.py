"""AI ile deliverable kategorizasyonu ve baglam analizi."""

import json
import re
from pathlib import Path

from json_repair import repair_json
from src.llm_client import call_llm


CATEGORIZATION_PROMPT = """Sen yazilim projelerinde deliverable kategorizasyonu yapan bir uzmansin.
Verilen WBS'teki her deliverable'i asagidaki 8 kategoriden birine ata.
Ayrica OneFrame framework eslesmesi yap ve WP'ler arasi reuse tespiti yap.

8 KATEGORİ (oncelik sirasina gore, ILK eslesen kategori kullanilir):

1. BACKGROUND_JOB: Job, Scheduler, Queue, Async islem, Batch islem, Worker, Cron
   DEGIL: Async button click, auto-save, countdown timer → SIMPLE_UI

2. INTEGRATION: SSO, 3rd party API, SAP, ERP, CRM, SOAP, dis sistem entegrasyonu
   DEGIL: YouTube embed, CDN upload, SMTP mail, LLM API call, webhook → SIMPLE_UI
   NOT: integration_points[] bos ise → SIMPLE_UI

3. RULE_ENGINE: Dinamik kural motoru, configurable puanlama, decision engine
   DEGIL: Form validasyon, basit hesaplama, if-else mantigi, filtreleme → SIMPLE_UI

4. EXPORT_REPORT: PDF/Excel/CSV olusturma, rapor generate, template bazli export
   DEGIL: PDF goruntule, dosya indir, rapor ekrani (sadece tablo) → SIMPLE_UI

5. FILE_PROCESS: Upload+parse, bulk import, dosya format donusumu
   DEGIL: Tek dosya upload (profil foto), dosya linki, indirme butonu → SIMPLE_UI

6. COMPLEX_UI: Dashboard+chart, drag-drop, wizard, tree view, real-time guncelleme
   DEGIL: Basit kartlar+liste, statik istatistik, basit form → SIMPLE_UI

7. AUTH_COMPONENT: Field masking, rol bazli alan gizleme, yetki bazli UI
   DEGIL: Basit login formu, sifre degistirme → SIMPLE_UI

8. SIMPLE_UI: Form, liste, modal, CRUD, basit ekranlar (FALLBACK kategori)

INDIRGEME ISTISNALARI (B/C profillerde kategori dusurulmez eger):
- integration_points[] > 0 (dis bagimliligi var)
- 3+ farkli veri kaynagindan normalize gerekiyor
- "real-time", "canli", "live" keyword'u var
- "guvenlik", "KVKK", "sifreleme", "maskeleme" keyword'u var

ONEFRAME ESLESMESI — asagidaki keyword'leri 5 alanda tara
(deliverable adi, WP description, backend_req, frontend_req, integration_points):
OF-AUTH: SSO, Login, OAuth, SAML, 2FA, KeyCloak, IdentityServer, Oturum
OF-AUTHZ: RBAC, Rol bazli, Permission, Yetki, Tenant, Claim
OF-CRUD: CRUD, Ekleme, Guncelleme, Silme, Listeleme, Repository
OF-DATA: EF Core, Code-First, Migration, Database
OF-CACHE: Cache, Redis, Onbellek
OF-SEARCH: Elasticsearch, Full-text search, Arama motoru
OF-AUDIT: Audit, Log kaydi, Islem gecmisi
OF-UI: Metronic, Bootstrap, Material Design, Responsive, Dark mode
OF-FORM: Form, Kayit formu, Basvuru formu, Input, Multi-step, Wizard form
OF-TABLE: Tablo, Liste, Grid, Data table, Sayfalama, Sorting
OF-MENU: Menu, Sidebar, Navigasyon, Dinamik menu
OF-DASH: Dashboard, Grafik, Chart, Istatistik, Ozet
OF-PROFILE: Profil, Kullanici bilgi, Hesap ayarlari
OF-REPORT: Rapor, Report, Raporlama
OF-NOTIF: Bildirim, Notification, E-posta gonderim, SMS, Push
OF-HANGFIRE: Hangfire, Background job, Scheduled task, Zamanli gorev
OF-RULE: Rule engine, Kural motoru, Is kurali, Dinamik kural
OF-WORKFLOW: Workflow, Is akisi, Onay akisi, Surec yonetimi
OF-DMS: Dokuman yonetim, DMS, Belge yonetim
OF-FILE: Dosya yukleme, Upload, Download, Storage
OF-UPLOAD: Upload widget, Drag drop upload
OF-CMS: CMS, WYSIWYG, Icerik yonetim
OF-FAQ: FAQ, SSS, Sikca sorulan
OF-VALID: FluentValidation, Validasyon
OF-I18N: Cok dil, Multi-language, Localization
OF-ERR: Exception, Hata yonetimi, Error handling, Middleware
OF-CHATBOT: Chatbot, Bot, Canli destek
OF-APIGW: API Gateway, Rate limit
OF-SIGNAL: SignalR, Real-time, WebSocket, Canli guncelleme

REUSE TESPITI: Asagidaki kriterlerden EN AZ 2'si eslesen WP'leri ayni reuse grubuna koy:
- Ayni baskin kategori
- Ayni veya komsu complexity (low-medium veya medium-high komsu)
- Deliverable sayisi farki <= 2
- Ayni modul veya benzer domain

BAGLAM ANALIZI — WBS'i inceleyerek asagidaki 2 boyutu OTOMATIK tespit et:

1. domain_karmasikligi: Projenin domain'ine bakarak sec:
   - "standart": Normal is uygulamasi, e-ticaret, portal
   - "finans": Finans, muhasebe, bankacilik, odeme, banka
   - "regulasyon": Regulasyona tabi, BDDK, SPK, KVKK uyum, yasal zorunluluk
   - "saglik": Saglik, hastane, HIPAA, tibbi cihaz
   - "kritik": Kritik altyapi, enerji, savunma, guvenlik

2. entegrasyon_yogunlugu: Tum WP'lerdeki TOPLAM benzersiz dis entegrasyon sayisini say
   (integration_points[] icerigini say, her benzersiz dis sistem 1 entegrasyon):
   - "0-2": 0-2 benzersiz dis sistem entegrasyonu
   - "3-4": 3-4 benzersiz dis sistem
   - "5-7": 5-7 benzersiz dis sistem
   - "8+": 8 veya daha fazla benzersiz dis sistem

CIKTI: SADECE JSON dondur:
{
  "wp_kategorileri": {
    "WP-001": {
      "deliverables": [
        {"adi": "...", "kategori": "SIMPLE_UI", "of_match": "OF-FORM", "neden": "kisa aciklama"}
      ],
      "baskin_kategori": "SIMPLE_UI",
      "reuse_grubu": null
    }
  },
  "reuse_gruplari": {
    "G1": ["WP-001", "WP-002"]
  },
  "baglam_analizi": {
    "domain_karmasikligi": "standart|finans|regulasyon|saglik|kritik",
    "domain_neden": "Neden bu domain secildi, kisa aciklama",
    "entegrasyon_yogunlugu": "0-2|3-4|5-7|8+",
    "benzersiz_entegrasyonlar": ["Azure AD", "TCMB EVDS", "..."],
    "entegrasyon_neden": "Toplam X benzersiz dis sistem tespit edildi"
  },
  "riskler": ["risk aciklamasi"],
  "notlar": ["onemli notlar"],
  "sorular": ["belirsiz kategoriler icin soru"]
}"""


# Raw API yanitlarini kaydetmek icin dizin
RAW_RESPONSE_DIR = Path("wbs/.raw_responses")


def _save_raw_response(raw_text: str, label: str = "categorize") -> Path:
    """Raw API yanitini dosyaya kaydeder. Parse hatasi olursa para bosa gitmesin."""
    RAW_RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = RAW_RESPONSE_DIR / f"{label}_{ts}.txt"
    filepath.write_text(raw_text, encoding="utf-8")
    return filepath


def _extract_json(text: str) -> dict:
    """API yanitindan JSON cikar. Markdown bloklari ve yaygin hatalari temizler.
    3 asamali: dogrudan parse → regex fix → json_repair kutuphanesi."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Ilk olarak { ile } arasini bul
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    # Asama 1: Dogrudan dene
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Asama 2: Basit regex fix (trailing comma, kontrol karakterleri)
    fixed = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    fixed = re.sub(r",\s*([\]}])", r"\1", fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Asama 3: json_repair kutuphanesi (en guclu onarim)
    repaired = repair_json(cleaned, return_objects=True)
    if isinstance(repaired, dict):
        return repaired

    raise json.JSONDecodeError("Tum onarim asamalari basarisiz", cleaned, 0)


def categorize_wbs(wbs: dict, max_retries: int = 2) -> dict:
    """WBS'teki deliverable'lari kategorize eder. Retry destekli."""
    wbs_json = json.dumps(wbs, ensure_ascii=False, indent=2)

    messages = [
        {"role": "user", "content": f"Asagidaki WBS'i kategorize et:\n\n{wbs_json}"}
    ]

    for attempt in range(max_retries + 1):
        raw_text = call_llm(
            system=CATEGORIZATION_PROMPT,
            messages=messages,
            tier="heavy",
            max_tokens=16000,
            timeout=600,
        )

        # Her yaniti kaydet — parse hatasi olursa dosyadan kurtarilabilir
        saved_path = _save_raw_response(raw_text, "categorize")

        try:
            return _extract_json(raw_text)
        except (json.JSONDecodeError, Exception) as e:
            if attempt < max_retries:
                # Hatali yaniti conversation'a ekle, duzeltme iste
                messages.append({"role": "assistant", "content": raw_text})
                messages.append({
                    "role": "user",
                    "content": (
                        f"JSON parse hatasi: {e}\n"
                        "Lutfen SADECE gecerli JSON dondur. "
                        "Trailing comma olmasin, tum stringler tirnak icinde olsun. "
                        "Tekrar dene."
                    ),
                })
            else:
                raise ValueError(
                    f"Kategorizasyon JSON parse hatasi ({max_retries + 1} deneme sonrasi): {e}\n"
                    f"Raw yanit kaydedildi: {saved_path}"
                )


def load_from_raw_response(filepath: str) -> dict:
    """Kaydedilmis raw API yanitindan kategorize parse etmeyi dener.
    Parse hatasi sonrasi 'tekrar API cagirmadan' kurtarma icin."""
    raw_text = Path(filepath).read_text(encoding="utf-8")
    return _extract_json(raw_text)
