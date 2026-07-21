from shared import *

def load_processed_data():
  df_asctb = load_json_as_df(load_list_cell_types(CACHE_FILE_ASCTB))
  df_hra_pop = load_json_as_df(load_list_cell_types(CACHE_FILE_HRA_POP))
  return pd.concat([df_asctb, df_hra_pop], ignore_index=True)

def visualize(data:pd.DataFrame):
  print(data)

if __name__ == "__main__":
    visualize(load_processed_data())
