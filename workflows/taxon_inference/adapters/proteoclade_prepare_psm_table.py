import argparse
import csv
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--peptide-hits", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(args.peptide_hits) as f_in, out_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.DictWriter(
            f_out,
            fieldnames=["Peptide", "Scan", "Score", "Intensity"],
            delimiter="\t",
        )
        writer.writeheader()

        for row in reader:
            peptide = row.get("peptide", "").strip()
            source = Path(row.get("source_file", "sample")).stem
            scan = row.get("scan", "").strip()
            score = row.get("score_value", "").strip()

            if not peptide or not scan:
                continue

            writer.writerow({
                "Peptide": peptide,
                "Scan": f"{source}:{scan}",
                "Score": score if score != "" else "0",
                "Intensity": "1",
            })


if __name__ == "__main__":
    main()
