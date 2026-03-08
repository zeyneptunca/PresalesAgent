def run_checks(wbs: dict, result: dict) -> list[str]:
    """CSV oncesi kalite kontrolu. Hata listesi dondurur (bos = gecti)."""
    errors = []

    # 1. WP sayisi eslesmesi
    wbs_wp_count = sum(
        len(mod["work_packages"]) for mod in wbs["wbs"]["modules"]
    )
    result_wp_count = len(result.get("wp_detaylari", []))
    if wbs_wp_count != result_wp_count:
        errors.append(
            f"WP sayisi uyusmazligi: WBS={wbs_wp_count}, sonuc={result_wp_count}"
        )

    # 2. Toplam dogrulama (±0.5 tolerans)
    for profile, label in [("a", "A"), ("b", "B"), ("c", "C")]:
        wp_sum = sum(
            wp.get(f"{profile}_toplam", 0) for wp in result.get("wp_detaylari", [])
        )
        faz_total = result.get("faz_toplamlari", {}).get(profile, {}).get("toplam", 0)
        if abs(wp_sum - faz_total) > 0.5:
            errors.append(
                f"Profil {label}: WP toplami ({wp_sum:.1f}) != faz toplami ({faz_total:.1f})"
            )

    # 3. Minimum efor kontrolu
    minimums = {"a": 1.5, "b": 0.5, "c": 1.0}
    for wp in result.get("wp_detaylari", []):
        for profile, min_val in minimums.items():
            val = wp.get(f"{profile}_toplam", 0)
            if isinstance(val, (int, float)) and val < min_val:
                errors.append(
                    f"{wp.get('wp_id', '?')}: Profil {profile.upper()} "
                    f"toplam={val} < minimum {min_val}"
                )

    # 4. Profil sirasi (uyari, hard error degil)
    warnings = []
    for wp in result.get("wp_detaylari", []):
        a = wp.get("a_toplam", 0)
        b = wp.get("b_toplam", 0)
        c = wp.get("c_toplam", 0)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a < b:
                warnings.append(f"{wp.get('wp_id', '?')}: A ({a}) < B ({b})")
        if isinstance(b, (int, float)) and isinstance(c, (int, float)):
            if b < c:
                warnings.append(f"{wp.get('wp_id', '?')}: B ({b}) < C ({c})")

    if warnings:
        print("  Uyarilar (profil sirasi):")
        for w in warnings:
            print(f"    - {w}")

    # 5. Sayisal alan kontrolu
    numeric_fields = [
        "a_fe", "a_be", "a_analiz", "a_tasarim", "a_mimari", "a_test", "a_toplam",
        "b_fe", "b_be", "b_analiz", "b_tasarim", "b_mimari", "b_test", "b_toplam",
        "c_fe", "c_be", "c_analiz", "c_tasarim", "c_mimari", "c_test", "c_toplam",
        "min_a", "max_a", "min_b", "max_b", "min_c", "max_c",
    ]
    for wp in result.get("wp_detaylari", []):
        for field in numeric_fields:
            val = wp.get(field)
            if val is not None and not isinstance(val, (int, float)):
                errors.append(
                    f"{wp.get('wp_id', '?')}: {field} sayi degil: {type(val).__name__}"
                )

    return errors
