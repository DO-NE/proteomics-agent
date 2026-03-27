import argparse
import csv
import json
from pathlib import Path


def load_truth(path):
    with open(path) as f:
        return json.load(f)


def load_pred(path):
    pred = {}
    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            species = row.get("species", "").strip()
            if not species:
                continue
            pred[species] = float(row.get("relative_abundance", 0.0))
    return pred


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pred", required=True)
    p.add_argument("--truth", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    truth = load_truth(args.truth)
    pred = load_pred(args.pred)

    species = sorted(set(truth) | set(pred))

    l1 = 0.0
    rmse_sum = 0.0
    detected = 0

    for s in species:
        t = truth.get(s, 0.0)
        p_ = pred.get(s, 0.0)
        l1 += abs(t - p_)
        rmse_sum += (t - p_) ** 2
        if p_ > 0:
            detected += 1

    rmse = (rmse_sum / len(species)) ** 0.5 if species else 0.0

    result = {
        "n_species_union": len(species),
        "l1_error": l1,
        "rmse": rmse,
        "n_detected_species": detected,
        "truth_species": len(truth),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
