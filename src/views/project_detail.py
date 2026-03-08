"""Project Detail view — mevcut proje detaylari (4 tab)."""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.views.components import (
    render_results_charts, render_results_details,
    render_notes_risks, render_export_section,
    short_name, format_datetime,
)
from src.chat_agent import chat as chat_with_agent
from src.param_manager import diff_from_defaults, load_params
import src.project_manager_v2 as pm


PROFILE_LABELS = {"A": "Geleneksel", "B": "Copilot+Claude", "C": "VibeCoding"}


def _render_structured_story(wp: dict, detay: dict):
    """Yapilandirilmis hesaplama hikayesini profil tab'lari ile gosterir."""
    wp_id = wp.get("wp_id", "")
    wp_adi = wp.get("wp_adi", "")

    with st.expander(f"**{wp_id}** — {wp_adi}", expanded=False):
        # Ozet metrikler — 3 profil yan yana
        cols = st.columns(3)
        for i, p in enumerate(["A", "B", "C"]):
            p_data = detay.get(p, {})
            total = p_data.get("total", wp.get(f"{p.lower()}_toplam", 0))
            p_min = p_data.get("min", wp.get(f"min_{p.lower()}", 0))
            p_max = p_data.get("max", wp.get(f"max_{p.lower()}", 0))
            cols[i].metric(
                f"Profil {p}",
                f"{total:.1f} AG",
                f"{p_min:.1f}–{p_max:.1f}",
                delta_color="off"
            )

        # Profil detay tab'lari
        tab_a, tab_b, tab_c = st.tabs([
            f"Profil A ({PROFILE_LABELS['A']})",
            f"Profil B ({PROFILE_LABELS['B']})",
            f"Profil C ({PROFILE_LABELS['C']})",
        ])

        for tab, p in zip([tab_a, tab_b, tab_c], ["A", "B", "C"]):
            with tab:
                p_data = detay.get(p, {})
                if not p_data:
                    st.caption("Bu profil icin detay mevcut degil.")
                    continue
                _render_profile_detail(p, p_data)


def _render_profile_detail(profile: str, data: dict):
    """Tek bir profil icin hesaplama detaylarini gosterir."""
    deliverables = data.get("deliverables", [])

    # 1. Deliverable tablosu
    if deliverables:
        st.markdown("**Deliverable Detaylari**")
        rows = []
        for d in deliverables:
            steps_text = ", ".join(
                f"{s['label']} x{s['carpan']}"
                for s in d.get("steps", [])
            )
            rows.append({
                "Deliverable": d.get("name", ""),
                "Kategori": d.get("kategori", ""),
                "Kaynak": d.get("kaynak", ""),
                "Baz FE": d.get("base_fe", 0),
                "Baz BE": d.get("base_be", 0),
                "Carpanlar": steps_text or "—",
                "Final FE": round(d.get("final_fe", 0), 2),
                "Final BE": round(d.get("final_be", 0), 2),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # 2. WP seviyesi carpanlar
    st.markdown("**WP Carpanlari**")
    int_mult = data.get("int_mult", 1.0)
    comp_mult = data.get("comp_mult", 1.0)
    int_points = data.get("int_points", 0)
    complexity = data.get("complexity", "")
    reuse_mult = data.get("reuse_mult")

    carpan_parts = []
    if int_mult != 1.0:
        carpan_parts.append(f"Entegrasyon ({int_points} nokta): **x{int_mult:.2f}**")
    if comp_mult != 1.0:
        carpan_parts.append(f"Kompleksite ({complexity}): **x{comp_mult:.2f}**")
    if reuse_mult:
        carpan_parts.append(f"Reuse: **x{reuse_mult:.2f}**")
    if data.get("min_wp_applied"):
        carpan_parts.append("Min WP eforu uygulanmis")

    if carpan_parts:
        st.markdown(" · ".join(carpan_parts))
    else:
        st.caption("Ek carpan uygulanmadi")

    # 3. Faz dagilimi
    phases = data.get("phases", {})
    if phases:
        st.markdown("**Faz Dagilimi (AG)**")
        phase_labels = {
            "analiz": "Analiz", "tasarim": "Tasarim",
            "mimari": "Mimari", "fe": "FE",
            "be": "BE", "test": "Test"
        }
        phase_row = {label: phases.get(key, 0) for key, label in phase_labels.items()}
        phase_row["Toplam"] = sum(phase_row.values())
        st.dataframe(pd.DataFrame([phase_row]), use_container_width=True, hide_index=True)

    # 4. Sonuc
    total = data.get("total", 0)
    p_min = data.get("min", 0)
    p_max = data.get("max", 0)
    st.markdown(f"**Sonuc:** {total:.1f} AG (Min: {p_min:.1f} — Max: {p_max:.1f})")


def _render_fallback_story(wp: dict, hikaye: str):
    """Eski format (duz metin) icin fallback — profil bazinda tab'lara boler."""
    wp_id = wp.get("wp_id", "")
    wp_adi = wp.get("wp_adi", "")

    with st.expander(f"**{wp_id}** — {wp_adi}", expanded=False):
        # String'i profil bloklarina bol
        import re
        blocks = re.split(r'\n(?=\[Profil [ABC]\])', hikaye)
        if len(blocks) >= 3:
            tab_a, tab_b, tab_c = st.tabs(["Profil A", "Profil B", "Profil C"])
            for tab, block in zip([tab_a, tab_b, tab_c], blocks[:3]):
                with tab:
                    st.code(block.strip(), language=None)
        else:
            st.code(hikaye, language=None)


def show_project_detail():
    """Proje detay ekrani — 4 tab: Genel Bakis, WBS, Sonuclar, Danisman."""
    project_id = st.session_state.get("active_project_id")
    if not project_id:
        st.warning("Aktif proje bulunamadi.")
        return

    meta = pm.load_meta(project_id)
    if not meta:
        st.error(f"Proje yuklenemedi: {project_id}")
        return

    # Baslik
    project_name = meta.get("project_name", "Proje")
    st.markdown(f"## {project_name}")
    desc = meta.get("project_description", "")
    if desc:
        st.caption(desc)

    # Tabs (Gecmis kaldirildi — WBS ve Sonuclar tab'larinda dropdown ile secim yapilir)
    tab_overview, tab_wbs, tab_results, tab_chat = st.tabs(
        ["Genel Bakis", "WBS", "Sonuclar", "Danisman"]
    )

    with tab_overview:
        _show_overview(meta, project_id)

    with tab_wbs:
        _show_wbs_tab(meta, project_id)

    with tab_results:
        _show_results_tab(meta, project_id)

    with tab_chat:
        _show_chat_tab(project_id)


# ── Overview Tab ────────────────────────────────────────────────────────────

def _show_overview(meta: dict, project_id: str):
    """Genel bakis: ozet kartlar, hizli aksiyonlar."""
    # Proje bilgisi
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        with st.container(border=True):
            st.markdown("**Proje Bilgisi**")
            st.caption(f"Olusturulma: {format_datetime(meta.get('created_at', ''))}")
            st.caption(f"Son guncelleme: {format_datetime(meta.get('updated_at', ''))}")
            scope = meta.get("scope")
            if scope:
                st.caption(f"Kapsam: {scope.get('pdf_filename', '-')} ({scope.get('pdf_pages', 0)} sayfa)")

    with col_info2:
        with st.container(border=True):
            st.markdown("**Durum**")
            wbs_versions = meta.get("wbs_versions", [])
            calcs = meta.get("calculations", [])
            st.caption(f"WBS versiyonlari: {len(wbs_versions)}")
            st.caption(f"Hesaplamalar: {len(calcs)}")
            if meta.get("active_wbs_version"):
                st.caption(f"Aktif WBS: {meta['active_wbs_version']}")

    # Son hesaplama sonuclari
    calcs = meta.get("calculations", [])
    if calcs:
        latest = calcs[-1]
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Profil A (Geleneksel)", f"{latest.get('a_total', 0):.1f} AG")
        col2.metric("Profil B (Copilot+Claude)", f"{latest.get('b_total', 0):.1f} AG")
        col3.metric("Profil C (VibeCoding)", f"{latest.get('c_total', 0):.1f} AG")

    # Hizli aksiyonlar
    st.divider()
    act_col1, act_col2, act_col3 = st.columns(3)
    with act_col1:
        if st.button("Yeni WBS Olustur", use_container_width=True, type="primary"):
            st.session_state.view_mode = "wizard"
            st.session_state.wizard_step = "scope"
            st.rerun()
    with act_col2:
        wbs = st.session_state.get("wbs")
        if wbs:
            if st.button("Tekrar Hesapla", use_container_width=True):
                st.session_state.view_mode = "wizard"
                st.session_state.wizard_step = "context"
                st.rerun()
        else:
            st.button("Tekrar Hesapla", use_container_width=True, disabled=True)
    with act_col3:
        if st.button("Projelere Don", use_container_width=True):
            st.session_state.view_mode = "dashboard"
            st.session_state.active_project_id = None
            st.rerun()


# ── WBS Tab ─────────────────────────────────────────────────────────────────

def _show_wbs_tab(meta: dict, project_id: str):
    """WBS versiyonlarini goster ve duzenleme imkani ver."""
    wbs_versions = meta.get("wbs_versions", [])

    if not wbs_versions:
        st.info("Henuz WBS olusturulmamis.")
        if st.button("WBS Olustur", type="primary"):
            st.session_state.view_mode = "wizard"
            st.session_state.wizard_step = "scope"
            st.rerun()
        return

    # Versiyon secici
    active_version = meta.get("active_wbs_version", wbs_versions[-1]["version"])
    version_options = [v["version"] for v in wbs_versions]
    version_labels = {v["version"]: f"{v['version']} ({format_datetime(v.get('created_at', ''))} — {v.get('source', '')})"
                      for v in wbs_versions}

    selected_version = st.selectbox(
        "WBS Versiyonu",
        version_options,
        index=version_options.index(active_version) if active_version in version_options else len(version_options) - 1,
        format_func=lambda v: version_labels.get(v, v),
    )

    # WBS yukle
    wbs = pm.load_wbs(project_id, selected_version)
    if not wbs:
        st.error(f"WBS {selected_version} yuklenemedi.")
        return

    modules = wbs.get("wbs", {}).get("modules", [])
    total_mod = len(modules)
    total_wp = sum(len(m.get("work_packages", [])) for m in modules)
    total_del = sum(len(wp.get("deliverables", []))
                    for m in modules for wp in m.get("work_packages", []))

    # Ozet metrikler
    col1, col2, col3 = st.columns(3)
    col1.metric("Modul", total_mod)
    col2.metric("Work Package", total_wp)
    col3.metric("Deliverable", total_del)

    # WBS tablosu (read-only)
    rows = []
    for mod in modules:
        for wp in mod.get("work_packages", []):
            int_points = wp.get("technical_context", {}).get("integration_points", [])
            rows.append({
                "Modul": mod["name"],
                "WP ID": wp["wp_id"],
                "WP Adi": wp["name"],
                "Complexity": wp["complexity"]["level"],
                "Deliverable": len(wp.get("deliverables", [])),
                "Entegrasyon": len(int_points),
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Detayli WP gosterimi — tum alanlar gorunur
    for mod in modules:
        with st.expander(f"{mod['module_id']} — {mod['name']} ({len(mod['work_packages'])} WP)", expanded=True):
            if mod.get("description"):
                st.caption(mod["description"])
            for wp in mod.get("work_packages", []):
                with st.container(border=True):
                    st.markdown(f"**{wp['wp_id']} — {wp['name']}** `[{wp['complexity']['level']}]`")
                    if wp.get("description"):
                        st.caption(wp["description"])

                    # Complexity drivers
                    drivers = wp.get("complexity", {}).get("drivers", [])
                    if drivers:
                        st.markdown(f"**Complexity Drivers:** {', '.join(drivers)}")

                    # Deliverables
                    deliverables = wp.get("deliverables", [])
                    if deliverables:
                        st.markdown("**Deliverables:**")
                        for d in deliverables:
                            d_name = d if isinstance(d, str) else d.get("name", d.get("adi", str(d)))
                            st.markdown(f"  - {d_name}")

                    # Technical Context
                    tc = wp.get("technical_context", {})
                    if tc:
                        tc_parts = []
                        if tc.get("frontend_requirements"):
                            tc_parts.append(f"**Frontend:** {tc['frontend_requirements']}")
                        if tc.get("backend_requirements"):
                            tc_parts.append(f"**Backend:** {tc['backend_requirements']}")
                        if tc.get("data_implications"):
                            tc_parts.append(f"**Veri:** {tc['data_implications']}")
                        int_pts = tc.get("integration_points", [])
                        if int_pts:
                            tc_parts.append(f"**Entegrasyonlar:** {', '.join(int_pts)}")
                        if tc_parts:
                            st.markdown("**Teknik Detay:**")
                            for part in tc_parts:
                                st.markdown(f"  {part}")

                    # Acceptance Criteria
                    criteria = wp.get("acceptance_criteria", [])
                    if criteria:
                        st.markdown("**Kabul Kriterleri:**")
                        for c in criteria:
                            st.markdown(f"  - {c}")

    # Aksiyonlar
    st.divider()
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("WBS Duzenle", type="primary", use_container_width=True, key="edit_wbs_btn"):
            # Secili versiyonu session'a yukle ve wizard'a git
            st.session_state.wbs = wbs
            st.session_state.view_mode = "wizard"
            st.session_state.wizard_step = "wbs_edit"
            st.rerun()
    with btn_col2:
        if st.button("Bu WBS'ten Hesapla", use_container_width=True, key="calc_from_wbs_btn"):
            st.session_state.wbs = wbs
            # Eger kategorileri yoksa once wbs_edit'ten kategorize etmeli
            if not st.session_state.get("categories"):
                st.session_state.view_mode = "wizard"
                st.session_state.wizard_step = "wbs_edit"
            else:
                st.session_state.view_mode = "wizard"
                st.session_state.wizard_step = "context"
            st.rerun()
    with btn_col3:
        if st.button("Yeniden Olustur (PDF'den)", use_container_width=True, key="regen_wbs_btn"):
            st.session_state.view_mode = "wizard"
            st.session_state.wizard_step = "scope"
            st.rerun()


# ── Results Tab ─────────────────────────────────────────────────────────────

def _show_results_tab(meta: dict, project_id: str):
    """Hesaplama sonuclarini goster."""
    calcs = meta.get("calculations", [])
    if not calcs:
        st.info("Henuz hesaplama yapilmamis.")
        return

    # Hesaplama secici — versiyon numarasi + tarih/saat ile
    calc_options = [c["calc_id"] for c in reversed(calcs)]
    calc_labels = {}
    for idx, c in enumerate(calcs, 1):
        dt = format_datetime(c.get("created_at", ""))
        ver = c.get("wbs_version", "?")
        total = f"A:{c.get('a_total', 0):.1f} B:{c.get('b_total', 0):.1f} C:{c.get('c_total', 0):.1f}"
        calc_labels[c["calc_id"]] = f"v{idx} | {dt} | WBS {ver} | {total} AG"

    active_calc = meta.get("active_calc_id", calcs[-1]["calc_id"])

    sel_col, del_col = st.columns([5, 1])
    with sel_col:
        selected_calc_id = st.selectbox(
            "Hesaplama Sec",
            calc_options,
            index=calc_options.index(active_calc) if active_calc in calc_options else 0,
            format_func=lambda c: calc_labels.get(c, c),
        )
    with del_col:
        st.markdown("")  # spacer for alignment
        if len(calcs) > 1:
            if st.button("🗑 Sil", key="delete_calc_btn", use_container_width=True,
                         help="Secili hesaplamayi kalici olarak sil"):
                st.session_state["_confirm_delete_calc"] = selected_calc_id

    # Silme onay dialogu
    if st.session_state.get("_confirm_delete_calc") == selected_calc_id:
        with st.container(border=True):
            st.warning(f"**{calc_labels.get(selected_calc_id, selected_calc_id)}** hesaplamasi silinecek. Bu islem geri alinamaz.")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("Evet, Sil", type="primary", key="confirm_delete_calc", use_container_width=True):
                    pm.delete_calculation(project_id, selected_calc_id)
                    st.session_state.pop("_confirm_delete_calc", None)
                    # Kalan hesaplamayi session'a yukle
                    updated_meta = pm.load_meta(project_id)
                    new_active = updated_meta.get("active_calc_id") if updated_meta else None
                    if new_active:
                        new_calc = pm.load_calculation(project_id, new_active)
                        if new_calc:
                            st.session_state.effort_result = new_calc.get("effort_result")
                            st.session_state.categories = new_calc.get("categories")
                            st.session_state.project_context = new_calc.get("context")
                    else:
                        st.session_state.effort_result = None
                        st.session_state.categories = None
                    st.toast("Hesaplama silindi")
                    st.rerun()
            with confirm_col2:
                if st.button("Iptal", key="cancel_delete_calc", use_container_width=True):
                    st.session_state.pop("_confirm_delete_calc", None)
                    st.rerun()

    # Hesaplama yukle
    calc_data = pm.load_calculation(project_id, selected_calc_id)
    if not calc_data or "effort_result" not in calc_data:
        st.error("Hesaplama sonucu yuklenemedi.")
        return

    result = calc_data["effort_result"]
    wbs_version = calc_data.get("wbs_version", "?")
    categories = calc_data.get("categories")
    wbs = pm.load_wbs(project_id, wbs_version)

    # Hesaplama bilgisi — versiyon + tarih
    calc_version_label = calc_labels.get(selected_calc_id, selected_calc_id)
    st.caption(f"Secili: {calc_version_label}")

    # Sonuc chartlari ve metrikler
    render_results_charts(result)
    render_notes_risks(result)

    # Detayli tablolar
    with st.expander("Detayli Tablolar", expanded=False):
        render_results_details(result)

    # Hesaplama Hikayesi — ayri expander, kolayca gorulebilir
    wp_data = result.get("wp_detaylari", [])
    if wp_data and any(wp.get("hesaplama_hikayesi") or wp.get("hesaplama_detay") for wp in wp_data):
        with st.expander("Hesaplama Hikayesi", expanded=False):
            st.caption("Her WP icin adim adim hesaplama detaylari.")
            for wp in wp_data:
                detay = wp.get("hesaplama_detay")
                hikaye = wp.get("hesaplama_hikayesi", "")
                if detay and isinstance(detay, dict) and any(k in detay for k in ["A", "B", "C"]):
                    _render_structured_story(wp, detay)
                elif hikaye and str(hikaye).strip():
                    _render_fallback_story(wp, str(hikaye))
                st.divider()

    # OF kapsam bilgisi
    if categories:
        wp_cat = categories.get("wp_kategorileri", {})
        total_del = sum(len(w.get("deliverables", [])) for w in wp_cat.values())
        of_del = sum(
            1 for w in wp_cat.values()
            for d in w.get("deliverables", [])
            if d.get("of_match")
        )
        if total_del > 0 and of_del == total_del:
            st.info(
                f"Tum deliverable'lar ({of_del}/{total_del}) OneFrame eslesmesine sahip. "
                f"Baz Efor degisiklikleri sonucu degistirmez — "
                f"OneFrame Residuel, Carpanlar veya Faz Yuzdeleri parametrelerini degistirin."
            )
        elif total_del > 0 and of_del / total_del > 0.8:
            st.info(
                f"Deliverable'larin %{of_del*100//total_del}'i OneFrame eslesmesine sahip. "
                f"Baz Efor degisiklikleri sinirli etki yapar."
            )

    # Hesaplama Parametreleri
    _show_calc_params(calc_data, selected_calc_id)

    # Export
    st.divider()
    exports_dir = calc_data.get("exports_dir")
    render_export_section(result, wbs, categories, exports_dir)

    # Aksiyonlar
    st.divider()
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("Tekrar Hesapla", use_container_width=True, key="recalc_btn"):
            st.session_state.view_mode = "wizard"
            st.session_state.wizard_step = "context"
            st.rerun()
    with act_col2:
        if st.button("Baglam Degistir", use_container_width=True, key="change_ctx_btn"):
            st.session_state.view_mode = "wizard"
            st.session_state.wizard_step = "context"
            st.rerun()


def _show_calc_params(calc_data: dict, calc_id: str):
    """Hesaplama parametrelerinin snapshot'ini goster."""
    saved_params = calc_data.get("params")
    if not saved_params:
        return

    # Aktif proje icin override bilgisi
    project_id = st.session_state.get("active_project_id")
    overrides = pm.load_project_params_overrides(project_id) if project_id else None

    with st.expander("Hesaplama Parametreleri", expanded=False):
        st.caption("Bu hesaplamada kullanilan parametre snapshot'i.")

        if overrides:
            override_keys = _count_override_keys(overrides)
            st.info(f"Bu projede **{len(override_keys)} parametre** projeye ozel override edilmis")

        diffs = diff_from_defaults(saved_params)
        diff_count = len(diffs)

        if diff_count > 0:
            st.warning(f"{diff_count} parametre varsayilandan farkli")
            for path, vals in diffs.items():
                st.caption(f"  `{path}`: {vals['varsayilan']} -> {vals['mevcut']}")
        else:
            st.success("Varsayilan parametreler kullanildi")


def _count_override_keys(overrides: dict) -> list:
    """Override dict icindeki leaf degerleri duz liste olarak dondurur."""
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


# ── Chat Tab ────────────────────────────────────────────────────────────────

@st.fragment
def _show_chat_tab(project_id: str):
    """Proje danismani — chat arayuzu."""
    st.header("Proje Danismani")
    st.caption("Hesaplama detaylari, WBS analizi veya proje hakkinda soru sorun.")

    result = st.session_state.get("effort_result")
    wbs = st.session_state.get("wbs")

    if not result:
        st.info("Hesaplama sonucu yok — once efor hesaplama yapin.")
        return

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Sorunuzu yazin... (orn: WP-001 nasil hesaplandi?)"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("Cevap hazirlaniyor...", expanded=False) as chat_status:
                try:
                    categories = st.session_state.get("categories")
                    response = chat_with_agent(
                        st.session_state.chat_messages, wbs, categories, result
                    )
                    chat_status.update(label="Cevap hazir", state="complete")
                except Exception as e:
                    chat_status.update(label="Hata!", state="error")
                    st.error(f"Hata: {e}")
                    response = None

            if response:
                st.markdown(response)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": response}
                )

        # Chat mesajlarini kaydet
        if project_id:
            pm.save_wizard_state(project_id, "results", st.session_state.chat_messages)

    if st.session_state.chat_messages:
        if st.button("Sohbet Gecmisini Temizle"):
            st.session_state.chat_messages = []
            if project_id:
                pm.save_wizard_state(project_id, "results", [])
            st.rerun()
