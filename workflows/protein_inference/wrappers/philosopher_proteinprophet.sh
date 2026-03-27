#!/usr/bin/env bash
set -euo pipefail

: "${WORKDIR:?}"
: "${FASTA:?}"
: "${PHILOSOPHER_BIN:?Set PHILOSOPHER_BIN}"

WORKDIR="$(realpath "${WORKDIR}")"
FASTA_ABS="$(realpath "${FASTA}")"

SEARCH_SUBDIR="${1:?Need search subdir name, e.g. msfragger/comet}"
SEARCH_DIR="${WORKDIR}/${SEARCH_SUBDIR}"
OUT_DIR="${WORKDIR}/proteinprophet"
mkdir -p "${OUT_DIR}"
SENTINEL_NO_DATA="${OUT_DIR}/NO_PROTEINPROPHET_DATA"
rm -f "${SENTINEL_NO_DATA}"

pushd "${OUT_DIR}" >/dev/null

# Reset workspace
"${PHILOSOPHER_BIN}" workspace --clean || true
"${PHILOSOPHER_BIN}" workspace --init
"${PHILOSOPHER_BIN}" database --annotate "${FASTA_ABS}" --prefix DECOY_

# Copy only raw search pepXML in (explicitly from search dir, not any combined outputs)
shopt -s nullglob
for f in "${SEARCH_DIR}"/*.pep.xml "${SEARCH_DIR}"/*.pepXML; do
    cp "$f" .
done
shopt -u nullglob

# Collect only the copied input files — explicitly exclude anything starting with "combined" or "interact"
shopt -s nullglob
input_xmls=()
for f in ./*.pep.xml ./*.pepXML; do
    base="$(basename "$f")"
    if [[ "$base" != combined* && "$base" != interact* ]]; then
        input_xmls+=( "$f" )
    fi
done
shopt -u nullglob

if [[ ${#input_xmls[@]} -eq 0 ]]; then
    echo "ERROR: No input pepXML files found in ${SEARCH_DIR}" >&2
    exit 1
fi

# Symlink mzML so RefreshParser can find it next to the pepXML
for xml in "${input_xmls[@]}"; do
    base_name=$(grep -m1 'msms_run_summary' "$xml" | grep -oP 'base_name="\K[^"]+')
    if [[ -n "$base_name" ]]; then
        mzml_src="${base_name}.mzML"
        mzml_link="${OUT_DIR}/$(basename "${base_name}").mzML"
        if [[ -f "$mzml_src" && ! -e "$mzml_link" ]]; then
            ln -sf "$mzml_src" "$mzml_link"
        fi
    fi
done

echo "[PeptideProphet] Input files: ${input_xmls[*]}"

"${PHILOSOPHER_BIN}" peptideprophet \
    --decoy DECOY_ \
    --database "${FASTA_ABS}" \
    --output combined \
    --nonparam \
    --expectscore \
    --decoyprobs \
    "${input_xmls[@]}"

# ProteinProphet — run on the combined output from PeptideProphet only
shopt -s nullglob
combined_xmls=( ./combined*.pep.xml )
interact_xmls=( ./interact*.pep.xml )
shopt -u nullglob

if [[ ${#combined_xmls[@]} -gt 0 ]]; then
    echo "[ProteinProphet] Input: ${combined_xmls[*]}"
    if ! grep -q "peptideprophet_result" "${combined_xmls[0]}"; then
        echo "WARNING: PeptideProphet output contains no peptideprophet_result entries; skipping ProteinProphet." >&2
        touch "${SENTINEL_NO_DATA}"
    else
        "${PHILOSOPHER_BIN}" proteinprophet "${combined_xmls[@]}"
    fi
elif [[ ${#interact_xmls[@]} -gt 0 ]]; then
    echo "[ProteinProphet] Input: ${interact_xmls[*]}"
    if ! grep -q "peptideprophet_result" "${interact_xmls[0]}"; then
        echo "WARNING: PeptideProphet output contains no peptideprophet_result entries; skipping ProteinProphet." >&2
        touch "${SENTINEL_NO_DATA}"
    else
        "${PHILOSOPHER_BIN}" proteinprophet "${interact_xmls[@]}"
    fi
else
    echo "ERROR: No combined/interact pepXML found after PeptideProphet" >&2
    exit 1
fi

# Filter and report (skip if ProteinProphet was intentionally skipped for empty input)
if [[ ! -f "${SENTINEL_NO_DATA}" ]]; then
    "${PHILOSOPHER_BIN}" filter --psm 0.01 --pep 0.01 --prt 0.01 || true
    "${PHILOSOPHER_BIN}" report || true
fi

popd >/dev/null

echo "[DONE] Philosopher/ProteinProphet finished"
