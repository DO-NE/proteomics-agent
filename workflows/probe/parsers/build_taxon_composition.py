import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--taxon-tsv", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    taxon_psms = defaultdict(int)
    taxon_proteins = defaultdict(int)
    taxon_peptides = defaultdict(int)

    with open(args.taxon_tsv) as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            taxon = row["taxon"]

            taxon_proteins[taxon] += 1
            taxon_psms[taxon] += int(row["n_psms"])
            taxon_peptides[taxon] += int(row["n_unique_peptides"])

    total_psms = sum(taxon_psms.values())

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "taxon",
                "n_proteins",
                "total_psms",
                "total_unique_peptides",
                "relative_abundance",
            ],
            delimiter="\t",
        )

        writer.writeheader()

        for taxon in sorted(taxon_psms):
            rel = taxon_psms[taxon] / total_psms if total_psms else 0

            writer.writerow({
                "taxon": taxon,
                "n_proteins": taxon_proteins[taxon],
                "total_psms": taxon_psms[taxon],
                "total_unique_peptides": taxon_peptides[taxon],
                "relative_abundance": rel,
            })


if __name__ == "__main__":
    main()
