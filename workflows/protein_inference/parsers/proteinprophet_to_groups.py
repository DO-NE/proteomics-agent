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

    pp_dir = Path(args.workdir) / "proteinprophet"
    sentinel = pp_dir / "NO_PROTEINPROPHET_DATA"
    prot_xmls = sorted(list(pp_dir.glob("*.prot.xml")) + list(pp_dir.glob("*.protXML")))

    rows = []
    group_id = 0

    if sentinel.exists():
        print(f"[WARN] ProteinProphet skipped due to empty PeptideProphet output: {sentinel}")
    elif not prot_xmls:
        raise FileNotFoundError(f"No ProteinProphet prot.xml found in {pp_dir}")
    else:
        prot_xml = prot_xmls[0]
        tree = ET.parse(prot_xml)
        root = tree.getroot()

        for elem in root.iter():
            if not tag_endswith(elem, "protein_group"):
                continue

            group_id += 1
            representative_protein = ""
            proteins = []
            probability = elem.attrib.get("probability", "")

            for child in elem.iter():
                if tag_endswith(child, "protein"):
                    name = child.attrib.get("protein_name", "")
                    if not representative_protein:
                        representative_protein = name
                    if name:
                        proteins.append(name)

            rows.append({
                "protein_group_id": f"PG{group_id}",
                "representative_protein": representative_protein,
                "proteins": ";".join(sorted(set(proteins))),
                "n_psms": "",
                "n_unique_peptides": "",
                "protein_probability": probability,
                "inference_method": "proteinprophet",
            })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

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
        writer.writerows(rows)


if __name__ == "__main__":
    main()
