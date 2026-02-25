import argparse
import subprocess
import time
from pathlib import Path
import os
import json

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
    p.add_argument("--tool-env-json", required=False, default="{}")
    args = p.parse_args()

    registry = load_registry(Path(args.registry))
    tools = registry.get("tools", {})
    if args.tool_id not in tools:
        raise SystemExit(f"tool_id not found in registry: {args.tool_id}")

    entry = tools[args.tool_id]
    wrapper = Path(entry["wrapper"])
    parser = Path(entry["parser"]) if "parser" in entry else None

    if not wrapper.exists():
        raise SystemExit(f"wrapper not found: {wrapper}")
    if parser is not None and not parser.exists():
        raise SystemExit(f"parser not found: {parser}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a dedicated workdir per tool run (kept next to metrics)
    workdir = out_path.parent / "workdir"
    workdir.mkdir(parents=True, exist_ok=True)

    # Run wrapper with env vars
    env = dict(os.environ)
    env.update({
        "TOOL_ID": args.tool_id,
        "MODALITY": args.modality,
        "PRESET": args.preset,
        "MZML": args.mzml,
        "FASTA": args.fasta,
        "WORKDIR": str(workdir),
    })

    # Merge per-tool env (from Snakefile --tool-env-json)
    tool_env = json.loads(args.tool_env_json)
    env.update({k: str(v) for k, v in tool_env.items()})

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

    # Store wrapper logs
    (out_path.parent / "wrapper.stdout.txt").write_text(proc.stdout)
    (out_path.parent / "wrapper.stderr.txt").write_text(proc.stderr)

    # If parser provided, use it to compute peptides/protein_groups/fdr_ok.
    if parser is not None and exit_code == 0:
        pres = subprocess.run(
            ["python", str(parser), "--workdir", str(workdir)],
            text=True,
            capture_output=True,
        )
        (out_path.parent / "parser.stdout.txt").write_text(pres.stdout)
        (out_path.parent / "parser.stderr.txt").write_text(pres.stderr)

        if pres.returncode == 0:
            lines = [ln.strip() for ln in pres.stdout.splitlines() if ln.strip() != ""]
            if len(lines) >= 3:
                peptides = int(lines[0])
                protein_groups = int(lines[1])
                fdr_ok = lines[2].lower()
            else:
                peptides, protein_groups, fdr_ok = 0, 0, "false"
        else:
            peptides, protein_groups, fdr_ok = 0, 0, "false"
    else:
        peptides = 1 if exit_code == 0 else 0
        protein_groups = 1 if exit_code == 0 else 0
        fdr_ok = "true" if exit_code == 0 else "false"

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
