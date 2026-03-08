def _find_wp(wbs: dict, wp_id: str) -> tuple[dict, dict]:
    """WP'yi bulur. (modul, wp) tuple dondurur. Bulamazsa ValueError."""
    for mod in wbs["wbs"]["modules"]:
        for wp in mod["work_packages"]:
            if wp["wp_id"] == wp_id:
                return mod, wp
    raise ValueError(f"WP bulunamadi: {wp_id}")


def update_complexity(wbs: dict, wp_id: str, new_level: str) -> dict:
    valid = {"low", "medium", "high", "very_high"}
    if new_level not in valid:
        raise ValueError(f"Gecersiz complexity: {new_level}. Gecerli: {valid}")
    _, wp = _find_wp(wbs, wp_id)
    old = wp["complexity"]["level"]
    wp["complexity"]["level"] = new_level
    print(f"  {wp_id}: {old} → {new_level}")
    return wbs


def add_deliverable(wbs: dict, wp_id: str, name: str) -> dict:
    _, wp = _find_wp(wbs, wp_id)
    wp["deliverables"].append(name)
    print(f"  {wp_id}: deliverable eklendi: {name}")
    return wbs


def remove_wp(wbs: dict, wp_id: str) -> dict:
    for mod in wbs["wbs"]["modules"]:
        for i, wp in enumerate(mod["work_packages"]):
            if wp["wp_id"] == wp_id:
                mod["work_packages"].pop(i)
                print(f"  {wp_id} silindi.")
                if not mod["work_packages"]:
                    wbs["wbs"]["modules"].remove(mod)
                    print(f"  {mod['module_id']} bos kaldi, silindi.")
                return wbs
    raise ValueError(f"WP bulunamadi: {wp_id}")


def add_wp(wbs: dict, module_id: str, wp_data: dict) -> dict:
    for mod in wbs["wbs"]["modules"]:
        if mod["module_id"] == module_id:
            if "wp_id" not in wp_data:
                all_ids = []
                for m in wbs["wbs"]["modules"]:
                    for w in m["work_packages"]:
                        num = int(w["wp_id"].replace("WP-", ""))
                        all_ids.append(num)
                next_id = max(all_ids) + 1 if all_ids else 1
                wp_data["wp_id"] = f"WP-{next_id:03d}"

            defaults = {
                "description": "",
                "deliverables": [],
                "technical_context": {
                    "frontend_requirements": "",
                    "backend_requirements": "",
                    "integration_points": [],
                    "data_implications": "",
                },
                "complexity": {"level": "medium", "drivers": []},
                "acceptance_criteria": [],
            }
            for k, v in defaults.items():
                wp_data.setdefault(k, v)

            mod["work_packages"].append(wp_data)
            print(f"  {wp_data['wp_id']} eklendi: {wp_data.get('name', '')}")
            return wbs

    raise ValueError(f"Modul bulunamadi: {module_id}")


def update_wp_name(wbs: dict, wp_id: str, new_name: str) -> dict:
    _, wp = _find_wp(wbs, wp_id)
    old = wp["name"]
    wp["name"] = new_name
    print(f"  {wp_id}: '{old}' → '{new_name}'")
    return wbs


def add_integration_point(wbs: dict, wp_id: str, point: str) -> dict:
    _, wp = _find_wp(wbs, wp_id)
    wp["technical_context"]["integration_points"].append(point)
    print(f"  {wp_id}: integration point eklendi: {point}")
    return wbs


def update_description(wbs: dict, wp_id: str, new_desc: str) -> dict:
    """WP aciklamasini gunceller."""
    _, wp = _find_wp(wbs, wp_id)
    wp["description"] = new_desc
    return wbs


def update_deliverable(wbs: dict, wp_id: str, index: int, new_name: str) -> dict:
    """Mevcut deliverable'in adini gunceller (index bazli)."""
    _, wp = _find_wp(wbs, wp_id)
    deliverables = wp.get("deliverables", [])
    if index < 0 or index >= len(deliverables):
        raise ValueError(f"Gecersiz deliverable index: {index}")
    old = deliverables[index]
    if isinstance(old, dict):
        old_name = old.get("name", old.get("adi", str(old)))
        old["name"] = new_name
        if "adi" in old:
            old["adi"] = new_name
    else:
        deliverables[index] = new_name
    return wbs


def remove_deliverable(wbs: dict, wp_id: str, index: int) -> dict:
    """Deliverable siler (index bazli)."""
    _, wp = _find_wp(wbs, wp_id)
    deliverables = wp.get("deliverables", [])
    if index < 0 or index >= len(deliverables):
        raise ValueError(f"Gecersiz deliverable index: {index}")
    deliverables.pop(index)
    return wbs


def update_technical_field(wbs: dict, wp_id: str, field: str, value: str) -> dict:
    """Teknik baglam alanini gunceller (frontend_requirements, backend_requirements, data_implications)."""
    valid_fields = {"frontend_requirements", "backend_requirements", "data_implications"}
    if field not in valid_fields:
        raise ValueError(f"Gecersiz alan: {field}. Gecerli: {valid_fields}")
    _, wp = _find_wp(wbs, wp_id)
    if "technical_context" not in wp:
        wp["technical_context"] = {"frontend_requirements": "", "backend_requirements": "",
                                    "integration_points": [], "data_implications": ""}
    wp["technical_context"][field] = value
    return wbs


def remove_integration_point(wbs: dict, wp_id: str, index: int) -> dict:
    """Entegrasyon noktasi siler (index bazli)."""
    _, wp = _find_wp(wbs, wp_id)
    points = wp.get("technical_context", {}).get("integration_points", [])
    if index < 0 or index >= len(points):
        raise ValueError(f"Gecersiz integration point index: {index}")
    points.pop(index)
    return wbs


def add_acceptance_criterion(wbs: dict, wp_id: str, criterion: str) -> dict:
    """Kabul kriteri ekler."""
    _, wp = _find_wp(wbs, wp_id)
    if "acceptance_criteria" not in wp:
        wp["acceptance_criteria"] = []
    wp["acceptance_criteria"].append(criterion)
    return wbs


def remove_acceptance_criterion(wbs: dict, wp_id: str, index: int) -> dict:
    """Kabul kriteri siler (index bazli)."""
    _, wp = _find_wp(wbs, wp_id)
    criteria = wp.get("acceptance_criteria", [])
    if index < 0 or index >= len(criteria):
        raise ValueError(f"Gecersiz acceptance criterion index: {index}")
    criteria.pop(index)
    return wbs


def update_complexity_drivers(wbs: dict, wp_id: str, drivers: list) -> dict:
    """Complexity driver listesini gunceller."""
    _, wp = _find_wp(wbs, wp_id)
    wp["complexity"]["drivers"] = drivers
    return wbs
