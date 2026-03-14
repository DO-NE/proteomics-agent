import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--peptide-tsv", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    protein_to_peptides = defaultdict(set)
    protein_to_psms = defaultdict(int)

    with open(args.peptide_tsv) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            protein = row["protein"]
            peptide = row["peptide"]

            protein_to_psms[protein] += 1
            protein_to_peptides[protein].add(peptide)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["protein", "n_psms", "n_unique_peptides", "peptides"],
            delimiter="\t",
        )
        writer.writeheader()

        for protein in sorted(protein_to_psms):
            peptides = sorted(protein_to_peptides[protein])
            writer.writerow({
                "protein": protein,
                "n_psms": protein_to_psms[protein],
                "n_unique_peptides": len(peptides),
                "peptides": ";".join(peptides),
            })


if __name__ == "__main__":
    main()
