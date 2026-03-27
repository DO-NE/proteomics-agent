import argparse
import subprocess
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--metalp-script", required=True)
    p.add_argument("--identification", required=True)
    p.add_argument("--pro2otu", required=True)
    p.add_argument("--otu-prob", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--fdr", type=float, default=0.01)
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    raw_out = outdir / "metalp_raw.txt"
    filt_out = outdir / "metalp_filtered.txt"

    cmd = [
        "python",
        args.metalp_script,
        "-i", args.identification,
        "-o", str(raw_out),
        "-g", str(filt_out),
        "-d", args.pro2otu,
        "-f", str(args.fdr),
        "-p", args.otu_prob,
    ]

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
