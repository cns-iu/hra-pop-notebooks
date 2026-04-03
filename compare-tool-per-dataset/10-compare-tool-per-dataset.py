import subprocess
import sys
from pathlib import Path
import pandas as pd
from pprint import pprint


def install_requirements(requirements_file="requirements.txt"):
    path = Path(requirements_file)

    if not path.exists():
        print(f"Error: {requirements_file} not found.")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_file}...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(path)])
        print("Installation complete.")
    except subprocess.CalledProcessError as e:
        print("Failed to install dependencies.")
        sys.exit(e.returncode)


def load_and_parse_data():
    df = pd.read_csv("data/Datasets with RUI_location - Sheet1.csv")

    print()
    # keep only 2 cols
    df_original = df[["record_key", "annotation_method"]].rename(
        columns={
            "record_key": "unique_dataset_id",
            "annotation_method": "cell_type_annotation_tool",
        }
    )

    # Remove suffixes from dataset ID
    df_original["unique_dataset_id"] = df_original["unique_dataset_id"].apply(
        lambda id: id.split("__")[0]
    )
    print(df_original.head())

    # Load sankey
    df_sankey = pd.read_csv(
        "https://raw.githubusercontent.com/x-atlas-consortia/hra-pop/refs/heads/main/output-data/v1.0/reports/universe-ad-hoc/sankey.csv",
    ).fillna("no cell type annotation")

    df_compare = df_sankey[["unique_dataset_id", "cell_type_annotation_tool"]]

    print()
    pprint(df_compare.head())
    print()

    merged = df_original.merge(
        df_compare,
        on="unique_dataset_id",
        how="left",
        suffixes=("_original", "_compare"),
    )

    merged["match_between_original_and_compare"] = (
        merged["cell_type_annotation_tool_original"]
        == merged["cell_type_annotation_tool_compare"]
    ).map({True: "YES", False: "NO"})

    print(merged.head())

    # Identify (dataset_id, tool) pairs that have at least one YES
    yes_pairs = set(
        merged.loc[
            merged["match_between_original_and_compare"] == "YES",
            ["unique_dataset_id", "cell_type_annotation_tool_original"],
        ].itertuples(index=False, name=None)
    )

    # Filter dataframe
    result = merged[
        merged.apply(
            lambda row: (
                (
                    (
                        row["unique_dataset_id"],
                        row["cell_type_annotation_tool_original"],
                    )
                    not in yes_pairs
                )
                or (row["match_between_original_and_compare"] == "YES")
            ),
            axis=1,
        )
    ]

    # Export results
    result.to_csv("output/dataset-comparison.csv", index=False)


def main():
    install_requirements()
    load_and_parse_data()


if __name__ == "__main__":
    main()
