from shared import *
import json
from pathlib import Path

# def download_asct_b_table(organ_name:str):

purl_base = "https://purl.humanatlas.io/asct-b/"
organ_as_ct_trios = {"asctb_tables": [], "hra_pop": []}
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "list_cell_types.json"


def save_list_cell_types(cell_types: list, cache_file: Path = CACHE_FILE) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cell_types, f, indent=2)


def load_list_cell_types(cache_file: Path = CACHE_FILE) -> list:
    with open(cache_file, encoding="utf-8") as f:
        return json.load(f)


def download_asctb_tables_and_extract_organ_as_cts() -> list:
    print("Downloading ASCT+B tables")
    with open("./data/11th Release (v2.5).csv") as f:
        df_data = pd.read_csv(f)
        pprint(df_data)

        list_csv_urls = df_data["csv"].apply(
            lambda url: url.split("/")[-1].split(".")[0]
        )

        list_organ_name = [
            organ_name.lower()
            .replace("_", "-")
            .replace("asct-b-", "")
            .replace("vh-", "")
            for organ_name in list_csv_urls
        ]

        list_cell_types = []
        for organ in list_organ_name:
            print(organ)
            asctb_json = make_http_request(purl_base + organ)
            for cell_type in asctb_json["data"]["cell_types"]:
                if "ccf_located_in" in cell_type:
                    new_cell_type = {
                        "organ": organ,
                        "cell_type_label": cell_type["ccf_pref_label"],
                        "cell_type_id": cell_type["id"],
                        "as_id": cell_type["ccf_located_in"],
                        "as_label": [
                            ontology_label_from_asctb(as_id, asctb_json)
                            for as_id in cell_type["ccf_located_in"]
                        ],
                    }
                    pprint(f"Compiled: {new_cell_type}")
                    print()
                    list_cell_types.append(new_cell_type)

                    # pprint(new_cell_type)
        return list_cell_types


def extract_unique_organ_as_ct_trios(cell_types: list):
    for item in cell_types:
        pprint(item)


def download_hra_pop_and_get_organ_as_ct_trios() -> None:
    print("Downloading HRApop")


if __name__ == "__main__":
    if CACHE_FILE.exists():
        print(f"Using cached list_cell_types from {CACHE_FILE}")
        list_cell_types = load_list_cell_types()
    else:
        list_cell_types = download_asctb_tables_and_extract_organ_as_cts()
        save_list_cell_types(list_cell_types)

    extract_unique_organ_as_ct_trios(list_cell_types)
    download_hra_pop_and_get_organ_as_ct_trios()
