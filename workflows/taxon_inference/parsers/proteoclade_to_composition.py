import argparse
import csv
from collections import defaultdict
from pathlib import Path


def detect_delimiter(path: Path):
    sample = path.read_text(errors="ignore")[:4096]
    return "\t" if "\t" in sample else ","


def choose_species_col(fieldnames):
    for name in fieldnames:
        low = name.lower()
        if "species" in low:
            return name
    return None


def choose_quant_col(fieldnames):
    preferences = [
        "Intensity", "Area", "Spectral Count", "SpectralCount",
        "Count", "count"
    ]
    for pref in preferences:
        if pref in fieldnames:
            return pref
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--proteoclade-outdir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    outdir = Path(args.proteoclade_outdir)

    candidates = list(outdir.glob("rollup_annotated_denovo_matched_*")) + list(outdir.glob("annotated_denovo_matched_*"))
    if not candidates:
        raise FileNotFoundError(f"No ProteoClade annotated output found in {outdir}")

    infile = sorted(candidates)[0]
    delim = detect_delimiter(infile)

    species_col = None
    quant_col = None
    counts = defaultdict(float)

    with infile.open() as f:
        reader = csv.DictReader(f, delimiter=delim)
        if reader.fieldnames is None:
            raise RuntimeError(f"ProteoClade output has no header: {infile}")

        species_col = choose_species_col(reader.fieldnames)
        quant_col = choose_quant_col(reader.fieldnames)

        if species_col is None:
            raise RuntimeError(f"Could not find species column in {infile}")

        for row in reader:
            species = row.get(species_col, "").strip()
            if not species:
                continue

            if quant_col:
                try:
                    val = float(row.get(quant_col, 0))
                except Exception:
                    val = 0.0
            else:
                val = 1.0

            counts[species] += val

    total = sum(counts.values())
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["species", "observation_count", "relative_abundance", "method"],
            delimiter="\t",
        )
        writer.writeheader()
        for species, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            writer.writerow({
                "species": species,
                "observation_count": cnt,
                "relative_abundance": cnt / total if total else 0.0,
                "method": "proteoclade",
            })


if __name__ == "__main__":
    main()
