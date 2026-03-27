import argparse
import subprocess
from pathlib import Path
import yaml


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def run(cmd):
    print("[RUN]", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pipeline-registry", required=True)
    p.add_argument("--tool-registry", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--selector-out", required=True)
    args = p.parse_args()

    pipe_reg = load_yaml(args.pipeline_registry)
    cfg = load_yaml(args.config)
    run_id = cfg["run_id"]
    results_root = Path("results/full") / run_id

    for rec in pipe_reg["pipelines"]:
        run([
            "python",
            "orchestrator/run_full_pipeline.py",
            "--pipeline-id", rec["pipeline_id"],
            "--pipeline-registry", args.pipeline_registry,
            "--tool-registry", args.tool_registry,
            "--config", args.config,
        ])

    run([
        "python",
        "orchestrator/select_pipeline.py",
        "--pipeline-registry", args.pipeline_registry,
        "--results-root", str(results_root),
        "--out", args.selector_out,
    ])


if __name__ == "__main__":
    main()
