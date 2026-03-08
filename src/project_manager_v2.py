"""Versiyonlu proje yonetimi — WBS versiyonlari, hesaplama gecmisi, parametre snapshot'lari."""

import copy
import json
import shutil
import streamlit as st
from datetime import datetime
from pathlib import Path

PROJECTS_DIR = Path("projects")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now().isoformat()


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_slug(name: str, max_len: int = 30) -> str:
    safe = name.lower().replace(" ", "_")
    safe = "".join(c for c in safe if c.isalnum() or c == "_")[:max_len] or "proje"
    return safe


# ── Project CRUD ────────────────────────────────────────────────────────────

def create_project(name: str, description: str = "") -> str:
    """Yeni proje olustur, project_id dondur."""
    project_id = f"{_safe_slug(name)}_{_now_ts()}"
    proj_dir = PROJECTS_DIR / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "scope").mkdir(exist_ok=True)
    (proj_dir / "wbs").mkdir(exist_ok=True)
    (proj_dir / "calculations").mkdir(exist_ok=True)

    meta = {
        "project_id": project_id,
        "project_name": name,
        "project_description": description,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "scope": None,
        "wbs_versions": [],
        "active_wbs_version": None,
        "calculations": [],
        "active_calc_id": None,
        "wizard_state": {
            "current_step": "scope",
            "chat_messages": [],
        },
    }
    _save_meta(project_id, meta)
    list_projects.clear()
    return project_id


def _save_meta(project_id: str, meta: dict) -> None:
    """project.json'i diske yaz."""
    meta["updated_at"] = _now_iso()
    filepath = PROJECTS_DIR / project_id / "project.json"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)


def load_meta(project_id: str) -> dict | None:
    """project.json oku. Yoksa eski formattan migrate etmeyi dene."""
    filepath = PROJECTS_DIR / project_id / "project.json"
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    # Eski format varsa migrate et
    old_file = PROJECTS_DIR / project_id / "project_state.json"
    if old_file.exists():
        meta = _migrate_project(project_id)
        return meta

    return None


def save_meta(project_id: str, meta: dict) -> None:
    """project.json'i guncelle."""
    _save_meta(project_id, meta)
    list_projects.clear()


def save_project_params(project_id: str, overrides: dict) -> None:
    """Projeye ozel parametre override'larini project.json'a kaydet."""
    meta = load_meta(project_id)
    if not meta:
        return
    meta["params_overrides"] = overrides
    save_meta(project_id, meta)


def load_project_params_overrides(project_id: str) -> dict | None:
    """project.json'dan parametre override'larini oku. Yoksa None."""
    meta = load_meta(project_id)
    if not meta:
        return None
    return meta.get("params_overrides")


def clear_project_params(project_id: str) -> None:
    """Projeye ozel parametre override'larini temizle."""
    meta = load_meta(project_id)
    if not meta:
        return
    meta.pop("params_overrides", None)
    save_meta(project_id, meta)


@st.cache_data(ttl=15)
def list_projects() -> list[dict]:
    """Tum projeleri tara, ozet bilgi dondur (son guncellemeye gore sirali)."""
    PROJECTS_DIR.mkdir(exist_ok=True)
    projects = []

    for proj_dir in PROJECTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        # Yeni format
        meta_file = proj_dir / "project.json"
        old_file = proj_dir / "project_state.json"
        if not meta_file.exists() and not old_file.exists():
            continue

        meta = load_meta(proj_dir.name)
        if not meta:
            continue

        # Son hesaplama sonuclari
        calcs = meta.get("calculations", [])
        latest_calc = calcs[-1] if calcs else None

        projects.append({
            "project_id": meta.get("project_id", proj_dir.name),
            "project_name": meta.get("project_name", proj_dir.name),
            "project_description": meta.get("project_description", ""),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
            "scope": meta.get("scope"),
            "wbs_version_count": len(meta.get("wbs_versions", [])),
            "active_wbs_version": meta.get("active_wbs_version"),
            "calc_count": len(calcs),
            "latest_a": latest_calc["a_total"] if latest_calc else None,
            "latest_b": latest_calc["b_total"] if latest_calc else None,
            "latest_c": latest_calc["c_total"] if latest_calc else None,
            "latest_band": latest_calc.get("band") if latest_calc else None,
            "module_count": latest_calc.get("module_count", 0) if latest_calc else _get_wbs_counts(meta)[0],
            "wp_count": latest_calc.get("wp_count", 0) if latest_calc else _get_wbs_counts(meta)[1],
            "current_step": meta.get("wizard_state", {}).get("current_step", "scope"),
        })

    projects.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return projects


def _get_wbs_counts(meta: dict) -> tuple[int, int]:
    """Meta'dan aktif WBS'in modul/WP sayisini dondur."""
    versions = meta.get("wbs_versions", [])
    if not versions:
        return (0, 0)
    active = meta.get("active_wbs_version")
    for v in versions:
        if v["version"] == active:
            return (v.get("module_count", 0), v.get("wp_count", 0))
    last = versions[-1]
    return (last.get("module_count", 0), last.get("wp_count", 0))


def delete_project(project_id: str) -> bool:
    """Proje klasorunu sil."""
    proj_dir = PROJECTS_DIR / project_id
    if proj_dir.exists() and proj_dir.is_dir():
        shutil.rmtree(proj_dir)
        list_projects.clear()
        return True
    return False


# ── Scope ───────────────────────────────────────────────────────────────────

def save_scope(project_id: str, pdf_bytes: bytes, extracted_text: str,
               pdf_filename: str, pages: int, words: int) -> None:
    """Scope dokümanini kaydet (PDF + metin)."""
    scope_dir = PROJECTS_DIR / project_id / "scope"
    scope_dir.mkdir(parents=True, exist_ok=True)

    # PDF'i kaydet
    pdf_path = scope_dir / "source.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Metni kaydet
    text_path = scope_dir / "extracted_text.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    # Meta guncelle
    meta = load_meta(project_id)
    if meta:
        meta["scope"] = {
            "pdf_filename": pdf_filename,
            "pdf_pages": pages,
            "pdf_words": words,
            "uploaded_at": _now_iso(),
        }
        save_meta(project_id, meta)


def load_scope_text(project_id: str) -> str | None:
    """Kaydedilmis scope metnini oku."""
    text_path = PROJECTS_DIR / project_id / "scope" / "extracted_text.txt"
    if text_path.exists():
        return text_path.read_text(encoding="utf-8")
    return None


# ── WBS Versioning ──────────────────────────────────────────────────────────

def save_wbs_version(project_id: str, wbs: dict, source: str = "generated",
                     note: str = "") -> str:
    """Yeni WBS versiyonu kaydet. Versiyon adini dondur (orn: 'v1')."""
    meta = load_meta(project_id)
    if not meta:
        raise ValueError(f"Proje bulunamadi: {project_id}")

    # Versiyon numarasi
    existing = meta.get("wbs_versions", [])
    version_num = len(existing) + 1
    version = f"v{version_num}"

    # WBS dosyasini kaydet
    wbs_dir = PROJECTS_DIR / project_id / "wbs"
    wbs_dir.mkdir(parents=True, exist_ok=True)
    wbs_path = wbs_dir / f"{version}.json"
    with open(wbs_path, "w", encoding="utf-8") as f:
        json.dump(wbs, f, ensure_ascii=False, indent=2)

    # Modul/WP sayilarini hesapla
    modules = wbs.get("wbs", {}).get("modules", [])
    module_count = len(modules)
    wp_count = sum(len(m.get("work_packages", [])) for m in modules)

    # Meta guncelle
    meta.setdefault("wbs_versions", []).append({
        "version": version,
        "created_at": _now_iso(),
        "source": source,
        "module_count": module_count,
        "wp_count": wp_count,
        "note": note or f"WBS {version}",
    })
    meta["active_wbs_version"] = version
    save_meta(project_id, meta)

    # Ayrica global wbs/ dizinine de kaydet (legacy uyumluluk)
    global_wbs_dir = Path("wbs")
    global_wbs_dir.mkdir(exist_ok=True)
    project_name = wbs.get("project_scope_summary", {}).get("project_name", "proje")
    safe_name = _safe_slug(project_name, 50) or "proje"
    global_path = global_wbs_dir / f"{safe_name}.json"
    with open(global_path, "w", encoding="utf-8") as f:
        json.dump(wbs, f, ensure_ascii=False, indent=2)

    return version


def update_active_wbs(project_id: str, wbs: dict) -> str:
    """Aktif WBS versiyonunu guncelle (in-place). Eger bu versiyon bir hesaplamada
    kullanildiysa yeni versiyon olustur. Versiyon adini dondur."""
    meta = load_meta(project_id)
    if not meta:
        raise ValueError(f"Proje bulunamadi: {project_id}")

    active_version = meta.get("active_wbs_version")
    if not active_version:
        # Henuz WBS yok, ilk versiyonu olustur
        return save_wbs_version(project_id, wbs, source="edited")

    # Bu versiyon bir hesaplamada kullanildi mi?
    calcs = meta.get("calculations", [])
    version_used = any(c.get("wbs_version") == active_version for c in calcs)

    if version_used:
        # Yeni versiyon olustur
        return save_wbs_version(project_id, wbs, source="edited",
                                note=f"{active_version} uzerinden duzenlendi")
    else:
        # In-place guncelle
        wbs_path = PROJECTS_DIR / project_id / "wbs" / f"{active_version}.json"
        with open(wbs_path, "w", encoding="utf-8") as f:
            json.dump(wbs, f, ensure_ascii=False, indent=2)

        # Meta'daki sayilari guncelle
        modules = wbs.get("wbs", {}).get("modules", [])
        for v in meta.get("wbs_versions", []):
            if v["version"] == active_version:
                v["module_count"] = len(modules)
                v["wp_count"] = sum(len(m.get("work_packages", [])) for m in modules)
                break
        save_meta(project_id, meta)
        return active_version


def load_wbs(project_id: str, version: str | None = None) -> dict | None:
    """WBS versiyonunu oku. version=None ise aktif versiyonu yukle."""
    meta = load_meta(project_id)
    if not meta:
        return None

    if version is None:
        version = meta.get("active_wbs_version")
    if not version:
        return None

    wbs_path = PROJECTS_DIR / project_id / "wbs" / f"{version}.json"
    if not wbs_path.exists():
        return None

    try:
        with open(wbs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def list_wbs_versions(project_id: str) -> list[dict]:
    """Tum WBS versiyonlarini listele."""
    meta = load_meta(project_id)
    if not meta:
        return []
    return meta.get("wbs_versions", [])


# ── Calculations ────────────────────────────────────────────────────────────

def save_calculation(project_id: str, wbs_version: str,
                     effort_result: dict, categories: dict,
                     context: dict, params: dict) -> str:
    """Hesaplama sonucunu kaydet. calc_id dondur."""
    meta = load_meta(project_id)
    if not meta:
        raise ValueError(f"Proje bulunamadi: {project_id}")

    calc_id = f"calc_{_now_ts()}"
    calc_dir = PROJECTS_DIR / project_id / "calculations" / calc_id
    calc_dir.mkdir(parents=True, exist_ok=True)
    (calc_dir / "exports").mkdir(exist_ok=True)

    # WBS versiyon pointer
    (calc_dir / "wbs_version.txt").write_text(wbs_version, encoding="utf-8")

    # Kategorileri kaydet
    with open(calc_dir / "categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2, default=str)

    # Context kaydet
    with open(calc_dir / "context.json", "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    # Parametre snapshot
    with open(calc_dir / "effort_params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    # Hesaplama sonucu
    with open(calc_dir / "effort_result.json", "w", encoding="utf-8") as f:
        json.dump(effort_result, f, ensure_ascii=False, indent=2, default=str)

    # Meta guncelle
    proje_toplami = effort_result.get("proje_toplami", {})
    a_total = proje_toplami.get("a", {}).get("toplam", 0)
    b_total = proje_toplami.get("b", {}).get("toplam", 0)
    c_total = proje_toplami.get("c", {}).get("toplam", 0)
    band = effort_result.get("tahmin_ozeti", {}).get("proje_bandi", "")

    # Modul/WP sayisi
    wbs = load_wbs(project_id, wbs_version)
    module_count = 0
    wp_count = 0
    if wbs:
        modules = wbs.get("wbs", {}).get("modules", [])
        module_count = len(modules)
        wp_count = sum(len(m.get("work_packages", [])) for m in modules)

    meta.setdefault("calculations", []).append({
        "calc_id": calc_id,
        "created_at": _now_iso(),
        "wbs_version": wbs_version,
        "a_total": a_total,
        "b_total": b_total,
        "c_total": c_total,
        "band": band,
        "module_count": module_count,
        "wp_count": wp_count,
    })
    meta["active_calc_id"] = calc_id
    save_meta(project_id, meta)

    return calc_id


def load_calculation(project_id: str, calc_id: str) -> dict | None:
    """Hesaplama sonucunu ve ilisikli verileri yukle."""
    calc_dir = PROJECTS_DIR / project_id / "calculations" / calc_id
    if not calc_dir.exists():
        return None

    result = {"calc_id": calc_id}

    # Effort result
    ef_path = calc_dir / "effort_result.json"
    if ef_path.exists():
        with open(ef_path, "r", encoding="utf-8") as f:
            result["effort_result"] = json.load(f)

    # Categories
    cat_path = calc_dir / "categories.json"
    if cat_path.exists():
        with open(cat_path, "r", encoding="utf-8") as f:
            result["categories"] = json.load(f)

    # Context
    ctx_path = calc_dir / "context.json"
    if ctx_path.exists():
        with open(ctx_path, "r", encoding="utf-8") as f:
            result["context"] = json.load(f)

    # Params
    params_path = calc_dir / "effort_params.json"
    if params_path.exists():
        with open(params_path, "r", encoding="utf-8") as f:
            result["params"] = json.load(f)

    # WBS version
    ver_path = calc_dir / "wbs_version.txt"
    if ver_path.exists():
        result["wbs_version"] = ver_path.read_text(encoding="utf-8").strip()

    # Exports path
    result["exports_dir"] = str(calc_dir / "exports")

    return result


def load_latest_calculation(project_id: str) -> dict | None:
    """En son hesaplamayi yukle."""
    meta = load_meta(project_id)
    if not meta:
        return None
    calc_id = meta.get("active_calc_id")
    if not calc_id:
        return None
    return load_calculation(project_id, calc_id)


def list_calculations(project_id: str) -> list[dict]:
    """Tum hesaplamalari listele (meta'dan)."""
    meta = load_meta(project_id)
    if not meta:
        return []
    return meta.get("calculations", [])


def get_calc_exports_dir(project_id: str, calc_id: str) -> Path:
    """Hesaplama exports dizinini dondur."""
    return PROJECTS_DIR / project_id / "calculations" / calc_id / "exports"


def delete_calculation(project_id: str, calc_id: str) -> bool:
    """Hesaplamayi sil (dosyalar + meta'dan cikar). Basarili ise True dondur."""
    import shutil

    meta = load_meta(project_id)
    if not meta:
        return False

    # Meta'dan cikar
    calcs = meta.get("calculations", [])
    new_calcs = [c for c in calcs if c.get("calc_id") != calc_id]
    if len(new_calcs) == len(calcs):
        return False  # bulunamadi

    meta["calculations"] = new_calcs

    # Active calc_id guncelle
    if meta.get("active_calc_id") == calc_id:
        if new_calcs:
            meta["active_calc_id"] = new_calcs[-1]["calc_id"]
        else:
            meta["active_calc_id"] = None

    save_meta(project_id, meta)

    # Dosyalari sil
    calc_dir = PROJECTS_DIR / project_id / "calculations" / calc_id
    if calc_dir.exists():
        shutil.rmtree(calc_dir, ignore_errors=True)

    # Cache temizle
    list_projects.clear()
    return True


# ── Wizard State ────────────────────────────────────────────────────────────

def save_wizard_state(project_id: str, step: str, chat_messages: list | None = None) -> None:
    """Wizard adimini kaydet."""
    meta = load_meta(project_id)
    if not meta:
        return
    meta.setdefault("wizard_state", {})["current_step"] = step
    if chat_messages is not None:
        meta["wizard_state"]["chat_messages"] = chat_messages
    save_meta(project_id, meta)


def load_wizard_state(project_id: str) -> dict:
    """Wizard state yukle."""
    meta = load_meta(project_id)
    if not meta:
        return {"current_step": "scope", "chat_messages": []}
    return meta.get("wizard_state", {"current_step": "scope", "chat_messages": []})


# ── Migration ───────────────────────────────────────────────────────────────

def _migrate_project(project_id: str) -> dict | None:
    """Eski project_state.json formatindan yeni formata migrasyon."""
    old_file = PROJECTS_DIR / project_id / "project_state.json"
    if not old_file.exists():
        return None

    try:
        with open(old_file, "r", encoding="utf-8") as f:
            old_state = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    old_meta = old_state.get("meta", {})

    # Yeni meta olustur
    meta = {
        "project_id": project_id,
        "project_name": old_meta.get("project_name", project_id),
        "project_description": old_meta.get("project_description", ""),
        "created_at": old_meta.get("created_at", _now_iso()),
        "updated_at": old_meta.get("updated_at", _now_iso()),
        "scope": None,
        "wbs_versions": [],
        "active_wbs_version": None,
        "calculations": [],
        "active_calc_id": None,
        "wizard_state": {
            "current_step": old_meta.get("current_step", "scope"),
            "chat_messages": old_state.get("chat_messages", []),
        },
    }

    proj_dir = PROJECTS_DIR / project_id
    (proj_dir / "scope").mkdir(exist_ok=True)
    (proj_dir / "wbs").mkdir(exist_ok=True)
    (proj_dir / "calculations").mkdir(exist_ok=True)

    # PDF text varsa scope olarak kaydet
    pdf_text = old_state.get("pdf_text")
    if pdf_text:
        text_path = proj_dir / "scope" / "extracted_text.txt"
        text_path.write_text(pdf_text, encoding="utf-8")

    # WBS varsa v1 olarak kaydet
    wbs = old_state.get("wbs")
    if wbs and isinstance(wbs, dict):
        wbs_path = proj_dir / "wbs" / "v1.json"
        with open(wbs_path, "w", encoding="utf-8") as f:
            json.dump(wbs, f, ensure_ascii=False, indent=2)

        modules = wbs.get("wbs", {}).get("modules", [])
        module_count = len(modules)
        wp_count = sum(len(m.get("work_packages", [])) for m in modules)

        meta["wbs_versions"].append({
            "version": "v1",
            "created_at": old_meta.get("created_at", _now_iso()),
            "source": "migrated",
            "module_count": module_count,
            "wp_count": wp_count,
            "note": "Eski formattan migrasyon",
        })
        meta["active_wbs_version"] = "v1"

    # Effort result varsa hesaplama olarak kaydet
    effort_result = old_state.get("effort_result")
    if effort_result and isinstance(effort_result, dict):
        ts = old_meta.get("updated_at", _now_iso())
        # Timestamp'ten calc_id olustur
        try:
            dt = datetime.fromisoformat(ts)
            calc_ts = dt.strftime("%Y%m%d_%H%M%S")
        except (ValueError, TypeError):
            calc_ts = _now_ts()

        calc_id = f"calc_{calc_ts}"
        calc_dir = proj_dir / "calculations" / calc_id
        calc_dir.mkdir(parents=True, exist_ok=True)
        (calc_dir / "exports").mkdir(exist_ok=True)

        # WBS version pointer
        wbs_ver = "v1" if meta["active_wbs_version"] else "unknown"
        (calc_dir / "wbs_version.txt").write_text(wbs_ver, encoding="utf-8")

        # Effort result
        with open(calc_dir / "effort_result.json", "w", encoding="utf-8") as f:
            json.dump(effort_result, f, ensure_ascii=False, indent=2, default=str)

        # Categories
        categories = old_state.get("categories")
        if categories:
            with open(calc_dir / "categories.json", "w", encoding="utf-8") as f:
                json.dump(categories, f, ensure_ascii=False, indent=2, default=str)

        # Context
        context = old_state.get("project_context")
        if context:
            with open(calc_dir / "context.json", "w", encoding="utf-8") as f:
                json.dump(context, f, ensure_ascii=False, indent=2)

        # Mevcut params snapshot (eski veriden alinmiyor, current defaults kullanilir)
        from src.param_manager import load_params
        params = load_params()
        with open(calc_dir / "effort_params.json", "w", encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False, indent=2)

        # Meta'ya hesaplama ekle
        proje_toplami = effort_result.get("proje_toplami", {})
        meta["calculations"].append({
            "calc_id": calc_id,
            "created_at": ts,
            "wbs_version": wbs_ver,
            "a_total": proje_toplami.get("a", {}).get("toplam", 0),
            "b_total": proje_toplami.get("b", {}).get("toplam", 0),
            "c_total": proje_toplami.get("c", {}).get("toplam", 0),
            "band": effort_result.get("tahmin_ozeti", {}).get("proje_bandi", ""),
            "module_count": meta["wbs_versions"][-1]["module_count"] if meta["wbs_versions"] else 0,
            "wp_count": meta["wbs_versions"][-1]["wp_count"] if meta["wbs_versions"] else 0,
        })
        meta["active_calc_id"] = calc_id

    # Yeni meta kaydet
    _save_meta(project_id, meta)

    # Eski dosyayi yedekle
    backup_path = old_file.with_suffix(".json.bak")
    if not backup_path.exists():
        shutil.copy2(old_file, backup_path)

    return meta


def migrate_all_projects() -> int:
    """Tum eski projeleri migrate et. Migrate edilen proje sayisini dondur."""
    PROJECTS_DIR.mkdir(exist_ok=True)
    count = 0
    for proj_dir in PROJECTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        meta_file = proj_dir / "project.json"
        old_file = proj_dir / "project_state.json"
        if not meta_file.exists() and old_file.exists():
            result = _migrate_project(proj_dir.name)
            if result:
                count += 1
    if count > 0:
        list_projects.clear()
    return count
