"""Generate QC summaries and visualizations for HRApop datasets.

The script:
1. Ensures the QC report CSV is decompressed.
2. Loads atlas metadata from the HRApop repository.
3. Prints grouped QC summary statistics by handler (= portal/source).
4. Creates and saves faceted scatter plots and a handler-level jitter plot.
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
import numpy


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
    """Build and persist per-handler threshold coverage counts.

    The output table contains one row per `(handler, metric)` combination and
    is written to `output/qc_summary_table.csv`.

    Args:
        df: QC DataFrame containing per-dataset metrics and a `handler` column.
        threshold: Dictionary with nested `ribo` and `mito` min/max thresholds.
    """

    def count_datasets(group_df: pd.DataFrame, mask: pd.Series) -> int:
        """Count unique datasets in a grouped frame that satisfy a boolean mask.

        Args:
            group_df: Handler-specific slice of the QC DataFrame.
            mask: Boolean mask aligned to `group_df.index`.

        Returns:
            Number of unique `dataset_id` values in rows where mask is True.
        """
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


def compute_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Compute and save a Pearson correlation matrix for QC metrics.

    Args:
        df: QC DataFrame containing numeric QC metrics.

    Returns:
        Correlation matrix DataFrame for the configured QC columns.
    """
    correlation_columns = [
        "percent_low_quality",
        "mean_pct_counts_ribo",
        "mean_pct_counts_mt",
        "mean_n_genes_by_counts",
        "mean_total_counts",
        "mean_pct_counts_in_top_20_genes",
        "mean_pct_counts_in_top_50_genes",
    ]

    missing_columns = [column for column in correlation_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns for correlation matrix: {missing_columns}"
        )

    correlation_matrix = df[correlation_columns].corr(method="pearson")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "qc_correlation_matrix.csv"
    correlation_matrix.to_csv(output_path)

    print("Correlation matrix:")
    print(correlation_matrix.to_string())
    print(f"Saved correlation matrix to {output_path}")

    return correlation_matrix


def enrich_summary_with_atlas_info(
    df: pd.DataFrame, atlas_metadata: pd.DataFrame
) -> pd.DataFrame:
    """Add atlas membership labels to the QC summary rows.

    Args:
        df: QC DataFrame with `dataset_id` values.
        atlas_metadata: DataFrame with atlas flags keyed by `dataset_id`.

    Returns:
        QC DataFrame enriched with `is_atlas_dataset` and `atlas_label` columns.
    """
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
    x_label: str,
    y_label: str,
    x_scale: str,
    y_scale: str,
    *,
    x_lim: tuple[float, float],
    y_lim: tuple[float, float],
    x_column: str = DEFAULT_X_COLUMN,
    y_column: str = DEFAULT_Y_COLUMN,
    show_ablines=False,
    x_ablines: list[tuple[str, str] | str] | None = None,
    y_ablines: list[tuple[str, str] | str] | None = None,
) -> None:
    """Create and save a faceted scatter plot by handler.

    Points are color/shape/size encoded by atlas status. Optional threshold
    lines are drawn for axes that map to configured ribo/mito threshold keys.

    Args:
        df: QC report DataFrame.
        name: Output file stem (PNG written to the output directory).
        x_label: Required label for the x-axis.
        y_label: Required label for the y-axis.
        x_scale: Required Matplotlib scale for the x-axis.
        y_scale: Required Matplotlib scale for the y-axis.
        x_lim: Required x-axis limits `(min, max)`.
        y_lim: Required y-axis limits `(min, max)`.
        x_column: Column to plot on the x-axis.
        y_column: Column to plot on the y-axis.
        show_ablines: Whether to draw threshold guide lines for known metrics.
        x_ablines: Optional list of vertical-line specs. Each spec can be either
            a threshold key string (for example `"low_quality"`, which expands to
            both min and max) or an explicit `(threshold_key, bound)` tuple.
        y_ablines: Optional list of horizontal-line specs. Uses the same format
            as `x_ablines`.
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

    if not x_label.strip() or not y_label.strip():
        raise ValueError("x_label and y_label are required and cannot be empty.")

    if not x_scale.strip() or not y_scale.strip():
        raise ValueError("x_scale and y_scale are required and cannot be empty.")

    if x_lim[0] >= x_lim[1] or y_lim[0] >= y_lim[1]:
        raise ValueError("x_lim and y_lim must be (min, max) with min < max.")

    x_threshold_key = THRESHOLD_COLUMN_MAP.get(x_column)
    y_threshold_key = THRESHOLD_COLUMN_MAP.get(y_column)

    def resolve_ablines(
        abline_specs: list[tuple[str, str] | str] | None,
        default_threshold_key: str | None,
    ) -> list[tuple[str, str]]:
        """Normalize ab-line specs into explicit `(threshold_key, bound)` tuples."""
        if abline_specs is None:
            if default_threshold_key is None:
                return []
            return [(default_threshold_key, "min"), (default_threshold_key, "max")]

        resolved_specs: list[tuple[str, str]] = []
        available_keys = list(thresholds.keys())
        valid_bounds = {"min", "max"}

        for spec in abline_specs:
            if isinstance(spec, str):
                threshold_key = spec
                if threshold_key not in thresholds:
                    raise ValueError(
                        f"Unknown threshold key '{threshold_key}'. Available: {available_keys}"
                    )
                for bound in ("min", "max"):
                    if bound in thresholds[threshold_key]:
                        resolved_specs.append((threshold_key, bound))
                continue

            threshold_key, bound = spec
            if threshold_key not in thresholds:
                raise ValueError(
                    f"Unknown threshold key '{threshold_key}'. Available: {available_keys}"
                )
            if bound not in valid_bounds:
                raise ValueError(
                    f"Unknown threshold bound '{bound}'. Use one of: {sorted(valid_bounds)}"
                )
            if bound not in thresholds[threshold_key]:
                raise ValueError(
                    f"Threshold key '{threshold_key}' does not define bound '{bound}'."
                )

            resolved_specs.append((threshold_key, bound))

        return resolved_specs

    x_abline_specs = resolve_ablines(x_ablines, x_threshold_key)
    y_abline_specs = resolve_ablines(y_ablines, y_threshold_key)

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
            for threshold_key, bound in x_abline_specs:
                ax.axvline(
                    thresholds[threshold_key][bound],
                    color="red",
                    linestyle="--",
                    linewidth=1.5,
                )
            for threshold_key, bound in y_abline_specs:
                ax.axhline(
                    thresholds[threshold_key][bound],
                    color="blue",
                    linestyle="--",
                    linewidth=1.5,
                )

        ax.set_xscale(x_scale)
        ax.set_yscale(y_scale)
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved plot to {output_path}")


def make_jitter_plot(df: pd.DataFrame, name: str) -> None:
    """Create and save a dataset-level jitter plot of low-quality percentages.

    Args:
        df: QC report DataFrame with `handler`, `percent_low_quality`, and
            `atlas_label` columns.
        name: Output file stem (PNG written to the output directory).
    """
    required_columns = ["handler", "percent_low_quality", "atlas_label"]
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Missing required columns for jitter graph: {missing_columns}"
        )

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
    """Run the end-to-end HRApop QC reporting workflow.

    The workflow loads QC data, enriches rows with atlas metadata, computes
    grouped summary statistics, writes threshold coverage summaries, and saves
    scatter and jitter visualizations under the output directory.
    """
    print("")
    print("")
    print("")
    print("=" * 100)
    atlas_metadata = load_hra_pop_data()
    df = load_qc_data()
    merged_df = enrich_summary_with_atlas_info(df, atlas_metadata)
    aggregate_by_handler(merged_df)
    make_summary_table(merged_df, load_qc_thresholds())
    make_scatter_graph(
        merged_df,
        name="qc_scatter_by_handler",
        x_label="Mean % counts ribo",
        y_label="Mean % counts mt",
        x_scale="log",
        y_scale="log",
        x_lim=(0.0, 100.0),
        y_lim=(0.0, 100.0),
        show_ablines=True,
    )
    make_scatter_graph(
        merged_df,
        name="qc_scatter_mito_vs_percentage_low_quality",
        x_column="mean_pct_counts_mt",
        y_column="percent_low_quality",
        x_label="Mean % counts mt",
        y_label="Percent low quality",
        x_scale="log",
        y_scale="linear",
        x_lim=(0.0, 100.0),
        y_lim=(0.0, 100.0),
        x_ablines=[("mito", "min"), ("mito", "max")],
        y_ablines=[("low_quality", "min"), ("low_quality", "max")],
        show_ablines=True,
    )
    make_jitter_plot(merged_df, name="qc_jitter_by_handler_quality")
    compute_correlation(merged_df)
    total_datasets_overall = int(merged_df["dataset_id"].nunique())
    print(f"Total datasets overall: {total_datasets_overall}")
    print("=" * 100)
    print("")
    print("")
    print("")


if __name__ == "__main__":
    main()
