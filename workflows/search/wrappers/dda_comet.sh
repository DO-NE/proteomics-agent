#!/usr/bin/env bash
set -euo pipefail
: "${TOOL_ID:?}"
: "${MODALITY:?}"
: "${PRESET:?}"
: "${MZML:?}"
: "${FASTA:?}"
: "${WORKDIR:?}"
: "${COMET_BIN:?Set COMET_BIN}"
WORKDIR="${WORKDIR:-$(pwd)/workdir}"
mkdir -p "${WORKDIR}/comet"
MZML_ABS="$(realpath "${MZML}")"
FASTA_ABS="$(realpath "${FASTA}")"
IN_DIR="$(dirname "${MZML_ABS}")"
BASE="$(basename "${MZML_ABS}")"
STEM="${BASE%.*}"
echo "[DDA Comet wrapper]"
echo "WORKDIR=${WORKDIR}"
echo "MZML=${MZML_ABS}"
echo "FASTA=${FASTA_ABS}"
echo "PRESET=${PRESET}"
PARAM_FILE="${WORKDIR}/comet/comet.params"
cat > "${PARAM_FILE}" <<EOF
# comet_version 2026.01 rev. 1 (e4f767c)
# Comet MS/MS search engine parameters file.
# Everything following the '#' symbol is treated as a comment.
#
database_name = ${FASTA_ABS}
decoy_search = 0                       # 0=no (default), 1=internal decoy concatenated, 2=internal decoy separate

num_threads = 4                        # 0=poll CPU to set num threads; else specify num threads directly (max 128)

#
# masses
#
peptide_mass_tolerance_upper = 20.0    # upper bound of the precursor mass tolerance
peptide_mass_tolerance_lower = -20.0   # lower bound of the precursor mass tolerance; USUALLY NEGATIVE TO BE LOWER THAN 0
peptide_mass_units = 2                 # 0=amu, 1=mmu, 2=ppm
precursor_tolerance_type = 1           # 0=MH+ (default), 1=precursor m/z; only valid for amu/mmu tolerances
isotope_error = 2                      # 0=off, 1=0/1 (C13 error), 2=0/1/2, 3=0/1/2/3, 4=-1/0/1/2/3, 5=-1/0/1

#
# search enzyme
#
search_enzyme_number = 1               # choose from list at end of this params file
search_enzyme2_number = 0              # second enzyme; set to 0 if no second enzyme
sample_enzyme_number = 1               # specifies the sample enzyme
num_enzyme_termini = 2                 # 1 (semi-digested), 2 (fully digested, default), 8 C-term unspecific , 9 N-term unspecific
allowed_missed_cleavage = 2            # maximum value is 5; for enzyme search

#
# variable modifications
#
variable_mod01 = 15.9949 M 0 3 -1 0 0 0.0
variable_mod02 = 0.0 X 0 3 -1 0 0 0.0
variable_mod03 = 0.0 X 0 3 -1 0 0 0.0
variable_mod04 = 0.0 X 0 3 -1 0 0 0.0
variable_mod05 = 0.0 X 0 3 -1 0 0 0.0
max_variable_mods_in_peptide = 5
require_variable_mod = 0

#
# fragment ions
#
fragment_bin_tol = 0.02                # binning to use on fragment ions
fragment_bin_offset = 0.0              # offset position to start the binning (0.0 to 1.0)
theoretical_fragment_ions = 0          # 0=use flanking peaks, 1=M peak only
use_A_ions = 0
use_B_ions = 1
use_C_ions = 0
use_X_ions = 0
use_Y_ions = 1
use_Z_ions = 0
use_Z1_ions = 0
use_NL_ions = 0

#
# output
#
output_sqtfile = 0
output_txtfile = 1
output_pepxmlfile = 1
output_mzidentmlfile = 0
output_percolatorfile = 1
num_output_lines = 5

#
# mzXML/mzML/raw file parameters
#
scan_range = 0 0
precursor_charge = 0 0
override_charge = 0
ms_level = 2
activation_method = ALL

#
# misc parameters
#
digest_mass_range = 600.0 5000.0
peptide_length_range = 5 50
max_duplicate_proteins = 10
max_fragment_charge = 3
min_precursor_charge = 1
max_precursor_charge = 6
clip_nterm_methionine = 0
spectrum_batch_size = 15000
decoy_prefix = DECOY_
equal_I_and_L = 1
mass_offsets =

#
# spectral processing
#
minimum_peaks = 10
minimum_intensity = 0
remove_precursor_peak = 0
remove_precursor_tolerance = 1.5
clear_mz_range = 0.0 0.0
percentage_base_peak = 0.0

#
# static modifications
#
add_Cterm_peptide = 0.0
add_Nterm_peptide = 0.0
add_Cterm_protein = 0.0
add_Nterm_protein = 0.0

add_G_glycine = 0.0000
add_A_alanine = 0.0000
add_S_serine = 0.0000
add_P_proline = 0.0000
add_V_valine = 0.0000
add_T_threonine = 0.0000
add_C_cysteine = 57.021464
add_L_leucine = 0.0000
add_I_isoleucine = 0.0000
add_N_asparagine = 0.0000
add_D_aspartic_acid = 0.0000
add_Q_glutamine = 0.0000
add_K_lysine = 0.0000
add_E_glutamic_acid = 0.0000
add_M_methionine = 0.0000
add_H_histidine = 0.0000
add_F_phenylalanine = 0.0000
add_U_selenocysteine = 0.0000
add_R_arginine = 0.0000
add_Y_tyrosine = 0.0000
add_W_tryptophan = 0.0000
add_O_pyrrolysine = 0.0000
add_B_user_amino_acid = 0.0000
add_J_user_amino_acid = 0.0000
add_X_user_amino_acid = 0.0000
add_Z_user_amino_acid = 0.0000

#
# COMET_ENZYME_INFO _must_ be at the end of this parameters file
#
[COMET_ENZYME_INFO]
0.  Cut_everywhere         0      -           -
1.  Trypsin                1      KR          P
2.  Trypsin/P              1      KR          -
3.  Lys_C                  1      K           P
4.  Lys_N                  0      K           -
5.  Arg_C                  1      R           P
6.  Asp_N                  0      DN          -
7.  CNBr                   1      M           -
8.  Asp-N_ambic            1      DE          -
9.  PepsinA                1      FL          -
10. Chymotrypsin           1      FWYL        P
11. No_cut                 1      @           @
EOF

# Symlink the mzML into workdir so Comet writes outputs there
ln -sf "${MZML_ABS}" "${WORKDIR}/comet/${BASE}"

pushd "${WORKDIR}/comet" >/dev/null
"${COMET_BIN}" -P"${PARAM_FILE}" "${BASE}"   # pass relative filename, not absolute path
popd >/dev/null

# Collect outputs in case Comet writes beside input or in cwd
shopt -s nullglob
for f in \
  "${WORKDIR}/comet/${STEM}"*.pep.xml \
  "${WORKDIR}/comet/${STEM}"*.pepXML \
  "${WORKDIR}/comet/${STEM}"*.pin \
  "${WORKDIR}/comet/${STEM}"*.txt \
  "${IN_DIR}/${STEM}"*.pep.xml \
  "${IN_DIR}/${STEM}"*.pepXML \
  "${IN_DIR}/${STEM}"*.pin \
  "${IN_DIR}/${STEM}"*.txt
do
  if [[ -f "$f" ]]; then
    src="$(realpath "$f")"
    dst_dir="$(realpath "${WORKDIR}/comet")"
    dst="${dst_dir}/$(basename "$f")"

    if [[ "$src" != "$dst" ]]; then
      mv -f "$src" "$dst"
    fi
  fi
done
shopt -u nullglob
