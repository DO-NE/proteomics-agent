# proteomics-agent

Probe workflow skeleton (Snakemake) + deterministic toolchain selector.

## What exists (v0)
- `workflows/probe/`: probe runner skeleton producing standardized `probe_metrics.json`
- `schemas/`: JSON schemas for dataset profile and probe metrics
- `orchestrator/selector.py`: deterministic selection based on probe metrics

## Setup (HPC)
python -m pip install --no-user --upgrade --force-reinstall -r requirements-workflow.txt
