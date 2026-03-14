import argparse
import csv
from pathlib import Path
import xml.etree.ElementTree as ET


def tag_endswith(elem, name: str) -> bool:
    return isinstance(elem.tag, str) and elem.tag.endswith(name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    msf_dir = Path(args.workdir) / "msfragger"
    pepxmls = sorted(msf_dir.glob("*.pepXML"))

    if not pepxmls:
        raise FileNotFoundError(f"No pepXML found in {msf_dir}")

    pepxml = pepxmls[0]

    tree = ET.parse(pepxml)
    root = tree.getroot()

    rows = []

    for sq in root.iter():
        if not tag_endswith(sq, "spectrum_query"):
            continue

        spectrum = sq.attrib.get("spectrum", "")
        scan = sq.attrib.get("start_scan", "")
        charge = sq.attrib.get("assumed_charge", "")

        best_hit = None
        best_expect = None

        for hit in sq.iter():
            if not tag_endswith(hit, "search_hit"):
                continue

            peptide = hit.attrib.get("peptide", "")
            protein = hit.attrib.get("protein", "")

            expect_val = None
            for score in hit.iter():
                if not tag_endswith(score, "search_score"):
                    continue
                if score.attrib.get("name") == "expect":
                    try:
                        expect_val = float(score.attrib.get("value"))
                    except Exception:
                        expect_val = None

            if best_hit is None:
                best_hit = (peptide, protein, expect_val)
                best_expect = expect_val if expect_val is not None else float("inf")
            else:
                curr = expect_val if expect_val is not None else float("inf")
                if curr < best_expect:
                    best_hit = (peptide, protein, expect_val)
                    best_expect = curr

        if best_hit is None:
            continue

        peptide, protein, expect_val = best_hit
        rows.append({
            "spectrum": spectrum,
            "scan": scan,
            "charge": charge,
            "peptide": peptide,
            "protein": protein,
            "expect": "" if expect_val is None else expect_val,
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["spectrum", "scan", "charge", "peptide", "protein", "expect"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
