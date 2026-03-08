"""Yeni sidebar — proje listesi, wizard adim navigasyonu, parametre butonu."""

import streamlit as st

from src.project_manager_v2 import (
    list_projects, load_meta, load_wbs, load_latest_calculation,
    load_project_params_overrides,
)
from src.param_manager import load_params, merge_params
import src.effort_tables as tables
from src.views.components import short_name, format_datetime, STEP_CONFIG, STEP_ORDER


def render_sidebar():
    """Ana sidebar renderer — view_mode'a gore uygun icerik gosterir."""
    with st.sidebar:
        st.markdown("### PresalesAgent")
        st.caption("Kurumsal yazilim efor tahmini")

        st.divider()

        view_mode = st.session_state.get("view_mode", "dashboard")
        active_project_id = st.session_state.get("active_project_id")

        # Yeni Proje butonu
        if st.button("+ Yeni Proje", use_container_width=True, type="primary"):
            st.session_state.view_mode = "dashboard"
            st.session_state.active_project_id = None
            st.rerun()

        st.divider()

        # ── Proje Listesi ──
        st.markdown("**PROJELER**")
        projects = list_projects()

        if projects:
            for p in projects[:15]:
                pid = p["project_id"]
                is_active = (pid == active_project_id)
                pname = short_name(p["project_name"] or pid, 24)

                # Proje bilgisi
                mc = p.get("module_count", 0)
                wc = p.get("wp_count", 0)
                info = f"{mc}m, {wc}wp" if mc > 0 else "yeni"

                # Aktif proje highlight
                if is_active:
                    st.markdown(f"**> {pname}**")
                    st.caption(f"  {info}")

                    # Wizard icindeyse adim navigasyonu goster
                    if view_mode == "wizard":
                        _render_wizard_nav()
                else:
                    if st.button(f"{pname}", key=f"sb_proj_{pid}",
                                 use_container_width=True,
                                 help=info):
                        _switch_to_project(pid)
        else:
            st.caption("Henuz proje yok")

        st.divider()

        # ── Parametreler — ana ekranda goster ──
        if st.button("Parametre Ayarlari", use_container_width=True, key="sb_params_btn"):
            st.session_state.view_mode = "params"
            st.rerun()


def _render_wizard_nav():
    """Wizard icindeyken adim navigasyonu goster."""
    current_step = st.session_state.get("wizard_step", "scope")
    current_idx = STEP_ORDER.index(current_step) if current_step in STEP_ORDER else 0

    for i, (key, label, num) in enumerate(STEP_CONFIG):
        if i < current_idx:
            if st.button(f"  ✓ {num}. {label}", key=f"sb_step_{key}",
                         use_container_width=True):
                st.session_state.wizard_step = key
                st.rerun()
        elif i == current_idx:
            st.markdown(f"  **→ {num}. {label}**")
        else:
            st.caption(f"    {num}. {label}")



def _switch_to_project(target_id: str):
    """Projeye gec."""
    # Widget key'leri temizle
    for wkey in ["ctx_scale", "ctx_team", "ctx_tech_debt", "ctx_domain", "ctx_int_density"]:
        st.session_state.pop(wkey, None)

    meta = load_meta(target_id)
    if not meta:
        st.error(f"Proje yuklenemedi: {target_id}")
        return

    st.session_state.active_project_id = target_id

    # WBS yukle
    wbs = load_wbs(target_id)
    st.session_state.wbs = wbs

    # Son hesaplama yukle
    calc = load_latest_calculation(target_id)
    if calc:
        st.session_state.effort_result = calc.get("effort_result")
        st.session_state.categories = calc.get("categories")
        st.session_state.project_context = calc.get("context")
    else:
        st.session_state.effort_result = None
        st.session_state.categories = None
        st.session_state.project_context = None

    st.session_state.chat_messages = meta.get("wizard_state", {}).get("chat_messages", [])

    # Context widget key'lerini set et
    ctx = st.session_state.project_context
    if ctx and isinstance(ctx, dict):
        for widget_key, ctx_key in [("ctx_scale", "scale"), ("ctx_team", "team"),
                                      ("ctx_tech_debt", "tech_debt"), ("ctx_domain", "domain"),
                                      ("ctx_int_density", "integration_density")]:
            if ctx_key in ctx:
                st.session_state[widget_key] = ctx[ctx_key]

    # Proje override parametrelerini yukle
    overrides = load_project_params_overrides(target_id)
    if overrides:
        global_params = load_params()
        merged = merge_params(global_params, overrides)
        tables.reload_tables(merged)
    else:
        tables.reload_tables()

    # View mode belirle
    wizard_step = meta.get("wizard_state", {}).get("current_step", "scope")
    if st.session_state.effort_result:
        st.session_state.view_mode = "project_detail"
        st.session_state.detail_tab = "overview"
    elif wbs:
        st.session_state.view_mode = "wizard"
        st.session_state.wizard_step = wizard_step if wizard_step in ["wbs_edit", "context", "calculate"] else "wbs_edit"
    else:
        st.session_state.view_mode = "wizard"
        st.session_state.wizard_step = "scope"

    list_projects.clear()
    st.rerun()
