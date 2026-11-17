from typing import Any, Dict, List, Optional


def _key(ans: Dict[str, Any]) -> Any:
    correct = ans.get("correct")
    return correct.get("selected") if isinstance(correct, dict) else correct


def _rules(ans: Dict[str, Any]) -> Dict[str, Any]:
    return {**(ans.get("meta") or {}), **(ans.get("scoring") or {})}


def _likert(ans: Dict[str, Any]) -> int:
    value = ans.get("response", {}).get("value", 3)
    return max(1, min(5, int(value) if str(value).isdigit() else 3))


def _level(pct: float, bands: List[tuple]) -> str:
    return next((label for threshold, label in bands if pct >= threshold), bands[-1][1])


def score_m1(answers: List[Dict]) -> Dict:
    if not answers:
        return {"raw": 0, "level": "a_developper", "by_section": {}, "max_possible": 0}

    by_section: Dict[str, int] = {}
    raw = 0
    for ans in answers:
        section = _rules(ans).get("section") or ans.get("category") or "general"
        by_section.setdefault(section, 0)
        if _key(ans) is not None and ans["response"].get("selected") == _key(ans):
            raw += 1
            by_section[section] += 1

    max_possible = len(answers)
    level = _level(raw / max_possible, [(0.90, "exceptionnel"), (0.80, "eleve"), (0.65, "solide"), (0.50, "modere"), (0, "a_developper")])
    return {"raw": raw, "level": level, "by_section": by_section, "max_possible": max_possible}


def score_m2(answers: List[Dict]) -> Dict:
    dims = ("O", "C", "E", "A", "N")
    if not answers:
        return {**{d: 24 for d in dims}, "archetype": "balanced", "social_desirability": False}

    totals = {d: 0 for d in dims}
    counts = {d: 0 for d in dims}
    inverted_maxed = {d: 0 for d in dims}
    for ans in answers:
        rules = _rules(ans)
        dim = rules.get("dimension")
        if dim not in totals:
            continue
        value = _likert(ans)
        if rules.get("inverted"):
            inverted_maxed[dim] += value == 5
            value = 6 - value
        totals[dim] += value
        counts[dim] += 1

    scores = {d: round(totals[d] / counts[d] * 8) if counts[d] else 24 for d in dims}
    return {
        **scores,
        "archetype": _compute_archetype(scores),
        "social_desirability": any(v > 3 for v in inverted_maxed.values()),
    }


def _compute_archetype(scores: Dict) -> str:
    O, C, E, A, N = scores["O"], scores["C"], scores["E"], scores["A"], scores["N"]
    stability = 40 - N
    if C >= 30 and O >= 28 and E <= 25:
        return "architect"
    if E >= 30 and A >= 28 and stability >= 20:
        return "catalyst"
    if C >= 30 and stability >= 22 and A >= 26:
        return "guardian"
    if O >= 30 and E >= 28:
        return "explorer"
    return "balanced"


def _ranking_points(ans: Dict[str, Any]) -> Optional[int]:
    optimal = _key(ans) or []
    if not optimal:
        return None
    ranking = ans["response"].get("ranking", [])
    hits = sum(1 for i, opt in enumerate(ranking) if i < len(optimal) and opt == optimal[i])
    return {4: 6, 3: 4, 2: 2}.get(hits, 0)


def score_m3(answers: List[Dict]) -> Dict:
    by_dim = {"people": 0, "pressure": 0, "ethics": 0, "vision": 0}
    dim_max = dict.fromkeys(by_dim, 0)
    if not answers:
        return {"raw": 0, "level": "a_developper", "by_dim": by_dim, "dim_max": dim_max, "style": "transactional", "max_possible": 0}

    raw, scored = 0, 0
    style_signals = {"transformational": 0, "directive": 0}
    for ans in answers:
        pts = _ranking_points(ans)
        if pts is None:
            continue
        scored += 1
        raw += pts
        rules = _rules(ans)
        if rules.get("dimension") in by_dim:
            by_dim[rules["dimension"]] += pts
            dim_max[rules["dimension"]] += 6
        if rules.get("style") in style_signals and pts >= 4:
            style_signals[rules["style"]] += 1

    max_possible = 6 * scored or 1
    level = _level(raw / max_possible, [(0.90, "exceptionnel"), (0.73, "solide"), (0.53, "modere"), (0, "a_developper")])
    style = next((s for s, n in style_signals.items() if n >= 4), "transactional")
    return {"raw": raw, "level": level, "by_dim": by_dim, "dim_max": dim_max, "style": style, "max_possible": max_possible}


def score_m4(answers: List[Dict]) -> Dict:
    if not answers:
        return {"engagement": 30, "values": {"top3": [], "bottom3": [], "raw": {}}}

    value_scores: Dict[str, int] = {}
    engagement_total, engagement_count = 0, 0
    for ans in answers:
        rules = _rules(ans)
        if ans.get("type") == "ranking" or "values" in rules:
            order = ans["response"].get("ranking") or ans["response"].get("order", [])
            for i, option_id in enumerate(order):
                dim = (rules.get("values") or {}).get(option_id)
                if dim:
                    value_scores[dim] = value_scores.get(dim, 0) + (4 - i)
        else:
            value = _likert(ans)
            engagement_total += 6 - value if rules.get("inverted") else value
            engagement_count += 1

    ranked = sorted(value_scores.items(), key=lambda x: x[1], reverse=True)
    engagement = round(engagement_total / engagement_count * 10) if engagement_count else 30
    return {
        "engagement": engagement,
        "values": {"top3": [v for v, _ in ranked[:3]], "bottom3": [v for v, _ in ranked[-3:]], "raw": value_scores},
    }


def _ratio(m3: Dict, dim: str) -> float:
    total = (m3.get("dim_max") or {}).get(dim, 0)
    return m3["by_dim"].get(dim, 0) / total if total else 0.5


def compute_global_score(m1: Dict, m2: Dict, m3: Optional[Dict], m4: Dict) -> Dict:
    m1_pct = m1["raw"] / (m1.get("max_possible") or 1)
    m2_avg = (m2["O"] + m2["C"] + m2["E"] + m2["A"] + (40 - m2["N"])) / 5
    m2_pct = m2_avg / 40
    m4_pct = m4["engagement"] / 50

    if m3:
        m3_pct = m3["raw"] / (m3.get("max_possible") or 1)
        score = (m1_pct * 30) + (m2_pct * 25) + (m3_pct * 30) + (m4_pct * 15)
    else:
        score = (m1_pct * 40) + (m2_pct * 35) + (m4_pct * 25)

    global_int = round(score * 100) / 100
    global_int = int(min(100, max(0, global_int)))

    label = (
        "tres_solide"     if global_int >= 80 else
        "solide"          if global_int >= 65 else
        "modere"          if global_int >= 50 else
        "en_progression"  if global_int >= 35 else
        "a_explorer"
    )
    return {"score": global_int, "label": label}


def compute_signals(m1: Dict, m2: Dict, m3: Optional[Dict], m4: Dict) -> List[Dict]:
    signals = []
    stability = 40 - m2["N"]

    if m1["raw"] >= 0.8 * (m1.get("max_possible") or 1) and m2["C"] >= 30 and stability >= 22:
        signals.append({
            "type": "positive", "modules": ["M1","M2"],
            "label": "Profil analytique stable",
            "detail": "Raisonnement solide et stabilité émotionnelle élevée. Fort potentiel pour des environnements exigeants."
        })

    if m2["E"] >= 30 and m2["A"] >= 28 and m3 and _ratio(m3, "people") >= 0.58:
        signals.append({
            "type": "positive", "modules": ["M2","M3"],
            "label": "Cohérence relationnelle forte",
            "detail": "Profil naturellement orienté personnes, confirmé par le jugement situationnel."
        })

    if m2["O"] >= 30 and "development" in m4["values"].get("top3", []):
        signals.append({
            "type": "positive", "modules": ["M2","M4"],
            "label": "Curiosité et motivation d'apprentissage alignées",
            "detail": "Profil ouvert et motivé par le développement. Éviter les environnements statiques."
        })

    if m1["raw"] <= 0.45 * (m1.get("max_possible") or 1) and m2["N"] >= 28:
        signals.append({
            "type": "alert", "modules": ["M1","M2"],
            "label": "Double signal sous pression",
            "detail": "Raisonnement limité et sensibilité émotionnelle élevée. Entretien impératif avant présentation."
        })

    if m3 and _ratio(m3, "ethics") <= 0.33:
        signals.append({
            "type": "alert", "modules": ["M3"],
            "label": "Arbitrages éthiques discutables",
            "detail": "Les scénarios éthiques révèlent une tendance à privilégier le résultat sur l'intégrité du processus."
        })

    if m2["N"] >= 26 and m4["engagement"] <= 27:
        signals.append({
            "type": "alert", "modules": ["M2","M4"],
            "label": "Motivation potentiellement fluctuante",
            "detail": "Sensibilité émotionnelle élevée combinée à un engagement modéré. À explorer en entretien."
        })

    if m2.get("social_desirability") and m3 and m3["raw"] >= 0.83 * m3["max_possible"]:
        signals.append({
            "type": "alert", "modules": ["M2","M3"],
            "label": "Possible optimisation consciente",
            "detail": "Pattern de désirabilité sociale détecté sur OCEAN. Résultats à interpréter avec prudence."
        })

    return signals
