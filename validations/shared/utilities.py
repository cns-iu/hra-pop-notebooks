from hra_api_client.models.sparql_query_request import SparqlQueryRequest
from hra_api_client.api import v1_api as default_api
import requests
import hra_api_client
from sklearn.metrics.pairwise import cosine_similarity
import json

# config
configuration = hra_api_client.Configuration(
    host="https://apps.humanatlas.io/api"
)


api_client = hra_api_client.ApiClient(configuration)
api_instance = default_api.V1Api(api_client)

def dict_to_vec(dict1: dict, dict2: dict):
  """Takes two dictionaries and returns a tuple of nornalized lists with values (0 if key not present)

  Args:
    dict1 (dict): dictionary 1
    dict2 (dict): dictionary 2
  Returns:
    result (tuple): a tuple with normalized lists
  """

  # initialize result
  dict1_list = []
  dict2_list = []

  # handle shared keys
  shared_keys = set(dict1['collisions'].keys()).intersection(
      dict2['collisions'].keys())

  for key in shared_keys:
    dict1_list.append(dict1['collisions'][key])
    dict2_list.append(dict2['collisions'][key])

  # handle not shared keys
  keys_in_dict1_not_in_dict2 = dict1.keys() - dict2.keys()
  for key in keys_in_dict1_not_in_dict2:
    dict1[key] = 0

  keys_in_dict2_not_in_dict1 = dict2.keys() - dict1.keys()
  for key in keys_in_dict2_not_in_dict1:
    dict1[key] = 0

  return (dict1_list, dict2_list)


def get_as_collision_items(iri: str, get_organ=False):
  """A function to get AS collision items for an IRI (extraction site) and return a dictionary with AS UBERON ID and intersection percentage of the extraction site. 
  This uses https://apps.humanatlas.io/api/#get-/v1/extraction-site to get the rui_location data given the IRI and https://apps.humanatlas.io/api/#post-/v1/collisions to get the collisions

  Args:
    iri (str): an IRI for an extraction site

  Returns:
    a dictionary with the IRI and a nested dictionary with collisions (ID and percentage) 
  """

  result = {

  }

  # get extraction site
  base_url_extraction_site = "https://apps.humanatlas.io/api/v1/extraction-site?iri="
  extraction_site = ""

  response = requests.get(base_url_extraction_site+iri)

  if response:
    extraction_site = json.loads(response.text)
  else:
    raise Exception(f"Non-success status code: {response.status_code}")

  # send extraction site to /collisions endpoints
  collisions = api_instance.collisions(extraction_site)
  for item in collisions:
    result[item['representation_of']] = item['percentage_of_tissue_block']
  if get_organ:
      result['organ'] = extraction_site['placement']['target']

  return result


def compute_cosine_similarity_by_as_percentage(iri_1: str, iri_2: str):
  """Takes two IRIs of extraction sites and returns the cosine similarity of their AS percentages

  Args:
          iri_1 (str): An IRI for an extraction site
          iri_2 (str): An IRI for an extraction site

Returns: 
          similarity (float): A cosine similarity
  """

  # Get AS collision items as dict
  dict1 = get_as_collision_items(iri_1)
  dict2 = get_as_collision_items(iri_2)

  # Get a combined set of all keys from both dictionaries
  all_keys = set(dict1.keys()).union(dict2.keys())

  # Create the two lists of values
  values1 = [dict1.get(key, 0) for key in all_keys]
  values2 = [dict2.get(key, 0) for key in all_keys]

  # Compute cosine similarity
  cosine_similarity_value = cosine_similarity([values1], [values2])

  return float(cosine_similarity_value[0][0])
