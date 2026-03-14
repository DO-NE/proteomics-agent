import argparse
import csv
from pathlib import Path


def extract_accession(protein: str) -> str:
    parts = protein.split("|")
    if len(parts) >= 2:
        return parts[1]
    return ""


def load_taxonomy_index(path: str):
    taxonomy = {}
    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            taxonomy[row["accession"]] = {
                "taxid": row["taxid"],
                "species": row["species"],
            }
    return taxonomy


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--protein-support", required=True)
    p.add_argument("--taxonomy-index", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    taxonomy = load_taxonomy_index(args.taxonomy_index)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(args.protein_support) as f_in, out_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.DictWriter(
            f_out,
            fieldnames=[
                "protein",
                "accession",
                "taxid",
                "species",
                "n_psms",
                "n_unique_peptides",
                "peptides",
            ],
            delimiter="\t",
        )
        writer.writeheader()

        for row in reader:
            protein = row["protein"]
            accession = extract_accession(protein)

            tax = taxonomy.get(accession, {"taxid": "NA", "species": "UNKNOWN"})

            writer.writerow({
                "protein": protein,
                "accession": accession,
                "taxid": tax["taxid"],
                "species": tax["species"],
                "n_psms": row["n_psms"],
                "n_unique_peptides": row["n_unique_peptides"],
                "peptides": row["peptides"],
            })


if __name__ == "__main__":
    main()
