import argparse
import csv
import json
import os
import subprocess
from pathlib import Path

import yaml


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def run(cmd, env=None):
    print("[RUN]", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, env=env)


def warn(message):
    print(f"[WARN] {message}")


def ensure_taxonomy_index(fasta, out_tsv):
    if Path(out_tsv).exists():
        return
    run([
        "python",
        "workflows/probe/parsers/build_protein_taxonomy_index.py",
        "--fasta", fasta,
        "--out", out_tsv,
    ])


def search_subdir(search_engine):
    mapping = {
        "dda_msfragger_philosopher": "msfragger",
        "dda_comet": "comet",
        "dda_msgfplus": "msgfplus",
    }
    if search_engine not in mapping:
        raise ValueError(f"Unsupported search engine for ProteinProphet: {search_engine}")
    return mapping[search_engine]


def run_optional_protein_inference(pi, pipeline, tool_reg, cfg, workdir, canonical, assets, fasta, peptide_hits):
    if not pi:
        warn("No protein_inference configured; skipping optional protein stage.")
        return None, {"status": "skipped", "reason": "not_configured"}

    protein_groups = canonical / "protein_groups.tsv"
    se = pipeline["search_engine"]

    try:
        if pi == "philosopher_proteinprophet":
            pi_rec = tool_reg["protein_inference"][pi]
            env_pi = os.environ.copy()
            env_pi["WORKDIR"] = str(workdir)
            env_pi["FASTA"] = fasta

            # allow dedicated block, or fall back to search engine block
            env_pi.update(cfg.get("tool_env", {}).get(pi, {}))
            env_pi.update(cfg.get("tool_env", {}).get(se, {}))

            run([
                "bash",
                pi_rec["wrapper"],
                search_subdir(se)
            ], env=env_pi)

            run([
                "python",
                pi_rec["parser"],
                "--workdir", str(workdir),
                "--out", str(protein_groups),
            ])

        elif pi == "metalp":
            pi_rec = tool_reg["protein_inference"][pi]

            metalp_id = assets / "metalp_identification.tsv"
            metalp_pro2otu = assets / "metalp_pro2otu.tsv"
            metalp_prob = assets / "metalp_otu_prob.tsv"
            metalp_outdir = workdir / "metalp"

            # optional prior: if a baseline composition exists in config, pass it; else uniform
            prior_comp = cfg.get("metalp_prior_composition")

            cmd = [
                "python",
                pi_rec["build_inputs"],
                "--peptide-hits", str(peptide_hits),
                "--taxonomy-index", str(assets / "protein_taxonomy_index.tsv"),
                "--out-identification", str(metalp_id),
                "--out-pro2otu", str(metalp_pro2otu),
                "--out-otu-prob", str(metalp_prob),
            ]
            if prior_comp:
                cmd.extend(["--prior-composition", prior_comp])
            run(cmd)

            metalp_script = cfg.get("tool_env", {}).get("metalp", {}).get("METALP_SCRIPT")
            if not metalp_script:
                raise RuntimeError("METALP_SCRIPT not set in config under tool_env.metalp")

            run([
                "python",
                pi_rec["adapter"],
                "--metalp-script", metalp_script,
                "--identification", str(metalp_id),
                "--pro2otu", str(metalp_pro2otu),
                "--otu-prob", str(metalp_prob),
                "--outdir", str(metalp_outdir),
            ])

            run([
                "python",
                pi_rec["parser"],
                "--metalp-outdir", str(metalp_outdir),
                "--out", str(protein_groups),
            ])
        else:
            raise ValueError(f"Unsupported protein inference: {pi}")
    except Exception as e:
        warn(f"Optional protein inference stage failed ({pi}): {e}")
        return None, {"status": "failed", "reason": str(e)}

    if not protein_groups.exists() or protein_groups.stat().st_size == 0:
        warn(f"Optional protein inference finished but no protein groups were written: {protein_groups}")
        return None, {"status": "failed", "reason": "no_protein_groups_output"}

    return protein_groups, {"status": "completed"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pipeline-id", required=True)
    p.add_argument("--pipeline-registry", required=True)
    p.add_argument("--tool-registry", required=True)
    p.add_argument("--config", required=True)
    args = p.parse_args()

    pipe_reg = load_yaml(args.pipeline_registry)
    tool_reg = load_yaml(args.tool_registry)
    cfg = load_yaml(args.config)

    pipeline = None
    for rec in pipe_reg["pipelines"]:
        if rec["pipeline_id"] == args.pipeline_id:
            pipeline = rec
            break
    if pipeline is None:
        raise ValueError(f"Unknown pipeline_id: {args.pipeline_id}")

    run_id = cfg["run_id"]
    mzml = cfg["mzml"]
    fasta = cfg["fasta"]
    truth = cfg.get("truth")

    root = (Path("results/full") / run_id / args.pipeline_id).resolve()
    workdir = (root / "workdir").resolve()
    canonical = (root / "canonical").resolve()
    assets = (root / "assets").resolve()
    metrics_dir = (root / "metrics").resolve()

    for d in [workdir, canonical, assets, metrics_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Shared taxonomy index
    taxonomy_index = assets / "protein_taxonomy_index.tsv"
    ensure_taxonomy_index(fasta, str(taxonomy_index))

    # ---- Search stage ----
    se = pipeline["search_engine"]
    se_rec = tool_reg["tools"][se]
    env = os.environ.copy()
    env.update({
        "TOOL_ID": se,
        "MODALITY": pipeline.get("modality", "DDA"),
        "PRESET": "default",
        "MZML": mzml,
        "FASTA": fasta,
        "WORKDIR": str(workdir),
    })
    env.update(cfg.get("tool_env", {}).get(se, {}))

    run(["bash", se_rec["wrapper"]], env=env)

    peptide_hits = canonical / "peptide_hits.tsv"
    if se == "dda_msfragger_philosopher":
        run([
            "python",
            "workflows/probe/parsers/extract_peptide_hits.py",
            "--workdir", str(workdir),
            "--out", str(peptide_hits),
        ])
    else:
        run([
            "python",
            se_rec["parser"],
            "--workdir", str(workdir),
            "--out", str(peptide_hits),
        ])

    # ---- Taxon inference stage ----
    ti = pipeline["taxon_inference"]
    taxon_comp = canonical / "taxon_composition.tsv"
    tax_assign = canonical / "taxon_assignments.tsv"

    if ti == "unipept_lca":
        ti_rec = tool_reg["taxon_inference"][ti]

        run([
            "python",
            ti_rec["adapter"],
            "--peptide-hits", str(peptide_hits),
            "--out", str(tax_assign),
        ])

        run([
            "python",
            ti_rec["parser"],
            "--taxon-assignments", str(tax_assign),
            "--out", str(taxon_comp),
        ])

    elif ti == "proteoclade":
        ti_rec = tool_reg["taxon_inference"][ti]

        psm_table = assets / "proteoclade_psm.tsv"
        p_outdir = workdir / "proteoclade"

        run([
            "python",
            ti_rec["prepare_inputs"],
            "--peptide-hits", str(peptide_hits),
            "--out", str(psm_table),
        ])

        pcdb = cfg.get("tool_env", {}).get("proteoclade", {}).get("PROTEOCLADE_PCDB")
        pctaxa = cfg.get("tool_env", {}).get("proteoclade", {}).get("PROTEOCLADE_PCTAXA")
        threads = str(cfg.get("tool_env", {}).get("proteoclade", {}).get("PROTEOCLADE_THREADS", 6))

        if not pcdb or not pctaxa:
            raise RuntimeError("PROTEOCLADE_PCDB and PROTEOCLADE_PCTAXA must be set in config under tool_env.proteoclade")

        run([
            "python",
            ti_rec["adapter"],
            "--psm-table", str(psm_table),
            "--pcdb", pcdb,
            "--pctaxa", pctaxa,
            "--outdir", str(p_outdir),
            "--threads", threads,
        ])

        run([
            "python",
            ti_rec["parser"],
            "--proteoclade-outdir", str(p_outdir),
            "--out", str(taxon_comp),
        ])

        # Normalize ProteoClade assignments into canonical taxon_assignments.tsv.
        candidates = (
            list(p_outdir.glob("rollup_annotated_denovo_matched_*")) +
            list(p_outdir.glob("annotated_denovo_matched_*"))
        )
        if not candidates:
            raise FileNotFoundError(f"No ProteoClade assignment table found in {p_outdir}")
        source_assign = sorted(candidates)[0]
        delim = "\t" if "\t" in source_assign.read_text(errors="ignore")[:4096] else ","

        with source_assign.open() as in_f, tax_assign.open("w", newline="") as out_f:
            reader = csv.DictReader(in_f, delimiter=delim)
            if reader.fieldnames is None:
                raise RuntimeError(f"ProteoClade assignment table has no header: {source_assign}")
            species_col = next((c for c in reader.fieldnames if "species" in c.lower()), None)
            peptide_col = next((c for c in reader.fieldnames if c.lower() in {"peptide", "sequence"}), None)
            if species_col is None:
                raise RuntimeError(f"Could not detect species column in {source_assign}")

            writer = csv.DictWriter(
                out_f,
                fieldnames=[
                    "entity_type",
                    "entity_id",
                    "taxid",
                    "rank",
                    "name",
                    "assignment_method",
                    "confidence",
                ],
                delimiter="\t",
            )
            writer.writeheader()
            for row in reader:
                species = row.get(species_col, "").strip()
                if not species:
                    continue
                writer.writerow({
                    "entity_type": "peptide",
                    "entity_id": row.get(peptide_col, "").strip() if peptide_col else "",
                    "taxid": "",
                    "rank": "species",
                    "name": species,
                    "assignment_method": "proteoclade",
                    "confidence": "",
                })

    else:
        raise ValueError(f"Unsupported taxon inference: {ti}")

    # ---- Optional protein inference stage ----
    pi = pipeline.get("protein_inference")
    protein_groups, protein_stage = run_optional_protein_inference(
        pi=pi,
        pipeline=pipeline,
        tool_reg=tool_reg,
        cfg=cfg,
        workdir=workdir,
        canonical=canonical,
        assets=assets,
        fasta=fasta,
        peptide_hits=peptide_hits,
    )

    # ---- Evaluation ----
    pipeline_metrics = canonical / "pipeline_metrics.json"
    if truth:
        run([
            "python",
            "workflows/evaluation/evaluate_pipeline.py",
            "--pred", str(taxon_comp),
            "--truth", truth,
            "--out", str(pipeline_metrics),
        ])
    else:
        with pipeline_metrics.open("w") as f:
            json.dump({"status": "no_truth_provided"}, f, indent=2)

    # ---- Manifest ----
    manifest = {
        "pipeline_id": args.pipeline_id,
        "run_id": run_id,
        "search_engine": se,
        "protein_inference": pi,
        "taxon_inference": ti,
        "protein_stage": protein_stage,
        "mzml": mzml,
        "fasta": fasta,
        "outputs": {
            "peptide_hits": str(peptide_hits),
            "taxon_assignments": str(tax_assign),
            "taxon_composition": str(taxon_comp),
            "pipeline_metrics": str(pipeline_metrics),
        },
    }
    if protein_groups is not None:
        manifest["outputs"]["protein_groups"] = str(protein_groups)

    with (canonical / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
