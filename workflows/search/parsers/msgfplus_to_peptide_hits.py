import argparse
import csv
from pathlib import Path


def pick(row, *names):
    for n in names:
        if n in row and row[n] != "":
            return row[n]
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    msgf_dir = Path(args.workdir) / "msgfplus"
    tsvs = sorted(msgf_dir.glob("*.tsv"))
    if not tsvs:
        raise FileNotFoundError(f"No MSGF+ TSV found in {msgf_dir}")

    in_tsv = tsvs[0]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with in_tsv.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            peptide = pick(row, "Peptide", "Sequence")
            protein = pick(row, "Protein", "ProteinName")
            spectrum = pick(row, "#SpecFile", "SpectrumFile")
            scan = pick(row, "ScanNum", "Scan#")
            charge = pick(row, "Charge")
            spec_evalue = pick(row, "SpecEValue", "EValue")
            qval = pick(row, "QValue")

            rows.append({
                "source_file": in_tsv.name,
                "spectrum": spectrum,
                "scan": scan,
                "charge": charge,
                "peptide": peptide,
                "modified_peptide": peptide,
                "proteins": protein,
                "score_name": "SpecEValue",
                "score_value": spec_evalue,
                "aux_score_name": "QValue",
                "aux_score_value": qval,
                "search_engine": "msgfplus",
            })

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file", "spectrum", "scan", "charge", "peptide",
                "modified_peptide", "proteins", "score_name", "score_value",
                "aux_score_name", "aux_score_value", "search_engine"
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
