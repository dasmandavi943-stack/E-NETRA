from typing import Dict


def calculate_composite_risk(
    financial_score: float,
    graph_score: float,
    visual_score: float,
    weights: Dict[str, float] | None = None,
) -> Dict[str, object]:
    """
    Compute the Composite Risk Index (CRI) on a 0-100 scale and assign a risk band.
    Default weights: 40% Financial, 30% Graph (Relational), 30% Visual (Physical).
    """
    w = weights or {"financial": 0.40, "graph": 0.30, "visual": 0.30}

    cri = (
        w["financial"] * financial_score
        + w["graph"] * graph_score
        + w["visual"] * visual_score
    )
    cri_rounded = round(float(max(0.0, min(100.0, cri))), 2)

    if cri_rounded >= 70.0:
        band = "RED"
        recommended_action = "Trigger immediate audit ticket, freeze pending tranche, and schedule field inspection."
    elif cri_rounded >= 35.0:
        band = "YELLOW"
        recommended_action = "Flag for document and milestone verification by district audit team."
    else:
        band = "GREEN"
        recommended_action = "Low risk; allow normal workflow progression."

    return {
        "cri_score": cri_rounded,
        "risk_band": band,
        "recommended_action": recommended_action,
        "component_scores": {
            "financial_score": round(float(financial_score), 2),
            "graph_score": round(float(graph_score), 2),
            "visual_score": round(float(visual_score), 2),
        },
    }
