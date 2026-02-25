import argparse
import csv
from pathlib import Path

def count_rows(tsv: Path) -> int:
    if not tsv.exists():
        return 0
    with tsv.open() as f:
        r = csv.reader(f, delimiter="\t")
        header = next(r, None)
        if header is None:
            return 0
        return sum(1 for _ in r)

def fdr_ok_from_tsv(tsv: Path, qcol_candidates=("q-value", "q_value", "qvalue")) -> bool:
    """
    Probe-level heuristic:
    - If q-value column exists, require at least one row with q <= 0.01
    - If q-value column absent, return True if file has any rows
    """
    if not tsv.exists():
        return False
    with tsv.open() as f:
        r = csv.reader(f, delimiter="\t")
        header = next(r, None)
        if not header:
            return False
        colmap = {h.strip().lower(): i for i, h in enumerate(header)}
        qidx = None
        for c in qcol_candidates:
            if c in colmap:
                qidx = colmap[c]
                break
        any_row = False
        if qidx is None:
            for _ in r:
                any_row = True
                break
            return any_row
        for row in r:
            if not row:
                continue
            any_row = True
            try:
                q = float(row[qidx])
                if q <= 0.01:
                    return True
            except Exception:
                continue
        return False if any_row else False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", required=True)
    args = p.parse_args()

    wd = Path(args.workdir)
    peptide_tsv = wd / "philosopher" / "peptide.tsv"
    protein_tsv = wd / "philosopher" / "protein.tsv"

    peptides = count_rows(peptide_tsv)
    protein_groups = count_rows(protein_tsv)

    # Prefer peptide-level q-values if available; fallback to "has rows"
    fdr_ok = fdr_ok_from_tsv(peptide_tsv)

    print(peptides)
    print(protein_groups)
    print("true" if fdr_ok else "false")

if __name__ == "__main__":
    main()
