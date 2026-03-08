# Efor Tahmin Agent — Claude Code

## Proje Özeti
Kurumsal yazılım projelerinin efor tahminini uçtan uca yapan konuşmaya dayalı agent.
PDF analiz dokümanı → WBS üretimi → Kullanıcı onayı → Efor hesaplama → CSV çıktı.

Her iki ana adımda da (WBS üretimi ve Efor hesaplama) Claude API kullanılır.
Karar ağacı dokümanı efor hesaplama adımında system prompt olarak gönderilir.
Bu yaklaşım Copilot Studio'daki çalışma biçiminin aynısıdır:
  Copilot Studio Instructions  →  Claude API system prompt
  Copilot Studio Knowledge Base →  karar_agaci_v12.md (system prompt'a eklenir)
  Copilot Studio Input          →  WBS JSON (user message)

## Proje Yapısı
```
efor-tahmin/
├── CLAUDE.md                         # Bu dosya
├── karar_agaci_v12.md                # Efor hesaplama kuralları (AI'a prompt olarak gider)
├── requirements.txt                  # pymupdf, anthropic
├── src/
│   ├── __init__.py
│   ├── main.py                       # Ana akış — konuşma döngüsü
│   ├── pdf_reader.py                 # PDF → metin çıkarma
│   ├── wbs_generator.py              # PDF metin → Claude API → WBS JSON
│   ├── wbs_editor.py                 # WBS düzenleme komutları
│   ├── wbs_display.py                # WBS → konsol tablo gösterim
│   ├── effort_calculator.py          # WBS + karar ağacı → Claude API → Efor JSON
│   ├── csv_writer.py                 # Efor JSON → 3 CSV dosyası
│   └── quality_check.py              # CSV öncesi doğrulama
├── uploads/                          # Kullanıcı PDF'leri
├── wbs/                              # Üretilen WBS JSON'ları
└── output/                           # Üretilen CSV çıktıları
```

## Teknoloji
- **Runtime:** Python 3.11+
- **PDF okuma:** pymupdf (fitz)
- **API:** Anthropic Python SDK
- **Model:** claude-opus-4-6 (hem WBS üretimi hem efor hesaplama)
- **API Key:** Ortam değişkeni `ANTHROPIC_API_KEY`
- **CSV:** Python csv modülü (built-in)

## Geliştirme Sırası
```
Adım 1: Proje iskeletini oluştur (dizinler, requirements.txt)
Adım 2: PDF okuma modülü
Adım 3: WBS üretim modülü (Claude API çağrısı #1)
Adım 4: WBS gösterim ve düzenleme
Adım 5: Efor hesaplama modülü (Claude API çağrısı #2)
Adım 6: CSV çıktı üretimi
Adım 7: Kalite kontrol
Adım 8: Ana akış (main.py — konuşma döngüsü)
```

---

# BÖLÜM 1: MİMARİ — İKİ API ÇAĞRISI

Agent'ın tamamı 2 Claude API çağrısı etrafında döner:

```
┌──────────────────────────────────────────────────────────┐
│                    API ÇAĞRISI #1: WBS                    │
│  system: WBS_SYSTEM_PROMPT (Bölüm 2'de)                  │
│  user:   PDF'den çıkarılmış metin                        │
│  çıktı:  WBS JSON                                        │
└──────────────────────────────────────────────────────────┘
                         ↓
              Kullanıcı düzenler / onaylar
                         ↓
┌──────────────────────────────────────────────────────────┐
│                  API ÇAĞRISI #2: EFOR                     │
│  system: karar_agaci_v12.md + EFOR_SYSTEM_PROMPT          │
│  user:   Onaylanmış WBS JSON                             │
│  çıktı:  Efor hesaplama JSON                             │
└──────────────────────────────────────────────────────────┘
                         ↓
              JSON → 3 CSV dosyası (algoritmik)
```

**Önemli:** Efor hesaplama sırasında AI, karar ağacı dokümanını prompt olarak alır
ve tüm kuralları (baz değerler, çarpanlar, faz formülleri, OneFrame eşleştirme vb.)
buna göre uygular. Copilot Studio'daki çalışma biçiminin aynısıdır, ancak:
- 8000 karakter sınırı YOK — karar ağacının tamamı gönderilir
- Çıktı JSON — sonra programatik olarak CSV'ye dönüştürülür
- Kararsız durumlarda agent kullanıcıya soru sorabilir

---

# BÖLÜM 2: KONUŞMA AKIŞI

```
[BAŞLA] → PDF_BEKLE → WBS_URET → WBS_GOSTER
                                      ↓
                         ┌─── DUZENLE ←──┐
                         │       ↓        │
                         │  GUNCELLENDI ──┘
                         ↓
                    ONAYLA → EFOR_HESAPLA → CSV_URET → [BİTTİ]
```

**PDF_BEKLE:**
"Analiz dokümanınızı uploads/ dizinine koyun ve dosya adını söyleyin."

**WBS_URET:**
PDF metnini Claude API'ye gönder (API çağrısı #1). JSON parse et, wbs/ altına kaydet.

**WBS_GOSTER:**
Tablo olarak göster. "X modül, Y WP. Değişiklik veya onay?"

**DUZENLE (döngü):**
Kullanıcı: "WP-003 complexity → high", "WP-005 sil", "deliverable ekle" vb.
Her değişiklik sonrası tablo tekrar gösterilir.

**ONAYLA:**
"onay/tamam/devam/hesapla" → efor hesaplamaya geç.

**EFOR_HESAPLA:**
karar_agaci_v12.md + efor prompt'unu system olarak, WBS JSON'u user olarak gönder
(API çağrısı #2). Dönen JSON'u parse et.

Eğer AI kararsız kalırsa (ör: kategori belirsiz), kullanıcıya soru sorar:
"WP-005 Veri Listeleme Grid — bu deliverable'ı COMPLEX_UI mi SIMPLE_UI mı 
kategorize edeyim? 5 farklı kaynaktan normalize gerekiyor."
Cevap alınca hesaplamayı tamamlar.

**CSV_URET:**
Efor JSON → 3 CSV dosyası. Özet göster. "Başka proje?"

---

# BÖLÜM 3: API ÇAĞRISI #1 — WBS ÜRETİMİ

## wbs_generator.py

```python
import anthropic

client = anthropic.Anthropic()

def generate_wbs(pdf_text: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16000,
        system=WBS_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Aşağıdaki analiz dokümanını oku ve WBS oluştur:\n\n{pdf_text}"}
        ]
    )
    # JSON parse et, doğrula, döndür
```

## WBS System Prompt (sabit string)

```
Sen bir "Senior Business Analyst & WBS Architect"sin.
Amacın: Verilen analiz dokümanını inceleyerek, efor tahminlemesine altlık oluşturacak
yapılandırılmış ve teknik detaylı bir İş Kırılım Yapısı (WBS) oluşturmaktır.

GÖREV: Dokümanı oku, projeyi yönetilebilir parçalara (Work Packages) böl.
Kesinlikle süre veya efor tahmini YAPMA. Sadece kapsamı ve karmaşıklığı tanımla.

KATI KURALLAR:
- Efor/saat/gün tahmini YAPMA.
- Sadece dokümandaki kapsamı kullan, varsayım yapma.
- Modül ve WP isimleri Türkçe.
- WP'ler "teslim edilecek ürün" odaklı olmalı.
- Her WP için technical_context alanını mutlaka doldur.
- Granülarite: Bir WP bir feature seti büyüklüğünde olmalı.
- Complexity drivers teknik terimlerle açıklanmalı.

ÇIKTI: SADECE JSON formatında yanıt ver, başka hiçbir metin ekleme.
JSON şeması:
{
  "meta": {"role": "WBS_Architect", "version": "1.0", "source_doc": ""},
  "project_scope_summary": {
    "project_name": "",
    "core_objective": "",
    "technical_stack_implications": [],
    "out_of_scope_items": []
  },
  "wbs": {
    "modules": [{
      "module_id": "MOD-001",
      "name": "",
      "description": "",
      "work_packages": [{
        "wp_id": "WP-001",
        "name": "",
        "description": "",
        "deliverables": [],
        "technical_context": {
          "frontend_requirements": "",
          "backend_requirements": "",
          "integration_points": [],
          "data_implications": ""
        },
        "complexity": {
          "level": "low|medium|high|very_high",
          "drivers": []
        },
        "acceptance_criteria": []
      }]
    }]
  },
  "architect_notes": []
}
```

## WBS Doğrulama
JSON parse sonrası kontrol:
- Her modülün module_id ve min 1 WP'si var mı
- Her WP: wp_id, name, deliverables[], technical_context, complexity.level mevcut mu
- complexity.level ∈ {low, medium, high, very_high}
- wp_id unique mi
Hata varsa retry (max 2).

---

# BÖLÜM 4: API ÇAĞRISI #2 — EFOR HESAPLAMA

## effort_calculator.py

Bu modül, karar ağacı dokümanını system prompt olarak Claude API'ye gönderir.
Copilot Studio'daki "Instructions + Knowledge Base" yapısının birebir karşılığıdır.

```python
import anthropic

client = anthropic.Anthropic()

def load_decision_tree() -> str:
    """karar_agaci_v12.md dosyasını oku ve string olarak döndür."""
    with open("karar_agaci_v12.md", "r", encoding="utf-8") as f:
        return f.read()

def calculate_effort(wbs_json: dict) -> dict:
    decision_tree = load_decision_tree()
    
    system_prompt = build_effort_system_prompt(decision_tree)
    user_message = json.dumps(wbs_json, ensure_ascii=False, indent=2)
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=32000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Aşağıdaki WBS'in efor tahminini yap:\n\n{user_message}"}
        ]
    )
    # JSON parse et, döndür
```

## Efor System Prompt

System prompt iki parçadan oluşur:
1. **Talimatlar** — hesaplama adımları, çıktı formatı
2. **Karar ağacı** — karar_agaci_v12.md'nin tamamı

```python
def build_effort_system_prompt(decision_tree: str) -> str:
    return f"""Sen kurumsal yazılım projelerinde efor tahmini yapan bir uzmansın.
Verilen WBS dokümanını analiz ederek, aşağıdaki KARAR AĞACI kurallarına göre
deterministik efor hesaplaması yapacaksın.

İki çalıştırma arasında %0 sapma olmalı — aynı WBS her zaman aynı sonucu vermeli.
WBS'te metodoloji belirtilmemişse 3 profili de (A, B, C) hesapla.

HESAPLAMA ADIMLARI (SIRASI DEĞİŞMEZ):
ADIM 0: Profil seç (A: Geleneksel, B: Copilot+Claude, C: VibeCoding)
ADIM 1: Kategorizasyon (karar ağacı Bölüm 1) + B/C indirgeme matrisi + istisnalar
ADIM 1.5: OneFrame eşleştirme (Bölüm 10) — ZORUNLU
ADIM 2: Batch çarpanı (Bölüm 3.1)
ADIM 3: Entegrasyon çarpanı (Bölüm 3.2)
ADIM 4: Kompleksite çarpanı (Bölüm 3.3)
ADIM 5: Faz hesaplama (Bölüm 4)
ADIM 6: WP toplam
ADIM 7: Reuse (Bölüm 3.4)
ADIM 8: Min-Max (Bölüm 6)
Sonra: Global eforlar (Bölüm 5), Bağlam çarpanları (Bölüm 11), Proje toplam

KARARSIZ KALIRSAN:
Eğer bir deliverable'ın kategorisi veya bir kararın sonucu belirsizse,
yanıtının başına "SORU:" bloğu ekle. Örnek:
  "SORU: WP-005 Veri Listeleme Grid — COMPLEX_UI mi SIMPLE_UI mı? 
   5 farklı kaynaktan normalize + virtual scrolling var."
Sorudan sonra EN OLASI senaryoyu varsayarak hesaplamaya devam et.
Kullanıcı cevaplarsa tekrar hesaplarsın.

ÇIKTI FORMATI:
SADECE JSON döndür, başka metin ekleme. Şema:
{{
  "tahmin_ozeti": {{
    "proje_adi": "",
    "tahmin_tarihi": "YYYY-MM-DD",
    "toplam_modul": 0,
    "toplam_wp": 0,
    "proje_bandi": "S|M|L|XL"
  }},
  "faz_formulleri": {{
    "analiz": "...",
    "ui_ux": "...",
    "mimari": "...",
    "fe": "Adj_FE",
    "be": "Adj_BE",
    "test": "..."
  }},
  "wp_detaylari": [{{
    "modul": "MOD-001",
    "wp_id": "WP-001",
    "wp_adi": "",
    "complexity": "",
    "deliverable_sayisi": 0,
    "baskin_kategori": "",
    "of_eslesmesi": "",
    "reuse_durumu": "",
    "hesaplama_hikayesi": "",
    "a_fe":0,"a_be":0,"a_analiz":0,"a_tasarim":0,"a_mimari":0,"a_test":0,"a_toplam":0,
    "b_fe":0,"b_be":0,"b_analiz":0,"b_tasarim":0,"b_mimari":0,"b_test":0,"b_toplam":0,
    "c_fe":0,"c_be":0,"c_analiz":0,"c_tasarim":0,"c_mimari":0,"c_test":0,"c_toplam":0,
    "min_a":0,"max_a":0,"min_b":0,"max_b":0,"min_c":0,"max_c":0
  }}],
  "modul_toplamlari": [{{"modul": "", "a_toplam":0, "b_toplam":0, "c_toplam":0}}],
  "faz_toplamlari": {{
    "a": {{"analiz":0,"tasarim":0,"mimari":0,"fe":0,"be":0,"test":0,"toplam":0}},
    "b": {{"analiz":0,"tasarim":0,"mimari":0,"fe":0,"be":0,"test":0,"toplam":0}},
    "c": {{"analiz":0,"tasarim":0,"mimari":0,"fe":0,"be":0,"test":0,"toplam":0}}
  }},
  "global_eforlar": {{
    "a": {{"pm":0,"tech_design":0,"devops":0,"deployment":0,"uat":0,"ba_base":0,"test_base":0,"uat_base":0,"toplam":0}},
    "b": {{"pm":0,"tech_design":0,"devops":0,"deployment":0,"uat":0,"ba_base":0,"test_base":0,"uat_base":0,"toplam":0}},
    "c": {{"pm":0,"tech_design":0,"devops":0,"deployment":0,"uat":0,"ba_base":0,"test_base":0,"uat_base":0,"toplam":0}}
  }},
  "proje_toplami": {{
    "a": {{"teknik":0,"global":0,"toplam":0,"min":0,"max":0}},
    "b": {{"teknik":0,"global":0,"toplam":0,"min":0,"max":0}},
    "c": {{"teknik":0,"global":0,"toplam":0,"min":0,"max":0}},
    "tasarruf_b_ag":0,"tasarruf_b_yuzde":0,
    "tasarruf_c_ag":0,"tasarruf_c_yuzde":0
  }},
  "baglam_carpanlari": {{
    "olcek":0,"ekip":0,"domain":0,"teknik_borc":0,"ent_yogunluk":0,
    "faktor_a_b":0,"faktor_c":0
  }},
  "sorular": ["varsa belirsiz kararlar için sorular"],
  "notlar": ["hesaplama kararları"],
  "riskler": [""],
  "kapsam_disi": [""]
}}

STABİLİTE KURALLARI:
1. Sıra: profil→base→OF(+dışEnt)→batch→entegrasyon→kompleksite→faz→reuse
2. Bağlam: proje toplamına. C:MAX 1.20. EntYoğunluk dahil.
3. Yuvarlama: ara 4 ondalık, nihai A=0.5/B,C=0.1
4. İşlem: module_id ASC → wp_id ASC
5. Kategori: tek, "DEĞİL" kontrol. B/C indirgeme + İSTİSNALAR (4 kural).
6. OF: 5 alan tara. Dış ent→res x1.5. "Kapsam dışı→OF gerekmez" KABUL EDİLMEZ.
7. Sayısal alanlara SADECE sayı yaz.

=== KARAR AĞACI BAŞLANGIÇ ===
{decision_tree}
=== KARAR AĞACI BİTİŞ ===
"""
```

## Soru-Cevap Döngüsü
API yanıtında `"sorular"` dizisi doluysa:
1. Soruları kullanıcıya göster
2. Cevapları al
3. Cevapları ekleyerek API'yi tekrar çağır:
```python
messages=[
    {"role": "user", "content": f"WBS:\n{wbs_json}"},
    {"role": "assistant", "content": f"İlk hesaplama:\n{ilk_yanit}"},
    {"role": "user", "content": f"Sorularına cevaplar:\n{cevaplar}\nBu cevaplara göre hesaplamayı güncelle."}
]
```

---

# BÖLÜM 5: KONUŞMA AKIŞI

```
[BAŞLA] → PDF_BEKLE → WBS_URET → WBS_GOSTER
                                      ↓
                         ┌─── DUZENLE ←──┐
                         │       ↓        │
                         │  GUNCELLENDI ──┘
                         ↓
                    ONAYLA → EFOR_HESAPLA → SORU_VAR_MI?
                                               ↓ hayır        ↓ evet
                                           CSV_URET    SORU_SOR → TEKRAR_HESAPLA
                                               ↓                       ↓
                                            [BİTTİ]               CSV_URET
```

### Durum Detayları

**PDF_BEKLE:**
"Analiz dokümanınızı (PDF) uploads/ dizinine koyun ve dosya adını söyleyin."

**WBS_URET:**
PDF → Claude API (çağrı #1) → WBS JSON → wbs/ altına kaydet.
Parse hatası → retry (max 2). "X modül, Y WP tespit edildi."

**WBS_GOSTER:**
Tablo: wp_id | wp_adi | complexity | deliverable_sayisi
"Değişiklik veya onay?"

**DUZENLE (döngü):**
- "WP-003 complexity → high"
- "WP-005 sil"
- "MOD-002'ye WP ekle: ..."
- "deliverable ekle/sil"
- "integration_points'e ... ekle"
Her değişiklik sonrası tablo tekrar. Kullanıcı "onay" diyene kadar.

**EFOR_HESAPLA:**
WBS JSON + karar_agaci_v12.md → Claude API (çağrı #2) → Efor JSON.

**SORU_VAR_MI:**
Efor JSON'da `sorular` dizisi doluysa → kullanıcıya göster, cevap al, tekrar hesapla.
Boşsa → direkt CSV'ye geç.

**CSV_URET:**
Efor JSON → 3 CSV dosyası (Bölüm 6). Özet göster.
"Başka proje hesaplamak ister misiniz?"

---

# BÖLÜM 6: CSV ÇIKTI FORMATI

3 dosya. UTF-8 BOM. Ayraç `;` (Excel TR uyumlu).
Dosya adı: `[proje_kisa_adi]_*.csv`

## 1. `[proje]_wp_detaylari.csv`
Her satır 1 WP. Excel'de filtrelenebilir.
```
modul;wp_id;wp_adi;complexity;deliverable_sayisi;baskin_kategori;of_eslesmesi;reuse_durumu;a_analiz;a_tasarim;a_mimari;a_fe;a_be;a_test;a_toplam;b_analiz;b_tasarim;b_mimari;b_fe;b_be;b_test;b_toplam;c_analiz;c_tasarim;c_mimari;c_fe;c_be;c_test;c_toplam;min_a;max_a;min_b;max_b;min_c;max_c;hesaplama_hikayesi
```

## 2. `[proje]_ozet.csv`
Dikey format — her satır 1 metrik:
```
bolum;kalem;profil_a;profil_b;profil_c
PROJE;proje_adi;...
PROJE;tarih;...
PROJE;toplam_modul;...
PROJE;toplam_wp;...
PROJE;proje_bandi;-;[bant];[bant]
MODUL;[MOD-001 Ad];[toplam];[toplam];[toplam]
FAZ;analiz;...
FAZ;tasarim;...
FAZ;mimari;...
FAZ;fe;...
FAZ;be;...
FAZ;test;...
FAZ;toplam;...
GLOBAL;pm;...
GLOBAL;tech_design;...
GLOBAL;devops;...
GLOBAL;deployment;...
GLOBAL;uat;...
GLOBAL;ba_base;0;[n];[n]
GLOBAL;test_base;0;[n];[n]
GLOBAL;uat_base;0;[n];[n]
GLOBAL;global_toplam;...
TOPLAM;teknik;...
TOPLAM;global;...
TOPLAM;genel_toplam;...
TOPLAM;min;...
TOPLAM;max;...
TOPLAM;tasarruf_ag;-;[n];[n]
TOPLAM;tasarruf_yuzde;-;[%];[%]
BAGLAM;faktor;...
```

## 3. `[proje]_notlar.csv`
```
tip;icerik
NOT;WP-001: 3xSIMPLE_UI + 1xAUTH_COMP, OF-AUTH eşleşti
RISK;BDDK bot mekanizması kritik
KAPSAM_DISI;EC entegrasyonu
```

---

# BÖLÜM 7: KALİTE KONTROL

CSV yazmadan ÖNCE Efor JSON üzerinde:
1. WP sayısı = WBS'teki WP sayısı
2. Σ(wp a_toplam) ≈ faz_toplamlari.a.toplam (yuvarlama farkı ±0.5 tolerans)
3. Hiçbir WP minimum eforun altında değil (A≥1.5, B≥0.5, C≥1.0)
4. Genellikle A ≥ B ≥ C (istisnalar hariç)
5. Sayısal alanlarda metin yok (sadece sayı)

Hata varsa kullanıcıya raporla, "Tekrar hesaplansın mı?" sor.

---

# BÖLÜM 8: MODÜL DETAYLARI

**pdf_reader.py:**
```python
def read_pdf(filepath: str) -> tuple[str, int, int]:
    """Döndürür: (metin, sayfa_sayisi, kelime_sayisi)"""
```

**wbs_generator.py:**
```python
def generate_wbs(pdf_text: str) -> dict:
    """Claude API çağrısı #1. WBS JSON döndür. Max 2 retry."""

def validate_wbs(wbs: dict) -> list[str]:
    """Hata listesi (boş = OK)."""
```

**wbs_editor.py:**
```python
def update_complexity(wbs, wp_id, new_level) -> dict
def add_deliverable(wbs, wp_id, name) -> dict
def remove_wp(wbs, wp_id) -> dict
def add_wp(wbs, module_id, wp_data) -> dict
def update_wp_name(wbs, wp_id, new_name) -> dict
def add_integration_point(wbs, wp_id, point) -> dict
```

**wbs_display.py:**
```python
def display_wbs_table(wbs: dict)
    """Konsola tablo olarak göster."""
```

**effort_calculator.py:**
```python
def load_decision_tree() -> str:
    """karar_agaci_v12.md oku."""

def build_effort_system_prompt(decision_tree: str) -> str:
    """Talimatlar + karar ağacı birleştir."""

def calculate_effort(wbs: dict) -> dict:
    """Claude API çağrısı #2. Efor JSON döndür."""

def recalculate_with_answers(wbs: dict, previous_result: str, answers: str) -> dict:
    """Soru cevaplarıyla tekrar hesapla."""
```

**csv_writer.py:**
```python
def write_wp_details(result: dict, filepath: str)
def write_summary(result: dict, filepath: str)
def write_notes(result: dict, filepath: str)
```

**quality_check.py:**
```python
def run_checks(wbs: dict, result: dict) -> list[str]:
    """Hata listesi (boş = geçti)."""
```

**main.py:**
```python
def main():
    """
    1. PDF bekle → oku
    2. WBS üret (API #1) → göster
    3. Düzenleme döngüsü (onaya kadar)
    4. Efor hesapla (API #2)
    5. Soru varsa → kullanıcıya sor → tekrar hesapla
    6. Kalite kontrol → CSV üret → özet göster
    7. Tekrar mı?
    """
```

---

# BÖLÜM 9: KONUŞMA ÖRNEKLERİ

```
Agent: Efor Tahmin Agent'a hoş geldiniz.
       Analiz dokümanınızı (PDF) uploads/ dizinine koyun ve dosya adını söyleyin.

User:  uploads/makro_ekonomi.pdf

Agent: ✓ PDF okundu: 12 sayfa, ~4500 kelime.
       WBS oluşturuluyor (Claude API)...
       
       ✓ WBS: 4 modül, 9 work package.
       ┌─────────┬─────────────────────────────────────┬───────────┬──────┐
       │ wp_id   │ wp_adi                              │ complexity│ del. │
       ├─────────┼─────────────────────────────────────┼───────────┼──────┤
       │ WP-001  │ Kullanıcı Giriş ve Azure SSO Ent.  │ medium    │ 4    │
       │ WP-002  │ Kullanıcı ve Rol Yönetimi           │ low       │ 3    │
       │ ...     │ ...                                 │ ...       │ ...  │
       └─────────┴─────────────────────────────────────┴───────────┴──────┘
       WBS: wbs/makro_ekonomi.json
       Değişiklik veya onay?

User:  WP-005 complexity high olsun

Agent: ✓ WP-005: medium → high
       [tablo güncellenir]
       Başka değişiklik?

User:  onay

Agent: ✓ WBS onaylandı. Efor hesaplanıyor (3 profil, Claude API)...
       
       ⚠ AI'ın 1 sorusu var:
       WP-008 "İzleme Dashboard'u" — chart library + real-time status göstergeleri
       içeriyor. COMPLEX_UI olarak mı hesaplayayım yoksa SIMPLE_UI olarak mı?
       (İndirgeme istisnası: real-time keyword var)

User:  COMPLEX_UI olsun

Agent: ✓ Güncelleniyor...
       
       Hesaplama tamamlandı:
       
       Profil A (Geleneksel):     127.1 AG (114–139 AG)
       Profil B (Copilot+Claude):  62.0 AG (55–68 AG)  — %51 tasarruf
       Profil C (VibeCoding):      41.5 AG (37–46 AG)  — %67 tasarruf
       
       Çıktılar:
         output/makro_wp_detaylari.csv
         output/makro_ozet.csv
         output/makro_notlar.csv
       
       Başka proje?
```

---

# BÖLÜM 10: ÖNEMLİ NOTLAR

1. **Karar ağacı = prompt.** karar_agaci_v12.md dosyası değiştiğinde sadece
   dosyayı güncelle. Kod değişikliği gerekmez. Yeni kurallar otomatik uygulanır.

2. **Determinizm hedef ama garanti değil.** AI tabanlı hesaplama olduğu için
   %100 aynı sonuç garanti edilemez. Ancak karar ağacındaki katı kurallar ve
   stabilite talimatları tutarlılığı maksimize eder.

3. **Soru mekanizması kritik.** AI belirsiz durumlarda varsayım yapmak yerine
   kullanıcıya sormalı. Bu, Copilot Studio'da olmayan bir avantaj.

4. **CSV → Excel uyumu.** UTF-8 BOM + `;` ayraç. Türkçe karakterler doğru
   görünmeli. Excel TR'de çift tıkla aç.

5. **API maliyeti.** Her proje 2 API çağrısı: WBS (~4K input / ~4K output) +
   Efor (~100K input / ~8K output). karar_agaci_v12.md ~90KB, bu context'e sığar.

6. **karar_agaci_v12.md boyutu.** ~1683 satır, ~90KB. Claude'un context window'una
   rahatlıkla sığar. Copilot Studio'nun 8K sınırı yok.

7. **Retry stratejisi.** API timeout veya parse hatası → max 2 retry.
   3. başarısızlıkta kullanıcıya hata mesajı.
