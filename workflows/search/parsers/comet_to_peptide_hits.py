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

    comet_dir = Path(args.workdir) / "comet"
    pepxmls = sorted(list(comet_dir.glob("*.pep.xml")) + list(comet_dir.glob("*.pepXML")))

    if not pepxmls:
        raise FileNotFoundError(f"No Comet pepXML found in {comet_dir}")

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
            xcorr_val = None

            for score in hit.iter():
                if not tag_endswith(score, "search_score"):
                    continue
                name = score.attrib.get("name", "")
                val = score.attrib.get("value", "")
                if name == "expect":
                    try:
                        expect_val = float(val)
                    except Exception:
                        pass
                elif name.lower() == "xcorr":
                    try:
                        xcorr_val = float(val)
                    except Exception:
                        pass

            current_rank = expect_val if expect_val is not None else float("inf")

            if best_hit is None or current_rank < best_expect:
                best_hit = (peptide, protein, expect_val, xcorr_val)
                best_expect = current_rank

        if best_hit is None:
            continue

        peptide, protein, expect_val, xcorr_val = best_hit
        rows.append({
            "source_file": pepxml.name,
            "spectrum": spectrum,
            "scan": scan,
            "charge": charge,
            "peptide": peptide,
            "modified_peptide": peptide,
            "proteins": protein,
            "score_name": "expect",
            "score_value": "" if expect_val is None else expect_val,
            "aux_score_name": "xcorr",
            "aux_score_value": "" if xcorr_val is None else xcorr_val,
            "search_engine": "comet",
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

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
