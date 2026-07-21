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

The easiest way to run the workflow is with the provided setup script:

```bash
cd asctb-vs-hra-pop
python set_up_and_run.py
```

This will:
- Create a Python virtual environment (`.venv`)
- Install all required dependencies
- Run all scripts in order
- Generate outputs in the `output/` directory

## Requirements

- Python 3.8+
- Dependencies (see `requirements.txt`):
  - `requests` - For HTTP downloads
  - `pandas` - Data processing and analysis
  - `matplotlib` - Visualization library
  - `seaborn` - Enhanced matplotlib visualizations

## Input Data

### Required Files

- **data/11th Release (v2.5).csv** - ASCT+B release manifest (provided in repo)
  - Contains URLs to all ASCT+B organ-specific CSV tables
  - You can download the file at [https://humanatlas.io/asctb-tables#summary-statistics](https://humanatlas.io/asctb-tables#summary-statistics)

### External Data Sources

The pipeline downloads data from:
- **ASCT+B**: `https://purl.humanatlas.io/asct-b/{organ}`
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