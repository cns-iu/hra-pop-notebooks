import pandas as pd
import requests
from pprint import pprint
# from urllib.parse import quote
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

CACHE_FILE_ASCTB = (
    Path(__file__).resolve().parent.parent / "data" / "list_cell_types_asctb.json"
)

CACHE_FILE_HRA_POP = (
    Path(__file__).resolve().parent.parent / "data" / "list_cell_types_hra_pop.json"
)

def save_list_cell_types(list_cell_types: list[dict], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(list_cell_types, f, indent=2)


def load_json_as_df(json_data: list[dict]) -> None:
    df = pd.DataFrame(json_data)
    pprint(df)
    return df


def load_list_cell_types(input_file: Path) -> list[dict]:
    with open(input_file, encoding="utf-8") as f:
        return json.load(f)

def make_http_request(url) -> dict:

    response = requests.get(
        url,
        headers={
            "Accept": "application/json",
        },
    )

    response.raise_for_status()
    data = response.json()
    return data


# def ontology_label_from_ebi(ontology_id: str) -> str | None:
#     """Return the label for a CL or UBERON ontology ID."""

#     iri = f'http://purl.obolibrary.org/obo/{ontology_id.replace(":", "_")}'

#     url = "https://www.ebi.ac.uk/ols4/api/terms" f'?iri={quote(iri, safe="")}'

#     response = requests.get(
#         url,
#         headers={"Accept": "application/json"},
#     )
#     response.raise_for_status()

#     data = response.json()

#     terms = data.get("_embedded", {}).get("terms", [])
#     if not terms:
#         return None

#     return terms[0]["label"]


def ontology_label_from_asctb(ontology_id: str, asctb_json: dict) -> str | None:
    for anatomical_structure in asctb_json["data"]["anatomical_structures"]:
        if anatomical_structure["id"] == ontology_id:
            return anatomical_structure["ccf_pref_label"]
