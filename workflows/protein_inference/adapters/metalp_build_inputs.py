import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_proteins(value: str):
    if not value:
        return []
    value = value.replace(",", ";")
    return [x.strip() for x in value.split(";") if x.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--peptide-hits", required=True)
    p.add_argument("--taxonomy-index", required=True)
    p.add_argument("--out-identification", required=True)
    p.add_argument("--out-pro2otu", required=True)
    p.add_argument("--out-otu-prob", required=True)
    p.add_argument("--prior-composition", required=False, default=None)
    args = p.parse_args()

    # accession -> (taxid, species)
    accession_to_tax = {}
    with open(args.taxonomy_index) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            accession_to_tax[row["accession"]] = (row["taxid"], row["species"])

    # Build peptide identification summary
    # Schema assumption for MetaLP input:
    # peptide \t score \t proteins
    best_by_peptide = {}
    observed_taxids = set()

    with open(args.peptide_hits) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            pep = row["peptide"].strip()
            if not pep:
                continue

            proteins = parse_proteins(row.get("proteins", ""))
            score_raw = row.get("score_value", "")

            try:
                score = float(score_raw)
            except Exception:
                score = 1.0

            # keep the best (lowest) score
            if pep not in best_by_peptide or score < best_by_peptide[pep]["score"]:
                best_by_peptide[pep] = {
                    "score": score,
                    "proteins": proteins,
                }

            for prot in proteins:
                parts = prot.split("|")
                acc = parts[1] if len(parts) >= 2 else prot
                if acc in accession_to_tax:
                    observed_taxids.add(accession_to_tax[acc][0])

    out_id = Path(args.out_identification)
    out_id.parent.mkdir(parents=True, exist_ok=True)
    with out_id.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["peptide", "score", "proteins"])
        for pep, rec in sorted(best_by_peptide.items()):
            writer.writerow([pep, rec["score"], ";".join(rec["proteins"])])

    # Build protein -> OTU mapping (use taxid as OTU)
    out_pro2otu = Path(args.out_pro2otu)
    out_pro2otu.parent.mkdir(parents=True, exist_ok=True)
    with out_pro2otu.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["protein", "otu"])
        for acc, (taxid, species) in sorted(accession_to_tax.items()):
            writer.writerow([acc, taxid])

    # Build OTU probabilities
    # If prior composition is supplied, map species -> taxid and use those probabilities.
    # Otherwise, assign uniform probability across observed taxids.
    otu_probs = defaultdict(float)

    if args.prior_composition:
        species_to_taxid = {}
        for acc, (taxid, species) in accession_to_tax.items():
            species_to_taxid[species] = taxid

        with open(args.prior_composition) as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                species = row.get("species", "").strip()
                if not species:
                    continue
                try:
                    rel = float(row.get("relative_abundance", 0.0))
                except Exception:
                    rel = 0.0
                if species in species_to_taxid:
                    otu_probs[species_to_taxid[species]] += rel

    if not otu_probs:
        taxids = sorted(observed_taxids)
        if taxids:
            uniform = 1.0 / len(taxids)
            for t in taxids:
                otu_probs[t] = uniform

    out_prob = Path(args.out_otu_prob)
    out_prob.parent.mkdir(parents=True, exist_ok=True)
    with out_prob.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["otu", "probability"])
        for otu, prob in sorted(otu_probs.items()):
            writer.writerow([otu, prob])


if __name__ == "__main__":
    main()
