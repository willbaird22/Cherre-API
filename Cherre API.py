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
            state: {_eq: "NC"},
            city: {_eq: "CHARLOTTE"},
            property_use_code_mapped: {_eq: "44"}
        """
    if last_id:
        where_clause += f', address: {{_gt: "{last_id}"}}'  # Use _gt for descending pagination
    where_clause += "}"
    
    query = f"""
    {{
      tax_assessor_v2(
        {where_clause}
        order_by: {{address: desc}}
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
        address
      }}
    }}
    """
    return query

def fetch_data():
    """Fetch all records with pagination."""
    all_results = []
    last_id = None  # Tracks the last address

    while True:
        query = build_query(last_id)
        print(f"Running query with last_id: {last_id}")  # Debug print

        try:
            data = run_query(query)
            print(json.dumps(data, indent=2))  # Print raw response for inspection
        except Exception as e:
            print(f"Error occurred: {e}")
            break

        # Extract records from the response
        records = data.get("data", {}).get("tax_assessor_v2", [])
        if not records:
            print("No more records found.")  # Debug print
            break  # Stop if no records are returned

        # Add records to the result list
        all_results.extend(records)

        # Stop if fewer than 1000 records are returned
        if len(records) < 1000:
            print("Less than 1000 records, stopping.")  # Debug print
            break

        # Update last_id to the smallest address for next query
        last_id = records[-1]["address"]

        # Sleep to avoid hitting API limits
        time.sleep(0.1)
    return all_results

# Execute and display the data
try:
    data = fetch_data()
    # Flatten and convert to DataFrame
    flat_data = [
        {
            "address": record["address"],
            "state": record["state"],
            "city": record["city"],
            "zip": record["zip"],
            "building_sq_ft": record["building_sq_ft"],
            "hvacc_cooling_code": record["hvacc_cooling_code"],
            "hvacc_heating_code": record["hvacc_heating_code"],
            "foundation_code": record["foundation_code"],
            "fl_fema_flood_zone": record["fl_fema_flood_zone"],
        }
        for record in data
    ]
    df = pd.DataFrame(flat_data)
    # Export the DataFrame to an Excel file
    output_file = '/Users/willpersonal/Documents/Home Brands/Cherre API/output.xlsx'
    df.to_excel(output_file, index=False)
    print(f"Data exported to {output_file}")
except Exception as e:
    print(f"Error occurred: {e}")