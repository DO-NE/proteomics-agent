import json
from pathlib import Path
from orchestrator.selector import select_toolchain

def read_json(p: Path):
    with p.open() as f:
        return json.load(f)

def main():
    profile = read_json(Path("profiles/dataset_profile.probe.json"))

    dda = read_json(Path("results/probe_local/DDA/dda_msfragger_philosopher/probe_metrics.json"))
    dia = read_json(Path("results/probe_local/DIA/dia_diann/probe_metrics.json"))

    # modality별로 따로 선택 (현 구조에 맞게)
    dda_choice = select_toolchain(profile, [dda])
    dia_choice = select_toolchain(profile, [dia])

    out = {
        "DDA": dda_choice,
        "DIA": dia_choice
    }

    Path("results/probe_local/chosen_toolchain.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
