#!/usr/bin/env bash
set -euo pipefail

: "${TOOL_ID:?}"
: "${MODALITY:?}"
: "${PRESET:?}"
: "${MZML:?}"
: "${FASTA:?}"
: "${WORKDIR:?}"
: "${MSGFPLUS_JAR:?Set MSGFPLUS_JAR}"
: "${JAVA_BIN:=java}"

WORKDIR="${WORKDIR:-$(pwd)/workdir}"
mkdir -p "${WORKDIR}/msgfplus"

MZML_ABS="$(realpath "${MZML}")"
FASTA_ABS="$(realpath "${FASTA}")"
BASE="$(basename "${MZML_ABS}")"
STEM="${BASE%.*}"

echo "[DDA MSGF+ wrapper]"
echo "WORKDIR=${WORKDIR}"
echo "MZML=${MZML_ABS}"
echo "FASTA=${FASTA_ABS}"
echo "PRESET=${PRESET}"

OUT_MZID="${WORKDIR}/msgfplus/${STEM}.mzid"
OUT_TSV="${WORKDIR}/msgfplus/${STEM}.tsv"

"${JAVA_BIN}" -Xmx16G -jar "${MSGFPLUS_JAR}" \
  -s "${MZML_ABS}" \
  -d "${FASTA_ABS}" \
  -o "${OUT_MZID}" \
  -tda 1 \
  -t 20ppm \
  -ti -1,2 \
  -m 3 \
  -inst 1 \
  -e 1 \
  -protocol 0 \
  -ntt 2 \
  -minLength 7 \
  -maxLength 50

"${JAVA_BIN}" -Xmx4G -cp "${MSGFPLUS_JAR}" edu.ucsd.msjava.ui.MzIDToTsv \
  -i "${OUT_MZID}" \
  -o "${OUT_TSV}" \
  -showQValue 1 \
  -showDecoy 0

echo "[DONE] MSGF+ wrapper finished"
