import pandas as pd
import requests
from pprint import pprint
# from urllib.parse import quote

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
