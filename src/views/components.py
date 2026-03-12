"""Paylasilan UI bilesenleri — kart, timeline, chart builder'lar."""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime


# ── Step Indicator ──────────────────────────────────────────────────────────

STEP_CONFIG = [
    ("scope", "Kapsam", "1"),
    ("wbs_edit", "WBS Duzenleme", "2"),
    ("context", "Baglam Ayarlari", "3"),
    ("calculate", "Hesaplama", "4"),
    ("results", "Sonuclar", "5"),
]
STEP_ORDER = [s[0] for s in STEP_CONFIG]

_STEP_LABELS = {
    "scope": "Kapsam",
    "wbs_edit": "WBS Duzenleme",
    "context": "Baglam Ayarlari",
    "calculate": "Hesaplama",
    "results": "Sonuclar",
}


def render_step_indicator(current_step: str):
    """5 adimli yatay step indicator."""
    current_idx = STEP_ORDER.index(current_step) if current_step in STEP_ORDER else 0
    items_html = ""
    for i, (key, label, num) in enumerate(STEP_CONFIG):
        if i < current_idx:
            cls, icon = "step-completed", "&#10003;"
        elif i == current_idx:
            cls, icon = "step-active", num
        else:
            cls, icon = "step-pending", num
        items_html += (
            f'<div class="step-item {cls}">'
            f'<div class="step-circle">{icon}</div>'
            f'<div class="step-label">{label}</div>'
            f'</div>'
        )
    st.html(
        '<style>'
        '.step-container{display:flex;justify-content:center;align-items:flex-start;gap:0;margin:0 auto;max-width:700px;font-family:sans-serif;}'
        '.step-item{text-align:center;position:relative;flex:1;min-width:80px;}'
        '.step-item:not(:last-child)::after{content:"";position:absolute;top:17px;left:55%;width:90%;height:3px;background:#dee2e6;z-index:0;}'
        '.step-item.step-completed:not(:last-child)::after{background:#28a745;}'
        '.step-item.step-active:not(:last-child)::after{background:linear-gradient(90deg,#0066CC 50%,#dee2e6 50%);}'
        '.step-circle{width:36px;height:36px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;position:relative;z-index:1;}'
        '.step-completed .step-circle{background:#28a745;color:#fff;box-shadow:0 2px 6px rgba(40,167,69,0.3);}'
        '.step-active .step-circle{background:#0066CC;color:#fff;box-shadow:0 2px 8px rgba(0,102,204,0.4);}'
        '.step-pending .step-circle{background:#dee2e6;color:#6c757d;}'
        '.step-label{margin-top:6px;font-size:0.72rem;font-weight:600;color:#6c757d;line-height:1.2;}'
        '.step-active .step-label{color:#0066CC;font-weight:700;}'
        '.step-completed .step-label{color:#28a745;}'
        '</style>'
        f'<div class="step-container">{items_html}</div>'
    )


# ── Chart Builders ──────────────────────────────────────────────────────────

def build_profile_chart(pt: dict) -> alt.Chart:
    a_t = pt.get("a", {}).get("toplam", 0)
    b_t = pt.get("b", {}).get("toplam", 0)
    c_t = pt.get("c", {}).get("toplam", 0)
    chart_data = pd.DataFrame({
        "Profil": ["A (Geleneksel)", "B (Copilot+Claude)", "C (VibeCoding)"],
        "Toplam (AG)": [a_t, b_t, c_t],
    })
    return alt.Chart(chart_data).mark_bar(
        cornerRadiusTopLeft=6, cornerRadiusTopRight=6,
    ).encode(
        x=alt.X("Profil:N", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Toplam (AG):Q"),
        color=alt.Color("Profil:N", scale=alt.Scale(
            domain=["A (Geleneksel)", "B (Copilot+Claude)", "C (VibeCoding)"],
            range=["#6c757d", "#0066CC", "#28a745"]
        ), legend=None),
        tooltip=["Profil", "Toplam (AG)"],
    ).properties(height=300)


def build_phase_chart(faz: dict) -> alt.Chart:
    phase_data = []
    phase_names = ["Analiz", "Tasarim", "Mimari", "FE", "BE", "Test"]
    phase_colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948"]
    for phase in phase_names:
        for profile, p_key in [("Profil A", "a"), ("Profil B", "b"), ("Profil C", "c")]:
            phase_data.append({
                "Faz": phase, "Profil": profile,
                "AG": faz.get(p_key, {}).get(phase.lower(), 0),
            })
    df = pd.DataFrame(phase_data)
    return alt.Chart(df).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("Profil:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("AG:Q", title="Adam-Gun", stack="zero"),
        color=alt.Color("Faz:N", sort=phase_names, scale=alt.Scale(
            domain=phase_names, range=phase_colors
        ), title="Faz"),
        order=alt.Order("faz_order:Q"),
        tooltip=["Profil", "Faz", alt.Tooltip("AG:Q", format=".1f")],
    ).transform_calculate(
        faz_order="indexof(['Analiz','Tasarim','Mimari','FE','BE','Test'], datum.Faz)"
    ).properties(height=350)


def build_global_chart(gl: dict) -> alt.Chart:
    kalem_names = ["PM", "Tech Design", "DevOps", "Deployment", "UAT", "BA Base", "Test Base"]
    kalem_keys = ["pm", "tech_design", "devops", "deployment", "uat", "ba_base", "test_base"]
    kalem_colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1"]
    data = []
    for kalem_name, kalem_key in zip(kalem_names, kalem_keys):
        for profile, p_key in [("Profil A", "a"), ("Profil B", "b"), ("Profil C", "c")]:
            data.append({
                "Kalem": kalem_name, "Profil": profile,
                "AG": gl.get(p_key, {}).get(kalem_key, 0),
            })
    df = pd.DataFrame(data)
    return alt.Chart(df).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("Profil:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("AG:Q", title="Adam-Gun", stack="zero"),
        color=alt.Color("Kalem:N", sort=kalem_names, scale=alt.Scale(
            domain=kalem_names, range=kalem_colors
        ), title="Kalem"),
        order=alt.Order("kalem_order:Q"),
        tooltip=["Profil", "Kalem", alt.Tooltip("AG:Q", format=".1f")],
    ).transform_calculate(
        kalem_order="indexof(['PM','Tech Design','DevOps','Deployment','UAT','BA Base','Test Base'], datum.Kalem)"
    ).properties(height=350)


def build_minmax_chart(pt: dict) -> alt.Chart:
    rows = []
    for label, key in [("A (Geleneksel)", "a"), ("B (Copilot+Claude)", "b"), ("C (VibeCoding)", "c")]:
        p = pt.get(key, {})
        rows.append({"Profil": label, "Min": p.get("min", 0),
                     "Toplam": p.get("toplam", 0), "Max": p.get("max", 0)})
    df = pd.DataFrame(rows)
    bars = alt.Chart(df).mark_bar(height=20, cornerRadius=4, opacity=0.3).encode(
        x=alt.X("Min:Q", title="Adam-Gun"), x2="Max:Q",
        y=alt.Y("Profil:N", sort=None, title=None),
        color=alt.Color("Profil:N", scale=alt.Scale(
            domain=["A (Geleneksel)", "B (Copilot+Claude)", "C (VibeCoding)"],
            range=["#6c757d", "#0066CC", "#28a745"]
        ), legend=None),
    )
    points = alt.Chart(df).mark_circle(size=100).encode(
        x="Toplam:Q", y=alt.Y("Profil:N", sort=None),
        color=alt.Color("Profil:N", scale=alt.Scale(
            domain=["A (Geleneksel)", "B (Copilot+Claude)", "C (VibeCoding)"],
            range=["#6c757d", "#0066CC", "#28a745"]
        ), legend=None),
        tooltip=["Profil", "Min", "Toplam", "Max"],
    )
    return (bars + points).properties(height=150)


# ── Results Display ─────────────────────────────────────────────────────────

def render_results_charts(result: dict):
    """Sonuc charlarini ve metriklerini render et."""
    pt = result.get("proje_toplami", {})
    a = pt.get("a", {})
    b = pt.get("b", {})
    c = pt.get("c", {})

    # Metrikler
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Profil A (Geleneksel)", f"{a.get('toplam', 0):.1f} AG",
                   f"{a.get('min', 0):.0f} - {a.get('max', 0):.0f} AG")
    with col2:
        sav_b = pt.get("tasarruf_b_yuzde", 0)
        st.metric("Profil B (Copilot+Claude)", f"{b.get('toplam', 0):.1f} AG",
                   f"%{sav_b} tasarruf", delta_color="inverse")
    with col3:
        sav_c = pt.get("tasarruf_c_yuzde", 0)
        st.metric("Profil C (VibeCoding)", f"{c.get('toplam', 0):.1f} AG",
                   f"%{sav_c} tasarruf", delta_color="inverse")

    # Chartlar
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("**Profil Karsilastirma**")
        st.altair_chart(build_profile_chart(pt), use_container_width=True)
    with chart_col2:
        st.markdown("**Min-Max Aralik**")
        st.altair_chart(build_minmax_chart(pt), use_container_width=True)

    faz = result.get("faz_toplamlari", {})
    gl = result.get("global_eforlar", {})
    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        if faz:
            st.markdown("**Faz Dagilimi**")
            st.altair_chart(build_phase_chart(faz), use_container_width=True)
    with chart_col4:
        if gl:
            st.markdown("**Global Eforlar**")
            st.altair_chart(build_global_chart(gl), use_container_width=True)

    # Tasarruf
    sav_b = pt.get("tasarruf_b_yuzde", 0)
    sav_c = pt.get("tasarruf_c_yuzde", 0)
    if a.get("toplam", 0) > 0:
        st.divider()
        with st.container(border=True):
            st.markdown("**Tasarruf Ozeti**")
            sav_col1, sav_col2 = st.columns(2)
            with sav_col1:
                b_sav = a.get("toplam", 0) - b.get("toplam", 0)
                st.markdown(f"**Profil B vs A:** `{b_sav:.1f} AG` tasarruf (`%{sav_b}`)")
                st.progress(min(sav_b / 100, 1.0) if sav_b > 0 else 0)
            with sav_col2:
                c_sav = a.get("toplam", 0) - c.get("toplam", 0)
                st.markdown(f"**Profil C vs A:** `{c_sav:.1f} AG` tasarruf (`%{sav_c}`)")
                st.progress(min(sav_c / 100, 1.0) if sav_c > 0 else 0)


def render_results_details(result: dict):
    """Detayli tablolari render et."""
    st.subheader("WP Detaylari")
    wp_data = result.get("wp_detaylari", [])
    if wp_data:
        df = pd.DataFrame(wp_data)
        display_cols = ["wp_id", "wp_adi", "complexity", "deliverable_sayisi",
                        "baskin_kategori", "of_eslesmesi",
                        "a_toplam", "b_toplam", "c_toplam",
                        "min_a", "max_a", "min_b", "max_b", "min_c", "max_c"]
        available = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available], use_container_width=True, hide_index=True)

        # Hesaplama Hikayesi — project_detail.py'deki ana expander'da gosterilir
        # Burada sadece referans verilir
        if any(row.get("hesaplama_hikayesi") or row.get("hesaplama_detay") for _, row in df.iterrows()):
            st.caption("Hesaplama hikayesi detaylari icin yukaridaki 'Hesaplama Hikayesi' bolumune bakiniz.")

    st.subheader("Faz Toplamlari")
    faz = result.get("faz_toplamlari", {})
    if faz:
        faz_rows = []
        for f_name in ["analiz", "tasarim", "mimari", "fe", "be", "test", "toplam"]:
            faz_rows.append({
                "Faz": f_name.capitalize(),
                "Profil A": faz.get("a", {}).get(f_name, 0),
                "Profil B": faz.get("b", {}).get(f_name, 0),
                "Profil C": faz.get("c", {}).get(f_name, 0),
            })
        st.dataframe(pd.DataFrame(faz_rows), use_container_width=True, hide_index=True)

    st.subheader("Global Eforlar")
    gl = result.get("global_eforlar", {})
    if gl:
        gl_rows = []
        for key in ["pm", "tech_design", "devops", "deployment", "uat",
                     "ba_base", "test_base", "toplam"]:
            gl_rows.append({
                "Kalem": key,
                "Profil A": gl.get("a", {}).get(key, 0),
                "Profil B": gl.get("b", {}).get(key, 0),
                "Profil C": gl.get("c", {}).get(key, 0),
            })
        st.dataframe(pd.DataFrame(gl_rows), use_container_width=True, hide_index=True)

    baglam_c = result.get("baglam_carpanlari", {})
    if baglam_c:
        st.subheader("Uygulanan Baglam Carpanlari")
        dim_labels = {
            "olcek": "Organizasyon Olcegi", "ekip": "Ekip Deneyimi",
            "domain": "Domain", "teknik_borc": "Teknik Borc",
            "ent_yogunluk": "Entegrasyon Yogunlugu",
        }
        ctx_rows = []
        for key in ["olcek", "ekip", "domain", "teknik_borc", "ent_yogunluk"]:
            val = baglam_c.get(key, {"AB": 1.0, "C": 1.0})
            if isinstance(val, dict):
                ctx_rows.append({"Boyut": dim_labels.get(key, key),
                                 "AB Carpan": val.get("AB", 1.0),
                                 "C Carpan": val.get("C", 1.0)})
            else:
                ctx_rows.append({"Boyut": dim_labels.get(key, key),
                                 "AB Carpan": val, "C Carpan": val})
        st.dataframe(pd.DataFrame(ctx_rows), use_container_width=True, hide_index=True)
        mc1, mc2 = st.columns(2)
        mc1.metric("Birlesik Carpan (A & B)", f"{baglam_c.get('faktor_a_b', 1.0):.4f}")
        mc2.metric("Birlesik Carpan (C)", f"{baglam_c.get('faktor_c', 1.0):.4f}")


def render_notes_risks(result: dict):
    """Notlar ve riskleri render et."""
    notlar = result.get("notlar", [])
    riskler = result.get("riskler", [])
    if notlar or riskler:
        with st.container(border=True):
            n_col, r_col = st.columns(2)
            with n_col:
                if notlar:
                    st.markdown("**Notlar**")
                    for n in notlar:
                        if n and str(n).strip():
                            st.markdown(f"- {n}")
            with r_col:
                if riskler:
                    st.markdown("**Riskler**")
                    for r in riskler:
                        if r and str(r).strip():
                            st.warning(r, icon="⚠")


# ── Export Helpers ──────────────────────────────────────────────────────────

def render_export_section(result: dict, wbs: dict | None, categories: dict | None,
                          exports_dir: str | None = None):
    """Excel export butonunu render et."""
    import tempfile
    from pathlib import Path
    from src.csv_writer import write_full_export

    project_name = result.get("tahmin_ozeti", {}).get("proje_adi", "proje")
    safe_name = project_name.lower().replace(" ", "_")[:20] if project_name else "proje"

    with st.container(border=True):
        st.markdown("**Cikti Indir**")
        if wbs and categories:
            def _get_xlsx_bytes():
                if exports_dir:
                    op = Path(exports_dir)
                    for f in op.glob("*_tam_export.xlsx"):
                        return f.read_bytes()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    write_full_export(wbs, categories, result, tmp.name)
                    return Path(tmp.name).read_bytes()

            xlsx_data = _get_xlsx_bytes()
            st.download_button(
                "Excel Indir (6 Sheet)", xlsx_data,
                f"{safe_name}_tam_export.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.caption("Excel export icin WBS ve kategorizasyon gerekli")


# ── Helpers ─────────────────────────────────────────────────────────────────

def short_name(name: str, max_len: int = 28) -> str:
    if len(name) <= max_len:
        return name
    return name[:max_len - 1].rstrip() + "…"


def format_datetime(iso_str: str) -> str:
    """ISO datetime string'i TR formatina cevir."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        return iso_str
