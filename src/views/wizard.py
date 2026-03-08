"""Wizard view — 5 adimli yeni proje olusturma akisi."""

import json
import os
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

from src.pdf_reader import read_pdf
from src.wbs_generator import generate_wbs, validate_wbs, WBSGenerationError, load_from_raw_response as wbs_load_raw
from src.categorizer import categorize_wbs, load_from_raw_response as cat_load_raw
from src.wbs_editor import (
    update_complexity, add_deliverable, remove_wp, update_wp_name,
    add_integration_point, update_description, update_deliverable,
    remove_deliverable, update_technical_field, remove_integration_point,
    add_acceptance_criterion, remove_acceptance_criterion, update_complexity_drivers,
)
from src.effort_engine import calculate_effort
from src.quality_check import run_checks
from src.chat_agent import chat as chat_with_agent
from src.param_manager import snapshot_params, load_params, save_params, diff_from_defaults, merge_params, extract_overrides
from src.views.components import (
    render_step_indicator, render_results_charts, render_results_details,
    render_notes_risks, render_export_section,
)
import src.effort_tables as tables
import src.project_manager_v2 as pm


CATEGORIES = [
    "SIMPLE_UI", "COMPLEX_UI", "FILE_PROCESS", "EXPORT_REPORT",
    "BACKGROUND_JOB", "INTEGRATION", "RULE_ENGINE", "AUTH_COMPONENT",
]
COMPLEXITY_LEVELS = ["low", "medium", "high", "very_high"]
_PROFILE_LABELS = {"A": "Profil A (Geleneksel)", "B": "Profil B (Copilot+Claude)", "C": "Profil C (VibeCoding)"}
OF_CODES = [
    "OF-AUTH", "OF-AUTHZ", "OF-CRUD", "OF-DATA", "OF-AUDIT", "OF-CACHE",
    "OF-SEARCH", "OF-MULTI", "OF-CICD", "OF-CLOUD", "OF-UI", "OF-FORM",
    "OF-TABLE", "OF-MENU", "OF-DASH", "OF-PROFILE", "OF-REPORT", "OF-NOTIF",
    "OF-HANGFIRE", "OF-RULE", "OF-WORKFLOW", "OF-DMS", "OF-FILE", "OF-UPLOAD",
    "OF-CMS", "OF-FAQ", "OF-VALID", "OF-I18N", "OF-ERR", "OF-CHATBOT",
    "OF-APIGW", "OF-SIGNAL",
]


def _count_overrides(overrides: dict) -> list:
    """Override dict icindeki leaf degerleri duz liste olarak dondurur (sayi icin)."""
    leaves = []
    def _walk(d, prefix=""):
        for k, v in d.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                _walk(v, path)
            else:
                leaves.append(path)
    _walk(overrides)
    return leaves


@st.dialog("Hesaplama Parametreleri (Projeye Ozel)", width="large")
def _edit_params_dialog():
    """Modal parametre duzenleyici — projeye ozel override kaydeder, global config degismez."""
    project_id = st.session_state.get("active_project_id")
    global_params = load_params()

    # Proje override varsa birlestirilmis hali goster
    overrides = pm.load_project_params_overrides(project_id) if project_id else None
    if overrides:
        params = merge_params(global_params, overrides)
        st.info(f"Bu projede **{len(_count_overrides(overrides))} parametre** projeye ozel override edilmis.")
    else:
        import copy
        params = copy.deepcopy(global_params)

    tab1, tab2, tab3, tab4 = st.tabs(["Baz Efor", "Carpanlar", "Faz Yuzdeleri", "OneFrame Residuel"])

    with tab1:
        st.markdown("**Baz Efor Degerleri (FE, BE) — Adam-Gun**")
        profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                               format_func=lambda x: _PROFILE_LABELS[x],
                               key="dlg_base_profile")
        base = params["base_effort"][profile]
        rows = []
        for cat in CATEGORIES:
            vals = base.get(cat, [0, 0])
            rows.append({"Kategori": cat, "FE": vals[0], "BE": vals[1]})
        df = pd.DataFrame(rows)
        edited = st.data_editor(df, key=f"dlg_base_edit_{profile}",
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "Kategori": st.column_config.TextColumn(disabled=True),
                                    "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                    "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                })
        for _, row in edited.iterrows():
            cat = row["Kategori"]
            params["base_effort"][profile][cat] = [round(row["FE"], 2), round(row["BE"], 2)]

    with tab2:
        st.markdown("**Kompleksite Carpanlari**")
        comp_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["complexity_multipliers"][p][level]
            comp_rows.append(row)
        df = pd.DataFrame(comp_rows)
        edited = st.data_editor(df, key="dlg_complexity_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{level: st.column_config.NumberColumn(min_value=0, step=0.05, format="%.2f")
                                       for level in COMPLEXITY_LEVELS}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["complexity_multipliers"][p][level] = round(row[level], 2)

        st.divider()

        st.markdown("**Batch Carpanlari**")
        for p in ["A", "B", "C"]:
            vals = params["batch_multipliers"][p]
            cols = st.columns(len(vals) + 1)
            cols[0].markdown(f"**{p}**")
            new_vals = []
            for i, v in enumerate(vals):
                nv = cols[i + 1].number_input(f"#{i+1}", value=float(v), step=0.05,
                                              min_value=0.0, max_value=2.0,
                                              key=f"dlg_batch_{p}_{i}", label_visibility="collapsed")
                new_vals.append(round(nv, 2))
            params["batch_multipliers"][p] = new_vals

        st.divider()

        st.markdown("**Entegrasyon Carpanlari**")
        int_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for k in ["0", "1", "3"]:
                row[f"Nokta {k}"] = params["integration_multipliers"][p].get(k, 1.0)
            int_rows.append(row)
        df = pd.DataFrame(int_rows)
        edited = st.data_editor(df, key="dlg_integration_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{f"Nokta {k}": st.column_config.NumberColumn(min_value=0, step=0.05, format="%.2f")
                                       for k in ["0", "1", "3"]}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            params["integration_multipliers"][p]["0"] = round(row["Nokta 0"], 2)
            params["integration_multipliers"][p]["1"] = round(row["Nokta 1"], 2)
            params["integration_multipliers"][p]["2"] = round(row["Nokta 1"], 2)
            params["integration_multipliers"][p]["3"] = round(row["Nokta 3"], 2)

    with tab3:
        st.markdown("**Analiz Yuzdeleri**")
        an_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["analysis_pct"][p][level]
            an_rows.append(row)
        df = pd.DataFrame(an_rows)
        edited = st.data_editor(df, key="dlg_analysis_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{level: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                       for level in COMPLEXITY_LEVELS}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["analysis_pct"][p][level] = round(row[level], 2)

        st.divider()

        st.markdown("**Tasarim & Mimari Yuzdeleri**")
        dm_cols = st.columns(2)
        with dm_cols[0]:
            st.caption("UI/UX Tasarim")
            for p in ["A", "B", "C"]:
                params["design_pct"][p] = round(st.number_input(
                    f"Profil {p}", value=float(params["design_pct"][p]),
                    step=0.01, min_value=0.0, max_value=1.0,
                    key=f"dlg_design_{p}", format="%.2f"), 2)
        with dm_cols[1]:
            st.caption("Yazilim Mimarisi")
            for p in ["A", "B", "C"]:
                params["architecture_pct"][p] = round(st.number_input(
                    f"Profil {p}", value=float(params["architecture_pct"][p]),
                    step=0.01, min_value=0.0, max_value=1.0,
                    key=f"dlg_arch_{p}", format="%.2f"), 2)

        st.divider()

        st.markdown("**Test Yuzdeleri**")
        test_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["test_pct"][p][level]
            test_rows.append(row)
        df = pd.DataFrame(test_rows)
        edited = st.data_editor(df, key="dlg_test_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{level: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                       for level in COMPLEXITY_LEVELS}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["test_pct"][p][level] = round(row[level], 2)

    with tab4:
        st.markdown("**OneFrame Residuel Efor Tablosu (FE, BE) — Adam-Gun**")
        st.caption("OF eslesmesi olan deliverable'lar icin Baz Efor yerine bu degerler kullanilir.")
        of_profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                                   format_func=lambda x: _PROFILE_LABELS[x],
                                   key="dlg_of_profile")
        of_data = params["oneframe_residual"].get(of_profile, {})
        of_rows = []
        for of_code in OF_CODES:
            vals = of_data.get(of_code, [0, 0])
            of_rows.append({"OF Kodu": of_code, "FE": vals[0], "BE": vals[1]})
        of_df = pd.DataFrame(of_rows)
        of_edited = st.data_editor(of_df, key=f"dlg_of_edit_{of_profile}",
                                    use_container_width=True, hide_index=True,
                                    column_config={
                                        "OF Kodu": st.column_config.TextColumn(disabled=True),
                                        "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                        "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                    })
        for _, row in of_edited.iterrows():
            of_code = row["OF Kodu"]
            params["oneframe_residual"][of_profile][of_code] = [round(row["FE"], 2), round(row["BE"], 2)]

    # Kaydet butonu
    st.divider()
    save_col1, save_col2, save_col3 = st.columns(3)
    with save_col1:
        if st.button("Kaydet ve Kapat", type="primary", use_container_width=True, key="dlg_save"):
            if project_id:
                # Sadece global'den farkli olan degerleri override olarak kaydet
                project_overrides = extract_overrides(params, global_params)
                pm.save_project_params(project_id, project_overrides)
                # Merged params ile tablolari yukle
                merged = merge_params(global_params, project_overrides)
                tables.reload_tables(merged)
                if project_overrides:
                    st.toast(f"Projeye ozel {len(_count_overrides(project_overrides))} parametre kaydedildi")
                else:
                    st.toast("Parametreler varsayilan degerlerde (override yok)")
            else:
                # Proje yoksa global kaydet (fallback)
                errors = save_params(params)
                if errors:
                    for e in errors:
                        st.error(e)
                    return
                tables.reload_tables()
                st.toast("Parametreler kaydedildi")
            st.rerun()
    with save_col2:
        if st.button("Varsayilanlara Don", use_container_width=True, key="dlg_reset"):
            if project_id:
                pm.clear_project_params(project_id)
                tables.reload_tables()
                st.toast("Proje override'lari temizlendi — varsayilan parametreler aktif")
            st.rerun()
    with save_col3:
        if st.button("Iptal", use_container_width=True, key="dlg_cancel"):
            st.rerun()


def show_wizard():
    """Wizard router — current step'e gore uygun view'i goster."""
    step = st.session_state.get("wizard_step", "scope")
    project_id = st.session_state.get("active_project_id")

    render_step_indicator(step)

    if step == "scope":
        _show_scope(project_id)
    elif step == "wbs_edit":
        _show_wbs_edit(project_id)
    elif step == "context":
        _show_context(project_id)
    elif step == "calculate":
        _show_calculate(project_id)
    elif step == "results":
        _show_results(project_id)


def _go_step(step: str, project_id: str | None = None):
    """Wizard step degistir ve kaydet."""
    st.session_state.wizard_step = step
    if project_id:
        pm.save_wizard_state(project_id, step, st.session_state.get("chat_messages"))
    st.rerun()


# ── STEP 1: Scope ──────────────────────────────────────────────────────────

def _show_scope(project_id: str):
    meta = pm.load_meta(project_id) if project_id else {}
    project_name = (meta or {}).get("project_name", "Yeni Proje")

    st.header(project_name)
    desc = (meta or {}).get("project_description", "")
    if desc:
        st.caption(desc)
    st.divider()

    # PDF Yukleme
    with st.container(border=True):
        st.subheader("Kapsam Dokumani Yukle")
        st.caption("PDF analiz dokumanindan WBS olusturun")

        # Onceden yuklu scope var mi?
        existing_text = pm.load_scope_text(project_id) if project_id else None
        if existing_text:
            st.success(f"Onceden yuklu kapsam metni mevcut (~{len(existing_text.split())} kelime)")
            if st.button("Mevcut Kapsam ile WBS Olustur", type="primary", use_container_width=True):
                _generate_wbs_from_text(existing_text, project_id)
                return
            st.divider()
            st.caption("veya yeni PDF yukleyin:")

        uploaded = st.file_uploader("PDF Sec", type=["pdf"], label_visibility="collapsed")

        if uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                text, pages, words = read_pdf(tmp_path)
                st.success(f"{pages} sayfa, ~{words} kelime")
                st.session_state.pdf_text = text

                # Scope kaydet
                if project_id:
                    uploaded.seek(0)
                    pm.save_scope(project_id, uploaded.read(), text, uploaded.name, pages, words)

                os.unlink(tmp_path)

                if st.button("WBS Olustur", type="primary", use_container_width=True):
                    _generate_wbs_from_text(text, project_id)
                    return
            except Exception as e:
                st.error(f"PDF okunamadi: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    # Mevcut WBS Yukle (alternatif)
    _show_existing_wbs_loader(project_id)


def _generate_wbs_from_text(text: str, project_id: str):
    """PDF metninden WBS olustur."""
    with st.status("WBS Olusturuluyor...", expanded=True) as status:
        st.write("PDF metni hazirlandi")
        st.caption(f"~{len(text)//1000}K karakter islenecek")
        st.write("Claude API'ye gonderiliyor... (20-60 sn)")
        try:
            wbs = generate_wbs(text)
            st.write("WBS JSON parse edildi")
        except WBSGenerationError as e:
            status.update(label="WBS Olusturulamadi!", state="error")
            st.error(f"Hata: {e}")
            err_msg = str(e)
            if "Raw yanit kaydedildi:" in err_msg:
                raw_path = err_msg.split("Raw yanit kaydedildi:")[-1].strip()
                if st.button("Raw Yanittan Kurtar", type="primary"):
                    try:
                        wbs = wbs_load_raw(raw_path)
                        st.session_state.wbs = wbs
                        if project_id:
                            pm.save_wbs_version(project_id, wbs, source="recovered")
                        _go_step("wbs_edit", project_id)
                    except Exception as e2:
                        st.error(f"Kurtarma basarisiz: {e2}")
            return

        st.session_state.wbs = wbs
        if project_id:
            pm.save_wbs_version(project_id, wbs, source="generated")
        status.update(label="WBS Olusturuldu!", state="complete")
        st.toast("WBS kaydedildi")
        _go_step("wbs_edit", project_id)


def _show_existing_wbs_loader(project_id: str):
    """Mevcut WBS dosyalarindan yukle."""
    wbs_dir = Path("wbs")
    if not wbs_dir.exists():
        return
    wbs_files = sorted(wbs_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not wbs_files:
        return

    with st.container(border=True):
        st.subheader("veya Mevcut WBS Yukle")
        for i, filepath in enumerate(wbs_files[:5]):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pname = data.get("project_scope_summary", {}).get("project_name", filepath.stem)
                modules = data.get("wbs", {}).get("modules", [])
                mc = len(modules)
                wc = sum(len(m.get("work_packages", [])) for m in modules)
                st.markdown(f"**{pname}** — `{mc}` modul, `{wc}` WP")
                if st.button("Yukle", key=f"load_wbs_{i}", use_container_width=True):
                    errors = validate_wbs(data)
                    if errors:
                        st.error(f"WBS dogrulama hatalari: {', '.join(errors)}")
                    else:
                        st.session_state.wbs = data
                        if project_id:
                            pm.save_wbs_version(project_id, data, source="imported")
                        _go_step("wbs_edit", project_id)
                if i < len(wbs_files) - 1:
                    st.divider()
            except (json.JSONDecodeError, OSError):
                continue


# ── STEP 2: WBS Edit ──────────────────────────────────────────────────────

def _show_wbs_edit(project_id: str):
    st.header("WBS Inceleme ve Duzenleme")

    wbs = st.session_state.wbs
    if not wbs:
        st.warning("WBS bulunamadi. Kapsam adimina donun.")
        if st.button("Kapsam Adimina Don", type="primary"):
            _go_step("scope", project_id)
        return

    modules = wbs["wbs"]["modules"]
    total_mod = len(modules)
    total_wp = sum(len(m["work_packages"]) for m in modules)

    # Ozet bilgi
    info_col1, info_col2, info_col3 = st.columns(3)
    info_col1.metric("Modul", total_mod)
    info_col2.metric("Work Package", total_wp)
    info_col3.metric("Toplam Deliverable",
                     sum(len(wp.get("deliverables", []))
                         for m in modules for wp in m["work_packages"]))

    # Hizli duzenleme tablosu
    st.subheader("Hizli Duzenleme")
    st.caption("Complexity ve WP Adi'ni dogrudan tabloda degistirebilirsiniz.")

    rows = []
    wp_index_map = {}
    idx = 0
    for mi, mod in enumerate(modules):
        for wi, wp in enumerate(mod["work_packages"]):
            int_points = wp.get("technical_context", {}).get("integration_points", [])
            rows.append({
                "Modul": mod["name"],
                "WP ID": wp["wp_id"],
                "WP Adi": wp["name"],
                "Complexity": wp["complexity"]["level"],
                "Deliverable": len(wp.get("deliverables", [])),
                "Entegrasyon": len(int_points),
            })
            wp_index_map[idx] = (mi, wi)
            idx += 1

    df = pd.DataFrame(rows)
    edited_df = st.data_editor(
        df, use_container_width=True, hide_index=True,
        column_config={
            "WP ID": st.column_config.TextColumn(disabled=True),
            "Modul": st.column_config.TextColumn(disabled=True),
            "Complexity": st.column_config.SelectboxColumn(
                options=["low", "medium", "high", "very_high"],
            ),
            "WP Adi": st.column_config.TextColumn(),
            "Deliverable": st.column_config.NumberColumn(disabled=True),
            "Entegrasyon": st.column_config.NumberColumn(disabled=True),
        },
        key="wbs_summary_editor",
    )

    # data_editor degisikliklerini uygula
    changes_applied = False
    for row_idx in range(len(edited_df)):
        mi, wi = wp_index_map[row_idx]
        wp = modules[mi]["work_packages"][wi]
        new_name = edited_df.iloc[row_idx]["WP Adi"]
        new_comp = edited_df.iloc[row_idx]["Complexity"]
        if new_name != wp["name"]:
            update_wp_name(wbs, wp["wp_id"], new_name)
            changes_applied = True
        if new_comp != wp["complexity"]["level"]:
            update_complexity(wbs, wp["wp_id"], new_comp)
            changes_applied = True

    if changes_applied:
        if project_id:
            pm.update_active_wbs(project_id, wbs)
        st.toast("Degisiklikler kaydedildi")
        st.rerun()

    # Detayli WP duzenleme
    st.subheader("Detayli WP Duzenleme")
    st.caption("Her WP'yi genisletip tum alanlarini duzenleyin, tek butonla kaydedin.")

    for mod in modules:
        with st.expander(f"**{mod['module_id']} — {mod['name']}** ({len(mod['work_packages'])} WP)", expanded=False):
            if mod.get("description"):
                st.caption(mod["description"])

            for wp in mod["work_packages"]:
                _render_wp_editor(wbs, wp, project_id)

    st.divider()

    if st.button("WBS'i Onayla ve Devam Et", type="primary", use_container_width=True):
        if project_id:
            pm.update_active_wbs(project_id, wbs)

        with st.status("Kategorizasyon yapiliyor...", expanded=True) as status:
            st.write("WBS kaydedildi")
            from src.llm_client import get_model_name, get_provider
            st.write(f"Deliverable'lar kategorize ediliyor ({get_provider().capitalize()} API)...")
            st.caption(f"{total_wp} WP | model: {get_model_name('heavy')} | 20-60 sn")
            try:
                categories = categorize_wbs(wbs)
                st.session_state.categories = categories
                wp_cat = categories.get("wp_kategorileri", {})
                st.write(f"Kategorizasyon tamamlandi — {len(wp_cat)} WP")

                ai_baglam = categories.get("baglam_analizi", {})
                ctx = {
                    "scale": "orta", "team": "mid", "tech_debt": "greenfield",
                    "domain": ai_baglam.get("domain_karmasikligi", "standart"),
                    "integration_density": ai_baglam.get("entegrasyon_yogunlugu", "0-2"),
                }
                st.session_state.project_context = ctx
                st.session_state.ctx_scale = ctx["scale"]
                st.session_state.ctx_team = ctx["team"]
                st.session_state.ctx_tech_debt = ctx["tech_debt"]
                st.session_state.ctx_domain = ctx["domain"]
                st.session_state.ctx_int_density = ctx["integration_density"]
                status.update(label="Kategorizasyon Tamamlandi!", state="complete")
            except Exception as e:
                status.update(label="Kategorizasyon Hatasi!", state="error")
                err_msg = str(e)
                st.error(f"Hata: {err_msg}")
                if "Raw yanit kaydedildi:" in err_msg:
                    raw_path = err_msg.split("Raw yanit kaydedildi:")[-1].strip()
                    st.warning(f"API yaniti: `{raw_path}`")
                    if st.button("Raw Yanittan Kurtar", type="primary"):
                        try:
                            categories = cat_load_raw(raw_path)
                            st.session_state.categories = categories
                            ai_baglam = categories.get("baglam_analizi", {})
                            ctx = {
                                "scale": "orta", "team": "mid", "tech_debt": "greenfield",
                                "domain": ai_baglam.get("domain_karmasikligi", "standart"),
                                "integration_density": ai_baglam.get("entegrasyon_yogunlugu", "0-2"),
                            }
                            st.session_state.project_context = ctx
                            st.session_state.ctx_scale = ctx["scale"]
                            st.session_state.ctx_team = ctx["team"]
                            st.session_state.ctx_tech_debt = ctx["tech_debt"]
                            st.session_state.ctx_domain = ctx["domain"]
                            st.session_state.ctx_int_density = ctx["integration_density"]
                            _go_step("context", project_id)
                        except Exception as e2:
                            st.error(f"Kurtarma basarisiz: {e2}")
                return

        _go_step("context", project_id)


def _render_wp_editor(wbs: dict, wp: dict, project_id: str):
    """Tek WP icin form bazli editor."""
    wp_id = wp["wp_id"]
    complexity = wp["complexity"]["level"]
    deliverables = wp.get("deliverables", [])
    tc = wp.get("technical_context", {})
    drivers = wp.get("complexity", {}).get("drivers", [])
    criteria = wp.get("acceptance_criteria", [])

    label = f"{wp_id} — {wp['name']}  [{complexity}]"
    with st.expander(label):
        with st.form(key=f"form_{wp_id}"):
            new_name = st.text_input("WP Adi", value=wp["name"], key=f"fname_{wp_id}")
            new_desc = st.text_area("Aciklama", value=wp.get("description", ""),
                                    key=f"fdesc_{wp_id}", height=80)

            fcol1, fcol2 = st.columns(2)
            with fcol1:
                levels = ["low", "medium", "high", "very_high"]
                current_idx = levels.index(complexity) if complexity in levels else 1
                new_level = st.selectbox("Complexity", levels,
                                         index=current_idx, key=f"fcomp_{wp_id}")
            with fcol2:
                drivers_str = ", ".join(drivers) if drivers else ""
                new_drivers_str = st.text_input("Complexity Drivers (virgul ile)",
                                                value=drivers_str, key=f"fdrivers_{wp_id}")

            st.markdown("**Deliverables**")
            deliv_names = []
            for i, d in enumerate(deliverables):
                d_name = d if isinstance(d, str) else d.get("name", d.get("adi", str(d)))
                new_d = st.text_input(f"Deliverable {i+1}", value=d_name,
                                      key=f"fdeliv_{wp_id}_{i}",
                                      label_visibility="collapsed")
                deliv_names.append(new_d)

            new_deliv = st.text_input("Yeni deliverable ekle",
                                      key=f"fadd_deliv_{wp_id}",
                                      placeholder="Yeni deliverable adi...")

            st.markdown("**Teknik Baglam**")
            new_fe = st.text_area("Frontend Requirements",
                                  value=tc.get("frontend_requirements", ""),
                                  key=f"ffe_{wp_id}", height=60)
            new_be = st.text_area("Backend Requirements",
                                  value=tc.get("backend_requirements", ""),
                                  key=f"fbe_{wp_id}", height=60)
            new_di = st.text_area("Data Implications",
                                  value=tc.get("data_implications", ""),
                                  key=f"fdi_{wp_id}", height=60)

            col_save, col_del = st.columns([4, 1])
            with col_save:
                submitted = st.form_submit_button("Degisiklikleri Kaydet",
                                                  type="primary", use_container_width=True)
            with col_del:
                delete_wp_btn = st.form_submit_button("WP Sil", use_container_width=True)

            if submitted:
                changed = False
                if new_name != wp["name"]:
                    update_wp_name(wbs, wp_id, new_name)
                    changed = True
                if new_desc != wp.get("description", ""):
                    update_description(wbs, wp_id, new_desc)
                    changed = True
                if new_level != complexity:
                    update_complexity(wbs, wp_id, new_level)
                    changed = True
                new_drivers = [d.strip() for d in new_drivers_str.split(",") if d.strip()]
                if new_drivers != drivers:
                    update_complexity_drivers(wbs, wp_id, new_drivers)
                    changed = True
                for i, new_d in enumerate(deliv_names):
                    d = deliverables[i]
                    d_name = d if isinstance(d, str) else d.get("name", d.get("adi", str(d)))
                    if new_d != d_name:
                        update_deliverable(wbs, wp_id, i, new_d)
                        changed = True
                if new_deliv and new_deliv.strip():
                    add_deliverable(wbs, wp_id, new_deliv.strip())
                    changed = True
                if new_fe != tc.get("frontend_requirements", ""):
                    update_technical_field(wbs, wp_id, "frontend_requirements", new_fe)
                    changed = True
                if new_be != tc.get("backend_requirements", ""):
                    update_technical_field(wbs, wp_id, "backend_requirements", new_be)
                    changed = True
                if new_di != tc.get("data_implications", ""):
                    update_technical_field(wbs, wp_id, "data_implications", new_di)
                    changed = True
                if changed:
                    st.toast(f"{wp_id} guncellendi")
                    if project_id:
                        pm.update_active_wbs(project_id, wbs)
                    st.rerun()
                else:
                    st.info("Degisiklik yok")

            if delete_wp_btn:
                remove_wp(wbs, wp_id)
                st.toast(f"{wp_id} silindi")
                if project_id:
                    pm.update_active_wbs(project_id, wbs)
                st.rerun()

        # Form disinda: entegrasyon noktalari ve kabul kriterleri
        int_points = tc.get("integration_points", [])
        if int_points:
            st.markdown("**Entegrasyon Noktalari**")
            for j, pt in enumerate(int_points):
                ip_col1, ip_col2 = st.columns([5, 1])
                with ip_col1:
                    st.write(f"{j+1}. {pt}")
                with ip_col2:
                    if st.button("Sil", key=f"rm_ip_{wp_id}_{j}"):
                        remove_integration_point(wbs, wp_id, j)
                        if project_id:
                            pm.update_active_wbs(project_id, wbs)
                        st.rerun()

        new_ip = st.text_input("Yeni entegrasyon noktasi", key=f"add_ip_{wp_id}",
                               placeholder="Entegrasyon noktasi...")
        if new_ip:
            if st.button("Ekle", key=f"btn_ip_{wp_id}"):
                add_integration_point(wbs, wp_id, new_ip)
                if project_id:
                    pm.update_active_wbs(project_id, wbs)
                st.rerun()

        if criteria:
            st.markdown("**Kabul Kriterleri**")
            for k, crit in enumerate(criteria):
                ac_col1, ac_col2 = st.columns([5, 1])
                with ac_col1:
                    st.write(f"- {crit}")
                with ac_col2:
                    if st.button("Sil", key=f"rm_ac_{wp_id}_{k}"):
                        remove_acceptance_criterion(wbs, wp_id, k)
                        if project_id:
                            pm.update_active_wbs(project_id, wbs)
                        st.rerun()

        new_ac = st.text_input("Yeni kabul kriteri", key=f"add_ac_{wp_id}",
                               placeholder="Kabul kriteri...")
        if new_ac:
            if st.button("Ekle", key=f"btn_ac_{wp_id}"):
                add_acceptance_criterion(wbs, wp_id, new_ac)
                if project_id:
                    pm.update_active_wbs(project_id, wbs)
                st.rerun()


# ── STEP 3: Context ────────────────────────────────────────────────────────

def _show_context(project_id: str):
    st.header("Baglam Ayarlari")
    st.caption("Projeye ozel baglam parametreleri — efor toplamina carpan olarak uygulanir.")

    current = st.session_state.project_context or {}
    ai_baglam = (st.session_state.categories.get("baglam_analizi", {})
                 if st.session_state.categories else {})

    SCALE_OPTIONS = [("orta", "Orta (500-5K)"), ("kucuk", "Kucuk (<500)"),
                     ("buyuk", "Buyuk (5K-50K)"), ("enterprise", "Enterprise (>50K)")]
    TEAM_OPTIONS = [("mid", "Mid-Level"), ("junior", "Junior Agirlikli"),
                    ("senior", "Senior Agirlikli"), ("expert", "Uzman Ekip")]
    TECH_DEBT_OPTIONS = [("greenfield", "Greenfield (Sifirdan)"), ("ekleme", "Mevcut Sisteme Ekleme"),
                         ("legacy_ent", "Legacy Entegrasyon"), ("legacy_mod", "Legacy Modernizasyon")]
    DOMAIN_OPTIONS = [("standart", "Standart"), ("finans", "Finans"),
                      ("regulasyon", "Regulasyon"), ("saglik", "Saglik"), ("kritik", "Kritik Altyapi")]
    INT_OPTIONS = [("0-2", "Dusuk (0-2)"), ("3-4", "Orta (3-4)"),
                   ("5-7", "Yuksek (5-7)"), ("8+", "Cok Yuksek (8+)")]

    def _find_index(options, value):
        for i, (k, _) in enumerate(options):
            if k == value:
                return i
        return 0

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("**Proje Ortami**")
            scale_keys = [k for k, _ in SCALE_OPTIONS]
            scale = st.radio("Organizasyon Olcegi", scale_keys,
                             index=_find_index(SCALE_OPTIONS, current.get("scale", "orta")),
                             format_func=lambda k: dict(SCALE_OPTIONS)[k],
                             horizontal=True, key="ctx_scale")
            team_keys = [k for k, _ in TEAM_OPTIONS]
            team = st.radio("Ekip Deneyimi", team_keys,
                            index=_find_index(TEAM_OPTIONS, current.get("team", "mid")),
                            format_func=lambda k: dict(TEAM_OPTIONS)[k],
                            horizontal=True, key="ctx_team")
            td_keys = [k for k, _ in TECH_DEBT_OPTIONS]
            tech_debt = st.radio("Teknik Borc", td_keys,
                                 index=_find_index(TECH_DEBT_OPTIONS, current.get("tech_debt", "greenfield")),
                                 format_func=lambda k: dict(TECH_DEBT_OPTIONS)[k],
                                 horizontal=True, key="ctx_tech_debt")

    with col2:
        with st.container(border=True):
            st.markdown("**Domain & Entegrasyon**")
            if ai_baglam.get("domain_neden") or ai_baglam.get("entegrasyon_neden"):
                ai_text = "**AI Tespiti**  \n"
                if ai_baglam.get("domain_neden"):
                    ai_text += f"Domain: {ai_baglam['domain_neden']}  \n"
                if ai_baglam.get("entegrasyon_neden"):
                    ai_text += f"Entegrasyon: {ai_baglam['entegrasyon_neden']}"
                st.info(ai_text)

            dom_keys = [k for k, _ in DOMAIN_OPTIONS]
            domain = st.radio("Domain Karmasikligi", dom_keys,
                              index=_find_index(DOMAIN_OPTIONS, current.get("domain", "standart")),
                              format_func=lambda k: dict(DOMAIN_OPTIONS)[k],
                              horizontal=True, key="ctx_domain")
            int_keys = [k for k, _ in INT_OPTIONS]
            int_density = st.radio("Entegrasyon Yogunlugu", int_keys,
                                   index=_find_index(INT_OPTIONS, current.get("integration_density", "0-2")),
                                   format_func=lambda k: dict(INT_OPTIONS)[k],
                                   horizontal=True, key="ctx_int_density")
            ent_list = ai_baglam.get("benzersiz_entegrasyonlar", [])
            if ent_list:
                st.caption(f"Tespit edilen: {', '.join(ent_list)}")

    # Carpan onizleme
    st.divider()
    context = {
        "scale": scale, "team": team, "tech_debt": tech_debt,
        "domain": domain, "integration_density": int_density,
    }
    dim_labels = {
        "scale": "Organizasyon Olcegi", "team": "Ekip Deneyimi",
        "domain": "Domain", "tech_debt": "Teknik Borc",
        "integration_density": "Entegrasyon Yogunlugu",
    }
    preview_rows = []
    factor_ab = 1.0
    factor_c = 1.0
    for dim_key, dim_val in context.items():
        cm = tables.CONTEXT_MULTIPLIERS.get(dim_key, {})
        vals = cm.get(dim_val, {"AB": 1.0, "C": 1.0})
        factor_ab *= vals["AB"]
        factor_c *= vals["C"]
        preview_rows.append({
            "Boyut": dim_labels.get(dim_key, dim_key),
            "Deger": dim_val,
            "AB Carpan": vals["AB"],
            "C Carpan": vals["C"],
        })
    factor_c_capped = min(factor_c, tables.VIBE_CONTEXT_CAP)

    with st.container(border=True):
        st.markdown("**Carpan Onizleme**")
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)
        m1, m2 = st.columns(2)
        m1.metric("Birlesik Carpan (A & B)", f"{factor_ab:.4f}")
        delta_msg = f"max {tables.VIBE_CONTEXT_CAP}" if factor_c >= tables.VIBE_CONTEXT_CAP else None
        m2.metric("Birlesik Carpan (C)", f"{factor_c_capped:.4f}", delta_msg)

    # Hesaplama Parametreleri — kompakt ozet ve duzenleme butonu
    project_overrides = pm.load_project_params_overrides(project_id) if project_id else None
    param_col1, param_col2 = st.columns([3, 1])
    with param_col1:
        if project_overrides:
            override_count = len(_count_overrides(project_overrides))
            st.info(f"⚙ Hesaplama Parametreleri: **{override_count} parametre** projeye ozel override edilmis")
        else:
            st.success("⚙ Hesaplama Parametreleri: Varsayilan (global) parametreler kullaniliyor")
    with param_col2:
        if st.button("Parametreleri Duzenle", use_container_width=True, key="ctx_edit_params"):
            _edit_params_dialog()

    # OF kapsam bilgisi — hangi parametreler etkili
    categories = st.session_state.categories
    if categories:
        wp_cat = categories.get("wp_kategorileri", {})
        total_del = sum(len(w.get("deliverables", [])) for w in wp_cat.values())
        of_del = sum(
            1 for w in wp_cat.values()
            for d in w.get("deliverables", [])
            if d.get("of_match")
        )
        if total_del > 0 and of_del == total_del:
            st.warning(
                f"Tum deliverable'lar ({of_del}/{total_del}) OneFrame eslesmesine sahip. "
                f"**Baz Efor degisiklikleri etkisiz** olacaktir. "
                f"Etkili parametreler: OneFrame Residuel, Carpanlar, Faz Yuzdeleri."
            )
        elif total_del > 0 and of_del / total_del > 0.8:
            st.warning(
                f"Deliverable'larin %{of_del*100//total_del}'i OneFrame eslesmesine sahip. "
                f"Baz Efor degisiklikleri sinirli etki yapar."
            )

    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Onayla ve Efor Hesapla", type="primary", use_container_width=True):
            st.session_state.project_context = context
            _go_step("calculate", project_id)
    with btn_col2:
        if st.button("WBS Duzenlemeye Don", use_container_width=True):
            _go_step("wbs_edit", project_id)


# ── STEP 4: Calculate ──────────────────────────────────────────────────────

def _show_calculate(project_id: str):
    st.header("Efor Hesaplama")

    wbs = st.session_state.wbs
    context = st.session_state.project_context
    categories = st.session_state.categories

    with st.status("Efor Hesaplama Baslatiliyor...", expanded=True) as status:
        st.write("Parametreler yukleniyor...")
        # Global + proje override birlestirilmis parametreleri yukle
        project_overrides = pm.load_project_params_overrides(project_id) if project_id else None
        if project_overrides:
            global_params = load_params()
            merged_params = merge_params(global_params, project_overrides)
            tables.reload_tables(merged_params)
            st.write(f"Projeye ozel {len(_count_overrides(project_overrides))} parametre override aktif")
        else:
            tables.reload_tables()
        st.write("Teknik Efor Hesaplama (3 Profil)...")
        result = calculate_effort(wbs, categories, context)
        st.session_state.effort_result = result

        pt = result.get("proje_toplami", {})
        a_t = pt.get("a", {}).get("toplam", 0)
        b_t = pt.get("b", {}).get("toplam", 0)
        c_t = pt.get("c", {}).get("toplam", 0)

        st.write("Kalite Kontrol...")
        errors = run_checks(wbs, result)
        if errors:
            for e in errors:
                st.write(f"Uyari: {e}")

        # Sonuclari project_manager_v2'ye kaydet
        if project_id:
            st.write("Sonuclar kaydediliyor...")
            meta = pm.load_meta(project_id)
            wbs_version = meta.get("active_wbs_version", "v1") if meta else "v1"
            # Hesaplamada kullanilan (merged) parametreleri kaydet
            if project_overrides:
                params = merged_params
            else:
                params = snapshot_params()
            calc_id = pm.save_calculation(
                project_id, wbs_version, result, categories, context, params
            )
            st.session_state.active_calc_id = calc_id

            # Ayrica legacy output dizinine de kaydet
            _save_legacy_output(result, wbs, categories)

        status.update(label="Hesaplama Tamamlandi!", state="complete")

    # OF kapsam uyarisi
    wp_cat = categories.get("wp_kategorileri", {})
    total_deliverables = sum(len(w.get("deliverables", [])) for w in wp_cat.values())
    of_matched = sum(
        1 for w in wp_cat.values()
        for d in w.get("deliverables", [])
        if d.get("of_match")
    )
    if total_deliverables > 0 and of_matched == total_deliverables:
        st.info(
            f"Bu projede tum deliverable'lar ({of_matched}/{total_deliverables}) "
            f"OneFrame eslesmesine sahip. **Baz Efor degerleri kullanilmiyor** — "
            f"sonuclari degistirmek icin OneFrame Residuel, Carpanlar (kompleksite, "
            f"batch, entegrasyon) veya Faz Yuzdeleri parametrelerini degistirin."
        )
    elif total_deliverables > 0 and of_matched / total_deliverables > 0.8:
        st.info(
            f"Deliverable'larin %{of_matched*100//total_deliverables}'i "
            f"({of_matched}/{total_deliverables}) OneFrame eslesmesine sahip. "
            f"Baz Efor degisiklikleri sinirli etki yapar."
        )

    # Kisa ozet
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Profil A", f"{a_t:.1f} AG")
    col2.metric("Profil B", f"{b_t:.1f} AG")
    col3.metric("Profil C", f"{c_t:.1f} AG")

    if st.button("Sonuclara Git", type="primary", use_container_width=True):
        st.session_state.chat_messages = []
        # Project detail view'a gec
        st.session_state.view_mode = "project_detail"
        st.session_state.detail_tab = "results"
        if project_id:
            pm.save_wizard_state(project_id, "results", [])
        st.rerun()


def _save_legacy_output(result: dict, wbs: dict, categories: dict):
    """Legacy output/ dizinine de kaydet (geriye uyumluluk)."""
    from datetime import datetime
    from src.csv_writer import (
        write_wp_details, write_summary, write_notes,
        write_wbs_details, write_categorization_details,
        write_context_analysis, write_full_export,
    )

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    project_name = result.get("tahmin_ozeti", {}).get("proje_adi", "proje")
    safe_name = project_name.lower().replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")[:30] or "proje"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_path = output_dir / f"{safe_name}_{timestamp}"
    dir_path.mkdir(exist_ok=True)

    try:
        with open(dir_path / "effort_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        with open(dir_path / "wbs.json", "w", encoding="utf-8") as f:
            json.dump(wbs, f, ensure_ascii=False, indent=2)
        if categories:
            with open(dir_path / "categories.json", "w", encoding="utf-8") as f:
                json.dump(categories, f, ensure_ascii=False, indent=2)
        ctx = st.session_state.get("project_context")
        if ctx:
            with open(dir_path / "project_context.json", "w", encoding="utf-8") as f:
                json.dump(ctx, f, ensure_ascii=False, indent=2)
        write_wp_details(result, str(dir_path / f"{safe_name}_wp_detaylari.csv"))
        write_summary(result, str(dir_path / f"{safe_name}_ozet.csv"))
        write_notes(result, str(dir_path / f"{safe_name}_notlar.csv"))
        if wbs:
            write_wbs_details(wbs, str(dir_path / f"{safe_name}_wbs_yapisi.csv"))
        if categories:
            write_categorization_details(categories, str(dir_path / f"{safe_name}_kategorizasyon.csv"))
            write_context_analysis(categories, result, str(dir_path / f"{safe_name}_baglam.csv"))
        try:
            if wbs and categories:
                write_full_export(wbs, categories, result,
                                  str(dir_path / f"{safe_name}_tam_export.xlsx"))
        except ImportError:
            pass
        st.session_state.output_path = str(dir_path)
    except OSError:
        pass


# ── STEP 5: Results (wizard icinde — sonra detail'e yonlendirilir) ──────

def _show_results(project_id: str):
    """Wizard icindeki sonuc gosterimi — normalde project_detail'e yonlendirilir."""
    result = st.session_state.effort_result
    if not result:
        st.warning("Hesaplama sonucu bulunamadi.")
        if st.button("Hesaplamaya Don", type="primary"):
            _go_step("calculate", project_id)
        return

    # Project detail'e yonlendir
    st.session_state.view_mode = "project_detail"
    st.session_state.detail_tab = "results"
    st.rerun()
