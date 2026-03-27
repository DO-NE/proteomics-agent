import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--taxon-assignments", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    counts = defaultdict(int)

    with open(args.taxon_assignments) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            name = row["name"].strip()
            if name:
                counts[name] += 1

    total = sum(counts.values())

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["species", "peptide_count", "relative_abundance", "method"],
            delimiter="\t",
        )
        writer.writeheader()

        for name, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            writer.writerow({
                "species": name,
                "peptide_count": cnt,
                "relative_abundance": cnt / total if total else 0.0,
                "method": "unipept_lca",
            })


if __name__ == "__main__":
    main()
