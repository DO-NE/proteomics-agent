#!/usr/bin/env bash
set -euo pipefail

: "${TOOL_ID:?}"
: "${MODALITY:?}"
: "${PRESET:?}"
: "${MZML:?}"
: "${FASTA:?}"

WORKDIR="${WORKDIR:-$(pwd)/workdir}"
mkdir -p "${WORKDIR}/msfragger" "${WORKDIR}/philosopher"

echo "[DDA MSFragger wrapper]"
echo "WORKDIR=${WORKDIR}"
echo "MZML=${MZML}"
echo "FASTA=${FASTA}"
echo "PRESET=${PRESET}"

APPTAINER_IMAGE="${APPTAINER_IMAGE:-}"

# -----------------------------
# Run MSFragger (probe-minimal)
# -----------------------------
MZML_ABS="$(realpath "${MZML}")"
FASTA_ABS="$(realpath "${FASTA}")"

mkdir -p "${WORKDIR}/msfragger"

pushd "${WORKDIR}/msfragger" >/dev/null

if [[ -n "${APPTAINER_IMAGE}" ]]; then
  echo "[MODE] apptainer"
  apptainer exec "${APPTAINER_IMAGE}" \
    java -Xmx8G -jar /opt/msfragger/MSFragger.jar \
    "${MZML_ABS}" \
    --database_name "${FASTA_ABS}"
else
  echo "[MODE] local"
  : "${MSFRAGGER_JAR:?Set MSFRAGGER_JAR or APPTAINER_IMAGE}"
  JAVA_BIN="${JAVA_BIN:-java}"
  "${JAVA_BIN}" -Xmx8G -jar "${MSFRAGGER_JAR}" \
    "${MZML_ABS}" \
    --database_name "${FASTA_ABS}"
fi

popd >/dev/null

# -----------------------------
# Collect outputs into WORKDIR
# -----------------------------
MZML_ABS="$(realpath "${MZML}")"
IN_DIR="$(dirname "${MZML_ABS}")"
BASE="$(basename "${MZML_ABS}")"
STEM="${BASE%.*}"   # dda1 from dda1.mzML

echo "[COLLECT] input_dir=${IN_DIR}"
echo "[COLLECT] stem=${STEM}"

# MSFragger commonly writes alongside input spectra; move them into workdir/msfragger
mkdir -p "${WORKDIR}/msfragger"

shopt -s nullglob
for f in "${IN_DIR}/${STEM}"*.pepXML \
         "${IN_DIR}/${STEM}"*.mzBIN* \
         "${IN_DIR}/${STEM}"*.pin \
         "${IN_DIR}/${STEM}"*.tsv \
         "${IN_DIR}/${STEM}"*.txt; do
  echo "[COLLECT] moving $(basename "$f") -> ${WORKDIR}/msfragger/"
  mv -f "$f" "${WORKDIR}/msfragger/"
done
shopt -u nullglob

# -----------------------------
# Philosopher (temporarily skipped in probe)
# -----------------------------
if [[ -n "${PHILOSOPHER_BIN:-}" && -x "${PHILOSOPHER_BIN:-}" ]]; then
  echo "[INFO] Philosopher available at ${PHILOSOPHER_BIN} (skipping in probe)"
else
  echo "[INFO] Philosopher not configured or not executable (skipping in probe)"
fi

echo "[DONE] Wrapper finished"
