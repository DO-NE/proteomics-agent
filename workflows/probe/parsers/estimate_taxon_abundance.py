import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--protein-taxonomy", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    species_psms = defaultdict(int)
    species_proteins = defaultdict(int)
    species_unique_peptides = defaultdict(int)

    with open(args.protein_taxonomy) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            species = row["species"]
            n_psms = int(row["n_psms"])
            n_unique_peptides = int(row["n_unique_peptides"])

            species_proteins[species] += 1
            species_psms[species] += n_psms
            species_unique_peptides[species] += n_unique_peptides

    total_psms = sum(species_psms.values())

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "species",
                "n_proteins",
                "total_psms",
                "total_unique_peptides",
                "relative_abundance",
            ],
            delimiter="\t",
        )
        writer.writeheader()

        for species in sorted(species_psms, key=lambda x: species_psms[x], reverse=True):
            rel = species_psms[species] / total_psms if total_psms > 0 else 0.0
            writer.writerow({
                "species": species,
                "n_proteins": species_proteins[species],
                "total_psms": species_psms[species],
                "total_unique_peptides": species_unique_peptides[species],
                "relative_abundance": rel,
            })


if __name__ == "__main__":
    main()
