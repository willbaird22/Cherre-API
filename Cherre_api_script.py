import json
import requests
import time
import pandas as pd

# User credentials
headers = {'Authorization': f'Bearer {"YXBpLWNsaWVudC1iOTdhNWE2OS03ODllLTQ2YmItYTYxMy05ZGFhMTljMDJhNjFAY2hlcnJlLmNvbTprMVdkaXBFIyFabVZhU0deR3VaKiVjb25HQm8wdEpASFYjdXFTUWI2NFJwbmhKMk1VUnJMekNvaldnY201RVBU"}'}
# API endpoint URL
url = 'https://graphql.cherre.com/graphql'

def run_query(query):
    response = requests.post(url, headers=headers, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with code {response.status_code}: {response.text}")

def build_query(last_id=None):
    """Build the query with dynamic pagination."""
    where_clause = """
        where: {
            state: {_eq: "VA"},
            city: {_eq: "RICHMOND"},
            property_use_code_mapped: {_eq: "44"}
        """
    if last_id:
        where_clause += f', tax_assessor_id: {{_gt: {last_id}}}'  # Use _gt for ascending pagination
    where_clause += "}"
    
    query = f"""
    {{
      tax_assessor_v2(
        {where_clause}
        order_by: {{tax_assessor_id: asc}}
        limit: 1000
      ) {{
        address
        state
        city
        zip
        building_sq_ft
        hvacc_cooling_code
        hvacc_heating_code
        foundation_code
        fl_fema_flood_zone
        tax_assessor_id
        usa_zip_code_boundary_v2__zip_code {{
          usa_demographics_v2__geography_id(order_by: {{vintage: desc}}, limit: 1) {{
            average_household_income
            vintage
          }}
        }}
      }}
    }}
    """
    return query

def fetch_data():
    all_results = []
    last_id = None

    while True:
        query = build_query(last_id)
        try:
            result = run_query(query)
            records = result["data"]["tax_assessor_v2"]
        except Exception as e:
            print(f"Error occurred: {e}")
            break  # Stop the loop if an error occurs

        if not records:
            print("No records returned, stopping.")
            break  # Stop if no records are returned

        # Add records to the result list
        all_results.extend(records)

        # Stop if fewer than 1000 records are returned
        if len(records) < 1000:
            print("Less than 1000 records, stopping.")  # Debug print
            break

        # Update last_id to the smallest address for next query
        last_id = records[-1]["tax_assessor_id"]

        # Sleep to avoid hitting API limits
        time.sleep(0.1)
    return all_results

# Execute and display the data
try:
    data = fetch_data()
    # Flatten and convert to DataFrame
    flat_data = []
    for record in data:
        if record is None:
            continue
        zip_code_data = record.get("usa_zip_code_boundary_v2__zip_code", {})
        if zip_code_data is None:
            zip_code_data = {}
        demographics_data = zip_code_data.get("usa_demographics_v2__geography_id", [{}])
        if demographics_data is None:
            demographics_data = [{}]
        flat_data.append({
            "address": record.get("address"),
            "state": record.get("state"),
            "city": record.get("city"),
            "zip": record.get("zip"),
            "building_sq_ft": record.get("building_sq_ft"),
            "hvacc_cooling_code": record.get("hvacc_cooling_code"),
            "hvacc_heating_code": record.get("hvacc_heating_code"),
            "foundation_code": record.get("foundation_code"),
            "fl_fema_flood_zone": record.get("fl_fema_flood_zone"),
            "tax_assessor_id": record.get("tax_assessor_id"),
            "average_household_income": demographics_data[0].get("average_household_income"),
            "vintage": demographics_data[0].get("vintage")
        })
    df = pd.DataFrame(flat_data)
    print(df)
    # Save the data to a CSV file
    df.to_csv("richmond_data.csv", index=False)
except Exception as e:
    print(f"Error occurred: {e}")