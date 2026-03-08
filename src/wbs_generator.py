import json
import re
from pathlib import Path

import anthropic
from json_repair import repair_json


WBS_SYSTEM_PROMPT = """Sen bir "Senior Business Analyst & WBS Architect"sin.
Amacin: Verilen analiz dokumanini inceleyerek, efor tahminlemesine altlik olusturacak
yapilandirilmis ve teknik detayli bir Is Kirilim Yapisi (WBS) olusturmaktir.

GOREV: Dokumani oku, projeyi yonetilebilir parcalara (Work Packages) bol.
Kesinlikle sure veya efor tahmini YAPMA. Sadece kapsami ve karmasikligi tanimla.

KATI KURALLAR:
- Efor/saat/gun tahmini YAPMA.
- Sadece dokumandaki kapsami kullan, varsayim yapma.
- Modul ve WP isimleri Turkce.
- WP'ler "teslim edilecek urun" odakli olmali.
- Her WP icin technical_context alanini mutlaka doldur.
- Granularite: Bir WP bir feature seti buyuklugunde olmali.
- Complexity drivers teknik terimlerle aciklanmali.

CIKTI: SADECE JSON formatinda yanit ver, baska hicbir metin ekleme.
JSON semasi:
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
}"""


class WBSGenerationError(Exception):
    pass


# Raw API yanitlarini kaydetmek icin dizin
RAW_RESPONSE_DIR = Path("wbs/.raw_responses")


def _save_raw_response(raw_text: str, label: str = "wbs") -> Path:
    """Raw API yanitini dosyaya kaydeder. Parse hatasi olursa para bosa gitmesin."""
    RAW_RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = RAW_RESPONSE_DIR / f"{label}_{ts}.txt"
    filepath.write_text(raw_text, encoding="utf-8")
    return filepath


def _extract_json(text: str) -> dict:
    """Yanit metninden JSON cikarir. Markdown code block varsa strip eder.
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


def validate_wbs(wbs: dict) -> list[str]:
    """WBS JSON'u dogrular. Hata listesi dondurur (bos = gecerli)."""
    errors = []

    for key in ("meta", "project_scope_summary", "wbs"):
        if key not in wbs:
            errors.append(f"Ust duzey anahtar eksik: {key}")

    if "wbs" not in wbs:
        return errors

    modules = wbs.get("wbs", {}).get("modules", [])
    if not modules:
        errors.append("En az 1 modul olmali")
        return errors

    valid_levels = {"low", "medium", "high", "very_high"}
    all_wp_ids = []
    all_mod_ids = []

    for mod in modules:
        mod_id = mod.get("module_id", "")
        if not mod_id:
            errors.append("Modul module_id eksik")
        all_mod_ids.append(mod_id)

        wps = mod.get("work_packages", [])
        if not wps:
            errors.append(f"{mod_id}: En az 1 work package olmali")

        for wp in wps:
            wp_id = wp.get("wp_id", "")
            if not wp_id:
                errors.append(f"{mod_id}: WP wp_id eksik")
            all_wp_ids.append(wp_id)

            for field in ("name", "description"):
                if not wp.get(field):
                    errors.append(f"{wp_id}: {field} eksik")

            if not wp.get("deliverables"):
                errors.append(f"{wp_id}: deliverables bos")

            tc = wp.get("technical_context", {})
            if not isinstance(tc, dict):
                errors.append(f"{wp_id}: technical_context dict olmali")
            else:
                for tc_field in ("frontend_requirements", "backend_requirements",
                                 "integration_points", "data_implications"):
                    if tc_field not in tc:
                        errors.append(f"{wp_id}: technical_context.{tc_field} eksik")

            complexity = wp.get("complexity") or {}
            level = complexity.get("level", "")
            if level not in valid_levels:
                # Eksik/gecersiz complexity'yi otomatik duzelt
                wp["complexity"] = complexity
                wp["complexity"]["level"] = "medium"
                wp["complexity"].setdefault("drivers", [])

    dupes = [x for x in all_wp_ids if all_wp_ids.count(x) > 1]
    if dupes:
        errors.append(f"Tekrarlayan wp_id: {set(dupes)}")

    mod_dupes = [x for x in all_mod_ids if all_mod_ids.count(x) > 1]
    if mod_dupes:
        errors.append(f"Tekrarlayan module_id: {set(mod_dupes)}")

    return errors


def generate_wbs(pdf_text: str) -> dict:
    """PDF metninden WBS JSON uretir. Claude API cagrisi #1. Max 2 retry."""
    client = anthropic.Anthropic(timeout=600.0)
    max_retries = 2

    messages = [
        {"role": "user", "content": f"Asagidaki analiz dokumanini oku ve WBS olustur:\n\n{pdf_text}"}
    ]

    for attempt in range(1 + max_retries):
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=16000,
                system=WBS_SYSTEM_PROMPT,
                messages=messages,
            )
            raw_text = response.content[0].text

            # Her yaniti kaydet — parse hatasi olursa dosyadan kurtarilabilir
            saved_path = _save_raw_response(raw_text, "wbs")

            try:
                wbs = _extract_json(raw_text)
            except (json.JSONDecodeError, Exception) as e:
                if attempt < max_retries:
                    messages.append({"role": "assistant", "content": raw_text})
                    messages.append({"role": "user", "content": "JSON parse hatasi olustu. Lutfen SADECE gecerli JSON formatinda yanit ver, baska metin ekleme."})
                    continue
                raise WBSGenerationError(
                    f"JSON parse edilemedi: {e}\n"
                    f"Raw yanit kaydedildi: {saved_path}"
                )

            errors = validate_wbs(wbs)
            if errors:
                if attempt < max_retries:
                    messages.append({"role": "assistant", "content": raw_text})
                    error_msg = "WBS dogrulama hatalari:\n" + "\n".join(f"- {e}" for e in errors)
                    messages.append({"role": "user", "content": f"{error_msg}\nBu hatalari duzelt ve tekrar SADECE JSON olarak yanit ver."})
                    continue
                print(f"  Uyari: WBS dogrulama hatalari: {errors}")

            return wbs

        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            if attempt < max_retries:
                print(f"  API baglanti hatasi, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                continue
            raise WBSGenerationError(f"API hatasi: {e}")

    raise WBSGenerationError("Maksimum deneme sayisina ulasildi")


def load_from_raw_response(filepath: str) -> dict:
    """Kaydedilmis raw API yanitindan WBS parse etmeyi dener.
    Parse hatasi sonrasi 'tekrar API cagirmadan' kurtarma icin."""
    raw_text = Path(filepath).read_text(encoding="utf-8")
    return _extract_json(raw_text)
