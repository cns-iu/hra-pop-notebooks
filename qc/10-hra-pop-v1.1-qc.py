"""Generate QC summaries and faceted scatter plots for HRApop datasets.

The script:
1. Ensures the QC report CSV is decompressed.
2. Loads atlas metadata from the HRApop repository.
3. Prints grouped QC summary statistics by handler (= portal/source).
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


DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
QC_THRESHOLDS_PATH = DATA_DIR / "qc_thresholds.json"
QC_REPORT_GZ_PATH = DATA_DIR / "hra-pop-v1.1-qc-report.csv.gz"
SANKEY_URL = (
    "https://raw.githubusercontent.com/x-atlas-consortia/hra-pop/refs/heads/main/"
    "output-data/v1.0/reports/universe-ad-hoc/sankey.csv"
)

ATLAS_LABEL = "Atlas dataset in HRApop v1.0"
NON_ATLAS_LABEL = "Non-atlas dataset in HRApop v1.0"
ATLAS_ORDER = [NON_ATLAS_LABEL, ATLAS_LABEL]

DEFAULT_X_COLUMN = "mean_pct_counts_ribo"
DEFAULT_Y_COLUMN = "mean_pct_counts_mt"

CUSTOM_PALETTE = {
    ATLAS_LABEL: "#ff0043",
    NON_ATLAS_LABEL: "#201e3d",
}
MARKER_MAP = {
    ATLAS_LABEL: "X",
    NON_ATLAS_LABEL: "o",
}
SIZE_MAP = {
    NON_ATLAS_LABEL: 12,
    ATLAS_LABEL: 28,
}

THRESHOLD_COLUMN_MAP = {
    DEFAULT_X_COLUMN: "ribo",
    DEFAULT_Y_COLUMN: "mito",
}

AXIS_LABEL_MAP = {
    DEFAULT_X_COLUMN: "Mean % counts ribo",
    DEFAULT_Y_COLUMN: "Mean % counts mt",
}


def gunzip_if_needed(gz_path: Path) -> Path:
    """Decompress a gzipped file if needed.

    Args:
        gz_path: Path to the .gz file.

    Returns:
        Path to the decompressed file.
    """
    gz_path = Path(gz_path)
    output_path = gz_path.with_suffix("")

    if output_path.exists():
        print(f"Already unzipped, skipping: {output_path}")
        return output_path

    print(f"Decompressing {gz_path} ...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(gz_path, "rb") as f_in, open(output_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    print(f"File extracted to: {output_path}")
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
        sankey[["unique_dataset_id", "portal", "is_atlas_dataset"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    result = result[result["is_atlas_dataset"] == True]
    result = result.rename(columns={"unique_dataset_id": "dataset_id"})
    return result


def load_qc_thresholds() -> dict:
    """Load threshold values used for QC overlays.

    Returns:
        Parsed threshold configuration dictionary.
    """
    with open(QC_THRESHOLDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate_by_handler(df: pd.DataFrame) -> pd.DataFrame:
    """Compute grouped summary statistics by handler.

    Args:
        df: QC report DataFrame.

    Returns:
        Aggregated DataFrame with per-handler summary metrics.
    """
    summary_table = (
        df.groupby("handler")
        .agg(
            {
                "percent_low_quality": ["mean", "median", "std"],
                "mean_pct_counts_ribo": ["mean", "median", "std"],
                "mean_pct_counts_mt": ["mean", "median", "std"],
                "mean_n_genes_by_counts": ["mean"],
                "mean_total_counts": ["mean"],
                "mean_pct_counts_in_top_20_genes": ["mean"],
                "mean_pct_counts_in_top_50_genes": ["mean"],
            }
        )
        .reset_index()
    )

    pprint(summary_table)
    return summary_table


def make_summary_table(df: pd.DataFrame, threshold: dict) -> None:
    """Print dataset counts against the configured mito and ribo thresholds."""

    def count_datasets(group_df: pd.DataFrame, mask: pd.Series) -> int:
        matching_rows = group_df.loc[mask]
        return int(matching_rows["dataset_id"].nunique())

    summary_rows: list[dict[str, str | int]] = []

    for handler, group_df in df.groupby("handler", sort=True):
        summary_rows.extend(
            [
                {
                    "handler": str(handler),
                    "metric": "datasets_total",
                    "dataset_count": int(group_df["dataset_id"].nunique()),
                },
                {
                    "handler": str(handler),
                    "metric": "datasets_at_or_above_ribo_min",
                    "dataset_count": count_datasets(
                        group_df,
                        group_df["mean_pct_counts_ribo"] >= threshold["ribo"]["min"],
                    ),
                },
                {
                    "handler": str(handler),
                    "metric": "datasets_at_or_below_ribo_max",
                    "dataset_count": count_datasets(
                        group_df,
                        group_df["mean_pct_counts_ribo"] <= threshold["ribo"]["max"],
                    ),
                },
                {
                    "handler": str(handler),
                    "metric": "datasets_at_or_above_mito_min",
                    "dataset_count": count_datasets(
                        group_df,
                        group_df["mean_pct_counts_mt"] >= threshold["mito"]["min"],
                    ),
                },
                {
                    "handler": str(handler),
                    "metric": "datasets_at_or_below_mito_max",
                    "dataset_count": count_datasets(
                        group_df,
                        group_df["mean_pct_counts_mt"] <= threshold["mito"]["max"],
                    ),
                },
                {
                    "handler": str(handler),
                    "metric": "datasets_within_mito_range",
                    "dataset_count": count_datasets(
                        group_df,
                        group_df["mean_pct_counts_mt"].between(
                            threshold["mito"]["min"],
                            threshold["mito"]["max"],
                            inclusive="both",
                        ),
                    ),
                },
                {
                    "handler": str(handler),
                    "metric": "datasets_within_ribo_and_mito_ranges",
                    "dataset_count": count_datasets(
                        group_df,
                        group_df["mean_pct_counts_ribo"].between(
                            threshold["ribo"]["min"],
                            threshold["ribo"]["max"],
                            inclusive="both",
                        )
                        & group_df["mean_pct_counts_mt"].between(
                            threshold["mito"]["min"],
                            threshold["mito"]["max"],
                            inclusive="both",
                        ),
                    ),
                },
            ]
        )

    summary_table = pd.DataFrame(summary_rows)

    print(summary_table.to_string(index=False))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_table.to_csv(OUTPUT_DIR / "qc_summary_table.csv", index=False)
    return


def enrich_summary_with_atlas_info(
    df: pd.DataFrame, atlas_metadata: pd.DataFrame
) -> pd.DataFrame:
    merged_df = pd.merge(df, atlas_metadata, on="dataset_id", how="left")
    merged_df["is_atlas_dataset"] = merged_df["is_atlas_dataset"].fillna(False)
    merged_df["atlas_label"] = merged_df["is_atlas_dataset"].map(
        {
            True: ATLAS_LABEL,
            False: NON_ATLAS_LABEL,
        }
    )
    return merged_df


def make_scatter_graph(
    df: pd.DataFrame,
    name: str,
    x_column: str = DEFAULT_X_COLUMN,
    y_column: str = DEFAULT_Y_COLUMN,
    x_label: str | None = None,
    y_label: str | None = None,
    x_scale: str = "log",
    y_scale: str = "log",
    show_ablines=False,
) -> None:
    """Create and save a faceted ribo-vs-mito scatter plot.

    Points are color/shape/size encoded by atlas status and overlaid with
    configured ribo/mito threshold lines.

    Args:
        df: QC report DataFrame.
        x_column: Column to plot on the x-axis.
        y_column: Column to plot on the y-axis.
        x_label: Optional custom label for the x-axis.
        y_label: Optional custom label for the y-axis.
        x_scale: Matplotlib scale for the x-axis.
        y_scale: Matplotlib scale for the y-axis.
    """
    thresholds = load_qc_thresholds()

    missing_columns = [
        column
        for column in (x_column, y_column, "handler", "atlas_label")
        if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Missing required columns for visualization: {missing_columns}"
        )

    x_label = x_label or AXIS_LABEL_MAP.get(x_column, x_column)
    y_label = y_label or AXIS_LABEL_MAP.get(y_column, y_column)
    x_threshold_key = THRESHOLD_COLUMN_MAP.get(x_column)
    y_threshold_key = THRESHOLD_COLUMN_MAP.get(y_column)

    merged_df = df.copy()

    mpl.rcParams["figure.figsize"] = (7, 6)

    g = sns.FacetGrid(
        merged_df,
        col="handler",
        col_wrap=2,
        sharex=True,
        sharey=True,
        height=4,
        hue="atlas_label",
        hue_order=ATLAS_ORDER,
        palette=CUSTOM_PALETTE,
    )

    g.map_dataframe(
        sns.scatterplot,
        x=x_column,
        y=y_column,
        style="atlas_label",
        style_order=ATLAS_ORDER,
        markers=MARKER_MAP,
        size="atlas_label",
        size_order=ATLAS_ORDER,
        sizes=SIZE_MAP,
        alpha=0.5,
        legend=False,
    )

    # remove per-axes legends (they repeat)
    for ax in g.axes.flatten():
        if ax.get_legend() is not None:
            ax.get_legend().remove()

    g.add_legend(title="Dataset type", loc="upper right", bbox_to_anchor=(0.85, 0.83))

    # Add threshold lines and axis formatting to each facet.
    for ax in g.axes.flatten():
        if show_ablines:
            if x_threshold_key is not None:
                for value in (
                    thresholds[x_threshold_key]["min"],
                    thresholds[x_threshold_key]["max"],
                ):
                    ax.axvline(value, color="red", linestyle="--", linewidth=1.5)
            if y_threshold_key is not None:
                for value in (
                    thresholds[y_threshold_key]["min"],
                    thresholds[y_threshold_key]["max"],
                ):
                    ax.axhline(value, color="blue", linestyle="--", linewidth=1.5)

        ax.set_xscale(x_scale)
        ax.set_yscale(y_scale)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved plot to {output_path}")

def make_jitter_plot(df: pd.DataFrame, name: str) -> None:
    """Create and save a jitter plot of percent low quality by handler."""
    required_columns = ["handler", "percent_low_quality", "atlas_label"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for jitter graph: {missing_columns}")

    plt.figure(figsize=(11, 6))
    ax = sns.stripplot(
        data=df,
        x="handler",
        y="percent_low_quality",
        hue="atlas_label",
        order=sorted(df["handler"].dropna().unique()),
        palette=CUSTOM_PALETTE,
        dodge=True,
        jitter=0.25,
        alpha=0.45,
        size=3,
    )

    ax.set_xlabel("Handler")
    ax.set_ylabel("Percent Low Quality")
    ax.set_title("Dataset-level Percent Low Quality by Handler")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Dataset type", bbox_to_anchor=(1.02, 1), loc="upper left")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved plot to {output_path}")

def main() -> None:
    """Run end-to-end QC summary generation and plotting."""
    print("")
    print("")
    print("")
    print("=" * 100)
    atlas_metadata = load_hra_pop_data()
    df = load_qc_data()
    merged_df = enrich_summary_with_atlas_info(df, atlas_metadata)
    aggregate_by_handler(merged_df)
    make_summary_table(merged_df, load_qc_thresholds())
    make_scatter_graph(merged_df, name="qc_scatter_by_handler", show_ablines=True)
    make_jitter_plot(merged_df, name="qc_jitter_by_handler_quality")
    # make_scatter_graph(
    #     merged_df,
    #     x_column="mean_n_genes_by_counts",
    #     y_column="mean_total_counts",
    #     name="qc_mean_genes_by_counts_vs_total_counts",
    #     x_scale="log",
    #     y_scale="linear",
    #     show_ablines=False,
    # )
    print("=" * 100)
    print("")
    print("")
    print("")


if __name__ == "__main__":
    main()
