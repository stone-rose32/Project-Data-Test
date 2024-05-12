import requests
import json
import pandas as pd
from tqdm import tqdm
import datetime

def call_url(year, month, variables):
  if year < 2024:
    if 'CBSA' in variables:
      variables[variables.index('CBSA')] = 'GTCBSA'
  else:
    if 'GTCBSA' in variables:
      variables[variables.index('GTCBSA')] = 'CBSA'
  url_var = ','.join(variables)
  base_url = 'https://api.census.gov/data/'
  year_month = f'{year}/cps/basic/{month}'
  census_var = f'get={url_var}'
  api_key = '9f3223244e7252dcbb1ed8348a071fc3673eb56e'

  url = f'{base_url}{year_month}?{census_var}&key={api_key}'

  return url

def get_data(url):
  response = requests.get(url)
  return response.json()

def get_variable_dict(years, months):
  year = max(years)
  month = months[-1]

  base_url = 'https://api.census.gov/data/'
  year_month = f'{year}/cps/basic/{month}/variables.json'
  url = f'{base_url}{year_month}'

  response = requests.get(url)

  data = response.json()
  variable_info = {}

  for variable, info in data["variables"].items():
    variable_info[variable] = {
      "label": info.get("label", ""),
      "suggested_weight": info.get("suggested-weight", ""),
      "values": {}
    }
    if "values" in info:
      if "item" in info["values"]:
        for value, label in info["values"]["item"].items():
          variable_info[variable]["values"][value] = label
      else:
        variable_info[variable]["values"] = info["values"]
  return variable_info

def get_data_from_census(years, months, variables):
    all_data = []
    for year in tqdm (years, desc="Loading..."):
      for month in months:
        url = call_url(year, month, variables)
        data = get_data(url)
        yearcol = 'Year'
        monthcol = 'Month'
        data[0].append(yearcol)
        data[0].append(monthcol)
        for row in data[1:]:
          row.append(year)
          row.append(month)
        all_data.extend(data)
    columns = all_data[0]
    rows = all_data[1:]

    census_data = pd.DataFrame(rows, columns=columns)
    return census_data

def data_refine_job(data_frame, variable_dict):
  if 'GTCBSA' in data_frame.columns:
    data_frame = data_frame.rename(columns={'GTCBSA': 'CBSA'})
  for column in data_frame.columns:
    if column in variable_dict:
      label_dict = variable_dict[column]['values']
      data_frame[column] = data_frame[column].astype(str).map(label_dict).fillna(data_frame[column])
  new_column_headers = []
  for header in data_frame.columns:
    if header in variable_dict:
      new_column_headers.append(variable_dict[header]['label'])
    else:
      new_column_headers.append(header)
  data_frame.columns = new_column_headers
  return data_frame


def get_update_year():
  current_year = []
  today = datetime.date.today().year
  current_year.append(today)

  return current_year

def update_data_job(current_year, current_month, variables, csv_file):
  new_data = get_data_from_census(current_year, current_month, variables)
  var_dict = get_variable_dict(current_year, current_month)
  new_rdata = data_refine_job(new_data, var_dict)

  new_rdata.to_csv('census_data.csv', index=False)

def main():
    current_year = get_update_year()
    current_month = ['jan']
    variables = ['CBSA', 'HEHOUSUT', 'HETENURE', 'HEFAMINC', 'HRNUMHOU', 'PEEDUCA', 'PESEX', 'PEMARITL', 'PEMLR', 'PWCMPWGT', 'HWHHWGT', 'PWFMWGT', 'PWLGWGT', 'PWORWGT', 'PWSSWGT']
    csv_file = 'census_data.csv'
    
    update_data_job(current_year, current_month, variables, csv_file)


if __name__ == "__main__":
    main()
