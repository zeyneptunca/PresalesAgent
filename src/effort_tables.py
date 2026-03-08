"""Karar agaci v12'den cikartilan tum sabit degerler ve tablolar.
Degerler config/effort_params.json dosyasindan yuklenir.
Parametreler degistirildiginde reload_tables() cagrilarak guncellenir.
"""

from src.param_manager import load_params


def _load(params=None):
    """JSON'dan parametreleri oku ve modul-seviyesi sabitleri guncelle.
    params verilirse diskten okumak yerine verilen dict kullanilir."""
    p = params if params is not None else load_params()
    g = globals()

    # Bolum 2: Baz efor degerleri — JSON array → tuple
    g["BASE_EFFORT"] = {
        profile: {cat: tuple(vals) for cat, vals in cats.items()}
        for profile, cats in p["base_effort"].items()
    }

    # Bolum 3.1: Batch carpanlari
    g["BATCH_MULTIPLIERS"] = p["batch_multipliers"]

    # Bolum 3.2: Entegrasyon carpani — JSON string keys → int keys
    g["INTEGRATION_MULTIPLIERS"] = {
        profile: {int(k): v for k, v in table.items()}
        for profile, table in p["integration_multipliers"].items()
    }

    # Bolum 3.3: Kompleksite carpani
    g["COMPLEXITY_MULTIPLIERS"] = p["complexity_multipliers"]

    # Bolum 3.4: Reuse carpanlari
    g["REUSE_MULTIPLIERS"] = p["reuse_multipliers"]

    # Bolum 4: Faz hesaplama yuzdeleri
    g["ANALYSIS_PCT"] = p["analysis_pct"]
    g["DESIGN_PCT"] = p["design_pct"]
    g["ARCHITECTURE_PCT"] = p["architecture_pct"]
    g["TEST_PCT"] = p["test_pct"]

    # Bolum 5: Global efor formulleri
    g["SIZE_BANDS"] = [(threshold, band) for threshold, band in p["size_bands"]]
    g["FIXED_BASES"] = p["fixed_bases"]
    g["GLOBAL_FORMULAS"] = p["global_formulas"]

    # Bolum 6: Min-max araligi — JSON array → tuple
    g["MIN_MAX_RANGES"] = {
        level: tuple(vals) for level, vals in p["min_max_ranges"].items()
    }

    # Bolum 10: OneFrame residuel — JSON array → tuple
    g["ONEFRAME_RESIDUAL"] = {
        profile: {of_code: tuple(vals) for of_code, vals in codes.items()}
        for profile, codes in p["oneframe_residual"].items()
    }

    # Bolum 11: Baglam carpanlari
    g["CONTEXT_MULTIPLIERS"] = p["context_multipliers"]
    g["VIBE_CONTEXT_CAP"] = p["vibe_context_cap"]

    # Bolum 12: Minimum efor korumasi
    g["MINIMUM_EFFORT"] = p["minimum_effort"]
    g["ROUNDING_PRECISION"] = p["rounding_precision"]


# Modul yuklendiginde config'den oku
_load()


def reload_tables(params=None):
    """Config dosyasi degistikten sonra tablolari tekrar yukle.
    params verilirse diskten okumak yerine verilen dict kullanilir
    (ornegin global + proje override birlestirilmis params)."""
    _load(params)


def get_integration_multiplier(profile: str, point_count: int) -> float:
    """Entegrasyon noktasi sayisina gore carpan dondur."""
    table = INTEGRATION_MULTIPLIERS[profile]
    if point_count == 0:
        return table[0]
    elif point_count <= 2:
        return table[1]
    else:
        return table[3]


def get_size_band(technical_total: float) -> str:
    """Teknik toplama gore proje buyukluk bandini dondur."""
    for threshold, band in SIZE_BANDS:
        if technical_total <= threshold:
            return band
    return "XL"


def round_effort(value: float, profile: str) -> float:
    """Profil bazli yuvarlama."""
    precision = ROUNDING_PRECISION[profile]
    return round(value / precision) * precision
