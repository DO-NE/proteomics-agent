import argparse
import os
from pathlib import Path

from proteoclade.pcannotate import annotate_denovo
from proteoclade.pcquant import roll_up


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--psm-table", required=True)
    p.add_argument("--pcdb", required=True)
    p.add_argument("--pctaxa", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--threads", type=int, default=6)
    args = p.parse_args()

    psm_table = Path(args.psm_table).resolve()
    pcdb = Path(args.pcdb).resolve()
    pctaxa = Path(args.pctaxa).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    old_cwd = Path.cwd()
    os.chdir(outdir)
    try:
        annotate_denovo(
            str(psm_table),
            str(pcdb),
            str(pctaxa),
            method="dbconstrain",
            taxon_levels=("species",),
            worker_threads=args.threads,
        )

        # ProteoClade writes files relative to cwd with known prefixes.
        denovo_matched = outdir / f"denovo_matched_{psm_table.name}"
        annotated = outdir / f"annotated_denovo_matched_{psm_table.name}"

        if annotated.exists():
            try:
                roll_up(str(annotated))
            except Exception:
                # roll_up is useful but not required for baseline composition
                pass
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
