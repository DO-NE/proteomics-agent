import argparse
import csv
from pathlib import Path


def detect_delimiter(path: Path):
    sample = path.read_text(errors="ignore")[:4096]
    return "\t" if "\t" in sample else ","


def first_nonempty(row, names):
    for n in names:
        v = row.get(n, "")
        if v not in ("", None):
            return v
    return ""


def representative(proteins_value: str):
    if not proteins_value:
        return ""
    proteins_value = proteins_value.replace(",", ";")
    return proteins_value.split(";")[0].strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--metalp-outdir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    outdir = Path(args.metalp_outdir)
    candidates = [
        outdir / "metalp_filtered.txt",
        outdir / "metalp_raw.txt",
    ]
    infile = None
    for c in candidates:
        if c.exists():
            infile = c
            break

    if infile is None:
        raise FileNotFoundError(f"No MetaLP output found in {outdir}")

    delim = detect_delimiter(infile)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows_out = []

    with infile.open() as f:
        reader = csv.DictReader(f, delimiter=delim)
        if reader.fieldnames is None:
            raise RuntimeError(f"MetaLP output appears to have no header: {infile}")

        for i, row in enumerate(reader, start=1):
            proteins = first_nonempty(row, [
                "proteins", "protein_group", "protein_group_members",
                "ProteinGroup", "Proteins", "protein"
            ])
            score = first_nonempty(row, [
                "score", "Score", "probability", "Probability"
            ])

            rows_out.append({
                "protein_group_id": f"MetaLP_{i}",
                "representative_protein": representative(proteins),
                "proteins": proteins,
                "n_psms": "",
                "n_unique_peptides": "",
                "protein_probability": score,
                "inference_method": "metalp",
            })

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "protein_group_id",
                "representative_protein",
                "proteins",
                "n_psms",
                "n_unique_peptides",
                "protein_probability",
                "inference_method",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows_out)


if __name__ == "__main__":
    main()
