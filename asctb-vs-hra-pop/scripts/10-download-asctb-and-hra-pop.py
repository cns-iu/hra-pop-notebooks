from shared import *
import json
from pathlib import Path

# def download_asct_b_table(organ_name:str):

purl_base = "https://purl.humanatlas.io/asct-b/"
organ_as_ct_trios = {"asctb_tables": [], "hra_pop": []}


def load_list_cell_types(cache_file: Path = CACHE_FILE_ASCTB) -> list:
    with open(cache_file, encoding="utf-8") as f:
        return json.load(f)


def normalize_cell_types(cell_types: list) -> list:
    normalized_cell_types = []
    for item in cell_types:
        as_ids = item.get("as_id")
        as_labels = item.get("as_label")

        if isinstance(as_ids, list):
            if isinstance(as_labels, list) and len(as_labels) == len(as_ids):
                pairs = zip(as_ids, as_labels)
            else:
                pairs = [(as_id, None) for as_id in as_ids]

            for as_id, as_label in pairs:
                new_item = item.copy()
                new_item["as_id"] = as_id
                new_item["as_label"] = as_label
                normalized_cell_types.append(new_item)
        else:
            normalized_cell_types.append(item)

    return normalized_cell_types


def download_asctb_tables_and_extract_organ_as_cts() -> list:
    print("Downloading ASCT+B tables")

    hra_data = make_http_request("https://purl.humanatlas.io/collection/hra")["data"]
    list_csv_urls = set()
    for item in hra_data:
        if "asct-b" in item and "crosswalk" not in item:
            organ_name = item.split("/")[1]
            list_csv_urls.add(organ_name)

    list_organ_name = [
        organ_name.lower().replace("_", "-").replace("asct-b-", "").replace("vh-", "")
        for organ_name in list_csv_urls
    ]

    list_cell_types = []
    for organ in list_organ_name:
        print(organ)
        asctb_json = make_http_request(purl_base + organ)
        for cell_type in asctb_json["data"]["cell_types"]:
            if "ccf_located_in" in cell_type:
                located_in = cell_type["ccf_located_in"]
                if not isinstance(located_in, list):
                    located_in = [located_in]

                for as_id in located_in:
                    new_cell_type = {
                        "organ": organ,
                        "cell_type_label": cell_type["ccf_pref_label"],
                        "cell_type_id": cell_type["id"],
                        "as_id": as_id,
                        "as_label": ontology_label_from_asctb(as_id, asctb_json),
                        "source": "asctb",
                    }
                    pprint(f"Compiled: {new_cell_type}")
                    print()
                    list_cell_types.append(new_cell_type)

                # pprint(new_cell_type)
    return list_cell_types


def extract_unique_organ_as_ct_trios(cell_types: list):
    for item in cell_types:
        pprint(item)


if __name__ == "__main__":
    if CACHE_FILE_ASCTB.exists():
        print(f"Using cached list_cell_types from {CACHE_FILE_ASCTB}")
        list_cell_types = load_list_cell_types()
        list_cell_types = normalize_cell_types(list_cell_types)
    else:
        list_cell_types = download_asctb_tables_and_extract_organ_as_cts()
        save_list_cell_types(list_cell_types, CACHE_FILE_ASCTB)

    extract_unique_organ_as_ct_trios(list_cell_types)
