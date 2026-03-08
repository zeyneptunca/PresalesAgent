"""Python math engine — tum efor hesaplamalarini yapar, AI cagrisi YOK."""

from collections import defaultdict
from datetime import date

import src.effort_tables as tables


def _get_batch_multiplier(profile: str, index: int) -> float:
    table = tables.BATCH_MULTIPLIERS[profile]
    if index < len(table):
        return table[index]
    return table[-1]


def _calculate_wp(wbs_wp: dict, wbs_module: dict, cat_data: dict,
                  profile: str, reuse_order: int) -> dict:
    """Tek bir WP icin efor hesaplar."""
    wp_id = wbs_wp["wp_id"]
    complexity = wbs_wp["complexity"]["level"]
    deliverables = cat_data.get("deliverables", [])
    int_points = wbs_wp.get("technical_context", {}).get("integration_points", [])
    has_external_integration = len(int_points) > 0

    # Deliverable bazinda FE/BE hesapla
    category_counts = defaultdict(int)
    total_fe = 0.0
    total_be = 0.0
    story_parts = []
    # Structured story data for readable display
    detail_deliverables = []

    story_parts.append(f"[Profil {profile}] {wp_id} ({complexity}, {len(deliverables)} deliverable)")

    for d in deliverables:
        cat = d.get("kategori", "SIMPLE_UI")
        of_match = d.get("of_match")
        d_name = d.get("adi", d.get("name", cat))
        category_counts[cat] += 1
        idx = category_counts[cat] - 1  # 0-based

        # Track structured deliverable info
        d_detail = {"name": d_name, "kategori": cat, "of_match": of_match, "steps": []}

        # Baz deger veya OneFrame residuel
        if of_match and of_match in tables.ONEFRAME_RESIDUAL.get(profile, {}):
            fe, be = tables.ONEFRAME_RESIDUAL[profile][of_match]
            d_detail["base_fe"] = fe
            d_detail["base_be"] = be
            d_detail["kaynak"] = f"OF={of_match}"
            story_parts.append(f"  {d_name}: OF={of_match} residuel FE={fe:.2f} BE={be:.2f}")
            # OF residuel birikim siniri: 3+ ayni OF → %50
            of_count = sum(1 for dd in deliverables
                          if dd.get("of_match") == of_match
                          and deliverables.index(dd) < deliverables.index(d))
            if of_count >= 2:
                fe *= 0.5
                be *= 0.5
                d_detail["steps"].append({"label": "OF birikim (3+)", "carpan": 0.5})
                story_parts.append(f"    OF birikim siniri (3+): x0.5 → FE={fe:.2f} BE={be:.2f}")
            # Dis entegrasyon carpani
            if has_external_integration:
                fe *= 1.5
                be *= 1.5
                d_detail["steps"].append({"label": "Dis entegrasyon", "carpan": 1.5})
                story_parts.append(f"    Dis entegrasyon carpani: x1.5 → FE={fe:.2f} BE={be:.2f}")
        else:
            fe, be = tables.BASE_EFFORT[profile].get(cat, tables.BASE_EFFORT[profile]["SIMPLE_UI"])
            d_detail["base_fe"] = fe
            d_detail["base_be"] = be
            d_detail["kaynak"] = cat
            story_parts.append(f"  {d_name}: {cat} baz FE={fe:.2f} BE={be:.2f}")

        # Batch carpani
        batch = _get_batch_multiplier(profile, idx)
        fe *= batch
        be *= batch
        d_detail["batch"] = batch
        if batch != 1.0:
            d_detail["steps"].append({"label": f"Batch (#{idx+1})", "carpan": batch})
            story_parts.append(f"    Batch carpani (idx={idx}): x{batch:.2f} → FE={fe:.2f} BE={be:.2f}")

        # Minimum deliverable eforu
        min_d = tables.MINIMUM_EFFORT["deliverable"][profile]
        if fe + be < min_d and fe + be > 0:
            ratio = min_d / (fe + be) if (fe + be) > 0 else 1
            fe *= ratio
            be *= ratio
            d_detail["steps"].append({"label": "Min deliverable", "carpan": round(ratio, 4)})
            story_parts.append(f"    Min deliverable eforu uygulanir: {min_d}")

        d_detail["final_fe"] = round(fe, 4)
        d_detail["final_be"] = round(be, 4)
        detail_deliverables.append(d_detail)
        total_fe += fe
        total_be += be

    story_parts.append(f"  Deliverable toplam: FE={total_fe:.2f} BE={total_be:.2f}")

    # Entegrasyon carpani (WP seviyesinde)
    int_mult = tables.get_integration_multiplier(profile, len(int_points))
    total_fe *= int_mult
    total_be *= int_mult
    if int_mult != 1.0:
        story_parts.append(f"  Entegrasyon carpani ({len(int_points)} nokta): x{int_mult:.2f} → FE={total_fe:.2f} BE={total_be:.2f}")

    # Kompleksite carpani
    comp_mult = tables.COMPLEXITY_MULTIPLIERS[profile][complexity]
    total_fe *= comp_mult
    total_be *= comp_mult
    if comp_mult != 1.0:
        story_parts.append(f"  Kompleksite carpani ({complexity}): x{comp_mult:.2f} → FE={total_fe:.2f} BE={total_be:.2f}")

    adj_fe = total_fe
    adj_be = total_be
    dev_total = adj_fe + adj_be

    # Faz hesaplama
    analiz = dev_total * tables.ANALYSIS_PCT[profile][complexity]
    tasarim = adj_fe * tables.DESIGN_PCT[profile] if adj_fe > 0 else 0
    mimari = dev_total * tables.ARCHITECTURE_PCT[profile]
    fe_phase = adj_fe
    be_phase = adj_be
    test = dev_total * tables.TEST_PCT[profile][complexity]

    story_parts.append(
        f"  Fazlar: Analiz={analiz:.2f} Tasarim={tasarim:.2f} Mimari={mimari:.2f} "
        f"FE={fe_phase:.2f} BE={be_phase:.2f} Test={test:.2f}"
    )

    # Reuse carpani (WP toplam)
    wp_total = analiz + tasarim + mimari + fe_phase + be_phase + test
    reuse_mult_val = None
    if reuse_order > 0:
        reuse_table = tables.REUSE_MULTIPLIERS[profile]
        r_idx = min(reuse_order, len(reuse_table) - 1)
        reuse_mult = reuse_table[r_idx]
        reuse_mult_val = reuse_mult
        wp_total *= reuse_mult
        # Faz degerlerini de oranla
        ratio = reuse_mult
        analiz *= ratio
        tasarim *= ratio
        mimari *= ratio
        fe_phase *= ratio
        be_phase *= ratio
        test *= ratio
        story_parts.append(f"  Reuse carpani (sira={reuse_order}): x{reuse_mult:.2f}")

    # Minimum WP eforu
    min_wp_applied = False
    min_wp = tables.MINIMUM_EFFORT["wp"][profile]
    if wp_total < min_wp:
        min_wp_applied = True
        story_parts.append(f"  Min WP eforu uygulanir: {wp_total:.2f} → {min_wp}")
        if wp_total > 0:
            ratio = min_wp / wp_total
            analiz *= ratio
            tasarim *= ratio
            mimari *= ratio
            fe_phase *= ratio
            be_phase *= ratio
            test *= ratio
        wp_total = min_wp

    # Minimum faz eforu
    min_phase = tables.MINIMUM_EFFORT["phase"][profile]
    phases = {"analiz": analiz, "tasarim": tasarim, "mimari": mimari,
              "fe": fe_phase, "be": be_phase, "test": test}
    for k, v in phases.items():
        if v > 0 and v < min_phase:
            phases[k] = min_phase

    # Yuvarlama
    for k in phases:
        phases[k] = tables.round_effort(phases[k], profile)

    wp_total = sum(phases.values())

    # Min-Max
    min_r, max_r = tables.MIN_MAX_RANGES[complexity]
    wp_min = tables.round_effort(wp_total * min_r, profile)
    wp_max = tables.round_effort(wp_total * max_r, profile)

    story_parts.append(f"  SONUC: Toplam={wp_total:.1f} (Min={wp_min:.1f} Max={wp_max:.1f})")

    baskin = cat_data.get("baskin_kategori", "SIMPLE_UI")
    of_matches = list(set(d.get("of_match", "") for d in deliverables if d.get("of_match")))

    # Structured detail data for readable UI display
    story_data = {
        "deliverables": detail_deliverables,
        "del_total": {"fe": round(total_fe / (int_mult * comp_mult) if int_mult * comp_mult != 0 else total_fe, 2),
                      "be": round(total_be / (int_mult * comp_mult) if int_mult * comp_mult != 0 else total_be, 2)},
        "int_mult": int_mult, "int_points": len(int_points),
        "comp_mult": comp_mult, "complexity": complexity,
        "phases": {k: round(v, 2) for k, v in phases.items()},
        "reuse_mult": reuse_mult_val,
        "min_wp_applied": min_wp_applied,
        "total": wp_total, "min": wp_min, "max": wp_max,
    }

    return {
        "modul": wbs_module["module_id"],
        "wp_id": wp_id,
        "wp_adi": wbs_wp["name"],
        "complexity": complexity,
        "deliverable_sayisi": len(deliverables),
        "baskin_kategori": baskin,
        "of_eslesmesi": ", ".join(of_matches) if of_matches else "",
        "reuse_durumu": f"reuse_{reuse_order}" if reuse_order > 0 else "",
        "hesaplama_hikayesi": "\n".join(story_parts),
        "hesaplama_detay": story_data,
        f"{profile.lower()}_analiz": phases["analiz"],
        f"{profile.lower()}_tasarim": phases["tasarim"],
        f"{profile.lower()}_mimari": phases["mimari"],
        f"{profile.lower()}_fe": phases["fe"],
        f"{profile.lower()}_be": phases["be"],
        f"{profile.lower()}_test": phases["test"],
        f"{profile.lower()}_toplam": wp_total,
        f"min_{profile.lower()}": wp_min,
        f"max_{profile.lower()}": wp_max,
    }


def calculate_effort(wbs: dict, categories: dict, context: dict | None = None) -> dict:
    """3 profil icin efor hesaplar. AI cagrisi YAPMAZ."""
    profiles = ["A", "B", "C"]
    wp_cat = categories.get("wp_kategorileri", {})
    reuse_groups = categories.get("reuse_gruplari", {})

    # Reuse sirasi hesapla
    reuse_order_map = {}
    for group_id, wp_ids in reuse_groups.items():
        for i, wp_id in enumerate(wp_ids):
            reuse_order_map[wp_id] = i  # 0 = orijinal, 1+ = reuse

    all_wp_results = []
    modules = wbs["wbs"]["modules"]

    for profile in profiles:
        for mod in modules:
            for wp in mod["work_packages"]:
                wp_id = wp["wp_id"]
                cat_data = wp_cat.get(wp_id, {"deliverables": [], "baskin_kategori": "SIMPLE_UI"})
                reuse_idx = reuse_order_map.get(wp_id, 0)

                result = _calculate_wp(wp, mod, cat_data, profile, reuse_idx)

                # Mevcut WP sonucuna ekle veya olustur
                existing = next((r for r in all_wp_results if r["wp_id"] == wp_id), None)
                if existing:
                    # Hesaplama hikayesini biriktir (her profil eklenir)
                    prev_story = existing.get("hesaplama_hikayesi", "")
                    new_story = result.get("hesaplama_hikayesi", "")
                    result["hesaplama_hikayesi"] = f"{prev_story}\n{new_story}" if prev_story else new_story
                    # Structured detay — profil bazinda birlestir
                    prev_detay = existing.get("hesaplama_detay", {})
                    new_detay = result.get("hesaplama_detay")
                    if isinstance(prev_detay, dict) and "deliverables" in prev_detay:
                        # Ilk profil henuz dict'e sarlanmamis, sarla
                        prev_detay = {profiles[0] if profiles[0] != profile else "?": prev_detay}
                    if isinstance(prev_detay, dict) and new_detay:
                        prev_detay[profile] = new_detay
                    result["hesaplama_detay"] = prev_detay
                    existing.update(result)
                else:
                    # Ilk profil — detay'i profil anahtari altina koy
                    detay = result.get("hesaplama_detay")
                    if detay:
                        result["hesaplama_detay"] = {profile: detay}
                    all_wp_results.append(result)

    # Modul toplamlari
    modul_toplamlari = []
    for mod in modules:
        mod_wp_ids = [wp["wp_id"] for wp in mod["work_packages"]]
        totals = {"modul": mod["module_id"]}
        for p in profiles:
            key = f"{p.lower()}_toplam"
            totals[f"{p.lower()}_toplam"] = sum(
                r.get(key, 0) for r in all_wp_results if r["wp_id"] in mod_wp_ids
            )
        modul_toplamlari.append(totals)

    # Faz toplamlari
    faz_toplamlari = {}
    for p in profiles:
        pl = p.lower()
        faz = {}
        for f in ["analiz", "tasarim", "mimari", "fe", "be", "test"]:
            faz[f] = sum(r.get(f"{pl}_{f}", 0) for r in all_wp_results)
        faz["toplam"] = sum(r.get(f"{pl}_toplam", 0) for r in all_wp_results)
        faz_toplamlari[pl] = faz

    # Global eforlar
    global_eforlar = {}
    module_count = len(modules)

    for p in profiles:
        pl = p.lower()
        tech_total = faz_toplamlari[pl]["toplam"]
        band = tables.get_size_band(tech_total)
        formulas = tables.GLOBAL_FORMULAS[p]

        gl = {}
        if p == "A":
            gl["pm"] = tables.round_effort(tech_total * formulas["pm_pct"], p)
            gl["tech_design"] = tables.round_effort(tech_total * formulas["tech_design_pct"], p)
            devops = 5 + (1 * module_count)
            gl["devops"] = tables.round_effort(min(devops, 8), p)
            gl["deployment"] = tables.round_effort(tech_total * formulas["deployment_pct"], p)
            gl["uat"] = tables.round_effort(tech_total * formulas["uat_pct"], p)
            gl["ba_base"] = 0
            gl["test_base"] = 0
            gl["uat_base"] = 0
        else:
            bases = tables.FIXED_BASES[band]
            gl["pm"] = tables.round_effort(bases["PM_Base"] + tech_total * formulas["pm_pct"], p)
            gl["tech_design"] = tables.round_effort(tech_total * formulas["tech_design_pct"], p)
            if p == "B":
                devops = 3 + (0.5 * module_count)
                gl["devops"] = tables.round_effort(min(devops, 5), p)
            else:  # C
                gl["devops"] = 3.0
            gl["deployment"] = tables.round_effort(tech_total * formulas["deployment_pct"], p)
            gl["uat"] = tables.round_effort(bases["UAT_Base"] + tech_total * formulas["uat_pct"], p)
            gl["ba_base"] = bases["BA_Base"]
            gl["test_base"] = bases["Test_Base"]
            gl["uat_base"] = bases["UAT_Base"]

        gl["toplam"] = sum(gl.values())
        global_eforlar[pl] = gl

    # Baglam carpanlari
    baglam = {"olcek": {"AB": 1.0, "C": 1.0}, "ekip": {"AB": 1.0, "C": 1.0},
              "domain": {"AB": 1.0, "C": 1.0}, "teknik_borc": {"AB": 1.0, "C": 1.0},
              "ent_yogunluk": {"AB": 1.0, "C": 1.0},
              "faktor_a_b": 1.0, "faktor_c": 1.0}

    if context:
        dims = [
            ("scale", context.get("scale", "orta"), "olcek"),
            ("team", context.get("team", "mid"), "ekip"),
            ("domain", context.get("domain", "standart"), "domain"),
            ("tech_debt", context.get("tech_debt", "greenfield"), "teknik_borc"),
            ("integration_density", context.get("integration_density", "0-2"), "ent_yogunluk"),
        ]
        factor_ab = 1.0
        factor_c = 1.0
        for dim_key, dim_val, out_key in dims:
            table = tables.CONTEXT_MULTIPLIERS.get(dim_key, {})
            vals = table.get(dim_val, {"AB": 1.0, "C": 1.0})
            baglam[out_key] = {"AB": vals["AB"], "C": vals["C"]}
            factor_ab *= vals["AB"]
            factor_c *= vals["C"]

        if factor_c > tables.VIBE_CONTEXT_CAP:
            factor_c = tables.VIBE_CONTEXT_CAP
        baglam["faktor_a_b"] = round(factor_ab, 4)
        baglam["faktor_c"] = round(factor_c, 4)

    # Proje toplami
    proje_toplami = {}
    for p in profiles:
        pl = p.lower()
        tech = faz_toplamlari[pl]["toplam"]
        gl_total = global_eforlar[pl]["toplam"]

        if p == "C":
            factor = baglam["faktor_c"]
        else:
            factor = baglam["faktor_a_b"]

        toplam = tables.round_effort((tech + gl_total) * factor, p)
        wp_mins = sum(r.get(f"min_{pl}", 0) for r in all_wp_results)
        wp_maxs = sum(r.get(f"max_{pl}", 0) for r in all_wp_results)
        prj_min = tables.round_effort((wp_mins + gl_total) * factor, p)
        prj_max = tables.round_effort((wp_maxs + gl_total) * factor, p)

        proje_toplami[pl] = {
            "teknik": tables.round_effort(tech * factor, p),
            "global": tables.round_effort(gl_total * factor, p),
            "toplam": toplam,
            "min": prj_min,
            "max": prj_max,
        }

    a_total = proje_toplami["a"]["toplam"]
    b_total = proje_toplami["b"]["toplam"]
    c_total = proje_toplami["c"]["toplam"]

    if a_total > 0:
        proje_toplami["tasarruf_b_ag"] = round(a_total - b_total, 1)
        proje_toplami["tasarruf_b_yuzde"] = round((1 - b_total / a_total) * 100)
        proje_toplami["tasarruf_c_ag"] = round(a_total - c_total, 1)
        proje_toplami["tasarruf_c_yuzde"] = round((1 - c_total / a_total) * 100)
    else:
        proje_toplami["tasarruf_b_ag"] = 0
        proje_toplami["tasarruf_b_yuzde"] = 0
        proje_toplami["tasarruf_c_ag"] = 0
        proje_toplami["tasarruf_c_yuzde"] = 0

    # Proje bandi
    band = tables.get_size_band(faz_toplamlari["a"]["toplam"])

    return {
        "tahmin_ozeti": {
            "proje_adi": wbs.get("project_scope_summary", {}).get("project_name", ""),
            "tahmin_tarihi": date.today().isoformat(),
            "toplam_modul": len(modules),
            "toplam_wp": sum(len(m["work_packages"]) for m in modules),
            "proje_bandi": band,
        },
        "wp_detaylari": all_wp_results,
        "modul_toplamlari": modul_toplamlari,
        "faz_toplamlari": faz_toplamlari,
        "global_eforlar": global_eforlar,
        "proje_toplami": proje_toplami,
        "baglam_carpanlari": baglam,
        "sorular": categories.get("sorular", []),
        "notlar": categories.get("notlar", []),
        "riskler": categories.get("riskler", []),
        "kapsam_disi": wbs.get("project_scope_summary", {}).get("out_of_scope_items", []),
    }
