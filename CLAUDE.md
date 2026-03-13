# PresalesAgent — Claude Code

## Proje Özeti
Kurumsal yazılım projelerinin efor tahminini uçtan uca yapan Streamlit web uygulaması.
PDF analiz dokümanı → WBS üretimi (AI) → Parametre ayarı → Efor hesaplama (Python) → Excel çıktı.

WBS üretimi ve deliverable kategorizasyonunda Claude/GPT API kullanılır.
Efor hesaplama tamamen deterministik Python motoruyla yapılır.
Hesaplama sonrası interaktif AI danışman (chat) ile sonuçlar sorgulanabilir.

## Proje Yapısı
```
PresalesAgent/
├── app.py                           # Streamlit entry point & router
├── requirements.txt                 # PyMuPDF, anthropic, openai, streamlit, openpyxl, json-repair
├── pyproject.toml                   # Paket metadata (v1.1.0)
├── Dockerfile                       # Docker image (Python 3.12-slim, port 8501)
├── CLAUDE.md                        # Bu dosya
├── KURULUM.md                       # Teknik olmayan kullanıcılar için kurulum kılavuzu
├── karar_agaci_v12.md               # Efor hesaplama kuralları referans dokümanı (~92KB)
├── .env                             # API key (git'e eklenmez)
├── .streamlit/config.toml           # Streamlit tema & server ayarları
├── config/
│   └── effort_params.json           # Tüm hesaplama parametreleri (baz değerler, çarpanlar vb.)
├── src/
│   ├── __init__.py
│   ├── llm_client.py                # LLM soyutlama katmanı (Anthropic + OpenAI)
│   ├── pdf_reader.py                # PDF → metin çıkarma (PyMuPDF)
│   ├── wbs_generator.py             # PDF metin → LLM → WBS JSON
│   ├── wbs_editor.py                # WBS düzenleme fonksiyonları
│   ├── categorizer.py               # Deliverable kategorizasyonu (AI destekli)
│   ├── effort_engine.py             # Saf Python efor hesaplama motoru
│   ├── effort_tables.py             # config/effort_params.json → Python modül değişkenleri
│   ├── param_manager.py             # Global & proje-seviye parametre yönetimi
│   ├── project_manager_v2.py        # Versiyonlu proje CRUD & state yönetimi
│   ├── csv_writer.py                # Excel (.xlsx) export (openpyxl)
│   ├── quality_check.py             # Hesaplama sonrası doğrulama
│   ├── chat_agent.py                # AI danışman (sonuçları sorgulama)
│   ├── sidebar_v2.py                # Sidebar navigasyon & proje listesi
│   ├── ui_theme.py                  # Custom CSS injection
│   ├── cli.py                       # CLI giriş noktası (opsiyonel)
│   └── views/
│       ├── __init__.py
│       ├── dashboard.py             # Ana ekran — yeni proje oluşturma
│       ├── wizard.py                # 5 adımlı proje sihirbazı
│       ├── project_detail.py        # Tamamlanmış proje görüntüleme
│       ├── params_view.py           # Global parametre editörü
│       └── components.py            # Paylaşılan UI bileşenleri & grafikler
├── projects/                        # Proje verileri (versiyonlu)
│   └── {project_id}/
│       ├── project.json             # Meta: ad, tarih, wizard durumu
│       ├── scope/extracted_text.txt  # PDF'den çıkarılmış metin
│       ├── wbs/v1.json, v2.json...  # Versiyonlu WBS dosyaları
│       └── calculations/calc_{ts}/  # Hesaplama geçmişi
├── output/                          # Üretilen Excel dosyaları
└── uploads/                         # Kullanıcı PDF'leri (geçici)
```

## Teknoloji
- **Runtime:** Python 3.11+
- **UI:** Streamlit (wide layout, custom tema)
- **PDF okuma:** PyMuPDF (fitz)
- **LLM:** Anthropic SDK + OpenAI SDK (llm_client.py ile soyutlanmış)
- **Modeller:** claude-opus-4-6 / gpt-4.1 (heavy), claude-sonnet-4-6 / gpt-4o (light)
- **LLM Seçimi:** `LLM_PROVIDER` ortam değişkeni (`anthropic` veya `openai`)
- **Excel:** openpyxl
- **JSON onarım:** json-repair (bozuk AI yanıtları için)
- **Container:** Docker (python:3.12-slim, port 8501)

---

# BÖLÜM 1: MİMARİ

```
┌──────────────────────────────────────────────────────────┐
│               LLM ÇAĞRISI #1: WBS ÜRETİMİ               │
│  wbs_generator.py → call_llm(tier="heavy")               │
│  system: WBS_SYSTEM_PROMPT                               │
│  user:   PDF'den çıkarılmış metin                        │
│  çıktı:  WBS JSON                                        │
└──────────────────────────────────────────────────────────┘
                         ↓
              Kullanıcı UI'da düzenler / onaylar
                         ↓
┌──────────────────────────────────────────────────────────┐
│           LLM ÇAĞRISI #2: KATEGORİZASYON                 │
│  categorizer.py → call_llm(tier="heavy")                 │
│  system: CATEGORIZATION_PROMPT                           │
│  user:   Onaylanmış WBS JSON                             │
│  çıktı:  Kategorizasyon JSON                             │
│  (deliverable→kategori, OF eşleşme, reuse, bağlam)      │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│             PARAMETRE AYARI (UI)                          │
│  config/effort_params.json → UI editör                   │
│  Proje-seviye override desteği                           │
│  AI'ın tespit ettiği bağlam değerleri önerilir           │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│          EFOR HESAPLAMA (Saf Python)                      │
│  effort_engine.calculate_effort(wbs, categories, params) │
│  AI çağrısı YOK — deterministik hesaplama                │
│  çıktı: Efor JSON (3 profil: A, B, C)                   │
└──────────────────────────────────────────────────────────┘
                         ↓
              Excel export + AI danışman (opsiyonel)
```

**3 LLM çağrısı:**
1. **WBS üretimi** (heavy) — PDF'den yapısal kırılım
2. **Kategorizasyon** (heavy) — her deliverable'ı 8 kategoriden birine ata + OF eşleştirme + reuse tespiti + bağlam analizi
3. **Chat danışman** (light, opsiyonel) — sonuçları sorgulama

**Efor hesaplama AI ile yapılmaz.** Kategorizasyon sonuçları + parametreler →
`effort_engine.py` tarafından deterministik olarak hesaplanır.
Aynı WBS + aynı kategoriler + aynı parametreler → her zaman aynı sonuç.

---

# BÖLÜM 2: WIZARD AKIŞI (5 ADIM)

```
[Dashboard] → Yeni Proje → SCOPE → WBS_EDIT ──→ CONTEXT → CALCULATE → RESULTS
                             ↓        ↓      ↓       ↓          ↓           ↓
                          PDF yükle  AI WBS  AI     Parametre   Python      Grafik +
                          metin çık  düzenle Kateg. ayarla      hesapla     Excel
```

### Adım 1: Scope (PDF Yükleme)
- Kullanıcı PDF yükler → `pdf_reader.read_pdf()` → metin, sayfa sayısı, kelime sayısı
- Metin `projects/{id}/scope/extracted_text.txt` olarak kaydedilir

### Adım 2: WBS Edit (AI + Manuel Düzenleme)
- PDF metni → `wbs_generator.generate_wbs()` → **LLM çağrısı #1** (heavy tier) → WBS JSON
- WBS tablo olarak gösterilir: wp_id | wp_adi | complexity | deliverable_sayisi
- Düzenleme: complexity değiştir, deliverable ekle/sil, WP ekle/sil
- Her değişiklik yeni versiyon oluşturur (v1, v2, v3...)
- Kullanıcı "Onayla ve Devam Et" dediğinde → **LLM çağrısı #2** (heavy tier):
  `categorizer.categorize_wbs(wbs)` otomatik çalışır
- Bu çağrı her deliverable'ı 8 kategoriden birine atar, OF eşleştirmesi yapar,
  reuse gruplarını tespit eder ve bağlam analizi (domain, entegrasyon yoğunluğu) çıkarır
- AI'ın tespit ettiği bağlam değerleri bir sonraki adımda önerilir

### Adım 3: Context (Parametre Ayarı)
- `config/effort_params.json` varsayılan değerlerle yüklenir
- AI kategorizasyonundan gelen bağlam önerileri (domain, entegrasyon yoğunluğu) gösterilir
- Kullanıcı proje-seviye override yapabilir (baz eforlar, çarpanlar, faz yüzdeleri vb.)
- Değişiklikler proje snapshot'ı olarak kaydedilir

### Adım 4: Calculate (Efor Hesaplama)
- `effort_engine.calculate_effort(wbs, categories, params)` → saf Python hesaplama
- Kategorizasyon sonuçlarını (deliverable→kategori, OF eşleşme, reuse) kullanır
- 3 profil: A (Geleneksel), B (Copilot+Claude), C (VibeCoding)
- Sonuç `projects/{id}/calculations/calc_{ts}/effort_result.json` olarak kaydedilir

### Adım 5: Results (Sonuçlar)
- Profil karşılaştırma grafikleri (Altair)
- WP detay tabloları (FE, BE, fazlar, çarpanlar)
- Faz özeti, global eforlar, risk notları
- Excel export butonu → `output/{proje}_{timestamp}.xlsx`
- AI danışman chat (**LLM çağrısı #3**, light tier) ile sonuçları sorgulama

---

# BÖLÜM 3: MODÜL DETAYLARI

## llm_client.py — LLM Soyutlama Katmanı
```python
def get_provider() -> str        # "anthropic" veya "openai"
def get_model_name(tier) -> str  # heavy: opus/gpt-4.1, light: sonnet/gpt-4o
def check_api_key() -> tuple     # (ok, mesaj)
def call_llm(system, messages, tier="heavy", max_tokens=16000, timeout=120) -> str
```
`LLM_PROVIDER` ortam değişkeni ile provider seçilir. Varsayılan: `anthropic`.

## pdf_reader.py — PDF Okuma
```python
def read_pdf(filepath: str) -> tuple[str, int, int]
    # Döndürür: (metin, sayfa_sayisi, kelime_sayisi)
```

## wbs_generator.py — WBS Üretimi (LLM Çağrısı)
```python
def generate_wbs(pdf_text: str) -> dict
    # Heavy tier LLM çağrısı. WBS JSON döndürür. json-repair ile onarım.
```
WBS JSON şeması:
```json
{
  "meta": {"role": "WBS_Architect", "version": "1.0", "source_doc": ""},
  "project_scope_summary": {
    "project_name": "", "core_objective": "",
    "technical_stack_implications": [], "out_of_scope_items": []
  },
  "wbs": {
    "modules": [{
      "module_id": "MOD-001", "name": "", "description": "",
      "work_packages": [{
        "wp_id": "WP-001", "name": "", "description": "",
        "deliverables": [],
        "technical_context": {
          "frontend_requirements": "", "backend_requirements": "",
          "integration_points": [], "data_implications": ""
        },
        "complexity": {"level": "low|medium|high|very_high", "drivers": []},
        "acceptance_criteria": []
      }]
    }]
  },
  "architect_notes": []
}
```

## wbs_editor.py — WBS Düzenleme
```python
def update_complexity(wbs, wp_id, new_level) -> dict
def add_deliverable(wbs, wp_id, name) -> dict
def remove_wp(wbs, wp_id) -> dict
def add_wp(wbs, module_id, wp_data) -> dict
def update_wp_name(wbs, wp_id, new_name) -> dict
def add_integration_point(wbs, wp_id, point) -> dict
```

## categorizer.py — Deliverable Kategorizasyonu (LLM Çağrısı #2)
WBS onaylandıktan sonra çalışır. Heavy tier LLM çağrısı ile her deliverable'ı kategorize eder.
```python
def categorize_wbs(wbs: dict, max_retries: int = 2) -> dict
    # Heavy tier LLM çağrısı. Retry + json-repair destekli.
    # Raw yanıtlar wbs/.raw_responses/ altına kaydedilir (para boşa gitmesin).
```
8 kategori (öncelik sırasına göre, İLK eşleşen kullanılır):
1. `BACKGROUND_JOB` — Job, Scheduler, Queue, Batch, Cron
2. `INTEGRATION` — 3rd party API, SAP, ERP, CRM, SSO
3. `RULE_ENGINE` — Dynamic rules, Decision engine
4. `EXPORT_REPORT` — PDF/Excel/CSV generation
5. `FILE_PROCESS` — Upload+parse, bulk import
6. `COMPLEX_UI` — Dashboard, charts, drag-drop, wizard, tree view
7. `AUTH_COMPONENT` — Field masking, role-based UI
8. `SIMPLE_UI` — Forms, lists, CRUD, modals (fallback)

AI ayrıca şunları yapar:
- **OneFrame eşleştirme** — 33 OF kodu (OF-AUTH, OF-CRUD, OF-DASH vb.) ile deliverable eşleşmesi
- **Reuse tespiti** — benzer WP'leri gruplama (aynı kategori + komşu complexity + benzer deliverable sayısı)
- **Bağlam analizi** — domain karmaşıklığı (standart/finans/regulasyon/sağlık/kritik) ve entegrasyon yoğunluğu (0-2/3-4/5-7/8+)
- **İndirgeme istisnaları** — B/C profillerde kategori düşürülmeyecek durumları tespit (dış entegrasyon, real-time, güvenlik vb.)

## effort_engine.py — Efor Hesaplama Motoru (Saf Python)
```python
def calculate_effort(wbs: dict, params: dict = None) -> dict
    # Deterministik hesaplama. AI çağrısı yok.
```
Hesaplama sırası:
1. Deliverable sayma & kategorizasyon → FE/BE baz değerler
2. OneFrame residual eşleştirme
3. OF birikim tavanı (3+ aynı OF → ×0.5)
4. Batch çarpanı (kategori içi sıralama: 1.0, 1.0, 0.6, 0.6, 0.4)
5. Entegrasyon çarpanı (nokta sayısına göre: 0→1.0, 1→1.15, 2→1.15, 3→1.30)
6. Kompleksite çarpanı (low: 0.8, medium: 1.0, high: 1.25, very_high: 1.50)
7. Faz yüzdeleri → Analiz, Tasarım, Mimari, Test
8. Min-Max aralıkları (×0.5 – ×2.0)
9. Reuse çarpanı (1.0, 0.7, 0.5, 0.4)
10. Global eforlar (PM, Tech Design, DevOps, Deployment, UAT)
11. Bağlam çarpanları (Ölçek, Ekip, Domain, Teknik Borç, Entegrasyon Yoğunluğu)
12. VibeCoding bağlam tavanı (Profil C max ×1.20)

## effort_tables.py — Parametre Yükleyici
```python
def reload_tables(params: dict)  # config/effort_params.json → modül globalleri
def get_integration_multiplier(profile, point_count) -> float
def get_size_band(technical_total) -> str  # S|M|L|XL
def round_effort(value, profile) -> float  # A: 0.5, B/C: 0.1
```

## param_manager.py — Parametre Yönetimi
```python
def load_params() -> dict            # config/effort_params.json oku
def save_params(params: dict)        # config/effort_params.json yaz
def snapshot_params(project_id, params)  # Proje-seviye snapshot
def merge_params(global_p, overrides) -> dict  # Global + override birleştir
def diff_from_defaults() -> dict     # Değişiklikleri göster
def reset_to_defaults()              # Varsayılanlara dön
```

## project_manager_v2.py — Proje Yönetimi (Versiyonlu)
```python
def create_project(name, description) -> str   # project_id döndür
def load_meta(project_id) -> dict              # project.json oku
def save_wbs_version(project_id, wbs) -> int   # v1, v2... döndür
def load_wbs(project_id, version="latest") -> dict
def save_calculation(project_id, calc_id, result)
def load_latest_calculation(project_id) -> dict
def migrate_all_projects() -> int              # Legacy format migration
```

Proje dizin yapısı:
```
projects/{project_id}/
├── project.json
├── scope/extracted_text.txt
├── wbs/v1.json, v2.json...
└── calculations/calc_{timestamp}/
    ├── wbs_version.txt
    ├── effort_params.json     # Parametre snapshot
    ├── categories.json
    ├── effort_result.json
    └── context.json
```

## csv_writer.py — Excel Export
```python
def write_excel(wbs, categories, effort_result, output_path)
    # Tek .xlsx dosyası, birden fazla sheet
```
Sheet'ler: WBS, Kategorization, Effort Results, Effort Summary, Phase Summary, Global Efforts, Notes & Risks

## chat_agent.py — AI Danışman
```python
def chat(messages, wbs, categories, effort_result, scope_text) -> str
    # Light tier LLM çağrısı. Hesaplama sonuçlarını açıklar, karşılaştırır.
```

## quality_check.py — Kalite Kontrol
```python
def run_checks(wbs: dict, result: dict) -> list[str]
    # Hata listesi (boş = geçti)
```
Kontroller:
1. WP sayısı = WBS'teki WP sayısı
2. Toplam tutarlılığı (±0.5 tolerans)
3. Minimum efor kontrolü (A≥1.5, B≥0.5, C≥1.0)
4. Profil sıralaması (genellikle A ≥ B ≥ C)
5. Sayısal alanlarda metin yok

---

# BÖLÜM 4: KONFİGÜRASYON

## config/effort_params.json
Tüm hesaplama parametrelerini içerir:
- `base_effort` — Profil × Kategori → [FE, BE] baz değerler
- `batch_multipliers` — Kategori içi sıralama çarpanları
- `integration_multipliers` — Entegrasyon nokta sayısına göre çarpanlar
- `complexity_multipliers` — Kompleksite seviyesine göre çarpanlar
- `reuse_multipliers` — Tekrar kullanım çarpanları
- `analysis_pct`, `design_pct`, `architecture_pct`, `test_pct` — Faz yüzdeleri
- `oneframe_residual` — OneFrame kod eşleştirmeleri
- `context_multipliers` — Bağlam çarpanları
- `size_bands` — Proje büyüklük bantları (S/M/L/XL)
- `fixed_bases` — Sabit global eforlar
- `global_formulas` — Global hesaplama formülleri
- `min_max_ranges` — Min-Max aralık çarpanları
- `minimum_effort`, `rounding_precision`, `vibe_context_cap`

Bu dosya değiştiğinde `effort_tables.reload_tables()` çağrılır ve tüm hesaplama tabloları güncellenir.
Kod değişikliği gerekmez.

## .streamlit/config.toml
```toml
[theme]
primaryColor = "#0066CC"
backgroundColor = "#FAFBFC"
textColor = "#1A1A2E"
font = "sans serif"

[server]
headless = true

[browser]
gatherUsageStats = false

[client]
showSidebarNavigation = false
```

## Ortam Değişkenleri
- `ANTHROPIC_API_KEY` — Anthropic API anahtarı (varsayılan provider)
- `OPENAI_API_KEY` — OpenAI API anahtarı (alternatif provider)
- `LLM_PROVIDER` — `anthropic` (varsayılan) veya `openai`

`.env` dosyası proje kök dizininde. `app.py` başlangıçta okur.

---

# BÖLÜM 5: DOCKER & DEPLOYMENT

## Dockerfile
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
COPY requirements.txt . && RUN pip install --no-cache-dir -r requirements.txt
COPY app.py karar_agaci_v12.md src/ config/ .streamlit/ .
RUN mkdir -p uploads wbs output projects wbs/.raw_responses
ENV STREAMLIT_SERVER_HEADLESS=true
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Çalıştırma
```bash
# Lokal
streamlit run app.py

# Docker
docker build -t presales-agent .
docker run -d -p 8501:8501 -e ANTHROPIC_API_KEY="..." presales-agent
```

## AWS Lightsail Deployment
Detaylı plan için bkz: `.claude/plans/` dizini.
Özet: Lightsail Instance ($10/ay) + Docker + Caddy (otomatik SSL) + domain.

---

# BÖLÜM 6: ÖNEMLİ NOTLAR

1. **Efor hesaplama = saf Python.** AI kullanılmaz. `effort_engine.py` deterministik hesaplama yapar.
   Aynı WBS + aynı parametreler → her zaman aynı sonuç. Parametre değişiklikleri
   `config/effort_params.json` üzerinden yapılır, kod değişikliği gerekmez.

2. **karar_agaci_v12.md = referans doküman.** Efor hesaplama kurallarının okunabilir açıklaması.
   Kod tarafından doğrudan kullanılmaz. Kurallar `effort_engine.py` ve
   `config/effort_params.json` içinde kodlanmıştır.

3. **LLM 3 yerde kullanılır:**
   - WBS üretimi (`wbs_generator.py`) — heavy tier
   - Deliverable kategorizasyonu (`categorizer.py`) — heavy tier
   - Chat danışman (`chat_agent.py`) — light tier

4. **Versiyonlama.** WBS her düzenlemede yeni versiyon oluşturur (v1, v2...).
   Her hesaplama ayrı dizinde saklanır (parametre snapshot dahil).

5. **Parametre override.** Global parametreler `config/effort_params.json`'da.
   Her proje kendi override'larını tanımlayabilir. Hesaplama sırasında
   global + override birleştirilir.

6. **Excel çıktı.** Tek `.xlsx` dosyası, birden fazla sheet.
   UTF-8, Excel TR locale uyumlu.

7. **Dual LLM provider.** `LLM_PROVIDER=openai` ile OpenAI'a geçilebilir.
   Kod değişikliği gerekmez.
