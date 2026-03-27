import argparse
import json
from pathlib import Path
import yaml


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def score_metrics(metrics):
    # Lower is better for l1/rmse
    l1 = metrics.get("l1_error", 1e9)
    rmse = metrics.get("rmse", 1e9)
    return -(0.7 * l1 + 0.3 * rmse)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pipeline-registry", required=True)
    p.add_argument("--results-root", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    reg = load_yaml(args.pipeline_registry)
    results_root = Path(args.results_root)

    best = None

    for pipe in reg["pipelines"]:
        pid = pipe["pipeline_id"]
        metrics_file = results_root / pid / "pipeline_metrics.json"
        if not metrics_file.exists():
            continue

        with open(metrics_file) as f:
            metrics = json.load(f)

        score = score_metrics(metrics)

        rec = {
            "pipeline_id": pid,
            "score": score,
            "metrics": metrics,
            "config": pipe,
        }

        if best is None or rec["score"] > best["score"]:
            best = rec

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as f:
        json.dump(best if best is not None else {}, f, indent=2)


if __name__ == "__main__":
    main()
