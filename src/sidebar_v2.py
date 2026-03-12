"""Sidebar — profesyonel navigasyon: brand, proje listesi, wizard adimlar, ayarlar."""

import streamlit as st

from src.project_manager_v2 import (
    list_projects, load_meta, load_wbs, load_latest_calculation,
    load_project_params_overrides, delete_project,
)
from src.param_manager import load_params, merge_params
import src.effort_tables as tables
from src.views.components import short_name, format_datetime, STEP_CONFIG, STEP_ORDER


# ── Wizard step kisa etiketleri ──
_STEP_SHORT = {
    "scope": "Kapsam",
    "wbs_edit": "WBS",
    "context": "Baglam",
    "calculate": "Hesaplama",
    "results": "Sonuclar",
}


def render_sidebar():
    """Ana sidebar renderer."""
    with st.sidebar:
        view_mode = st.session_state.get("view_mode", "dashboard")
        active_project_id = st.session_state.get("active_project_id")

        # ────────────────────── BRAND ──────────────────────
        st.markdown(
            '<div class="sb-brand">'
            '<span class="sb-brand-icon">P</span>'
            '<div class="sb-brand-text">'
            '<div class="sb-brand-title">PresalesAgent</div>'
            '<div class="sb-brand-sub">Kurumsal yazilim efor tahmini</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sb-spacer-lg"></div>', unsafe_allow_html=True)

        # ────────────────────── YENI PROJE ──────────────────────
        if st.button("＋  Yeni Proje", use_container_width=True, type="primary",
                      key="sb_new_project"):
            st.session_state.view_mode = "dashboard"
            st.session_state.active_project_id = None
            st.rerun()

        st.markdown('<div class="sb-spacer-md"></div>', unsafe_allow_html=True)

        # ────────────────────── PROJE LISTESI ──────────────────────
        projects = list_projects()
        count = len(projects)

        st.markdown(
            f'<div class="sb-section-header">'
            f'<span>PROJELER</span>'
            f'<span class="sb-section-badge">{count}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if not projects:
            st.markdown(
                '<div class="sb-empty">Henuz proje yok. Yeni proje olusturun.</div>',
                unsafe_allow_html=True,
            )
        else:
            for p in projects[:15]:
                pid = p["project_id"]
                is_active = (pid == active_project_id)
                pname = short_name(p["project_name"] or pid, 22)
                mc = p.get("module_count", 0)
                wc = p.get("wp_count", 0)
                has_result = (p.get("calc_count", 0) > 0)

                if mc > 0:
                    info = f"{mc} modul · {wc} WP"
                else:
                    info = "Yeni proje"

                # Dot rengi belirle
                if has_result:
                    dot_cls = "done"
                elif mc > 0:
                    dot_cls = "progress"
                else:
                    dot_cls = "new"

                if is_active:
                    # ── Aktif proje — ayni st.button, disabled + CSS ile secili gorunum ──
                    if has_result:
                        status_text = "Tamamlandi"
                    elif mc > 0:
                        status_text = "Devam ediyor"
                    else:
                        status_text = "Yeni proje"

                    col_dot, col_btn = st.columns([0.12, 0.88], gap="small")
                    with col_dot:
                        st.markdown(
                            '<div class="sb-dot-col">'
                            '<span class="sb-project-dot sb-dot-active"></span>'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                    with col_btn:
                        st.button(f"{pname}  »", key=f"sb_proj_{pid}",
                                  use_container_width=True, disabled=True)
                    st.markdown(
                        f'<div class="sb-active-status">{status_text}</div>',
                        unsafe_allow_html=True,
                    )

                    # Wizard adim navigasyonu
                    if view_mode == "wizard":
                        _render_wizard_nav()

                else:
                    # ── Inaktif proje ──
                    col_dot, col_btn = st.columns([0.12, 0.88], gap="small")
                    with col_dot:
                        st.markdown(
                            f'<div class="sb-dot-col"><span class="sb-project-dot sb-dot-{dot_cls}"></span></div>',
                            unsafe_allow_html=True,
                        )
                    with col_btn:
                        btn_col, del_col = st.columns([0.85, 0.15], gap="small")
                        with btn_col:
                            if st.button(pname, key=f"sb_proj_{pid}",
                                         use_container_width=True, help=info):
                                _switch_to_project(pid)
                        with del_col:
                            if st.button("×", key=f"sb_del_{pid}",
                                         use_container_width=True, help="Sil"):
                                st.session_state[f"_confirm_delete_{pid}"] = True
                                st.rerun()

                    # Silme onay
                    if st.session_state.get(f"_confirm_delete_{pid}"):
                        st.warning(f"**{pname}** silinecek. Emin misiniz?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Evet, Sil", key=f"sb_confirm_del_{pid}",
                                         type="primary", use_container_width=True):
                                delete_project(pid)
                                st.session_state.pop(f"_confirm_delete_{pid}", None)
                                if active_project_id == pid:
                                    st.session_state.active_project_id = None
                                    st.session_state.view_mode = "dashboard"
                                list_projects.clear()
                                st.rerun()
                        with c2:
                            if st.button("Iptal", key=f"sb_cancel_del_{pid}",
                                         use_container_width=True):
                                st.session_state.pop(f"_confirm_delete_{pid}", None)
                                st.rerun()

        # ────────────────────── AYARLAR ──────────────────────
        st.markdown('<div class="sb-spacer-lg"></div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="sb-section-header"><span>AYARLAR</span></div>',
            unsafe_allow_html=True,
        )

        is_params_active = (view_mode == "params")
        params_cls = "sb-settings-active" if is_params_active else "sb-settings"

        if is_params_active:
            st.markdown(
                f'<div class="{params_cls}">'
                '<span class="sb-settings-icon">⚙</span>'
                '<span>Parametre Ayarlari</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("⚙  Parametre Ayarlari", use_container_width=True,
                         key="sb_params_btn"):
                st.session_state.view_mode = "params"
                st.rerun()


def _render_wizard_nav():
    """Aktif proje altinda wizard adim navigasyonu — tek HTML blogu."""
    current_step = st.session_state.get("wizard_step", "scope")
    current_idx = STEP_ORDER.index(current_step) if current_step in STEP_ORDER else 0

    parts = ['<div class="sb-wizard-steps">']

    for i, (key, _label, num) in enumerate(STEP_CONFIG):
        short = _STEP_SHORT[key]

        if i < current_idx:
            # Tamamlanmis adim — ayni yapi, check, silik degil
            parts.append(
                f'<div class="sb-step sb-step-done">'
                f'<span class="sb-step-num">✓</span>'
                f'<span class="sb-step-label">{short}</span>'
                f'</div>'
            )
        elif i == current_idx:
            # Aktif adim
            parts.append(
                f'<div class="sb-step sb-step-active">'
                f'<span class="sb-step-num">{num}</span>'
                f'<span class="sb-step-label">{short}</span>'
                f'</div>'
            )
        else:
            # Bekleyen adim
            parts.append(
                f'<div class="sb-step sb-step-pending">'
                f'<span class="sb-step-num">{num}</span>'
                f'<span class="sb-step-label">{short}</span>'
                f'</div>'
            )

    parts.append('</div>')
    st.markdown('\n'.join(parts), unsafe_allow_html=True)


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
