import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

def tag_endswith(elem, name: str) -> bool:
    # Handles namespace tags like "{...}spectrum_query"
    return isinstance(elem.tag, str) and elem.tag.endswith(name)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", required=True)
    args = p.parse_args()

    msf_dir = Path(args.workdir) / "msfragger"
    pepxmls = sorted(msf_dir.glob("*.pepXML"))

    if not pepxmls:
        print("0")
        print("0")
        print("false")
        return

    pepxml = pepxmls[0]

    try:
        tree = ET.parse(pepxml)
        root = tree.getroot()
    except Exception as e:
        # optional debug
        print(f"[msfragger_parser] failed to parse pepXML: {pepxml} err={e}", file=sys.stderr)
        print("0")
        print("0")
        print("false")
        return

    psm = 0
    peptides = set()

    # Iterate namespace-agnostic
    for sq in root.iter():
        if not tag_endswith(sq, "spectrum_query"):
            continue
        psm += 1

        # search_hit elements are descendants of spectrum_query
        for hit in sq.iter():
            if not tag_endswith(hit, "search_hit"):
                continue
            pep = hit.attrib.get("peptide")
            if pep:
                peptides.add(pep)

    peptide_count = len(peptides)

    # Probe QC heuristic (tune later)
    fdr_ok = "true" if peptide_count >= 50 else "false"

    print(str(peptide_count))
    print("0")  # protein_groups: not computed in probe
    print(fdr_ok)

if __name__ == "__main__":
    main()
