import argparse, json

def parse_bool(x: str) -> bool:
    return x.lower() in ("1", "true", "yes", "y")

p = argparse.ArgumentParser()
p.add_argument("--tool-id", required=True)
p.add_argument("--modality", required=True, choices=["DDA","DIA"])
p.add_argument("--preset", required=False, default="")
p.add_argument("--walltime-sec", type=float, required=True)
p.add_argument("--max-rss-gb", type=float, required=True)
p.add_argument("--exit-code", type=int, required=True)
p.add_argument("--peptides", type=int, required=True)
p.add_argument("--protein-groups", type=int, required=True)
p.add_argument("--fdr-ok", required=True)
p.add_argument("--out", required=True)
args = p.parse_args()

obj = {
  "tool_id": args.tool_id,
  "modality": args.modality,
  "resources": {
    "walltime_sec": args.walltime_sec,
    "max_rss_gb": args.max_rss_gb,
    "exit_code": args.exit_code
  },
  "ids": {
    "peptides": args.peptides,
    "protein_groups": args.protein_groups
  },
  "qc": {
    "fdr_ok": parse_bool(args.fdr_ok)
  }
}

with open(args.out, "w") as f:
    json.dump(obj, f, indent=2)
