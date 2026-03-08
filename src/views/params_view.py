"""Parametre Ayarlari — ana ekranda gosterilen parametre duzenleyici."""

import streamlit as st
import pandas as pd

from src.param_manager import load_params, save_params, get_defaults, reset_to_defaults, diff_from_defaults
import src.effort_tables as tables

CATEGORIES = [
    "SIMPLE_UI", "COMPLEX_UI", "FILE_PROCESS", "EXPORT_REPORT",
    "BACKGROUND_JOB", "INTEGRATION", "RULE_ENGINE", "AUTH_COMPONENT",
]

COMPLEXITY_LEVELS = ["low", "medium", "high", "very_high"]

PROFILE_LABELS = {"A": "Profil A (Geleneksel)", "B": "Profil B (Copilot+Claude)", "C": "Profil C (VibeCoding)"}

CONTEXT_DIM_LABELS = {
    "scale": "Organizasyon Olcegi",
    "team": "Ekip Deneyimi",
    "domain": "Domain Karmasikligi",
    "tech_debt": "Teknik Borc",
    "integration_density": "Entegrasyon Yogunlugu",
}

OF_CODES = [
    "OF-AUTH", "OF-AUTHZ", "OF-CRUD", "OF-DATA", "OF-AUDIT", "OF-CACHE",
    "OF-SEARCH", "OF-MULTI", "OF-CICD", "OF-CLOUD", "OF-UI", "OF-FORM",
    "OF-TABLE", "OF-MENU", "OF-DASH", "OF-PROFILE", "OF-REPORT", "OF-NOTIF",
    "OF-HANGFIRE", "OF-RULE", "OF-WORKFLOW", "OF-DMS", "OF-FILE", "OF-UPLOAD",
    "OF-CMS", "OF-FAQ", "OF-VALID", "OF-I18N", "OF-ERR", "OF-CHATBOT",
    "OF-APIGW", "OF-SIGNAL",
]


def _load_current():
    if "params" not in st.session_state:
        st.session_state.params = load_params()


def _show_base_effort(params: dict):
    st.subheader("Baz Efor Degerleri (FE, BE) — Adam-Gun")
    st.caption("Her kategori ve profil icin Frontend (FE) ve Backend (BE) baz efor degerleri.")

    profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                           format_func=lambda x: PROFILE_LABELS[x],
                           key="pv_base_effort_profile")

    base = params["base_effort"][profile]
    rows = []
    for cat in CATEGORIES:
        vals = base.get(cat, [0, 0])
        rows.append({"Kategori": cat, "FE": vals[0], "BE": vals[1]})

    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key=f"pv_base_effort_edit_{profile}",
                            use_container_width=True, hide_index=True,
                            column_config={
                                "Kategori": st.column_config.TextColumn(disabled=True),
                                "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                            })

    for _, row in edited.iterrows():
        cat = row["Kategori"]
        params["base_effort"][profile][cat] = [round(row["FE"], 2), round(row["BE"], 2)]


def _show_multipliers(params: dict):
    st.subheader("Carpanlar")

    st.markdown("**Batch Carpanlari**")
    for profile in ["A", "B", "C"]:
        vals = params["batch_multipliers"][profile]
        cols = st.columns(len(vals) + 1)
        cols[0].markdown(f"**{profile}**")
        new_vals = []
        for i, v in enumerate(vals):
            nv = cols[i + 1].number_input(f"#{i+1}", value=float(v), step=0.05,
                                          min_value=0.0, max_value=2.0,
                                          key=f"pv_batch_{profile}_{i}", label_visibility="collapsed")
            new_vals.append(round(nv, 2))
        params["batch_multipliers"][profile] = new_vals

    st.divider()

    st.markdown("**Kompleksite Carpanlari**")
    rows = []
    for profile in ["A", "B", "C"]:
        row = {"Profil": profile}
        for level in COMPLEXITY_LEVELS:
            row[level] = params["complexity_multipliers"][profile][level]
        rows.append(row)

    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_complexity_edit", use_container_width=True, hide_index=True,
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

    st.markdown("**Entegrasyon Carpanlari**")
    rows = []
    for profile in ["A", "B", "C"]:
        row = {"Profil": profile}
        for k in ["0", "1", "3"]:
            row[f"Nokta {k}"] = params["integration_multipliers"][profile].get(k, 1.0)
        rows.append(row)
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_integration_edit", use_container_width=True, hide_index=True,
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
    for profile in ["A", "B", "C"]:
        vals = params["reuse_multipliers"][profile]
        cols = st.columns(len(vals) + 1)
        cols[0].markdown(f"**{profile}**")
        new_vals = []
        for i, v in enumerate(vals):
            label = ["Orijinal", "2. kopya", "3. kopya", "4+ kopya"][i] if i < 4 else f"#{i+1}"
            nv = cols[i + 1].number_input(label, value=float(v), step=0.05,
                                          min_value=0.0, max_value=2.0,
                                          key=f"pv_reuse_{profile}_{i}")
            new_vals.append(round(nv, 2))
        params["reuse_multipliers"][profile] = new_vals


def _show_phase_pcts(params: dict):
    st.subheader("Faz Hesaplama Yuzdeleri")

    st.markdown("**Analiz Yuzdeleri**")
    rows = []
    for profile in ["A", "B", "C"]:
        row = {"Profil": profile}
        for level in COMPLEXITY_LEVELS:
            row[level] = params["analysis_pct"][profile][level]
        rows.append(row)
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_analysis_edit", use_container_width=True, hide_index=True,
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
    cols = st.columns(2)
    with cols[0]:
        st.caption("UI/UX Tasarim")
        for p in ["A", "B", "C"]:
            params["design_pct"][p] = round(st.number_input(
                f"Profil {p}", value=float(params["design_pct"][p]),
                step=0.01, min_value=0.0, max_value=1.0,
                key=f"pv_design_{p}", format="%.2f"), 2)
    with cols[1]:
        st.caption("Yazilim Mimarisi")
        for p in ["A", "B", "C"]:
            params["architecture_pct"][p] = round(st.number_input(
                f"Profil {p}", value=float(params["architecture_pct"][p]),
                step=0.01, min_value=0.0, max_value=1.0,
                key=f"pv_arch_{p}", format="%.2f"), 2)

    st.divider()

    st.markdown("**Test Yuzdeleri**")
    rows = []
    for profile in ["A", "B", "C"]:
        row = {"Profil": profile}
        for level in COMPLEXITY_LEVELS:
            row[level] = params["test_pct"][profile][level]
        rows.append(row)
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_test_edit", use_container_width=True, hide_index=True,
                            column_config={
                                "Profil": st.column_config.TextColumn(disabled=True),
                                **{level: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                   for level in COMPLEXITY_LEVELS}
                            })
    for _, row in edited.iterrows():
        p = row["Profil"]
        for level in COMPLEXITY_LEVELS:
            params["test_pct"][p][level] = round(row[level], 2)


def _show_global(params: dict):
    st.subheader("Global Efor Formulleri")

    st.markdown("**Yuzde Bazli Formuller**")
    rows = []
    for profile in ["A", "B", "C"]:
        f = params["global_formulas"][profile]
        rows.append({
            "Profil": profile,
            "PM %": f["pm_pct"],
            "Tech Design %": f["tech_design_pct"],
            "Deployment %": f["deployment_pct"],
            "UAT %": f["uat_pct"],
        })
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_global_edit", use_container_width=True, hide_index=True,
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

    st.markdown("**Sabit Taban Degerleri** (B ve C)")
    rows = []
    for band in ["S", "M", "L", "XL"]:
        b = params["fixed_bases"][band]
        rows.append({
            "Bant": band,
            "PM_Base": b["PM_Base"], "BA_Base": b["BA_Base"],
            "Test_Base": b["Test_Base"], "UAT_Base": b["UAT_Base"],
        })
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_fixed_bases_edit", use_container_width=True, hide_index=True,
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

    st.markdown("**Proje Buyukluk Bant Esikleri**")
    bands = params["size_bands"]
    cols = st.columns(len(bands))
    new_bands = []
    for i, (threshold, label) in enumerate(bands):
        with cols[i]:
            st.markdown(f"**{label}**")
            if label != "XL":
                t = st.number_input(f"Ust sinir", value=float(threshold),
                                    step=5.0, min_value=1.0,
                                    key=f"pv_band_{label}")
                new_bands.append([t, label])
            else:
                st.caption("Sonsuz")
                new_bands.append([1e18, label])
    params["size_bands"] = new_bands


def _show_oneframe(params: dict):
    st.subheader("OneFrame Residuel Efor Tablosu")

    profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                           format_func=lambda x: PROFILE_LABELS[x],
                           key="pv_of_profile")

    of_data = params["oneframe_residual"].get(profile, {})
    rows = []
    for of_code in OF_CODES:
        vals = of_data.get(of_code, [0, 0])
        rows.append({"OF Kodu": of_code, "FE": vals[0], "BE": vals[1]})

    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key=f"pv_of_edit_{profile}", use_container_width=True, hide_index=True,
                            column_config={
                                "OF Kodu": st.column_config.TextColumn(disabled=True),
                                "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                            })
    for _, row in edited.iterrows():
        of_code = row["OF Kodu"]
        params["oneframe_residual"][profile][of_code] = [round(row["FE"], 2), round(row["BE"], 2)]


def _show_context_multipliers(params: dict):
    st.subheader("Baglam Carpanlari")

    for dim_key, dim_label in CONTEXT_DIM_LABELS.items():
        st.markdown(f"**{dim_label}**")
        dim_data = params["context_multipliers"].get(dim_key, {})
        rows = []
        for val_key, val_data in dim_data.items():
            rows.append({
                "Deger": val_key,
                "AB Carpan": val_data.get("AB", 1.0),
                "C Carpan": val_data.get("C", 1.0),
            })
        df = pd.DataFrame(rows)
        edited = st.data_editor(df, key=f"pv_ctx_{dim_key}", use_container_width=True, hide_index=True,
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
    params["vibe_context_cap"] = round(st.number_input(
        "VibeCoding Baglam Carpani Ust Siniri",
        value=float(params.get("vibe_context_cap", 1.35)),
        step=0.05, min_value=1.0, max_value=3.0,
        key="pv_vibe_cap", format="%.2f"), 2)


def _show_minimums(params: dict):
    st.subheader("Minimum Efor Korumasi")

    rows = []
    for level in ["deliverable", "wp", "phase"]:
        row = {"Seviye": level}
        for p in ["A", "B", "C"]:
            row[f"Profil {p}"] = params["minimum_effort"][level][p]
        rows.append(row)
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_min_effort_edit", use_container_width=True, hide_index=True,
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
    cols = st.columns(3)
    for i, p in enumerate(["A", "B", "C"]):
        with cols[i]:
            params["rounding_precision"][p] = round(st.number_input(
                f"Profil {p}", value=float(params["rounding_precision"][p]),
                step=0.1, min_value=0.1, max_value=1.0,
                key=f"pv_round_{p}", format="%.1f"), 1)

    st.divider()

    st.markdown("**Min-Max Araliklari**")
    rows = []
    for level in COMPLEXITY_LEVELS:
        vals = params["min_max_ranges"].get(level, [0.9, 1.1])
        rows.append({"Complexity": level, "Min Carpan": vals[0], "Max Carpan": vals[1]})
    df = pd.DataFrame(rows)
    edited = st.data_editor(df, key="pv_minmax_edit", use_container_width=True, hide_index=True,
                            column_config={
                                "Complexity": st.column_config.TextColumn(disabled=True),
                                "Min Carpan": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.05, format="%.2f"),
                                "Max Carpan": st.column_config.NumberColumn(min_value=1.0, max_value=3.0, step=0.05, format="%.2f"),
                            })
    for _, row in edited.iterrows():
        level = row["Complexity"]
        params["min_max_ranges"][level] = [round(row["Min Carpan"], 2), round(row["Max Carpan"], 2)]


def _count_section_diffs(diffs: list, section_keys: list[str]) -> int:
    count = 0
    for d in diffs:
        for key in section_keys:
            if key in d:
                count += 1
                break
    return count


def show_params():
    """Parametre ayarlarini ana ekranda goster."""
    st.header("Parametre Ayarlari")
    st.caption("Efor hesaplama motorundaki tum parametreleri duzenleyin. "
               "Degisiklikler kaydedildiginde bir sonraki hesaplamada kullanilir.")

    _load_current()
    params = st.session_state.params

    # Fark analizi
    diffs = diff_from_defaults(params)
    total_diffs = len(diffs)

    # Ust butonlar
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Kaydet", type="primary", use_container_width=True, key="pv_save"):
                errors = save_params(params)
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    tables.reload_tables()
                    st.toast("Parametreler kaydedildi")
                    st.success("Parametreler kaydedildi ve yuklendi.")
        with col2:
            if st.button("Tum Varsayilanlara Don", use_container_width=True, key="pv_reset"):
                reset_to_defaults()
                tables.reload_tables()
                st.session_state.params = get_defaults()
                st.toast("Varsayilanlar yuklendi")
                st.rerun()
        with col3:
            if total_diffs > 0:
                st.info(f"{total_diffs} parametre varsayilandan farkli")
            else:
                st.success("Tum parametreler varsayilan degerlerde")

    # Tab'lar
    tab_sections = {
        "Baz Efor": ["base_effort"],
        "Carpanlar": ["batch", "complexity", "integration", "reuse"],
        "Faz Yuzdeleri": ["analysis", "design", "architecture", "test"],
        "Global": ["global", "fixed_bases", "size_bands"],
        "OneFrame": ["oneframe"],
        "Baglam": ["context", "vibe"],
        "Min & Yuvarlama": ["minimum", "rounding", "min_max"],
    }

    tab_names = []
    for name, keys in tab_sections.items():
        n = _count_section_diffs(diffs, keys)
        tab_names.append(f"{name} ({n})" if n > 0 else name)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)

    with tab1:
        _show_base_effort(params)
    with tab2:
        _show_multipliers(params)
    with tab3:
        _show_phase_pcts(params)
    with tab4:
        _show_global(params)
    with tab5:
        _show_oneframe(params)
    with tab6:
        _show_context_multipliers(params)
    with tab7:
        _show_minimums(params)
