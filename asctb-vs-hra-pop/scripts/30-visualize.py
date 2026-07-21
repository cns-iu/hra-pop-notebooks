from shared import *


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
SUMMARY_FILE = OUTPUT_DIR / "as_ct_overlap_by_organ.csv"
PLOT_FILE = OUTPUT_DIR / "as_ct_overlap_by_organ_grouped.png"
PLOT_RC_PARAMS = {
    "figure.dpi": 120,
    "savefig.dpi": 200,
    "axes.titlesize": 20,
    "axes.labelsize": 17,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 15,
    "legend.title_fontsize": 15,
    "axes.grid": True,
    "grid.alpha": 0.25,
}


def load_processed_data():
    df_asctb = load_json_as_df(load_list_cell_types(CACHE_FILE_ASCTB))
    df_hra_pop = load_json_as_df(load_list_cell_types(CACHE_FILE_HRA_POP))
    df_concat = pd.concat([df_asctb, df_hra_pop], ignore_index=True)

    if "source" not in df_concat.columns:
        df_concat["source"] = "unknown"
    else:
        df_concat["source"] = df_concat["source"].fillna("unknown")

    # Build a unique AS-CT key to count distinct combinations per organ/source.
    df_concat["as_ct_combo"] = (
        df_concat["as_id"].astype(str) + "||" + df_concat["cell_type_id"].astype(str)
    )

    return df_concat


def summarize_as_ct_overlap_by_organ(data: pd.DataFrame) -> pd.DataFrame:
    df = data.dropna(subset=["organ", "as_id", "cell_type_id", "source"]).copy()
    df["source"] = df["source"].str.lower().str.strip()

    rows = []
    for organ in sorted(df["organ"].dropna().unique()):
        organ_df = df[df["organ"] == organ]

        asctb_set = set(organ_df.loc[organ_df["source"] == "asctb", "as_ct_combo"])
        hra_pop_set = set(
            organ_df.loc[organ_df["source"].isin(["hra_pop", "hrapop"]), "as_ct_combo"]
        )

        rows.append(
            {
                "organ": organ,
                "overlap_type": "only_hra_pop",
                "as_ct_count": len(hra_pop_set - asctb_set),
            }
        )
        rows.append(
            {
                "organ": organ,
                "overlap_type": "only_asctb",
                "as_ct_count": len(asctb_set - hra_pop_set),
            }
        )
        rows.append(
            {
                "organ": organ,
                "overlap_type": "both",
                "as_ct_count": len(asctb_set & hra_pop_set),
            }
        )

    return pd.DataFrame(rows)


def apply_plot_rc_params() -> None:
    plt.rcParams.update(PLOT_RC_PARAMS)


def visualize(summary: pd.DataFrame) -> None:
    if summary.empty:
        print("No data available to visualize.")
        return

    apply_plot_rc_params()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_FILE, index=False)

    plt.figure(figsize=(max(12, len(summary["organ"].unique()) * 0.8), 7))
    ax = sns.barplot(
        data=summary,
        x="organ",
        y="as_ct_count",
        hue="overlap_type",
        order=sorted(summary["organ"].unique()),
        hue_order=["only_hra_pop", "only_asctb", "both"],
        palette={
            "only_hra_pop": "#F9CE8D",
            "only_asctb": "#7495AE",
            "both": "#8DC599",
        },
    )
    ax.set_xlabel("Organ")
    ax.set_ylabel("Unique AS-CT combinations")
    ax.set_title("AS-CT Overlap by Organ")
    ax.tick_params(axis="x", rotation=60)
    ax.legend(title="Overlap Type")

    for container in ax.containers:
        ax.bar_label(container, fmt="%d", fontsize=7, padding=1)

    plt.yscale("log")
    plt.tight_layout()
    plt.savefig(PLOT_FILE, bbox_inches="tight")
    plt.close()

    print(f"Saved summary: {SUMMARY_FILE}")
    print(f"Saved plot: {PLOT_FILE}")


if __name__ == "__main__":
    df_processed = load_processed_data()
    df_summary = summarize_as_ct_overlap_by_organ(df_processed)
    visualize(df_summary)
