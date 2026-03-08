"""Dashboard view — yeni proje olusturma."""

import streamlit as st
from src.project_manager_v2 import create_project, list_projects


def show_dashboard():
    """Ana ekran: yeni proje olusturma formu."""

    st.header("Efor Tahmin Agent")
    st.caption("Kurumsal yazilim projelerinin efor tahminini yapin.")

    # ── Yeni Proje Olusturma ──
    with st.container(border=True):
        with st.form("new_project_form", clear_on_submit=True):
            st.subheader("Yeni Proje Olustur")
            f_col1, f_col2 = st.columns([2, 3])
            with f_col1:
                proj_name = st.text_input("Proje Adi *", placeholder="orn: Makro Ekonomi Platformu")
            with f_col2:
                proj_desc = st.text_input("Kisa Aciklama", placeholder="Projenin amaci ve kapsami...")
            submitted = st.form_submit_button("Olustur", type="primary", use_container_width=True)

            if submitted:
                if not proj_name or not proj_name.strip():
                    st.error("Proje adi zorunludur.")
                else:
                    pid = create_project(proj_name.strip(), proj_desc.strip() if proj_desc else "")
                    st.session_state.view_mode = "wizard"
                    st.session_state.wizard_step = "scope"
                    st.session_state.active_project_id = pid
                    # Clear working data
                    st.session_state.wbs = None
                    st.session_state.categories = None
                    st.session_state.effort_result = None
                    st.session_state.pdf_text = None
                    st.session_state.project_context = None
                    st.session_state.chat_messages = []
                    list_projects.clear()
                    st.rerun()
