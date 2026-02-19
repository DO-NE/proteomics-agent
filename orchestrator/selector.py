from typing import Dict, List, Any


def score_probe_result(profile: Dict[str, Any], probe: Dict[str, Any]) -> float:
    """
    Simple deterministic scoring logic.
    Can be expanded later with more advanced criteria.
    """

    score = 0.0

    # Must pass QC
    if not probe.get("qc", {}).get("fdr_ok", False):
        return -1e9  # effectively disqualify

    # Prefer more identifications
    score += probe.get("ids", {}).get("peptides", 0) * 1.0
    score += probe.get("ids", {}).get("protein_groups", 0) * 2.0

    # Penalize high memory usage
    score -= probe.get("resources", {}).get("max_rss_gb", 0) * 0.5

    # Penalize long runtime
    score -= probe.get("resources", {}).get("walltime_sec", 0) * 0.001

    return score


def select_toolchain(profile: Dict[str, Any], probe_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select best toolchain based on probe metrics.
    """

    if not probe_results:
        raise ValueError("No probe results provided.")

    scored = [
        (score_probe_result(profile, p), p)
        for p in probe_results
    ]

    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_probe = scored[0]

    return {
        "selected_tool_id": best_probe["tool_id"],
        "modality": best_probe["modality"],
        "score": best_score
    }
