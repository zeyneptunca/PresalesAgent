"""Parametre Ayarlari — ana ekranda gosterilen parametre duzenleyici.

Her bolum st.form icinde render edilir — hucre duzenlemeleri rerun
tetiklemez, sadece 'Kaydet' butonuyla topluca kaydedilir.
"""

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


def _save_and_reload(params: dict) -> bool:
    """Parametre kaydet, tablo yukle, toast goster. Basarili ise True."""
    errors = save_params(params)
    if errors:
        for e in errors:
            st.error(e)
        return False
    tables.reload_tables()
    st.session_state.params = load_params()
    st.toast("Parametreler kaydedildi")
    return True


# ── Section renderers ──────────────────────────────────────────────────────
# Her fonksiyon st.form icerir. Form submit edilince params guncellenir
# ve diske kaydedilir. Form icinde data_editor rerun TETIKLEMEZ.


def _show_base_effort(params: dict):
    st.markdown(
        "Her deliverable'in temel efor degeri, kategorisine gore bu tablodan alinir. "
        "**FE** (Frontend) ve **BE** (Backend) olarak ayri tanimlanir. "
        "Tum hesaplama bu degerlerden baslar — carpanlar (batch, entegrasyon, kompleksite) sirayla bu degerlerin uzerine uygulanir."
    )

    # Profil secici form DISINDA — degistirince sadece tablo yenilenir
    profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                           format_func=lambda x: PROFILE_LABELS[x],
                           key="pv_base_effort_profile")

    base = params["base_effort"][profile]
    rows = []
    for cat in CATEGORIES:
        vals = base.get(cat, [0, 0])
        rows.append({"Kategori": cat, "FE": vals[0], "BE": vals[1]})

    with st.form("pv_form_base_effort"):
        df = pd.DataFrame(rows)
        edited = st.data_editor(df, key=f"pv_base_effort_edit_{profile}",
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "Kategori": st.column_config.TextColumn(disabled=True),
                                    "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                    "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                })
        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for _, row in edited.iterrows():
            cat = row["Kategori"]
            params["base_effort"][profile][cat] = [round(row["FE"], 2), round(row["BE"], 2)]
        _save_and_reload(params)
        st.rerun()


def _show_multipliers(params: dict):
    st.markdown(
        "Baz efor uzerine sirayla uygulanan carpanlar. "
        "Hesaplama sirasi: her deliverable icin **Batch** → sonra WP seviyesinde **Entegrasyon** → **Kompleksite**. "
        "**Reuse** ise faz dagilimi yapildiktan sonra WP toplamina uygulanir."
    )

    with st.form("pv_form_multipliers"):
        st.markdown("**Kompleksite Carpanlari**")
        st.caption("Deliverable toplamina (FE+BE) WP seviyesinde uygulanir. "
                   "Ornek: FE+BE=5 AG ve high=1.25 ise → 5 x 1.25 = 6.25 AG.")
        comp_rows = []
        for profile in ["A", "B", "C"]:
            row = {"Profil": profile}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["complexity_multipliers"][profile][level]
            comp_rows.append(row)
        df = pd.DataFrame(comp_rows)
        comp_edited = st.data_editor(df, key="pv_complexity_edit", use_container_width=True, hide_index=True,
                                     column_config={
                                         "Profil": st.column_config.TextColumn(disabled=True),
                                         **{level: st.column_config.NumberColumn(min_value=0, step=0.05, format="%.2f")
                                            for level in COMPLEXITY_LEVELS}
                                     })

        st.divider()

        st.markdown("**Batch Carpanlari**")
        st.caption("Her deliverable'in **kendi baz eforuna (FE ve BE)** ayri ayri uygulanir. "
                   "Ayni kategoride birden fazla deliverable oldugunda sirasina gore indirim yapilir. "
                   "Ornek: 3. SIMPLE_UI deliverable'i icin FE=0.8 x 0.6 = 0.48 AG.")
        batch_rows = []
        for profile in ["A", "B", "C"]:
            vals = params["batch_multipliers"][profile]
            row = {"Profil": profile}
            for i, v in enumerate(vals):
                row[f"#{i+1}"] = v
            batch_rows.append(row)
        df = pd.DataFrame(batch_rows)
        batch_edited = st.data_editor(df, key="pv_batch_edit", use_container_width=True, hide_index=True,
                                      column_config={
                                          "Profil": st.column_config.TextColumn(disabled=True),
                                          **{f"#{i+1}": st.column_config.NumberColumn(min_value=0, max_value=2.0, step=0.05, format="%.2f")
                                             for i in range(len(params["batch_multipliers"]["A"]))}
                                      })

        st.divider()

        st.markdown("**Entegrasyon Carpanlari**")
        st.caption("WP'nin **deliverable toplamina (FE+BE)** uygulanir. Entegrasyon noktasi sayisina gore: "
                   "0 nokta = carpan yok, 1-2 nokta = orta, 3+ nokta = yuksek. "
                   "Batch'ten sonra, kompleksite'den once uygulanir.")
        int_rows = []
        for profile in ["A", "B", "C"]:
            row = {"Profil": profile}
            for k in ["0", "1", "3"]:
                row[f"Nokta {k}"] = params["integration_multipliers"][profile].get(k, 1.0)
            int_rows.append(row)
        df = pd.DataFrame(int_rows)
        int_edited = st.data_editor(df, key="pv_integration_edit", use_container_width=True, hide_index=True,
                                    column_config={
                                        "Profil": st.column_config.TextColumn(disabled=True),
                                        **{f"Nokta {k}": st.column_config.NumberColumn(min_value=0, step=0.05, format="%.2f")
                                           for k in ["0", "1", "3"]}
                                    })

        st.divider()

        st.markdown("**Reuse Carpanlari**")
        st.caption("Faz dagilimi yapildiktan sonra **WP toplamina** (analiz+tasarim+mimari+FE+BE+test) uygulanir. "
                   "Farkli modullerde tekrar eden benzer WP'lere indirim saglar. "
                   "Ilk WP tam efor, 2. kopya %70, 3. kopya %50, 4+ kopya %40.")
        reuse_labels = ["Orijinal", "2. kopya", "3. kopya", "4+ kopya"]
        reuse_rows = []
        for profile in ["A", "B", "C"]:
            vals = params["reuse_multipliers"][profile]
            row = {"Profil": profile}
            for i, v in enumerate(vals):
                label = reuse_labels[i] if i < len(reuse_labels) else f"#{i+1}"
                row[label] = v
            reuse_rows.append(row)
        df = pd.DataFrame(reuse_rows)
        reuse_edited = st.data_editor(df, key="pv_reuse_edit", use_container_width=True, hide_index=True,
                                      column_config={
                                          "Profil": st.column_config.TextColumn(disabled=True),
                                          **{label: st.column_config.NumberColumn(min_value=0, max_value=2.0, step=0.05, format="%.2f")
                                             for label in reuse_labels}
                                      })

        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for _, row in comp_edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["complexity_multipliers"][p][level] = round(row[level], 2)

        for _, row in batch_edited.iterrows():
            p = row["Profil"]
            new_vals = []
            for i in range(len(params["batch_multipliers"][p])):
                new_vals.append(round(row[f"#{i+1}"], 2))
            params["batch_multipliers"][p] = new_vals

        for _, row in int_edited.iterrows():
            p = row["Profil"]
            params["integration_multipliers"][p]["0"] = round(row["Nokta 0"], 2)
            params["integration_multipliers"][p]["1"] = round(row["Nokta 1"], 2)
            params["integration_multipliers"][p]["2"] = round(row["Nokta 1"], 2)
            params["integration_multipliers"][p]["3"] = round(row["Nokta 3"], 2)

        for _, row in reuse_edited.iterrows():
            p = row["Profil"]
            new_vals = []
            for i in range(len(params["reuse_multipliers"][p])):
                label = reuse_labels[i] if i < len(reuse_labels) else f"#{i+1}"
                new_vals.append(round(row[label], 2))
            params["reuse_multipliers"][p] = new_vals

        _save_and_reload(params)
        st.rerun()


def _show_phase_pcts(params: dict):
    st.markdown(
        "Carpanlar uygulandiktan sonra ortaya cikan **FE** ve **BE** degerleri dogrudan faz olarak yazilir. "
        "Diger fazlar (Analiz, Tasarim, Mimari, Test) ise bu degerlerden yuzde hesabiyla turetilir."
    )

    with st.form("pv_form_phase"):
        st.markdown("**Analiz Yuzdeleri**")
        st.caption("**FE+BE toplami** (dev_total) ile carpilir. Kompleksite seviyesine gore degisir. "
                   "Ornek: FE+BE=6 AG, high=%24 → Analiz = 6 x 0.24 = 1.44 AG.")
        an_rows = []
        for profile in ["A", "B", "C"]:
            row = {"Profil": profile}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["analysis_pct"][profile][level]
            an_rows.append(row)
        df = pd.DataFrame(an_rows)
        an_edited = st.data_editor(df, key="pv_analysis_edit", use_container_width=True, hide_index=True,
                                   column_config={
                                       "Profil": st.column_config.TextColumn(disabled=True),
                                       **{level: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                          for level in COMPLEXITY_LEVELS}
                                   })

        st.divider()

        st.markdown("**Tasarim & Mimari Yuzdeleri**")
        st.caption("UI/UX Tasarim → **sadece FE** (adj_fe) ile carpilir. "
                   "Yazilim Mimarisi → **FE+BE toplami** (dev_total) ile carpilir. Tum kompleksite seviyelerinde sabittir.")
        dm_rows = []
        for p in ["A", "B", "C"]:
            dm_rows.append({
                "Profil": p,
                "UI/UX Tasarim": params["design_pct"][p],
                "Yazilim Mimarisi": params["architecture_pct"][p],
            })
        df = pd.DataFrame(dm_rows)
        dm_edited = st.data_editor(df, key="pv_design_arch_edit", use_container_width=True, hide_index=True,
                                   column_config={
                                       "Profil": st.column_config.TextColumn(disabled=True),
                                       "UI/UX Tasarim": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f"),
                                       "Yazilim Mimarisi": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f"),
                                   })

        st.divider()

        st.markdown("**Test Yuzdeleri**")
        st.caption("**FE+BE toplami** (dev_total) ile carpilir. Kompleksite arttikca test orani da artar. "
                   "Ornek: FE+BE=6 AG, high=%36 → Test = 6 x 0.36 = 2.16 AG.")
        test_rows = []
        for profile in ["A", "B", "C"]:
            row = {"Profil": profile}
            for level in COMPLEXITY_LEVELS:
                row[level] = params["test_pct"][profile][level]
            test_rows.append(row)
        df = pd.DataFrame(test_rows)
        test_edited = st.data_editor(df, key="pv_test_edit", use_container_width=True, hide_index=True,
                                     column_config={
                                         "Profil": st.column_config.TextColumn(disabled=True),
                                         **{level: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                            for level in COMPLEXITY_LEVELS}
                                     })

        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for _, row in an_edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["analysis_pct"][p][level] = round(row[level], 2)

        for _, row in dm_edited.iterrows():
            p = row["Profil"]
            params["design_pct"][p] = round(row["UI/UX Tasarim"], 2)
            params["architecture_pct"][p] = round(row["Yazilim Mimarisi"], 2)

        for _, row in test_edited.iterrows():
            p = row["Profil"]
            for level in COMPLEXITY_LEVELS:
                params["test_pct"][p][level] = round(row[level], 2)

        _save_and_reload(params)
        st.rerun()


def _show_global(params: dict):
    st.markdown(
        "WP bazli hesaplamalar bittikten sonra proje geneline eklenen eforlar. "
        "**Teknik toplam** = tum WP'lerin faz dahil toplam eforu (analiz+tasarim+mimari+FE+BE+test)."
    )

    with st.form("pv_form_global"):
        st.markdown("**Yuzde Bazli Formuller**")
        st.caption("**Teknik toplam** ile carpilir. "
                   "Profil A: yuzde x teknik toplam. "
                   "Profil B/C: Sabit Taban + (yuzde x teknik toplam). "
                   "Ornek: UAT %15, teknik toplam 80 AG, UAT_Base 2 → B icin UAT = 2 + (0.15 x 80) = 14 AG.")
        gl_rows = []
        for profile in ["A", "B", "C"]:
            f = params["global_formulas"][profile]
            gl_rows.append({
                "Profil": profile,
                "PM %": f["pm_pct"],
                "Tech Design %": f["tech_design_pct"],
                "Deployment %": f["deployment_pct"],
                "UAT %": f["uat_pct"],
            })
        df = pd.DataFrame(gl_rows)
        gl_edited = st.data_editor(df, key="pv_global_edit", use_container_width=True, hide_index=True,
                                   column_config={
                                       "Profil": st.column_config.TextColumn(disabled=True),
                                       **{col: st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.01, format="%.2f")
                                          for col in ["PM %", "Tech Design %", "Deployment %", "UAT %"]}
                                   })

        st.divider()

        st.markdown("**Sabit Taban Degerleri** (B ve C)")
        st.caption("Proje buyukluk bandina gore B ve C profillerinde yuzde hesabinin ustune eklenen sabit adam-gun. "
                   "A profilinde sabit taban kullanilmaz — sadece yuzde hesabi yapilir.")
        fb_rows = []
        for band in ["S", "M", "L", "XL"]:
            b = params["fixed_bases"][band]
            fb_rows.append({
                "Bant": band,
                "PM_Base": b["PM_Base"], "BA_Base": b["BA_Base"],
                "Test_Base": b["Test_Base"], "UAT_Base": b["UAT_Base"],
            })
        df = pd.DataFrame(fb_rows)
        fb_edited = st.data_editor(df, key="pv_fixed_bases_edit", use_container_width=True, hide_index=True,
                                   column_config={
                                       "Bant": st.column_config.TextColumn(disabled=True),
                                       **{col: st.column_config.NumberColumn(min_value=0, step=1)
                                          for col in ["PM_Base", "BA_Base", "Test_Base", "UAT_Base"]}
                                   })

        st.divider()

        st.markdown("**Proje Buyukluk Bant Esikleri**")
        st.caption("Teknik toplam adam-gune gore proje hangi buyukluk bandina duser. "
                   "Bant, sabit taban degerlerini ve global formulleri etkiler.")
        bands = params["size_bands"]
        band_rows = []
        for threshold, label in bands:
            if label != "XL":
                band_rows.append({"Bant": label, "Ust Sinir (AG)": float(threshold)})
            else:
                band_rows.append({"Bant": label, "Ust Sinir (AG)": 9999.0})
        df = pd.DataFrame(band_rows)
        band_edited = st.data_editor(df, key="pv_size_bands_edit", use_container_width=True, hide_index=True,
                                     column_config={
                                         "Bant": st.column_config.TextColumn(disabled=True),
                                         "Ust Sinir (AG)": st.column_config.NumberColumn(min_value=1.0, step=5.0, format="%.0f"),
                                     })

        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for _, row in gl_edited.iterrows():
            p = row["Profil"]
            params["global_formulas"][p] = {
                "pm_pct": round(row["PM %"], 2),
                "tech_design_pct": round(row["Tech Design %"], 2),
                "deployment_pct": round(row["Deployment %"], 2),
                "uat_pct": round(row["UAT %"], 2),
            }

        for _, row in fb_edited.iterrows():
            band = row["Bant"]
            params["fixed_bases"][band] = {
                "PM_Base": int(row["PM_Base"]), "BA_Base": int(row["BA_Base"]),
                "Test_Base": int(row["Test_Base"]), "UAT_Base": int(row["UAT_Base"]),
            }

        new_bands = []
        for _, row in band_edited.iterrows():
            label = row["Bant"]
            if label == "XL":
                new_bands.append([1e18, label])
            else:
                new_bands.append([float(row["Ust Sinir (AG)"]), label])
        params["size_bands"] = new_bands

        _save_and_reload(params)
        st.rerun()


def _show_oneframe(params: dict):
    st.markdown(
        "OneFrame platformu uzerinde deliver edilen componentlerin **residuel (artik) efor** degerleri. "
        "Bir deliverable OneFrame koduyla eslestiginde, normal baz efor yerine bu degerler kullanilir. "
        "Daha dusuk degerler = OneFrame'in o component icin sagladigi hazir altyapinin daha fazla oldugu anlamina gelir."
    )

    profile = st.selectbox("Profil Sec", ["A", "B", "C"],
                           format_func=lambda x: PROFILE_LABELS[x],
                           key="pv_of_profile")

    of_data = params["oneframe_residual"].get(profile, {})
    rows = []
    for of_code in OF_CODES:
        vals = of_data.get(of_code, [0, 0])
        rows.append({"OF Kodu": of_code, "FE": vals[0], "BE": vals[1]})

    with st.form("pv_form_oneframe"):
        df = pd.DataFrame(rows)
        edited = st.data_editor(df, key=f"pv_of_edit_{profile}", use_container_width=True, hide_index=True,
                                column_config={
                                    "OF Kodu": st.column_config.TextColumn(disabled=True),
                                    "FE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                    "BE": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
                                })
        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for _, row in edited.iterrows():
            of_code = row["OF Kodu"]
            params["oneframe_residual"][profile][of_code] = [round(row["FE"], 2), round(row["BE"], 2)]
        _save_and_reload(params)
        st.rerun()


def _show_context_multipliers(params: dict):
    st.markdown(
        "**(Teknik toplam + Global toplam)** uzerine uygulanan son carpan. "
        "5 boyutun carpanlari birbiriyle carpilarak birlesik faktor olusturulur. "
        "A ve B profilleri ayni carpani (AB) kullanir, C profili icin ayri bir carpan vardir. "
        "Ornek: AB faktor=1.15 ve teknik+global=100 AG → proje toplam = 100 x 1.15 = 115 AG."
    )

    with st.form("pv_form_context"):
        ctx_captions = {
            "scale": "Musteri organizasyonunun buyuklugu. Buyuk organizasyonlar daha fazla koordinasyon ve uyum sureci gerektirir.",
            "team": "Gelistirme ekibinin deneyim seviyesi. Junior ekipler daha fazla efor harcar, uzman ekipler daha az.",
            "domain": "Projenin faaliyet alani. Finans, saglik gibi regulasyonlu alanlar ekstra efor gerektirir.",
            "tech_debt": "Mevcut kod tabaninin durumu. Legacy sistemlere entegrasyon veya modernizasyon ek efor gerektirir.",
            "integration_density": "Projedeki benzersiz dis entegrasyon sayisi. Fazla entegrasyon koordinasyon ve test yukunu arttirir.",
        }
        all_ctx_edited = {}
        for dim_key, dim_label in CONTEXT_DIM_LABELS.items():
            st.markdown(f"**{dim_label}**")
            st.caption(ctx_captions[dim_key])
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
            all_ctx_edited[dim_key] = edited
            st.markdown("")

        st.divider()
        st.markdown("**VibeCoding Baglam Carpani Ust Siniri**")
        st.caption("C profilinin birlesik baglam carpani bu degeri asamaz. "
                   "Amac: VibeCoding'in maliyet avantajini korumak.")
        cap_rows = [{"Parametre": "Vibe Context Cap", "Deger": float(params.get("vibe_context_cap", 1.35))}]
        df = pd.DataFrame(cap_rows)
        cap_edited = st.data_editor(df, key="pv_vibe_cap_edit", use_container_width=True, hide_index=True,
                                    column_config={
                                        "Parametre": st.column_config.TextColumn(disabled=True),
                                        "Deger": st.column_config.NumberColumn(min_value=1.0, max_value=3.0, step=0.05, format="%.2f"),
                                    })

        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for dim_key, edited in all_ctx_edited.items():
            for _, row in edited.iterrows():
                val_key = row["Deger"]
                params["context_multipliers"][dim_key][val_key] = {
                    "AB": round(row["AB Carpan"], 2),
                    "C": round(row["C Carpan"], 2),
                }
        params["vibe_context_cap"] = round(float(cap_edited.iloc[0]["Deger"]), 2)
        _save_and_reload(params)
        st.rerun()


def _show_minimums(params: dict):
    st.markdown(
        "Hesaplama sonucunda herhangi bir degerin cok dusuk kalmasini onleyen alt sinirlar "
        "ve nihai sonuclarin yuvarlanma hassasiyeti."
    )

    with st.form("pv_form_minimums"):
        st.markdown("**Minimum Efor Degerleri**")
        st.caption("Bir deliverable, WP veya faz icin hesaplanan efor bu degerlerin altindaysa, "
                   "otomatik olarak bu degere yukseltilir. Profil bazinda ayri minimum degerler tanimlanir.")
        min_rows = []
        for level in ["deliverable", "wp", "phase"]:
            row = {"Seviye": level}
            for p in ["A", "B", "C"]:
                row[f"Profil {p}"] = params["minimum_effort"][level][p]
            min_rows.append(row)
        df = pd.DataFrame(min_rows)
        min_edited = st.data_editor(df, key="pv_min_effort_edit", use_container_width=True, hide_index=True,
                                    column_config={
                                        "Seviye": st.column_config.TextColumn(disabled=True),
                                        **{f"Profil {p}": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f")
                                           for p in ["A", "B", "C"]}
                                    })

        st.divider()

        st.markdown("**Yuvarlama Hassasiyeti**")
        st.caption("Nihai efor degerlerinin yuvarlanma birimi. "
                   "A profili 0.5 AG hassasiyetle (ornegin 12.5), B ve C profilleri 0.1 AG hassasiyetle (ornegin 12.3) yuvarlanir.")
        round_rows = []
        for p in ["A", "B", "C"]:
            round_rows.append({"Profil": p, "Hassasiyet": float(params["rounding_precision"][p])})
        df = pd.DataFrame(round_rows)
        round_edited = st.data_editor(df, key="pv_round_edit", use_container_width=True, hide_index=True,
                                      column_config={
                                          "Profil": st.column_config.TextColumn(disabled=True),
                                          "Hassasiyet": st.column_config.NumberColumn(min_value=0.1, max_value=1.0, step=0.1, format="%.1f"),
                                      })

        st.divider()

        st.markdown("**Min-Max Araliklari**")
        st.caption("Her **WP toplamina** uygulanarak o WP'nin min ve max degerini olusturur. "
                   "Kompleksite arttikca aralik genisler. Ornek: WP toplam=10 AG, high: min=10x0.80=8, max=10x1.25=12.5.")
        mm_rows = []
        for level in COMPLEXITY_LEVELS:
            vals = params["min_max_ranges"].get(level, [0.9, 1.1])
            mm_rows.append({"Complexity": level, "Min Carpan": vals[0], "Max Carpan": vals[1]})
        df = pd.DataFrame(mm_rows)
        mm_edited = st.data_editor(df, key="pv_minmax_edit", use_container_width=True, hide_index=True,
                                   column_config={
                                       "Complexity": st.column_config.TextColumn(disabled=True),
                                       "Min Carpan": st.column_config.NumberColumn(min_value=0, max_value=1.0, step=0.05, format="%.2f"),
                                       "Max Carpan": st.column_config.NumberColumn(min_value=1.0, max_value=3.0, step=0.05, format="%.2f"),
                                   })

        submitted = st.form_submit_button("Kaydet", type="primary", use_container_width=True)

    if submitted:
        for _, row in min_edited.iterrows():
            level = row["Seviye"]
            for p in ["A", "B", "C"]:
                params["minimum_effort"][level][p] = round(row[f"Profil {p}"], 1)

        for _, row in round_edited.iterrows():
            p = row["Profil"]
            params["rounding_precision"][p] = round(float(row["Hassasiyet"]), 1)

        for _, row in mm_edited.iterrows():
            level = row["Complexity"]
            params["min_max_ranges"][level] = [round(row["Min Carpan"], 2), round(row["Max Carpan"], 2)]

        _save_and_reload(params)
        st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────

_TAB_NAMES = [
    "Baz Efor", "Carpanlar", "Faz Yuzdeleri", "Global",
    "OneFrame", "Baglam", "Min & Yuvarlama",
]


def show_params():
    """Parametre ayarlarini ana ekranda goster."""
    st.header("Parametre Ayarlari")

    _load_current()
    params = st.session_state.params

    # Fark analizi
    diffs = diff_from_defaults(params)
    total_diffs = len(diffs)

    # Ust bilgi cubugu
    col_status, col_reset = st.columns([3, 1])
    with col_status:
        if total_diffs > 0:
            st.caption(f":orange[{total_diffs} parametre fabrika degerinden farkli]")
        else:
            st.caption(":green[Tum parametreler fabrika degerlerinde]")
    with col_reset:
        if st.button(":factory: Fabrika Ayarlarina Don", key="pv_reset", type="secondary",
                     use_container_width=True):
            reset_to_defaults()
            tables.reload_tables()
            st.session_state.params = get_defaults()
            st.toast("Orijinal fabrika degerleri yuklendi")
            st.rerun()

    # Tab secimi — statik isimler (dynamic isim = tab reset bug)
    tabs = st.tabs(_TAB_NAMES)

    renderers = [
        _show_base_effort, _show_multipliers, _show_phase_pcts, _show_global,
        _show_oneframe, _show_context_multipliers, _show_minimums,
    ]

    for tab, renderer in zip(tabs, renderers):
        with tab:
            renderer(params)
