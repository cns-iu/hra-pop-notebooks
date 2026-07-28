from shared import *

# def download_asct_b_table(organ_name:str):

purl_base = "https://purl.humanatlas.io/asct-b/"
organ_as_ct_trios = {"asctb_tables": [], "hra_pop": []}


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


def _ontology_id_and_label(value, asctb_json: dict):
    if isinstance(value, dict):
        ontology_id = value.get("id") or value.get("ontology_id")
        ontology_label = value.get("label") or value.get("ccf_pref_label")
        if ontology_id and not ontology_label:
            ontology_label = ontology_label_from_asctb(ontology_id, asctb_json)
        return ontology_id, ontology_label

    return value, ontology_label_from_asctb(value, asctb_json)


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
        cell_marker_descriptors = asctb_json["data"].get("cell_marker_descriptor", [])
        for descriptor in cell_marker_descriptors:
            primary_cell_type = descriptor.get("primary_cell_type")
            primary_anatomical_structure = descriptor.get("primary_anatomical_structure")

            primary_cell_type_id, primary_cell_type_label = _ontology_id_and_label(
                primary_cell_type, asctb_json
            )
            as_id, as_label = _ontology_id_and_label(primary_anatomical_structure, asctb_json)

            if not primary_cell_type_id or not as_id:
                continue

            new_cell_type = {
                "organ": organ,
                # "cell_type_label": primary_cell_type_label,
                "cell_type_id": primary_cell_type_id,
                "as_id": as_id,
                "as_label": as_label,
                "source": "asctb",
            }
            pprint(f"Compiled: {new_cell_type}")
            print()
            list_cell_types.append(new_cell_type)
    return list_cell_types


def extract_unique_organ_as_ct_trios(cell_types: list):
    for item in cell_types:
        pprint(item)


if __name__ == "__main__":
    if CACHE_FILE_ASCTB.exists():
        print(f"Using cached list_cell_types from {CACHE_FILE_ASCTB}")
        list_cell_types = load_list_cell_types(CACHE_FILE_ASCTB)
        if not list_cell_types:
            print(f"Cached list_cell_types at {CACHE_FILE_ASCTB} is empty; regenerating")
            list_cell_types = download_asctb_tables_and_extract_organ_as_cts()
            save_list_cell_types(list_cell_types, CACHE_FILE_ASCTB)
        else:
            list_cell_types = normalize_cell_types(list_cell_types)
    else:
        list_cell_types = download_asctb_tables_and_extract_organ_as_cts()
        save_list_cell_types(list_cell_types, CACHE_FILE_ASCTB)

    extract_unique_organ_as_ct_trios(list_cell_types)
