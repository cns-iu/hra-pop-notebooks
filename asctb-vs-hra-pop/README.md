# ASCT+B vs HRApop Comparison Workflow

This Python workflow compares anatomical structures (AS) and cell types (CT) located in them between:
- **ASCT+B**: Anatomical Structure, Cell type, and Biomarker tables (canonical)
- **HRApop**: HRA Cell Type Populations v1.1 (experimental)

## Overview

The workflow performs three main steps:

1. **Download & Extract ASCT+B Data**: Fetches ASCT+B tables from the Human Reference Atlas (HRA) Knowledge Graph (KG) and extracts organ-AS-CT trios
2. **Download & Extract HRApop Data**: Fetches HRApop data and extracts the same organ-AS-CT trios but removes laterality from organ names, e.g., it changes `left kidney` -> `kidney`
3. **Visualize Overlap**: Creates a grouped bar graph with log scale on y-axis showing which AS-CT combinations by organ are unique to each source or shared between both

## Quick Start (Automated)

The easiest way to run the workflow is with the provided setup script. From `asctb-vs-hra-pop`, run:
```bash
python set_up_and_run.py
```

This will:
- Create a Python virtual environment (`.venv`) if one doesn't exist yet
- Install all required dependencies from `requirements.txt`
- Run all scripts in `scripts/` in order (`10-download-asctb-and-hra-pop.py`, `20-process-hra-pop.py`, `30-visualize.py`)
- Generate outputs in the `output/` directory

## Manual Run

To run or debug an individual script, activate the virtual environment first so `python` resolves to the project's `.venv` instead of your global Python.

From `asctb-vs-hra-pop`:
```powershell
.venv\Scripts\Activate.ps1
```
(If PowerShell blocks the script with an execution-policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once first.)

Then run the scripts in order, e.g. from `asctb-vs-hra-pop\scripts`:
```bash
python .\10-download-asctb-and-hra-pop.py
python .\20-process-hra-pop.py
python .\30-visualize.py
```

Deactivate when done with `deactivate`.

## Scripts

| Script | Description |
|--------|-------------|
| `shared.py` | Shared helpers (HTTP requests, JSON cache I/O, imports) used by all other scripts |
| `10-download-asctb-and-hra-pop.py` | Downloads ASCT+B tables and extracts organ-AS-CT trios; caches result to `data/list_cell_types_asctb.json` |
| `20-process-hra-pop.py` | Downloads the HRApop CSV, normalizes it into organ-AS-CT trios, and removes organ laterality (e.g. `left kidney` → `kidney`); caches result to `data/list_cell_types_hra_pop.json` |
| `30-visualize.py` | Loads both cached datasets, summarizes AS-CT overlap by organ, and writes the summary CSV and grouped bar plot to `output/` |

## Requirements

- Python 3.8+
- Dependencies (see `requirements.txt`):
  - `requests` - For HTTP downloads
  - `pandas` - Data processing and analysis
  - `matplotlib` - Visualization library
  - `seaborn` - Enhanced matplotlib visualizations

## Input Data

### External Data Sources

The pipeline downloads data from:
- **ASCT+B**: `https://purl.humanatlas.io/asct-b/{organ}`, one request per organ. The list of organs is discovered dynamically from the HRA collection endpoint (`https://purl.humanatlas.io/collection/hra`).
- **HRApop**: `https://raw.githubusercontent.com/x-atlas-consortia/hra-pop/refs/heads/main/output-data/v1.1/reports/atlas-ad-hoc/cell-types-in-anatomical-structurescts-per-as.csv`

Note: The scripts cache downloaded data locally to avoid re-downloading:
- `data/list_cell_types_asctb.json` - ASCT+B cache
- `data/list_cell_types_hra_pop.json` - HRApop cache

## Output Files

After running the pipeline, outputs are generated in the `output/` directory:

| File | Description |
|------|-------------|
| `as_ct_overlap_by_organ.csv` | Summary table with AS-CT overlap counts by organ and source |
| `as_ct_overlap_by_organ_grouped.png` | Grouped bar graph visualization |

### Output CSV Columns

- `organ` - Organ name
- `overlap_type` - One of: `only_asctb` (unique to ASCT+B), `only_hra_pop` (unique to HRA-POP), `both` (in both)
- `as_ct_count` - Number of unique anatomical structure-cell type combinations