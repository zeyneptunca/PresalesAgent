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


def _render_params_inline(project_id: str):
    """Hesaplama parametrelerini inline expander'lar ile gosterir."""
    global_params = load_params()
    # Reset counter — key'leri benzersiz yapmak icin
    _rc = st.session_state.get("_params_reset_counter", 0)
    _pfx = f"dlg{_rc}_"

    overrides = pm.load_project_params_overrides(project_id) if project_id else None
    if overrides:
        import copy
        params = merge_params(global_params, overrides)
    else:
        import copy
        params = copy.deepcopy(global_params)

    CONTEXT_DIM_LABELS = {
        "scale": "Organizasyon Olcegi",
        "team": "Ekip Deneyimi",
        "domain": "Domain Karmasikligi",
        "tech_debt": "Teknik Borc",
        "integration_density": "Entegrasyon Yogunlugu",
    }

    with st.expander("Baz Efor"):
        st.markdown("**Baz Efor Degerleri (FE, BE) — Adam-Gun**")
        profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                               format_func=lambda x: _PROFILE_LABELS[x],
                               key=f"{_pfx}base_profile")
        base = params["base_effort"][profile]
        rows = []
        for cat in CATEGORIES:
            vals = base.get(cat, [0, 0])
            rows.append({"Kategori": cat, "FE": vals[0], "BE": vals[1]})
        df = pd.DataFrame(rows)
        edited = st.data_editor(df, key=f"{_pfx}base_edit_{profile}",
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "Kategori": st.column_config.TextColumn(disabled=True),
                                    "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                    "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                })
        for _, row in edited.iterrows():
            cat = row["Kategori"]
            params["base_effort"][profile][cat] = [round(row["FE"], 2), round(row["BE"], 2)]

    with st.expander("Carpanlar"):
        st.markdown("**Kompleksite Carpanlari**")
        comp_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["complexity_multipliers"][p][level]
            comp_rows.append(row)
        df = pd.DataFrame(comp_rows)
        edited = st.data_editor(df, key=f"{_pfx}complexity_edit", use_container_width=True, hide_index=True,
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
        batch_rows = []
        for p in ["A", "B", "C"]:
            vals = params["batch_multipliers"][p]
            row = {"Profil": p}
            for i, v in enumerate(vals):
                row[f"#{i+1}"] = v
            batch_rows.append(row)
        df = pd.DataFrame(batch_rows)
        edited = st.data_editor(df, key=f"{_pfx}batch_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{f"#{i+1}": st.column_config.NumberColumn(min_value=0, max_value=2.0, step=0.05, format="%.2f")
                                       for i in range(len(params["batch_multipliers"]["A"]))}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            new_vals = []
            for i in range(len(params["batch_multipliers"][p])):
                new_vals.append(round(row[f"#{i+1}"], 2))
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
        edited = st.data_editor(df, key=f"{_pfx}integration_edit", use_container_width=True, hide_index=True,
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

        st.divider()

        st.markdown("**Reuse Carpanlari**")
        reuse_labels = ["Orijinal", "2. kopya", "3. kopya", "4+ kopya"]
        reuse_rows = []
        for p in ["A", "B", "C"]:
            vals = params["reuse_multipliers"][p]
            row = {"Profil": p}
            for i, v in enumerate(vals):
                label = reuse_labels[i] if i < len(reuse_labels) else f"#{i+1}"
                row[label] = v
            reuse_rows.append(row)
        df = pd.DataFrame(reuse_rows)
        edited = st.data_editor(df, key=f"{_pfx}reuse_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{label: st.column_config.NumberColumn(min_value=0, max_value=2.0, step=0.05, format="%.2f")
                                       for label in reuse_labels}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            new_vals = []
            for i in range(len(params["reuse_multipliers"][p])):
                label = reuse_labels[i] if i < len(reuse_labels) else f"#{i+1}"
                new_vals.append(round(row[label], 2))
            params["reuse_multipliers"][p] = new_vals

    with st.expander("Faz Yuzdeleri"):
        st.markdown("**Analiz Yuzdeleri**")
        an_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["analysis_pct"][p][level]
            an_rows.append(row)
        df = pd.DataFrame(an_rows)
        edited = st.data_editor(df, key=f"{_pfx}analysis_edit", use_container_width=True, hide_index=True,
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
        dm_rows = []
        for p in ["A", "B", "C"]:
            dm_rows.append({
                "Profil": p,
                "UI/UX Tasarim": params["design_pct"][p],
                "Yazilim Mimarisi": params["architecture_pct"][p],
            })
        df = pd.DataFrame(dm_rows)
        edited = st.data_editor(df, key=f"{_pfx}design_arch_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    "UI/UX Tasarim": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f"),
                                    "Yazilim Mimarisi": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f"),
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            params["design_pct"][p] = round(row["UI/UX Tasarim"], 2)
            params["architecture_pct"][p] = round(row["Yazilim Mimarisi"], 2)

        st.divider()

        st.markdown("**Test Yuzdeleri**")
        test_rows = []
        for p in ["A", "B", "C"]:
            row = {"Profil": p}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["test_pct"][p][level]
            test_rows.append(row)
        df = pd.DataFrame(test_rows)
        edited = st.data_editor(df, key=f"{_pfx}test_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{level: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                       for level in COMPLEXITY_LEVELS}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["test_pct"][p][level] = round(row[level], 2)

    with st.expander("Global & Bantlar"):
        st.markdown("**Global Efor Yuzdeleri (PM, Tech Design, Deployment, UAT)**")
        st.caption("Profil bazli yuzde formuller — Technical Total uzerine uygulanir.")
        gl_rows = []
        for p in ["A", "B", "C"]:
            f = params["global_formulas"][p]
            gl_rows.append({
                "Profil": p,
                "PM %": f["pm_pct"],
                "Tech Design %": f["tech_design_pct"],
                "Deployment %": f["deployment_pct"],
                "UAT %": f["uat_pct"],
            })
        df = pd.DataFrame(gl_rows)
        edited = st.data_editor(df, key=f"{_pfx}global_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    **{col: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                       for col in ["PM %", "Tech Design %", "Deployment %", "UAT %"]}
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            params["global_formulas"][p] = {
                "pm_pct": round(row["PM %"], 2),
                "tech_design_pct": round(row["Tech Design %"], 2),
                "deployment_pct": round(row["Deployment %"], 2),
                "uat_pct": round(row["UAT %"], 2),
            }

        st.divider()

        st.markdown("**Sabit Taban Degerleri** (B ve C profillerinde uygulanir)")
        st.caption("PM_Base, BA_Base, Test_Base, UAT_Base — bant bazli minimum degerler.")
        fb_rows = []
        for band in ["S", "M", "L", "XL"]:
            b = params["fixed_bases"][band]
            fb_rows.append({
                "Bant": band,
                "PM_Base": b["PM_Base"], "BA_Base": b["BA_Base"],
                "Test_Base": b["Test_Base"], "UAT_Base": b["UAT_Base"],
            })
        df = pd.DataFrame(fb_rows)
        edited = st.data_editor(df, key=f"{_pfx}fixed_bases_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Bant": st.column_config.TextColumn(disabled=True),
                                    **{col: st.column_config.NumberColumn(min_value=0, step=1)
                                       for col in ["PM_Base", "BA_Base", "Test_Base", "UAT_Base"]}
                                })
        for _, row in edited.iterrows():
            band = row["Bant"]
            params["fixed_bases"][band] = {
                "PM_Base": int(row["PM_Base"]), "BA_Base": int(row["BA_Base"]),
                "Test_Base": int(row["Test_Base"]), "UAT_Base": int(row["UAT_Base"]),
            }

        st.divider()

        st.markdown("**Proje Buyukluk Bant Esikleri (AG)**")
        bands = params["size_bands"]
        band_rows = []
        for threshold, label in bands:
            if label != "XL":
                band_rows.append({"Bant": label, "Ust Sinir (AG)": float(threshold)})
            else:
                band_rows.append({"Bant": label, "Ust Sinir (AG)": 9999.0})
        df = pd.DataFrame(band_rows)
        edited = st.data_editor(df, key=f"{_pfx}size_bands_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Bant": st.column_config.TextColumn(disabled=True),
                                    "Ust Sinir (AG)": st.column_config.NumberColumn(min_value=1.0, step=5.0, format="%.0f"),
                                })
        new_bands = []
        for _, row in edited.iterrows():
            label = row["Bant"]
            if label == "XL":
                new_bands.append([1e18, label])
            else:
                new_bands.append([float(row["Ust Sinir (AG)"]), label])
        params["size_bands"] = new_bands

    with st.expander("OneFrame"):
        st.markdown("**OneFrame Residuel Efor Tablosu (FE, BE) — Adam-Gun**")
        st.caption("OF eslesmesi olan deliverable'lar icin Baz Efor yerine bu degerler kullanilir.")
        of_profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                                   format_func=lambda x: _PROFILE_LABELS[x],
                                   key=f"{_pfx}of_profile")
        of_data = params["oneframe_residual"].get(of_profile, {})
        of_rows = []
        for of_code in OF_CODES:
            vals = of_data.get(of_code, [0, 0])
            of_rows.append({"OF Kodu": of_code, "FE": vals[0], "BE": vals[1]})
        of_df = pd.DataFrame(of_rows)
        of_edited = st.data_editor(of_df, key=f"{_pfx}of_edit_{of_profile}",
                                    use_container_width=True, hide_index=True,
                                    column_config={
                                        "OF Kodu": st.column_config.TextColumn(disabled=True),
                                        "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                        "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                    })
        for _, row in of_edited.iterrows():
            of_code = row["OF Kodu"]
            params["oneframe_residual"][of_profile][of_code] = [round(row["FE"], 2), round(row["BE"], 2)]

    with st.expander("Baglam Carpanlari"):
        st.caption("Proje baglami icin AB (Profil A/B) ve C (Profil C) carpanlari.")
        for dim_key, dim_label in CONTEXT_DIM_LABELS.items():
            st.markdown(f"**{dim_label}**")
            dim_data = params["context_multipliers"].get(dim_key, {})
            ctx_rows = []
            for val_key, val_data in dim_data.items():
                ctx_rows.append({
                    "Deger": val_key,
                    "AB Carpan": val_data.get("AB", 1.0),
                    "C Carpan": val_data.get("C", 1.0),
                })
            df = pd.DataFrame(ctx_rows)
            edited = st.data_editor(df, key=f"{_pfx}ctx_{dim_key}", use_container_width=True, hide_index=True,
                                    column_config={
                                        "Deger": st.column_config.TextColumn(disabled=True),
                                        "AB Carpan": st.column_config.NumberColumn(min_value=0, step=0.05, format="%.2f"),
                                        "C Carpan": st.column_config.NumberColumn(min_value=0, step=0.05, format="%.2f"),
                                    })
            for _, row in edited.iterrows():
                val_key = row["Deger"]
                params["context_multipliers"][dim_key][val_key] = {
                    "AB": round(row["AB Carpan"], 2),
                    "C": round(row["C Carpan"], 2),
                }
            st.markdown("")

        st.divider()
        st.markdown("**VibeCoding Baglam Carpani Ust Siniri**")
        cap_rows = [{"Parametre": "Vibe Context Cap", "Deger": float(params.get("vibe_context_cap", 1.35))}]
        df = pd.DataFrame(cap_rows)
        edited = st.data_editor(df, key=f"{_pfx}vibe_cap_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Parametre": st.column_config.TextColumn(disabled=True),
                                    "Deger": st.column_config.NumberColumn(min_value=1.0, max_value=3.0, step=0.05, format="%.2f"),
                                })
        params["vibe_context_cap"] = round(float(edited.iloc[0]["Deger"]), 2)

    with st.expander("Min & Yuvarlama"):
        st.markdown("**Minimum Efor Korumasi**")
        st.caption("Deliverable, WP ve faz bazinda minimum efor degerleri.")
        min_rows = []
        for level in ["deliverable", "wp", "phase"]:
            row = {"Seviye": level}
            for p in ["A", "B", "C"]:
                row[f"Profil {p}"] = params["minimum_effort"][level][p]
            min_rows.append(row)
        df = pd.DataFrame(min_rows)
        edited = st.data_editor(df, key=f"{_pfx}min_effort_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Seviye": st.column_config.TextColumn(disabled=True),
                                    **{f"Profil {p}": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f")
                                       for p in ["A", "B", "C"]}
                                })
        for _, row in edited.iterrows():
            level = row["Seviye"]
            for p in ["A", "B", "C"]:
                params["minimum_effort"][level][p] = round(row[f"Profil {p}"], 1)

        st.divider()

        st.markdown("**Yuvarlama Hassasiyeti**")
        round_rows = []
        for p in ["A", "B", "C"]:
            round_rows.append({"Profil": p, "Hassasiyet": float(params["rounding_precision"][p])})
        df = pd.DataFrame(round_rows)
        edited = st.data_editor(df, key=f"{_pfx}round_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Profil": st.column_config.TextColumn(disabled=True),
                                    "Hassasiyet": st.column_config.NumberColumn(min_value=0.1, max_value=1.0, step=0.1, format="%.1f"),
                                })
        for _, row in edited.iterrows():
            p = row["Profil"]
            params["rounding_precision"][p] = round(float(row["Hassasiyet"]), 1)

        st.divider()

        st.markdown("**Min-Max Araliklari**")
        mm_rows = []
        for level in COMPLEXITY_LEVELS:
            vals = params["min_max_ranges"].get(level, [0.9, 1.1])
            mm_rows.append({"Complexity": level, "Min Carpan": vals[0], "Max Carpan": vals[1]})
        df = pd.DataFrame(mm_rows)
        edited = st.data_editor(df, key=f"{_pfx}minmax_edit", use_container_width=True, hide_index=True,
                                column_config={
                                    "Complexity": st.column_config.TextColumn(disabled=True),
                                    "Min Carpan": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.05, format="%.2f"),
                                    "Max Carpan": st.column_config.NumberColumn(min_value=1.0, max_value=3.0, step=0.05, format="%.2f"),
                                })
        for _, row in edited.iterrows():
            level = row["Complexity"]
            params["min_max_ranges"][level] = [round(row["Min Carpan"], 2), round(row["Max Carpan"], 2)]

    # Duzenlenmis parametreleri session state'e yaz — "Onayla" butonu kullanir
    st.session_state._edited_params = params
    st.session_state._edited_params_global = global_params

    if st.button("Varsayilanlara Don", use_container_width=True, key="dlg_reset"):
        if project_id:
            pm.clear_project_params(project_id)
            tables.reload_tables()
            # Counter artir — tum widget key'leri degisir, eski state'ler gecersiz olur
            st.session_state["_params_reset_counter"] = _rc + 1
            st.session_state.pop("_edited_params", None)
            st.session_state.pop("_edited_params_global", None)
            st.toast("Varsayilan parametreler yuklendi")
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
    # Hesaplama adimina yeniden girildiginde flag temizle
    if step == "calculate":
        st.session_state.pop("_calc_done", None)
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

    # Hesaplama Parametreleri — inline
    _render_params_inline(project_id)

    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Onayla ve Efor Hesapla", type="primary", use_container_width=True):
            # Duzenlenmis parametreleri otomatik kaydet
            edited_params = st.session_state.get("_edited_params")
            edited_global = st.session_state.get("_edited_params_global")
            if edited_params and edited_global and project_id:
                project_overrides = extract_overrides(edited_params, edited_global)
                pm.save_project_params(project_id, project_overrides)
                merged = merge_params(edited_global, project_overrides)
                tables.reload_tables(merged)
            st.session_state.project_context = context
            _go_step("calculate", project_id)
    with btn_col2:
        if st.button("WBS Duzenlemeye Don", use_container_width=True):
            _go_step("wbs_edit", project_id)


# ── STEP 4: Calculate ──────────────────────────────────────────────────────

def _show_calculate(project_id: str):
    st.header("Efor Hesaplama")

    # Rerun'da tekrar hesaplama yapmayi onle
    if st.session_state.get("_calc_done"):
        result = st.session_state.effort_result
        if result:
            pt = result.get("proje_toplami", {})
            st.success("Hesaplama Tamamlandi!")
        else:
            st.warning("Hesaplama sonucu bulunamadi.")
    else:
        wbs = st.session_state.wbs
        context = st.session_state.project_context
        categories = st.session_state.categories

        with st.status("Efor Hesaplama Baslatiliyor...", expanded=True) as status:
            st.write("Parametreler yukleniyor...")
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
                if project_overrides:
                    params = merged_params
                else:
                    params = snapshot_params()
                calc_id = pm.save_calculation(
                    project_id, wbs_version, result, categories, context, params
                )
                st.session_state.active_calc_id = calc_id

                _save_legacy_output(result, wbs, categories)

            status.update(label="Hesaplama Tamamlandi!", state="complete")
            st.session_state["_calc_done"] = True

    # OF kapsam uyarisi
    categories = st.session_state.categories or {}
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
    """Legacy output/ dizinine kaydet."""
    from datetime import datetime
    from src.csv_writer import write_full_export

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
        if wbs and categories:
            write_full_export(wbs, categories, result,
                              str(dir_path / f"{safe_name}_tam_export.xlsx"))
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
