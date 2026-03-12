"""PresalesAgent — Ana uygulama router'i."""

import os
import streamlit as st

# ── .env ve Streamlit Secrets'tan API key yukle ──────────────────────────────
def _load_env():
    """Oncelik sirasi: 1) .env dosyasi (lokal), 2) Streamlit secrets (cloud)."""
    # 1) .env dosyasindan oku (lokal gelistirme icin)
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))

    # 2) Streamlit secrets'tan oku (cloud deploy icin)
    try:
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ.setdefault(key, value)
    except Exception:
        pass  # secrets yoksa devam et

_load_env()

from src.ui_theme import inject_custom_css
from src.sidebar_v2 import render_sidebar
from src.project_manager_v2 import migrate_all_projects
from src.views.dashboard import show_dashboard
from src.views.wizard import show_wizard
from src.views.project_detail import show_project_detail
from src.views.params_view import show_params

st.set_page_config(page_title="PresalesAgent", layout="wide")
inject_custom_css()


# ── State ──────────────────────────────────────────────────────────────────

def init_state():
    """Session state'i initialize et."""
    defaults = {
        "view_mode": "dashboard",       # dashboard | wizard | project_detail | params
        "wizard_step": "scope",          # scope | wbs_edit | context | calculate | results
        "detail_tab": "overview",        # overview | wbs | results | consultant
        "active_project_id": None,
        "wbs": None,
        "categories": None,
        "effort_result": None,
        "pdf_text": None,
        "project_context": None,
        "chat_messages": [],
        "output_path": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
    if st.session_state.chat_messages is None:
        st.session_state.chat_messages = []

    # Legacy migration (bir kez)
    if "_migrated" not in st.session_state:
        count = migrate_all_projects()
        st.session_state._migrated = True
        if count > 0:
            st.toast(f"{count} proje migrate edildi")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    from src.llm_client import check_api_key
    ok, msg = check_api_key()
    if not ok:
        st.error(msg)
        return
    else:
        st.sidebar.caption(msg)

    init_state()
    render_sidebar()

    view_mode = st.session_state.view_mode

    if view_mode == "dashboard":
        show_dashboard()
    elif view_mode == "wizard":
        show_wizard()
    elif view_mode == "project_detail":
        show_project_detail()
    elif view_mode == "params":
        show_params()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
