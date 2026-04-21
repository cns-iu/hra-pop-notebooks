"""Generate QC summaries and faceted scatter plots for HRA-POP datasets.

The script:
1. Ensures the QC report CSV is decompressed.
2. Loads atlas metadata from the HRA-POP repository.
3. Prints grouped QC summary statistics by handler.
4. Creates and saves a faceted ribo-vs-mito scatter plot with threshold lines.
"""

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
SANKEY_URL = (
    'https://raw.githubusercontent.com/x-atlas-consortia/hra-pop/refs/heads/main/'
    'output-data/v1.0/reports/universe-ad-hoc/sankey.csv'
)

ATLAS_LABEL = "Atlas dataset in HRApop v1.0"
NON_ATLAS_LABEL = 'Non-atlas dataset in HRApop v1.0'
ATLAS_ORDER = [NON_ATLAS_LABEL, ATLAS_LABEL]

CUSTOM_PALETTE = {
    ATLAS_LABEL: '#ff0043',
    NON_ATLAS_LABEL: '#201e3d',
}
MARKER_MAP = {
    ATLAS_LABEL: 'X',
    NON_ATLAS_LABEL: 'o',
}
SIZE_MAP = {
    NON_ATLAS_LABEL: 12,
    ATLAS_LABEL: 28,
}


def gunzip_if_needed(gz_path: Path) -> Path:
    """Decompress a gzipped file if needed.

    Args:
        gz_path: Path to the .gz file.

    Returns:
        Path to the decompressed file.
    """
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
    """Load the QC report into a DataFrame.

    Returns:
        QC report rows loaded from the decompressed CSV.
    """
    csv_path = gunzip_if_needed(QC_REPORT_GZ_PATH)
    return pd.read_csv(csv_path)


def load_hra_pop_data() -> pd.DataFrame:
    """Load atlas metadata used to tag QC rows.

    Returns:
        DataFrame with dataset_id and is_atlas_dataset flag for atlas datasets.
    """
    sankey = pd.read_csv(SANKEY_URL)

    result = (
        sankey[['unique_dataset_id', 'portal', 'is_atlas_dataset']]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    result = result[result['is_atlas_dataset'] == True]
    result = result.rename(columns={'unique_dataset_id': 'dataset_id'})
    return result


def load_qc_thresholds() -> dict:
    """Load threshold values used for QC overlays.

    Returns:
        Parsed threshold configuration dictionary.
    """
    with open(QC_THRESHOLDS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def compile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute grouped summary statistics by handler.

    Args:
        df: QC report DataFrame.

    Returns:
        Aggregated DataFrame with per-handler summary metrics.
    """
    summary_table = (
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

    pprint(summary_table)
    return summary_table


def make_visualization(df: pd.DataFrame, atlas_metadata: pd.DataFrame) -> None:
    """Create and save a faceted ribo-vs-mito scatter plot.

    Points are color/shape/size encoded by atlas status and overlaid with
    configured ribo/mito threshold lines.

    Args:
        df: QC report DataFrame.
        atlas_metadata: DataFrame containing dataset_id atlas flags.
    """
    thresholds = load_qc_thresholds()

    merged_df = pd.merge(df, atlas_metadata, on='dataset_id', how='left')
    merged_df['is_atlas_dataset'] = merged_df['is_atlas_dataset'].fillna(False)
    merged_df['atlas_label'] = merged_df['is_atlas_dataset'].map(
        {
            True: ATLAS_LABEL,
            False: NON_ATLAS_LABEL,
        }
    )

    print(merged_df.head())

    mpl.rcParams['figure.figsize'] = (7, 6)

    merged_df = merged_df.copy()
    merged_df['is_in_mito_range'] = merged_df['mean_pct_counts_mt'].between(
        thresholds['mito']['min'],
        thresholds['mito']['max'],
        inclusive='both',
    )

    print('+' * 28)
    print(merged_df['is_in_mito_range'].sum())
    print('+' * 28)

    mito_summary = merged_df.groupby('handler')['is_in_mito_range'].agg(
        true_count='sum',
        total='count',
    )
    mito_summary['pct_true'] = mito_summary['true_count'] / mito_summary['total']
    print(mito_summary)

    g = sns.FacetGrid(
        merged_df,
        col='handler',
        col_wrap=2,
        sharex=True,
        sharey=True,
        height=4,
        hue='atlas_label',
        hue_order=ATLAS_ORDER,
        palette=CUSTOM_PALETTE,
    )

    g.map_dataframe(
        sns.scatterplot,
        x='mean_pct_counts_ribo',
        y='mean_pct_counts_mt',
        style='atlas_label',
        style_order=ATLAS_ORDER,
        markers=MARKER_MAP,
        size='atlas_label',
        size_order=ATLAS_ORDER,
        sizes=SIZE_MAP,
        alpha=0.5,
        legend=False,
    )

    # remove per-axes legends (they repeat)
    for ax in g.axes.flatten():
        if ax.get_legend() is not None:
            ax.get_legend().remove()

    g.add_legend(title='Dataset type', loc='upper right', bbox_to_anchor=(.85, .83))

    # Add threshold lines and axis formatting to each facet.
    for ax in g.axes.flatten():
        for value in (thresholds['ribo']['min'], thresholds['ribo']['max']):
            ax.axvline(value, color='red', linestyle='--', linewidth=1.5)
        for value in (thresholds['mito']['min'], thresholds['mito']['max']):
            ax.axhline(value, color='blue', linestyle='--', linewidth=1.5)

        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel('Mean % counts ribo')
        ax.set_ylabel('Mean % counts mt')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / 'qc_scatter_by_handler.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved plot to {output_path}")


def main() -> None:
    """Run end-to-end QC summary generation and plotting."""
    print("")
    print("")
    print("")
    print('=' * 100)
    atlas_metadata = load_hra_pop_data()
    df = load_qc_data()
    print(df.columns)
    compile_stats(df)
    make_visualization(df, atlas_metadata)
    print('=' * 100)
    print("")
    print("")
    print("")


if __name__ == '__main__':
    main()
