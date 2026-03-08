"""Efor parametrelerini JSON dosyasindan yukleyen ve kaydeden modul."""

import copy
import json
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "effort_params.json"

# effort_tables.py'deki mevcut varsayilan degerler
DEFAULTS = {
    "base_effort": {
        "A": {
            "BACKGROUND_JOB": [0.0, 3.0], "INTEGRATION": [0.0, 3.0],
            "RULE_ENGINE": [0.0, 4.0], "EXPORT_REPORT": [1.2, 1.5],
            "FILE_PROCESS": [0.5, 2.0], "COMPLEX_UI": [2.5, 2.0],
            "AUTH_COMPONENT": [0.5, 1.5], "SIMPLE_UI": [0.8, 0.8],
        },
        "B": {
            "SIMPLE_UI": [0.44, 0.44], "EXPORT_REPORT": [0.66, 0.82],
            "FILE_PROCESS": [0.30, 1.20], "COMPLEX_UI": [1.62, 1.30],
            "BACKGROUND_JOB": [0.0, 1.95], "AUTH_COMPONENT": [0.40, 1.20],
            "INTEGRATION": [0.0, 2.40], "RULE_ENGINE": [0.0, 3.20],
        },
        "C": {
            "SIMPLE_UI": [0.24, 0.24], "EXPORT_REPORT": [0.42, 0.52],
            "FILE_PROCESS": [0.20, 0.80], "COMPLEX_UI": [1.12, 0.90],
            "BACKGROUND_JOB": [0.0, 1.50], "AUTH_COMPONENT": [0.35, 1.05],
            "INTEGRATION": [0.0, 2.25], "RULE_ENGINE": [0.0, 3.20],
        },
    },
    "batch_multipliers": {
        "A": [1.0, 1.0, 0.6, 0.6, 0.4],
        "B": [1.0, 1.0, 0.6, 0.6, 0.4],
        "C": [1.0, 1.0, 0.6, 0.6, 0.4],
    },
    "integration_multipliers": {
        "A": {"0": 1.0, "1": 1.15, "2": 1.15, "3": 1.30},
        "B": {"0": 1.0, "1": 1.15, "2": 1.15, "3": 1.30},
        "C": {"0": 1.0, "1": 1.10, "2": 1.10, "3": 1.20},
    },
    "complexity_multipliers": {
        "A": {"low": 0.8, "medium": 1.0, "high": 1.25, "very_high": 1.50},
        "B": {"low": 0.8, "medium": 1.0, "high": 1.25, "very_high": 1.50},
        "C": {"low": 0.85, "medium": 1.0, "high": 1.20, "very_high": 1.40},
    },
    "reuse_multipliers": {
        "A": [1.0, 0.7, 0.5, 0.4],
        "B": [1.0, 0.7, 0.5, 0.4],
        "C": [1.0, 0.7, 0.5, 0.4],
    },
    "analysis_pct": {
        "A": {"low": 0.18, "medium": 0.18, "high": 0.24, "very_high": 0.30},
        "B": {"low": 0.15, "medium": 0.15, "high": 0.20, "very_high": 0.25},
        "C": {"low": 0.15, "medium": 0.15, "high": 0.18, "very_high": 0.22},
    },
    "design_pct": {"A": 0.20, "B": 0.18, "C": 0.15},
    "architecture_pct": {"A": 0.10, "B": 0.08, "C": 0.08},
    "test_pct": {
        "A": {"low": 0.24, "medium": 0.30, "high": 0.36, "very_high": 0.42},
        "B": {"low": 0.20, "medium": 0.25, "high": 0.30, "very_high": 0.35},
        "C": {"low": 0.18, "medium": 0.22, "high": 0.28, "very_high": 0.35},
    },
    "size_bands": [[20, "S"], [60, "M"], [120, "L"], [1e18, "XL"]],
    "fixed_bases": {
        "S": {"PM_Base": 1, "BA_Base": 1, "Test_Base": 1, "UAT_Base": 2},
        "M": {"PM_Base": 2, "BA_Base": 2, "Test_Base": 2, "UAT_Base": 3},
        "L": {"PM_Base": 3, "BA_Base": 3, "Test_Base": 3, "UAT_Base": 4},
        "XL": {"PM_Base": 4, "BA_Base": 4, "Test_Base": 4, "UAT_Base": 5},
    },
    "global_formulas": {
        "A": {"pm_pct": 0.09, "tech_design_pct": 0.04, "deployment_pct": 0.03, "uat_pct": 0.30},
        "B": {"pm_pct": 0.07, "tech_design_pct": 0.02, "deployment_pct": 0.02, "uat_pct": 0.20},
        "C": {"pm_pct": 0.06, "tech_design_pct": 0.02, "deployment_pct": 0.02, "uat_pct": 0.20},
    },
    "min_max_ranges": {
        "low": [0.90, 1.10], "medium": [0.85, 1.15],
        "high": [0.80, 1.25], "very_high": [0.70, 1.40],
    },
    "oneframe_residual": {
        "A": {
            "OF-AUTH": [0.0, 1.0], "OF-AUTHZ": [0.0, 1.0], "OF-CRUD": [0.0, 0.5],
            "OF-DATA": [0.0, 0.5], "OF-AUDIT": [0.0, 0.5], "OF-CACHE": [0.0, 0.3],
            "OF-SEARCH": [0.0, 0.5], "OF-MULTI": [0.0, 0.5], "OF-CICD": [0.0, 0.0],
            "OF-CLOUD": [0.0, 0.0], "OF-UI": [0.1, 0.0], "OF-FORM": [0.1, 0.1],
            "OF-TABLE": [0.1, 0.1], "OF-MENU": [0.1, 0.1], "OF-DASH": [0.2, 0.2],
            "OF-PROFILE": [0.1, 0.2], "OF-REPORT": [0.2, 0.3], "OF-NOTIF": [0.0, 0.5],
            "OF-HANGFIRE": [0.0, 0.3], "OF-RULE": [0.0, 0.5], "OF-WORKFLOW": [0.0, 0.5],
            "OF-DMS": [0.1, 0.3], "OF-FILE": [0.0, 0.3], "OF-UPLOAD": [0.1, 0.1],
            "OF-CMS": [0.1, 0.3], "OF-FAQ": [0.1, 0.2], "OF-VALID": [0.0, 0.3],
            "OF-I18N": [0.1, 0.2], "OF-ERR": [0.0, 0.2], "OF-CHATBOT": [0.1, 0.3],
            "OF-APIGW": [0.0, 0.3], "OF-SIGNAL": [0.1, 0.3],
        },
        "B": {
            "OF-AUTH": [0.0, 0.80], "OF-AUTHZ": [0.0, 0.80], "OF-RULE": [0.0, 0.40],
            "OF-WORKFLOW": [0.0, 0.40], "OF-APIGW": [0.0, 0.24], "OF-SIGNAL": [0.08, 0.24],
            "OF-VALID": [0.0, 0.24], "OF-DATA": [0.0, 0.35], "OF-AUDIT": [0.0, 0.35],
            "OF-CACHE": [0.0, 0.21], "OF-SEARCH": [0.0, 0.35], "OF-MULTI": [0.0, 0.35],
            "OF-DASH": [0.14, 0.14], "OF-PROFILE": [0.07, 0.14], "OF-REPORT": [0.14, 0.21],
            "OF-NOTIF": [0.0, 0.35], "OF-HANGFIRE": [0.0, 0.21], "OF-DMS": [0.07, 0.21],
            "OF-FILE": [0.0, 0.21], "OF-CMS": [0.07, 0.21], "OF-CHATBOT": [0.07, 0.21],
            "OF-CRUD": [0.0, 0.28], "OF-UI": [0.06, 0.0], "OF-FORM": [0.06, 0.06],
            "OF-TABLE": [0.06, 0.06], "OF-MENU": [0.06, 0.06], "OF-UPLOAD": [0.06, 0.06],
            "OF-FAQ": [0.06, 0.11], "OF-I18N": [0.06, 0.11], "OF-ERR": [0.0, 0.11],
            "OF-CICD": [0.0, 0.0], "OF-CLOUD": [0.0, 0.0],
        },
        "C": {
            "OF-AUTH": [0.0, 0.70], "OF-AUTHZ": [0.0, 0.70], "OF-RULE": [0.0, 0.35],
            "OF-WORKFLOW": [0.0, 0.35], "OF-APIGW": [0.0, 0.21], "OF-SIGNAL": [0.07, 0.21],
            "OF-VALID": [0.0, 0.21], "OF-DATA": [0.0, 0.25], "OF-AUDIT": [0.0, 0.25],
            "OF-CACHE": [0.0, 0.15], "OF-SEARCH": [0.0, 0.25], "OF-MULTI": [0.0, 0.25],
            "OF-DASH": [0.10, 0.10], "OF-PROFILE": [0.05, 0.10], "OF-REPORT": [0.10, 0.15],
            "OF-NOTIF": [0.0, 0.25], "OF-HANGFIRE": [0.0, 0.15], "OF-DMS": [0.05, 0.15],
            "OF-FILE": [0.0, 0.15], "OF-CMS": [0.05, 0.15], "OF-CHATBOT": [0.05, 0.15],
            "OF-CRUD": [0.0, 0.15], "OF-UI": [0.03, 0.0], "OF-FORM": [0.03, 0.03],
            "OF-TABLE": [0.03, 0.03], "OF-MENU": [0.03, 0.03], "OF-UPLOAD": [0.03, 0.03],
            "OF-FAQ": [0.03, 0.06], "OF-I18N": [0.03, 0.06], "OF-ERR": [0.0, 0.06],
            "OF-CICD": [0.0, 0.00], "OF-CLOUD": [0.0, 0.00],
        },
    },
    "context_multipliers": {
        "scale": {
            "kucuk": {"AB": 0.85, "C": 0.90}, "orta": {"AB": 1.00, "C": 1.00},
            "buyuk": {"AB": 1.20, "C": 1.10}, "enterprise": {"AB": 1.40, "C": 1.15},
        },
        "team": {
            "junior": {"AB": 1.30, "C": 1.15}, "mid": {"AB": 1.00, "C": 1.00},
            "senior": {"AB": 0.85, "C": 0.95}, "expert": {"AB": 0.75, "C": 0.90},
        },
        "domain": {
            "standart": {"AB": 1.00, "C": 1.00}, "finans": {"AB": 1.15, "C": 1.08},
            "regulasyon": {"AB": 1.25, "C": 1.12}, "saglik": {"AB": 1.30, "C": 1.15},
            "kritik": {"AB": 1.40, "C": 1.18},
        },
        "tech_debt": {
            "greenfield": {"AB": 1.00, "C": 1.00}, "ekleme": {"AB": 1.10, "C": 1.05},
            "legacy_ent": {"AB": 1.25, "C": 1.10}, "legacy_mod": {"AB": 1.40, "C": 1.15},
        },
        "integration_density": {
            "0-2": {"AB": 1.00, "C": 1.00}, "3-4": {"AB": 1.05, "C": 1.05},
            "5-7": {"AB": 1.10, "C": 1.10}, "8+": {"AB": 1.15, "C": 1.15},
        },
    },
    "vibe_context_cap": 1.35,
    "minimum_effort": {
        "deliverable": {"A": 0.5, "B": 0.3, "C": 0.2},
        "wp": {"A": 1.5, "B": 1.0, "C": 0.8},
        "phase": {"A": 0.5, "B": 0.3, "C": 0.2},
    },
    "rounding_precision": {"A": 0.5, "B": 0.1, "C": 0.1},
}


def load_params() -> dict:
    """JSON config dosyasindan parametreleri oku. Yoksa/bozuksa default dondur."""
    if not CONFIG_PATH.exists():
        return copy.deepcopy(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # _meta anahtarini cikar
        data.pop("_meta", None)
        # Eksik anahtarlari defaults'tan tamamla
        merged = copy.deepcopy(DEFAULTS)
        for key in DEFAULTS:
            if key in data:
                merged[key] = data[key]
        return merged
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(DEFAULTS)


def save_params(params: dict) -> list[str]:
    """Parametreleri JSON'a kaydet. Hata varsa hata listesi dondur, yoksa bos liste."""
    errors = validate_params(params)
    if errors:
        return errors

    data = copy.deepcopy(params)
    data["_meta"] = {
        "version": "1.0",
        "description": "Efor hesaplama parametre dosyasi.",
        "last_modified": datetime.now().isoformat(),
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return []


def get_defaults() -> dict:
    """Varsayilan degerlerin kopyasini dondur."""
    return copy.deepcopy(DEFAULTS)


def reset_to_defaults() -> None:
    """Config dosyasini varsayilanlara sifirla."""
    save_params(DEFAULTS)


def validate_params(params: dict) -> list[str]:
    """Parametre yapisini ve deger araliklarini kontrol et."""
    errors = []
    required_keys = [
        "base_effort", "batch_multipliers", "integration_multipliers",
        "complexity_multipliers", "reuse_multipliers", "analysis_pct",
        "design_pct", "architecture_pct", "test_pct", "size_bands",
        "fixed_bases", "global_formulas", "min_max_ranges",
        "oneframe_residual", "context_multipliers", "vibe_context_cap",
        "minimum_effort", "rounding_precision",
    ]
    for key in required_keys:
        if key not in params:
            errors.append(f"Eksik anahtar: {key}")

    if errors:
        return errors

    profiles = ["A", "B", "C"]
    categories = [
        "SIMPLE_UI", "COMPLEX_UI", "FILE_PROCESS", "EXPORT_REPORT",
        "BACKGROUND_JOB", "INTEGRATION", "RULE_ENGINE", "AUTH_COMPONENT",
    ]

    # base_effort kontrol
    for p in profiles:
        if p not in params.get("base_effort", {}):
            errors.append(f"base_effort icinde '{p}' profili eksik")
            continue
        for cat in categories:
            val = params["base_effort"][p].get(cat)
            if val is None:
                errors.append(f"base_effort[{p}][{cat}] eksik")
            elif not isinstance(val, list) or len(val) != 2:
                errors.append(f"base_effort[{p}][{cat}] [FE, BE] formatinda olmali")

    # Skaler deger kontrolleri
    if not isinstance(params.get("vibe_context_cap"), (int, float)):
        errors.append("vibe_context_cap sayisal olmali")
    elif params["vibe_context_cap"] <= 0:
        errors.append("vibe_context_cap pozitif olmali")

    return errors


def snapshot_params() -> dict:
    """Mevcut parametrelerin deep copy'sini dondur (hesaplama snapshot'i icin)."""
    return load_params()


def merge_params(base: dict, overrides: dict) -> dict:
    """Deep merge — overrides'taki degerler base'in ustune yazilir.
    Sadece yaprak degerleri override eder, ara dict'leri recursive birlestirir.
    """
    result = copy.deepcopy(base)

    def _merge(target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                _merge(target[key], value)
            else:
                target[key] = copy.deepcopy(value)

    _merge(result, overrides)
    return result


def extract_overrides(params: dict, base: dict | None = None) -> dict:
    """Sadece base'den farkli olan degerleri sparse dict olarak cikarir.
    base verilmezse global config (disk) kullanilir.
    """
    if base is None:
        base = load_params()
    overrides = {}

    def _extract(current, default, target):
        if isinstance(default, dict) and isinstance(current, dict):
            for key in current:
                if key not in default:
                    target[key] = copy.deepcopy(current[key])
                else:
                    sub = {}
                    _extract(current[key], default[key], sub)
                    if sub:
                        target[key] = sub
        elif current != default:
            # Yaprak deger farkli — olduğu gibi kopyala (parent dict'e yazilir)
            pass  # Bu durumda parent dict seviyesinde handle edilir

    def _extract_full(current, default):
        result = {}
        if isinstance(default, dict) and isinstance(current, dict):
            for key in current:
                if key not in default:
                    result[key] = copy.deepcopy(current[key])
                elif isinstance(default[key], dict) and isinstance(current[key], dict):
                    sub = _extract_full(current[key], default[key])
                    if sub:
                        result[key] = sub
                elif current[key] != default[key]:
                    result[key] = copy.deepcopy(current[key])
        return result

    return _extract_full(params, base)


def diff_from_defaults(params: dict) -> dict:
    """Mevcut parametreleri varsayilanlarla karsilastir, farklari dondur."""
    diffs = {}
    defaults = DEFAULTS

    def _compare(current, default, path=""):
        if isinstance(default, dict):
            for key in default:
                _compare(
                    current.get(key) if isinstance(current, dict) else None,
                    default[key],
                    f"{path}.{key}" if path else key,
                )
        elif isinstance(default, list):
            if current != default:
                diffs[path] = {"varsayilan": default, "mevcut": current}
        else:
            if current != default:
                diffs[path] = {"varsayilan": default, "mevcut": current}

    _compare(params, defaults)
    return diffs
