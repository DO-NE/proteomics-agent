import argparse
import subprocess
import time
from pathlib import Path

import yaml


def load_registry(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registry", required=True)
    p.add_argument("--tool-id", required=True)
    p.add_argument("--modality", required=True, choices=["DDA", "DIA"])
    p.add_argument("--preset", required=False, default="")
    p.add_argument("--mzml", required=True)
    p.add_argument("--fasta", required=True)
    p.add_argument("--emit-metrics", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    registry = load_registry(Path(args.registry))
    tools = registry.get("tools", {})
    if args.tool_id not in tools:
        raise SystemExit(f"tool_id not found in registry: {args.tool_id}")

    entry = tools[args.tool_id]
    wrapper = Path(entry["wrapper"])
    if not wrapper.exists():
        raise SystemExit(f"wrapper not found: {wrapper}")

    # Run wrapper with env vars (common pattern for wrappers)
    env = dict(**{k: v for k, v in dict(**__import__("os").environ).items()})
    env.update({
        "TOOL_ID": args.tool_id,
        "MODALITY": args.modality,
        "PRESET": args.preset,
        "MZML": args.mzml,
        "FASTA": args.fasta,
    })

    start = time.perf_counter()
    proc = subprocess.run(
        ["bash", str(wrapper)],
        env=env,
        text=True,
        capture_output=True,
    )
    walltime_sec = time.perf_counter() - start

    # For now we don't measure RSS here (Slurm profile later via sacct)
    max_rss_gb = 0.0
    exit_code = proc.returncode

    # Stub IDs for now (real parsers will fill these later)
    peptides = 1
    protein_groups = 1
    fdr_ok = "true" if exit_code == 0 else "false"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Store wrapper logs next to metrics
    (out_path.parent / "wrapper.stdout.txt").write_text(proc.stdout)
    (out_path.parent / "wrapper.stderr.txt").write_text(proc.stderr)

    # Emit standardized metrics json
    subprocess.run(
        [
            "python",
            args.emit_metrics,
            "--tool-id", args.tool_id,
            "--modality", args.modality,
            "--preset", args.preset,
            "--mzml", args.mzml,
            "--fasta", args.fasta,
            "--walltime-sec", str(walltime_sec),
            "--max-rss-gb", str(max_rss_gb),
            "--exit-code", str(exit_code),
            "--peptides", str(peptides),
            "--protein-groups", str(protein_groups),
            "--fdr-ok", fdr_ok,
            "--out", str(out_path),
        ],
        check=True,
        text=True,
    )


if __name__ == "__main__":
    main()
