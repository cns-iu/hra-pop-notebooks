import gzip
import json
import shutil
from pathlib import Path
from pprint import pprint

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


DATA_DIR = Path('data')
OUTPUT_DIR = Path('output')
QC_THRESHOLDS_PATH = DATA_DIR / 'qc_thresholds.json'
QC_REPORT_GZ_PATH = DATA_DIR / 'hra-pop-v1.1-qc-report.csv.gz'
QC_REPORT_CSV_PATH = DATA_DIR / 'hra-pop-v1.1-qc-report.csv'


def gunzip_if_needed(gz_path: Path) -> Path:
    """Decompress a .gz file if needed and return the extracted path."""
    gz_path = Path(gz_path)
    output_path = gz_path.with_suffix('')

    if output_path.exists():
        print(f'Already unzipped, skipping: {output_path}')
        return output_path

    print(f'Decompressing {gz_path} ...')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(gz_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    print(f'File extracted to: {output_path}')
    return output_path


def load_qc_data() -> pd.DataFrame:
    """Load the QC report CSV, decompressing it first if needed."""
    csv_path = gunzip_if_needed(QC_REPORT_GZ_PATH)
    return pd.read_csv(csv_path)


def load_qc_thresholds() -> dict:
    """Load QC threshold configuration."""
    with open(QC_THRESHOLDS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def compile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute grouped summary statistics by handler."""
    qc_table_merged = (
        df.groupby('handler')
        .agg(
            {
                'percent_low_quality': ['mean', 'median', 'std'],
                'mean_pct_counts_ribo': ['mean', 'median', 'std'],
                'mean_pct_counts_mt': ['mean', 'median', 'std'],
                'mean_n_genes_by_counts': ['mean'],
                'mean_total_counts': ['mean'],
                'mean_pct_counts_in_top_20_genes': ['mean'],
                'mean_pct_counts_in_top_50_genes': ['mean'],
            }
        )
        .reset_index()
    )

    pprint(qc_table_merged)
    return qc_table_merged


def make_visualization(df: pd.DataFrame) -> None:
    """Create and save a scatter plot for ribo vs mito percentages."""
    thresholds = load_qc_thresholds()

    print(df.head())

    mpl.rcParams["figure.figsize"] = (7, 6)

    df = df.copy()
    df["is_in_mito_range"] = df["mean_pct_counts_mt"].between(
        thresholds["mito"]["min"],
        thresholds["mito"]["max"],
        inclusive="both",
    )

    print("+" * 28)
    print(df["is_in_mito_range"].sum())
    print("+" * 28)

    summary = df.groupby("handler")["is_in_mito_range"].agg(
        true_count="sum",
        total="count",
    )
    summary["pct_true"] = summary["true_count"] / summary["total"]
    print(summary)

    g = sns.FacetGrid(
        df,
        col='handler',
        col_wrap=2,
        sharex=True,
        sharey=True,
        height=4,
        hue='handler',
        palette='tab10',
    )

    g.map_dataframe(
        sns.scatterplot,
        x='mean_pct_counts_ribo',
        y='mean_pct_counts_mt',
        s=5,
        alpha=0.5,
    )

    # remove per-axes legends (they repeat)
    for ax in g.axes.flatten():
        if ax.get_legend() is not None:
            ax.get_legend().remove()

    # add threshold lines + formatting
    for ax in g.axes.flatten():
        ax.axvline(
            thresholds['ribo']['min'],
            color='red',
            linestyle='--',
            linewidth=1.5,
        )
        ax.axvline(
            thresholds['ribo']['max'],
            color='red',
            linestyle='--',
            linewidth=1.5,
        )
        ax.axhline(
            thresholds['mito']['min'],
            color='blue',
            linestyle='--',
            linewidth=1.5,
        )
        ax.axhline(
            thresholds['mito']['max'],
            color='blue',
            linestyle='--',
            linewidth=1.5,
        )

        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel('Mean % counts ribo')
        ax.set_ylabel('Mean % counts mt')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "qc_scatter_by_handler.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved plot to {output_path}")


def main() -> None:
    df = load_qc_data()
    compile_stats(df)
    make_visualization(df)


if __name__ == '__main__':
    main()
