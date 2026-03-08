"""Efor Tahmin Agent — Ana uygulama router'i."""

import os
import streamlit as st

from src.ui_theme import inject_custom_css
from src.sidebar_v2 import render_sidebar
from src.project_manager_v2 import migrate_all_projects
from src.views.dashboard import show_dashboard
from src.views.wizard import show_wizard
from src.views.project_detail import show_project_detail
from src.views.params_view import show_params

st.set_page_config(page_title="Efor Tahmin Agent", page_icon="📊", layout="wide")
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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("ANTHROPIC_API_KEY ortam degiskeni ayarlanmamis!")
        st.code("export ANTHROPIC_API_KEY='sk-...'")
        return

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
