# Proteomics Agent

A modular, agent-ready proteomics workflow for running proteomics search pipelines, converting raw search outputs into structured intermediate tables, mapping identified proteins to taxonomy, and estimating species-level composition from mass spectrometry data.

At its current stage, the system provides a **baseline DDA pipeline** built around **MSFragger**. It accepts **mzML** and **FASTA** inputs, performs peptide identification, aggregates protein-level evidence, links proteins to taxonomy metadata, and generates a preliminary **species composition table**. The workflow is designed to be extensible so that additional search engines and downstream inference modules can later be integrated into the same framework.

---

## What the system currently supports

The current implementation supports the following:

- input of tandem mass spectrometry data in **mzML** format
- input of a protein sequence database in **FASTA** format
- baseline **DDA** search pipeline using **MSFragger**
- generation of structured outputs at multiple stages:
  - peptide-level hits
  - protein-level support
  - protein-to-taxonomy mapping
  - species composition estimation
- a modular execution framework based on:
  - Snakemake orchestration
  - tool registry
  - wrapper scripts
  - parser scripts

At present, the repository is focused on a **baseline DDA workflow**. The downstream taxonomic composition estimation is currently implemented as a simple baseline aggregation method.

---

## Pipeline overview

The main biological pipeline is:

```text
mzML
→ search engine
→ peptide hits
→ protein support
→ protein-taxonomy mapping
→ species composition
```

The execution framework around this pipeline is:

```text
Snakemake
→ dispatch tool
→ wrapper
→ parser
→ standardized outputs
```

This separation allows the system to remain modular. The workflow manager does not directly encode tool-specific behaviour. Instead, each tool can be integrated through a wrapper and parser while using a common execution pattern.

---

## Repository structure

The most important folders and files are listed below.

```text
.
├── data/
│   ├── db/
│   └── probe/
├── orchestrator/
│   ├── run_selector.py
│   └── selector.py
├── registry/
│   └── tool_registry.yaml
├── results/
├── workflows/
│   └── probe/
│       ├── Snakefile
│       ├── config/
│       │   └── probe.yaml
│       ├── parsers/
│       ├── scripts/
│       └── wrappers/
├── requirements-workflow.txt
└── README.md
```

### Important components

- **`workflows/probe/Snakefile`**
  Defines the Snakemake workflow for running tool candidates and generating probe outputs.

- **`workflows/probe/config/probe.yaml`**
  Main configuration file for a run. This is where users specify the input mzML, FASTA, and tool environment paths.

- **`registry/tool_registry.yaml`**
  Registry that maps each tool ID to its corresponding wrapper and parser.

- **`workflows/probe/wrappers/`**
  Contains tool-specific execution scripts.

- **`workflows/probe/parsers/`**
  Contains scripts that parse search outputs and generate structured tables.

- **`results/`**
  Stores all outputs. Each run is written into its own subdirectory using the configured `run_id`.

---

## Prerequisites

The baseline workflow currently assumes the following:

- Linux-based environment
- Python 3
- conda environment or equivalent Python environment
- Java installed and available on the command line
- Snakemake installed
- MSFragger downloaded locally
- optional: Philosopher downloaded locally

### Required software

- **Python**
- **Snakemake**
- **Java** (required for MSFragger)
- **MSFragger** jar file

### Optional software

- **Philosopher**
  Currently optional in the baseline probe workflow. The present implementation can run without fully using Philosopher downstream.

---

## Installation and setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd proteomics-agent
```

### 2. Create and activate an environment

Example using conda:

```bash
conda create -n proteomics-agent python=3.10 -y
conda activate proteomics-agent
```

### 3. Install workflow dependencies

```bash
python -m pip install --no-user --upgrade --force-reinstall -r requirements-workflow.txt
```

### 4. Verify Snakemake

```bash
python -m snakemake --version
```

### 5. Verify Java

```bash
java -version
```

### 6. Download MSFragger

Download MSFragger from the official MSFragger release source and place it somewhere accessible, for example:

```text
/home/<username>/tools/msfragger/MSFragger-4.4.1/MSFragger-4.4.1.jar
```

### 7. Optional: Download Philosopher

If Philosopher is available locally, place the binary somewhere accessible, for example:

```text
/home/<username>/tools/philosopher/bin/philosopher
```

### 8. Verify file paths

Before running the workflow, make sure you know the correct paths to:

- the mzML input file
- the FASTA file
- the MSFragger jar
- the Philosopher binary, if used

---

## Input data requirements

The workflow requires two main biological inputs.

### 1. mzML file

An **mzML** file is the mass spectrometry data file that contains the observed spectra.

Example:

```text
/mnt/data3/PXD028735/LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01.mzML
```

### 2. FASTA file

A **FASTA** file is the protein sequence database used for search.

Example:

```text
/mnt/data3/PXD028735/PXD028735.fasta
```

### FASTA header requirement

For taxonomy mapping, the FASTA headers should include taxonomy metadata. The baseline taxonomy parser currently expects headers containing fields such as:

- `OS=` for organism species
- `OX=` for taxonomy ID

Example FASTA header:

```text
>sp|P00350|6PGD_ECOLI 6-phosphogluconate dehydrogenase OS=Escherichia coli (strain K12) OX=83333 GN=gnd PE=1 SV=2
```

Without organism metadata in the FASTA header, the taxonomy indexing step will not work correctly.

---

## Configuration guide

The main configuration file is:

```text
workflows/probe/config/probe.yaml
```

A typical example looks like this:

```yaml
run_id: "pxd028735_alpha01"

inputs:
  dda_mzml: "/mnt/data3/PXD028735/LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01.mzML"

fasta: "/mnt/data3/PXD028735/PXD028735.fasta"

candidates:
  DDA:
    - tool_id: "dda_msfragger_philosopher"
      preset: "dda_tryptic_lfq_default"

tool_env:
  dda_msfragger_philosopher:
    MSFRAGGER_JAR: "/home/dkwak/tools/msfragger/MSFragger-4.4.1/MSFragger-4.4.1.jar"
    PHILOSOPHER_BIN: "/home/dkwak/tools/philosopher/bin/philosopher"
    JAVA_BIN: "java"
```

### Field-by-field explanation

#### `run_id`
A unique identifier for the run.

Example:

```yaml
run_id: "pxd028735_alpha01"
```

All results will be written under:

```text
results/<run_id>/
```

This keeps different runs separate from one another.

#### `inputs.dda_mzml`
Path to the DDA mzML file.

Example:

```yaml
dda_mzml: "/mnt/data3/PXD028735/LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01.mzML"
```

#### `fasta`
Path to the FASTA database.

Example:

```yaml
fasta: "/mnt/data3/PXD028735/PXD028735.fasta"
```

#### `candidates`
Defines which tool candidates should be run.

Current baseline example:

```yaml
candidates:
  DDA:
    - tool_id: "dda_msfragger_philosopher"
      preset: "dda_tryptic_lfq_default"
```

At present, the main baseline tool is `dda_msfragger_philosopher`.

#### `tool_env`
Provides tool-specific environment paths and binaries.

Example:

```yaml
tool_env:
  dda_msfragger_philosopher:
    MSFRAGGER_JAR: "/home/dkwak/tools/msfragger/MSFragger-4.4.1/MSFragger-4.4.1.jar"
    PHILOSOPHER_BIN: "/home/dkwak/tools/philosopher/bin/philosopher"
    JAVA_BIN: "java"
```

Edit these paths to match your own environment.

---

## Quickstart

This section shows the minimal path from input files to a species composition table.

### Step 1. Edit the config file

Open:

```text
workflows/probe/config/probe.yaml
```

and set:

- `run_id`
- `inputs.dda_mzml`
- `fasta`
- `tool_env.dda_msfragger_philosopher.MSFRAGGER_JAR`

### Step 2. Run the search workflow

```bash
python -m snakemake \
  -s workflows/probe/Snakefile \
  --configfile workflows/probe/config/probe.yaml \
  --cores 1 \
  -R run_candidate
```

This performs the baseline DDA search and generates:

- `probe_metrics.json`
- MSFragger workdir outputs
- search output files such as pepXML

### Step 3. Extract peptide hits

```bash
python workflows/probe/parsers/extract_peptide_hits.py \
  --workdir results/<run_id>/DDA/dda_msfragger_philosopher/workdir \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/peptide_hits.tsv
```

### Step 4. Build protein support

```bash
python workflows/probe/parsers/build_protein_support.py \
  --peptide-tsv results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/peptide_hits.tsv \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_support.tsv
```

### Step 5. Build the protein taxonomy index

```bash
python workflows/probe/parsers/build_protein_taxonomy_index.py \
  --fasta /path/to/database.fasta \
  --out /path/to/protein_taxonomy_index.tsv
```

### Step 6. Join proteins with taxonomy

```bash
python workflows/probe/parsers/join_protein_with_taxonomy.py \
  --protein-support results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_support.tsv \
  --taxonomy-index /path/to/protein_taxonomy_index.tsv \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_taxon_support.tsv
```

### Step 7. Estimate species abundance

```bash
python workflows/probe/parsers/estimate_taxon_abundance.py \
  --protein-taxonomy results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_taxon_support.tsv \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/taxon_composition.tsv
```

At this point, the baseline species composition table is available.

---

## Detailed usage guide

### 1. Running the search workflow

The Snakemake workflow runs the candidate tool defined in the config file. In the current baseline implementation, this means running MSFragger through a wrapper script.

Command:

```bash
python -m snakemake \
  -s workflows/probe/Snakefile \
  --configfile workflows/probe/config/probe.yaml \
  --cores 1 \
  -R run_candidate
```

What this does:

- reads the config file
- resolves the candidate tool
- calls the dispatch layer
- launches the wrapper
- runs MSFragger
- collects search outputs
- generates a `probe_metrics.json`

### 2. Extracting peptide-level hits

The pepXML output from MSFragger is transformed into a tabular peptide-hit file.

Command:

```bash
python workflows/probe/parsers/extract_peptide_hits.py \
  --workdir results/<run_id>/DDA/dda_msfragger_philosopher/workdir \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/peptide_hits.tsv
```

This produces `peptide_hits.tsv`, which stores spectrum-level best-hit information.

### 3. Aggregating protein support

The peptide-hit file is then aggregated into protein-level evidence.

Command:

```bash
python workflows/probe/parsers/build_protein_support.py \
  --peptide-tsv results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/peptide_hits.tsv \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_support.tsv
```

This produces `protein_support.tsv`.

### 4. Building a taxonomy index from the FASTA

The taxonomy index is created from the FASTA database. This step only needs to be performed once per FASTA file.

Command:

```bash
python workflows/probe/parsers/build_protein_taxonomy_index.py \
  --fasta /path/to/database.fasta \
  --out /path/to/protein_taxonomy_index.tsv
```

This produces a reusable accession-to-taxonomy lookup table.

### 5. Joining protein evidence with taxonomy

The protein support table is joined with the taxonomy index.

Command:

```bash
python workflows/probe/parsers/join_protein_with_taxonomy.py \
  --protein-support results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_support.tsv \
  --taxonomy-index /path/to/protein_taxonomy_index.tsv \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_taxon_support.tsv
```

This produces `protein_taxon_support.tsv`.

### 6. Estimating species composition

Finally, protein-level taxonomic evidence is aggregated to species-level abundance.

Command:

```bash
python workflows/probe/parsers/estimate_taxon_abundance.py \
  --protein-taxonomy results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/protein_taxon_support.tsv \
  --out results/<run_id>/DDA/dda_msfragger_philosopher/workdir/msfragger/taxon_composition.tsv
```

This produces `taxon_composition.tsv`.

---

## Output files and how to read them

### `probe_metrics.json`
Stores high-level search statistics for the run.

Typical fields:
- number of peptides identified
- runtime
- exit code
- basic QC flag

This file is intended to support future agent-based comparison of pipeline candidates.

### `peptide_hits.tsv`
Stores spectrum-level best-hit peptide information.

Typical columns:
- spectrum
- scan
- charge
- peptide
- protein
- expect

This file is useful when inspecting peptide-level identifications.

### `protein_support.tsv`
Stores protein-level evidence aggregated from peptide hits.

Typical columns:
- protein
- n_psms
- n_unique_peptides
- peptides

This file summarises how strongly each protein is supported by the data.

### `protein_taxon_support.tsv`
Stores protein-level evidence together with taxonomy metadata.

Typical columns:
- protein
- accession
- taxid
- species
- n_psms
- n_unique_peptides
- peptides

This file connects proteomics evidence with biological taxonomy.

### `taxon_composition.tsv`
Stores the baseline species composition estimate.

Typical columns:
- species
- n_proteins
- total_psms
- total_unique_peptides
- relative_abundance

This file is the final baseline output of the current workflow.
