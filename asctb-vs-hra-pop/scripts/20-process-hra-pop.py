from shared import *


def purl_to_id(purl: str) -> str:
    return purl.split("/")[-1].replace("_", ":")


def download_hra_pop_and_get_organ_as_ct_trios() -> None:
    df_hra_pop = pd.read_csv(
        "https://raw.githubusercontent.com/x-atlas-consortia/hra-pop/refs/heads/main/output-data/v1.1/reports/atlas-ad-hoc/cell-types-in-anatomical-structurescts-per-as.csv"
    )

    df_hra_pop_trio = df_hra_pop.drop_duplicates(
        subset=["organ", "as", "as_label", "cell_id", "cell_label"]
    )[["organ", "as", "as_label", "cell_id", "cell_label"]]

    df_hra_pop_trio[["as", "cell_id"]] = df_hra_pop_trio[["as", "cell_id"]].map(
        purl_to_id
    )
    return df_hra_pop_trio


def extract_unique_organ_as_ct_trios_hra_pop(df: pd.DataFrame) -> list[dict]:
    required_cols = ["organ", "as", "as_label", "cell_id", "cell_label"]
    df_hra_pop_trio = df[required_cols].copy()

    df_hra_pop_trio = df_hra_pop_trio.rename(
        columns={
            "cell_label": "cell_type_label",
            "cell_id": "cell_type_id",
            "as": "as_id",
        }
    )

    df_hra_pop_trio = df_hra_pop_trio[
        ["organ", "cell_type_label", "cell_type_id", "as_id", "as_label"]
    ].drop_duplicates()

    df_hra_pop_trio["source"] = "hra_pop"

    # remove lateriality
    df_hra_pop_trio["organ"] = df_hra_pop_trio["organ"].replace(
        {
            "Left kidney": "kidney",
            "Left ureter": "ureter",
            "Left knee": "knee",
            "Left mammary gland": "mammary gland",
            "Left ovary": "ovary",
            "Right kidney": "kidney",
            "Right ureter": "ureter",
            "Right knee": "knee",
            "Right mammary gland": "mammary gland",
            "Right ovary": "ovary",
        }
    )

    return df_hra_pop_trio.to_dict(orient="records")


if __name__ == "__main__":
    if CACHE_FILE_HRA_POP.exists():
        print(f"Using cached HRApop list_cell_types from {CACHE_FILE_HRA_POP}")
        list_cell_types = load_list_cell_types(CACHE_FILE_HRA_POP)
    else:
        df_hra_pop_trio = download_hra_pop_and_get_organ_as_ct_trios()
        list_cell_types = extract_unique_organ_as_ct_trios_hra_pop(df_hra_pop_trio)
        save_list_cell_types(list_cell_types, CACHE_FILE_HRA_POP)
        print(f"Saved HRApop list_cell_types to {CACHE_FILE_HRA_POP}")

    pprint(list_cell_types)
