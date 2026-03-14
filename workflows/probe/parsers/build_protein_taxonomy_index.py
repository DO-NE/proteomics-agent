import argparse
import re
from pathlib import Path


def parse_header(header):

    accession = None
    species = None
    taxid = None

    # accession
    parts = header.split("|")
    if len(parts) >= 2:
        accession = parts[1]

    # species
    m = re.search(r"OS=([^=]+?) OX=", header)
    if m:
        species = m.group(1).strip()

    # taxid
    m = re.search(r"OX=(\d+)", header)
    if m:
        taxid = m.group(1)

    return accession, taxid, species


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    fasta = Path(args.fasta)
    out = Path(args.out)

    with open(fasta) as f, open(out, "w") as o:

        o.write("accession\ttaxid\tspecies\n")

        for line in f:

            if not line.startswith(">"):
                continue

            header = line[1:].strip()

            acc, taxid, species = parse_header(header)

            if acc and taxid and species:
                o.write(f"{acc}\t{taxid}\t{species}\n")


if __name__ == "__main__":
    main()
