"""Proje state yonetimi — her proje icin izole state bundle kaydet/yukle."""

import json
import shutil
import streamlit as st
from datetime import datetime
from pathlib import Path

PROJECTS_DIR = Path("projects")

# Session state key'leri (capture/restore icin)
_STATE_KEYS = [
    "wbs", "wbs_source", "categories", "project_context",
    "effort_result", "output_path", "chat_messages", "pdf_text",
    "project_description",
]

# Streamlit widget key'leri (radio butonlar)
_WIDGET_KEYS = ["ctx_scale", "ctx_team", "ctx_tech_debt", "ctx_domain", "ctx_int_density"]

# Widget key → project_context key eslestirmesi
_WIDGET_TO_CTX = {
    "ctx_scale": "scale",
    "ctx_team": "team",
    "ctx_tech_debt": "tech_debt",
    "ctx_domain": "domain",
    "ctx_int_density": "integration_density",
}


def generate_project_id(project_name: str) -> str:
    """Proje adindan unique ID uret: slug + timestamp."""
    safe = project_name.lower().replace(" ", "_")
    safe = "".join(c for c in safe if c.isalnum() or c == "_")[:30] or "proje"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe}_{ts}"


def create_project(name: str, description: str = "") -> str:
    """Yeni proje olustur, project_id dondur. Bos state ile baslar."""
    project_id = generate_project_id(name)
    state = {key: None for key in _STATE_KEYS}
    state["chat_messages"] = []
    state["project_description"] = description
    state["meta"] = {
        "project_id": project_id,
        "project_name": name,
        "project_description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "current_step": "scope",
        "status": "active",
    }
    save_project(project_id, state)
    return project_id


def save_project(project_id: str, state: dict) -> str:
    """Proje state bundle'i diske kaydet.

    Returns: kaydedilen dosya yolu.
    """
    PROJECTS_DIR.mkdir(exist_ok=True)
    proj_dir = PROJECTS_DIR / project_id
    proj_dir.mkdir(exist_ok=True)

    # Meta guncelle
    if "meta" in state:
        state["meta"]["updated_at"] = datetime.now().isoformat()

    filepath = proj_dir / "project_state.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)

    # Cache'i invalidate et
    list_projects.clear()

    return str(filepath)


def load_project(project_id: str) -> dict | None:
    """Proje state bundle'i diskten oku."""
    filepath = PROJECTS_DIR / project_id / "project_state.json"
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


@st.cache_data(ttl=15)
def list_projects() -> list[dict]:
    """Tum projeleri tara ve ozet bilgi dondur (son guncellemeye gore sirali)."""
    PROJECTS_DIR.mkdir(exist_ok=True)
    projects = []

    for proj_dir in PROJECTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        state_file = proj_dir / "project_state.json"
        if not state_file.exists():
            continue
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            meta = state.get("meta", {})

            # WBS'ten modul/WP sayisi
            wbs = state.get("wbs")
            module_count = 0
            wp_count = 0
            if wbs and isinstance(wbs, dict):
                modules = wbs.get("wbs", {}).get("modules", [])
                module_count = len(modules)
                wp_count = sum(len(m.get("work_packages", [])) for m in modules)

            projects.append({
                "project_id": meta.get("project_id", proj_dir.name),
                "project_name": meta.get("project_name", proj_dir.name),
                "project_description": meta.get("project_description", ""),
                "current_step": meta.get("current_step", "scope"),
                "status": meta.get("status", "active"),
                "updated_at": meta.get("updated_at", ""),
                "created_at": meta.get("created_at", ""),
                "module_count": module_count,
                "wp_count": wp_count,
            })
        except (json.JSONDecodeError, OSError):
            continue

    # Son guncellemeye gore sirala (en yeni basta)
    projects.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return projects


def delete_project(project_id: str) -> bool:
    """Proje klasorunu sil."""
    proj_dir = PROJECTS_DIR / project_id
    if proj_dir.exists() and proj_dir.is_dir():
        shutil.rmtree(proj_dir)
        list_projects.clear()
        return True
    return False


def capture_session() -> dict:
    """st.session_state'ten serilestirilebilir proje state bundle olustur."""
    state = {}

    for key in _STATE_KEYS:
        val = st.session_state.get(key)
        state[key] = val

    # chat_messages None ise bos liste yap
    if state.get("chat_messages") is None:
        state["chat_messages"] = []

    # Meta bilgisi
    project_id = st.session_state.get("current_project_id", "")
    project_name = ""
    wbs = state.get("wbs")
    if wbs and isinstance(wbs, dict):
        project_name = wbs.get("project_scope_summary", {}).get("project_name", "")
    project_description = state.get("project_description", "")

    # Mevcut meta varsa koru, yoksa olustur
    existing_meta = st.session_state.get("_project_meta")
    if existing_meta:
        state["meta"] = {
            **existing_meta,
            "project_id": project_id,
            "project_name": project_name or existing_meta.get("project_name", ""),
            "project_description": project_description or existing_meta.get("project_description", ""),
            "current_step": st.session_state.get("step", "scope"),
            "updated_at": datetime.now().isoformat(),
        }
    else:
        state["meta"] = {
            "project_id": project_id,
            "project_name": project_name,
            "project_description": project_description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_step": st.session_state.get("step", "scope"),
            "status": "active",
        }

    return state


def restore_session(state: dict) -> None:
    """State bundle'i st.session_state'e yukle (widget key'ler dahil)."""
    # Ana state key'leri
    for key in _STATE_KEYS:
        st.session_state[key] = state.get(key)

    # chat_messages None ise bos liste
    if st.session_state.chat_messages is None:
        st.session_state.chat_messages = []

    # Step
    meta = state.get("meta", {})
    st.session_state.step = meta.get("current_step", "scope")
    st.session_state.current_project_id = meta.get("project_id")

    # Meta'yi session'da sakla (sonraki capture icin)
    st.session_state._project_meta = meta

    # Widget key'leri project_context'ten set et
    ctx = state.get("project_context")
    if ctx and isinstance(ctx, dict):
        for widget_key, ctx_key in _WIDGET_TO_CTX.items():
            if ctx_key in ctx:
                st.session_state[widget_key] = ctx[ctx_key]
    else:
        # Context yoksa widget key'leri temizle
        for wkey in _WIDGET_KEYS:
            st.session_state.pop(wkey, None)


def _auto_save() -> None:
    """Aktif proje varsa mevcut state'i kaydet. Adim gecislerinde cagrilir."""
    pid = st.session_state.get("current_project_id")
    if pid:
        save_project(pid, capture_session())
