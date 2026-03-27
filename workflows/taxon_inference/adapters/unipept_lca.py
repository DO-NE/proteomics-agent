import argparse
import csv
import json
import time
from pathlib import Path
from urllib import request

API_URL = "https://api.unipept.ugent.be/api/v1/pept2lca.json"


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def fetch_lca(peptides):
    payload = json.dumps({"peptides": peptides}).encode("utf-8")
    req = request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--peptide-hits", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    peptides = []
    with open(args.peptide_hits) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            pep = row["peptide"].strip()
            if pep:
                peptides.append(pep)

    peptides = sorted(set(peptides))

    rows = []
    for batch in chunked(peptides, 100):
        result = fetch_lca(batch)
        for item in result:
            rows.append({
                "entity_type": "peptide",
                "entity_id": item.get("peptide", ""),
                "taxid": item.get("taxon_id", ""),
                "rank": item.get("taxon_rank", ""),
                "name": item.get("taxon_name", ""),
                "assignment_method": "unipept_lca",
                "confidence": "",
            })
        time.sleep(0.2)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "entity_type",
                "entity_id",
                "taxid",
                "rank",
                "name",
                "assignment_method",
                "confidence",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
