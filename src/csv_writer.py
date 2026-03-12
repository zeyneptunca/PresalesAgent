"""Excel export modulu — tum veriyi tek .xlsx dosyasina yazar."""

import openpyxl


def _try_numeric(value):
    """String degeri mumkunse int veya float'a cevir."""
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s:
        return s
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return value


def _join_list(items: list, sep: str = " | ") -> str:
    """Liste elemanlarini string olarak birlestirir."""
    if not items:
        return ""
    str_items = []
    for item in items:
        if isinstance(item, dict):
            str_items.append(item.get("name", item.get("adi", str(item))))
        else:
            str_items.append(str(item))
    return sep.join(str_items)


def _write_wbs_sheet(ws, wbs: dict) -> None:
    """WBS yapisi — her satir 1 WP."""
    headers = [
        "modul_id", "modul_adi", "modul_aciklama",
        "wp_id", "wp_adi", "wp_aciklama",
        "complexity", "complexity_drivers",
        "deliverables", "deliverable_sayisi",
        "frontend_requirements", "backend_requirements", "data_implications",
        "integration_points", "entegrasyon_sayisi",
        "acceptance_criteria",
    ]
    ws.append(headers)

    for mod in wbs.get("wbs", {}).get("modules", []):
        mod_id = mod.get("module_id", "")
        mod_name = mod.get("name", "")
        mod_desc = mod.get("description", "")

        for wp in mod.get("work_packages", []):
            tc = wp.get("technical_context", {})
            int_points = tc.get("integration_points", [])
            deliverables = wp.get("deliverables", [])
            drivers = wp.get("complexity", {}).get("drivers", [])
            criteria = wp.get("acceptance_criteria", [])

            ws.append([
                mod_id, mod_name, mod_desc,
                wp.get("wp_id", ""), wp.get("name", ""), wp.get("description", ""),
                wp.get("complexity", {}).get("level", ""),
                _join_list(drivers),
                _join_list(deliverables),
                len(deliverables),
                tc.get("frontend_requirements", ""),
                tc.get("backend_requirements", ""),
                tc.get("data_implications", ""),
                _join_list(int_points),
                len(int_points),
                _join_list(criteria),
            ])


def _write_categorization_sheet(ws, categories: dict) -> None:
    """Kategorizasyon detaylari — her satir 1 deliverable."""
    headers = [
        "wp_id", "baskin_kategori",
        "deliverable_adi", "kategori", "of_match", "neden",
    ]
    ws.append(headers)

    wp_cat = categories.get("wp_kategorileri", {})
    for wp_id, cat_data in wp_cat.items():
        baskin = cat_data.get("baskin_kategori", "")
        deliverables = cat_data.get("deliverables", [])
        for d in deliverables:
            ws.append([
                wp_id, baskin,
                d.get("adi", d.get("name", "")),
                d.get("kategori", ""),
                d.get("of_match", ""),
                d.get("neden", ""),
            ])


def _write_wp_details_sheet(ws, result: dict) -> None:
    """Her satir 1 WP olan efor detay sheeti."""
    headers = [
        "modul", "wp_id", "wp_adi", "complexity", "deliverable_sayisi",
        "baskin_kategori", "of_eslesmesi", "reuse_durumu",
        "a_analiz", "a_tasarim", "a_mimari", "a_fe", "a_be", "a_test", "a_toplam",
        "b_analiz", "b_tasarim", "b_mimari", "b_fe", "b_be", "b_test", "b_toplam",
        "c_analiz", "c_tasarim", "c_mimari", "c_fe", "c_be", "c_test", "c_toplam",
        "min_a", "max_a", "min_b", "max_b", "min_c", "max_c",
        "hesaplama_hikayesi",
    ]
    ws.append(headers)

    for wp in result.get("wp_detaylari", []):
        ws.append([_try_numeric(wp.get(h, "")) for h in headers])


def _write_summary_sheet(ws, result: dict) -> None:
    """Dikey format ozet sheeti."""
    headers = ["bolum", "kalem", "profil_a", "profil_b", "profil_c"]
    ws.append(headers)

    ozet = result.get("tahmin_ozeti", {})
    ws.append(["PROJE", "proje_adi", ozet.get("proje_adi", ""), "", ""])
    ws.append(["PROJE", "tarih", ozet.get("tahmin_tarihi", ""), "", ""])
    ws.append(["PROJE", "toplam_modul", _try_numeric(str(ozet.get("toplam_modul", ""))), "", ""])
    ws.append(["PROJE", "toplam_wp", _try_numeric(str(ozet.get("toplam_wp", ""))), "", ""])
    ws.append(["PROJE", "proje_bandi", "-",
               ozet.get("proje_bandi", ""), ozet.get("proje_bandi", "")])

    for mt in result.get("modul_toplamlari", []):
        ws.append(["MODUL", mt.get("modul", ""),
                   _try_numeric(mt.get("a_toplam", 0)),
                   _try_numeric(mt.get("b_toplam", 0)),
                   _try_numeric(mt.get("c_toplam", 0))])

    faz = result.get("faz_toplamlari", {})
    for profil_key in ["analiz", "tasarim", "mimari", "fe", "be", "test", "toplam"]:
        ws.append(["FAZ", profil_key,
                   _try_numeric(faz.get("a", {}).get(profil_key, 0)),
                   _try_numeric(faz.get("b", {}).get(profil_key, 0)),
                   _try_numeric(faz.get("c", {}).get(profil_key, 0))])

    gl = result.get("global_eforlar", {})
    for g_key in ["pm", "tech_design", "devops", "deployment", "uat",
                   "ba_base", "test_base", "uat_base", "toplam"]:
        label = "global_toplam" if g_key == "toplam" else g_key
        ws.append(["GLOBAL", label,
                   _try_numeric(gl.get("a", {}).get(g_key, 0)),
                   _try_numeric(gl.get("b", {}).get(g_key, 0)),
                   _try_numeric(gl.get("c", {}).get(g_key, 0))])

    pt = result.get("proje_toplami", {})
    for t_key in ["teknik", "global", "toplam", "min", "max"]:
        label = "genel_toplam" if t_key == "toplam" else t_key
        ws.append(["TOPLAM", label,
                   _try_numeric(pt.get("a", {}).get(t_key, 0)),
                   _try_numeric(pt.get("b", {}).get(t_key, 0)),
                   _try_numeric(pt.get("c", {}).get(t_key, 0))])

    ws.append(["TOPLAM", "tasarruf_ag", "-",
               _try_numeric(pt.get("tasarruf_b_ag", 0)),
               _try_numeric(pt.get("tasarruf_c_ag", 0))])
    ws.append(["TOPLAM", "tasarruf_yuzde", "-",
               _try_numeric(pt.get("tasarruf_b_yuzde", 0)),
               _try_numeric(pt.get("tasarruf_c_yuzde", 0))])

    bc = result.get("baglam_carpanlari", {})
    ws.append(["BAGLAM", "faktor",
               _try_numeric(bc.get("faktor_a_b", 0)),
               _try_numeric(bc.get("faktor_a_b", 0)),
               _try_numeric(bc.get("faktor_c", 0))])


def _write_context_sheet(ws, categories: dict, effort_result: dict) -> None:
    """Baglam analizi ve carpanlar sheeti."""
    headers = ["bolum", "kalem", "deger", "aciklama"]
    ws.append(headers)

    baglam = categories.get("baglam_analizi", {})

    ws.append(["DOMAIN", "karmasiklik",
               baglam.get("domain_karmasikligi", ""),
               baglam.get("domain_neden", "")])

    ws.append(["ENTEGRASYON", "yogunluk",
               baglam.get("entegrasyon_yogunlugu", ""),
               baglam.get("entegrasyon_neden", "")])

    ent_list = baglam.get("benzersiz_entegrasyonlar", [])
    if ent_list:
        ws.append(["ENTEGRASYON", "liste", ", ".join(ent_list),
                   f"{len(ent_list)} benzersiz entegrasyon"])

    reuse = categories.get("reuse_gruplari", {})
    if isinstance(reuse, dict):
        for group_id, group_data in reuse.items():
            if isinstance(group_data, dict):
                wps = group_data.get("wp_ids", group_data.get("wps", []))
                neden = group_data.get("neden", group_data.get("reason", ""))
                ws.append(["REUSE", group_id,
                           ", ".join(wps) if isinstance(wps, list) else str(wps),
                           neden])
            elif isinstance(group_data, list):
                ws.append(["REUSE", group_id, ", ".join(str(x) for x in group_data), ""])
    elif isinstance(reuse, list):
        for i, group in enumerate(reuse):
            ws.append(["REUSE", f"grup_{i+1}", str(group), ""])

    bc = effort_result.get("baglam_carpanlari", {})
    carpan_labels = {
        "olcek": "Organizasyon Olcegi",
        "ekip": "Ekip Deneyimi",
        "domain": "Domain Karmasikligi",
        "teknik_borc": "Teknik Borc",
        "ent_yogunluk": "Entegrasyon Yogunlugu",
        "faktor_a_b": "Birlesik Faktor (A ve B)",
        "faktor_c": "Birlesik Faktor (C, max 1.20)",
    }
    for key, label in carpan_labels.items():
        val = bc.get(key, "")
        if val != "":
            if isinstance(val, dict):
                ws.append(["CARPAN", key,
                           f"AB={val.get('AB', 1.0)} C={val.get('C', 1.0)}", label])
            else:
                ws.append(["CARPAN", key, _try_numeric(val), label])


def _write_notes_sheet(ws, result: dict) -> None:
    """Not, risk ve kapsam disi sheeti."""
    headers = ["tip", "icerik"]
    ws.append(headers)

    for note in result.get("notlar", []):
        if note and str(note).strip():
            ws.append(["NOT", note])

    for risk in result.get("riskler", []):
        if risk and str(risk).strip():
            ws.append(["RISK", risk])

    for kd in result.get("kapsam_disi", []):
        if kd and str(kd).strip():
            ws.append(["KAPSAM_DISI", kd])


def write_full_export(wbs: dict, categories: dict, effort_result: dict,
                      filepath: str) -> None:
    """Tek Excel dosyasi (.xlsx) — 6 sheet ile tum veri.
    Sayisal degerler gercek sayi olarak yazilir, boylece Excel
    kullanicinin locale ayarina gore (TR: virgul) gosterir."""
    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "WBS Yapisi"
    _write_wbs_sheet(ws1, wbs)

    ws2 = wb.create_sheet("Kategorizasyon")
    _write_categorization_sheet(ws2, categories)

    ws3 = wb.create_sheet("Efor Detaylari")
    _write_wp_details_sheet(ws3, effort_result)

    ws4 = wb.create_sheet("Ozet")
    _write_summary_sheet(ws4, effort_result)

    ws5 = wb.create_sheet("Baglam ve Carpanlar")
    _write_context_sheet(ws5, categories, effort_result)

    ws6 = wb.create_sheet("Notlar ve Riskler")
    _write_notes_sheet(ws6, effort_result)

    wb.save(filepath)
