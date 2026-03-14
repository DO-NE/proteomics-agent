import argparse
import csv
from pathlib import Path


def extract_taxon_from_protein(protein: str) -> str:
    """
    Very simple parser for UniProt-like names:
    sp|P60174|TPIS_HUMAN  -> HUMAN

    Later, for real metaproteomics DBs, this should be replaced by:
    accession -> taxid/species mapping
    """
    parts = protein.split("|")
    if len(parts) >= 3:
        name = parts[2]
        if "_" in name:
            return name.split("_")[-1]
    return "UNKNOWN"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--protein-tsv", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(args.protein_tsv) as f_in, out_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.DictWriter(
            f_out,
            fieldnames=["protein", "taxon", "n_psms", "n_unique_peptides", "peptides"],
            delimiter="\t",
        )
        writer.writeheader()

        for row in reader:
            protein = row["protein"]
            taxon = extract_taxon_from_protein(protein)

            writer.writerow({
                "protein": protein,
                "taxon": taxon,
                "n_psms": row["n_psms"],
                "n_unique_peptides": row["n_unique_peptides"],
                "peptides": row["peptides"],
            })


if __name__ == "__main__":
    main()
