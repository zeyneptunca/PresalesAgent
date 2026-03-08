"""Proje danismani sohbet modulu. Tum baglama erisimi olan AI chat agent."""

import json

import anthropic

import src.effort_tables as tables

CHAT_SYSTEM_PROMPT = """Sen kurumsal yazilim projelerinde efor tahmini yapan bir uzman danismansin.
Asagidaki tum bilgilere erisimin var ve kullanicinin sorularina bu bilgilerle cevap veriyorsun.

YAPABILECEKLERIN:
- Her WP'nin efor hesaplamasini adim adim acikla (hesaplama hikayesine bak)
- Neden belirli bir carpanin uygulandigini acikla (tablolara bak)
- Profiller arasi karsilastirma yap (A vs B vs C)
- En yuksek/dusuk eforlu WP'leri analiz et
- "Eger X olsaydi ne olurdu?" senaryolarina tahmini cevap ver
- Kategorizasyon kararlarini acikla
- OneFrame eslesmelerini acikla
- Baglam carpanlarinin etkisini goster
- Risk ve optimizasyon onerileri sun

KURALLAR:
- Turkce cevap ver
- Sayisal verilerle destekle, tablo format kullan
- Kisa ve net ol, gereksiz uzatma
- Hesaplama hikayesindeki adimlari referans goster
- Kesin bilmediginde bunu belirt

{context_block}
"""


def _format_tables_summary() -> str:
    """Efor tablolarini ozet olarak formatlar."""
    lines = []
    lines.append("=== BAZ EFOR DEGERLERI (FE, BE) ===")
    for profile in ["A", "B", "C"]:
        lines.append(f"Profil {profile}:")
        for cat, (fe, be) in tables.BASE_EFFORT[profile].items():
            lines.append(f"  {cat}: FE={fe} BE={be}")

    lines.append("\n=== BATCH CARPANLARI ===")
    for profile in ["A", "B", "C"]:
        lines.append(f"Profil {profile}: {tables.BATCH_MULTIPLIERS[profile]}")

    lines.append("\n=== KOMPLEKSITE CARPANLARI ===")
    for profile in ["A", "B", "C"]:
        lines.append(f"Profil {profile}: {tables.COMPLEXITY_MULTIPLIERS[profile]}")

    lines.append("\n=== FAZ YUZDELERI ===")
    for profile in ["A", "B", "C"]:
        lines.append(f"Profil {profile}: Analiz={tables.ANALYSIS_PCT[profile]}, "
                     f"Tasarim={tables.DESIGN_PCT[profile]}, Mimari={tables.ARCHITECTURE_PCT[profile]}, "
                     f"Test={tables.TEST_PCT[profile]}")

    lines.append("\n=== MIN-MAX ARALIKLARI ===")
    for level, (mn, mx) in tables.MIN_MAX_RANGES.items():
        lines.append(f"  {level}: min=x{mn} max=x{mx}")

    lines.append("\n=== MINIMUM EFORLAR ===")
    lines.append(f"  WP: {tables.MINIMUM_EFFORT['wp']}")
    lines.append(f"  Deliverable: {tables.MINIMUM_EFFORT['deliverable']}")
    lines.append(f"  Faz: {tables.MINIMUM_EFFORT['phase']}")

    lines.append("\n=== REUSE CARPANLARI ===")
    for profile in ["A", "B", "C"]:
        lines.append(f"Profil {profile}: {tables.REUSE_MULTIPLIERS[profile]}")

    lines.append("\n=== BAGLAM CARPANLARI ===")
    for dim, values in tables.CONTEXT_MULTIPLIERS.items():
        lines.append(f"  {dim}: {values}")
    lines.append(f"  VibeCoding context cap: {tables.VIBE_CONTEXT_CAP}")

    lines.append("\n=== ONEFRAME RESIDUEL (OF) ===")
    for profile in ["A", "B", "C"]:
        of_data = tables.ONEFRAME_RESIDUAL.get(profile, {})
        if of_data:
            lines.append(f"Profil {profile}:")
            for of_id, (fe, be) in of_data.items():
                lines.append(f"  {of_id}: FE={fe} BE={be}")

    return "\n".join(lines)


def build_context_block(wbs: dict, categories: dict | None,
                        effort_result: dict | None) -> str:
    """Tum baglam bilgisini system prompt'a eklenecek string olarak olusturur."""
    parts = []

    # WBS ozeti
    if wbs:
        parts.append("=== PROJE WBS ===")
        scope = wbs.get("project_scope_summary", {})
        parts.append(f"Proje: {scope.get('project_name', 'Bilinmiyor')}")
        parts.append(f"Amac: {scope.get('core_objective', '')}")

        modules = wbs.get("wbs", {}).get("modules", [])
        for mod in modules:
            parts.append(f"\n--- {mod['module_id']}: {mod['name']} ---")
            if mod.get("description"):
                parts.append(f"  {mod['description']}")
            for wp in mod.get("work_packages", []):
                wp_id = wp["wp_id"]
                parts.append(f"  {wp_id}: {wp['name']} [{wp['complexity']['level']}]")
                parts.append(f"    Deliverables: {wp.get('deliverables', [])}")
                tc = wp.get("technical_context", {})
                if tc.get("integration_points"):
                    parts.append(f"    Entegrasyonlar: {tc['integration_points']}")

    # Kategorizasyon
    if categories:
        parts.append("\n=== KATEGORIZASYON SONUCLARI ===")
        wp_cat = categories.get("wp_kategorileri", {})
        for wp_id, cat_data in wp_cat.items():
            deliverables = cat_data.get("deliverables", [])
            baskin = cat_data.get("baskin_kategori", "")
            parts.append(f"{wp_id}: baskin={baskin}")
            for d in deliverables:
                parts.append(f"  {d.get('adi', '')}: {d.get('kategori', '')} "
                             f"OF={d.get('of_match', '')} ({d.get('neden', '')})")

        baglam = categories.get("baglam_analizi", {})
        if baglam:
            parts.append(f"\nBaglam: domain={baglam.get('domain_karmasikligi', '')} "
                         f"({baglam.get('domain_neden', '')})")
            parts.append(f"Entegrasyon yogunlugu: {baglam.get('entegrasyon_yogunlugu', '')}")

        reuse = categories.get("reuse_gruplari", {})
        if reuse:
            parts.append(f"Reuse gruplari: {reuse}")

    # Efor sonuclari
    if effort_result:
        parts.append("\n=== EFOR HESAPLAMA SONUCLARI ===")
        ozet = effort_result.get("tahmin_ozeti", {})
        parts.append(f"Proje bandi: {ozet.get('proje_bandi', '')}")
        parts.append(f"Toplam: {ozet.get('toplam_modul', 0)} modul, {ozet.get('toplam_wp', 0)} WP")

        pt = effort_result.get("proje_toplami", {})
        for p in ["a", "b", "c"]:
            pd_ = pt.get(p, {})
            parts.append(f"Profil {p.upper()}: {pd_.get('toplam', 0):.1f} AG "
                         f"(min={pd_.get('min', 0):.1f} max={pd_.get('max', 0):.1f})")

        parts.append(f"Tasarruf B: %{pt.get('tasarruf_b_yuzde', 0)}")
        parts.append(f"Tasarruf C: %{pt.get('tasarruf_c_yuzde', 0)}")

        baglam_c = effort_result.get("baglam_carpanlari", {})
        parts.append(f"Baglam carpanlari: {baglam_c}")

        # WP detaylari (hesaplama hikayeleri dahil)
        parts.append("\n--- WP DETAYLARI ---")
        for wp in effort_result.get("wp_detaylari", []):
            parts.append(f"\n{wp['wp_id']}: {wp.get('wp_adi', '')}")
            parts.append(f"  Complexity: {wp.get('complexity', '')}")
            parts.append(f"  Kategori: {wp.get('baskin_kategori', '')} | OF: {wp.get('of_eslesmesi', '')}")
            parts.append(f"  A={wp.get('a_toplam', 0):.1f} B={wp.get('b_toplam', 0):.1f} C={wp.get('c_toplam', 0):.1f}")
            story = wp.get("hesaplama_hikayesi", "")
            if story:
                parts.append(f"  Hesaplama hikayesi:\n{story}")

    # Efor tablolari
    parts.append("\n" + _format_tables_summary())

    return "\n".join(parts)


def chat(messages: list[dict], wbs: dict, categories: dict | None,
         effort_result: dict | None) -> str:
    """Tek bir sohbet turu. Kullanici mesajini alir, AI cevabini dondurur."""
    client = anthropic.Anthropic()

    context_block = build_context_block(wbs, categories, effort_result)
    system = CHAT_SYSTEM_PROMPT.format(context_block=context_block)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system,
        messages=messages,
    )
    return response.content[0].text
