import csv

# Define the list of airports and airstrips
airports_data = [
    {"name": "Jomo Kenyatta International Airport", "type": "Airport", "latitude": -1.319167, "longitude": 36.9275, "elevation": 5330, "icao": "HKJK", "iata": "NBO"},
    {"name": "Moi International Airport", "type": "Airport", "latitude": -4.034833, "longitude": 39.59425, "elevation": 200, "icao": "HKMO", "iata": "MBA"},
    {"name": "Eldoret International Airport", "type": "Airport", "latitude": 0.404458, "longitude": 35.238889, "elevation": 7016, "icao": "HKEL", "iata": "EDL"},
    {"name": "Kisumu International Airport", "type": "Airport", "latitude": -0.086139, "longitude": 34.728892, "elevation": 3740, "icao": "HKKI", "iata": "KIS"},
    {"name": "Wilson Airport", "type": "Airport", "latitude": -1.321719, "longitude": 36.814833, "elevation": 5535, "icao": "HKNW", "iata": "WIL"},
    {"name": "Malindi Airport", "type": "Airport", "latitude": -3.229311, "longitude": 40.101666, "elevation": 80, "icao": "HKML", "iata": "MYD"},
    {"name": "Ukunda Airport", "type": "Airport", "latitude": -4.293333, "longitude": 39.571667, "elevation": 98, "icao": "HKUK", "iata": "UKA"},
    {"name": "Wajir Airport", "type": "Airport", "latitude": 1.733239, "longitude": 40.091472, "elevation": 770, "icao": "HKWJ", "iata": "WJR"},
    {"name": "Lokichogio Airport", "type": "Airport", "latitude": 4.298056, "longitude": 34.348056, "elevation": 2080, "icao": "HKLK", "iata": "LKG"},
    {"name": "Garissa Airport", "type": "Airport", "latitude": -0.463228, "longitude": 39.648333, "elevation": 476, "icao": "HKGA", "iata": "GAS"},
]

airstrips_data = [
    {"name": "Amboseli Airstrip", "type": "Airstrip", "latitude": -2.643, "longitude": 37.256, "elevation": 3750, "icao": "HKAM", "iata": ""},
    {"name": "Nanyuki Airstrip", "type": "Airstrip", "latitude": -0.0663, "longitude": 37.041, "elevation": 6150, "icao": "HKNY", "iata": "NYK"},
    {"name": "Keekorok Airstrip", "type": "Airstrip", "latitude": -1.585, "longitude": 35.2506, "elevation": 5300, "icao": "HKKR", "iata": ""},
    {"name": "Manda Airstrip", "type": "Airstrip", "latitude": -2.252, "longitude": 40.913, "elevation": 20, "icao": "HKLU", "iata": "LAU"},
    {"name": "Kichwa Tembo Airstrip", "type": "Airstrip", "latitude": -1.408, "longitude": 35.010, "elevation": 5100, "icao": "HKKT", "iata": ""},
    {"name": "Ol Kiombo Airstrip", "type": "Airstrip", "latitude": -1.421, "longitude": 35.011, "elevation": 5000, "icao": "HKOK", "iata": ""},
    {"name": "Olare Orok Airstrip", "type": "Airstrip", "latitude": -1.352, "longitude": 35.003, "elevation": 4970, "icao": "HKOR", "iata": ""},
    {"name": "Mugie Airstrip", "type": "Airstrip", "latitude": 0.282, "longitude": 36.793, "elevation": 6800, "icao": "HKMG", "iata": ""},
    {"name": "Loisaba Airstrip", "type": "Airstrip", "latitude": 0.205, "longitude": 36.799, "elevation": 6000, "icao": "HKLS", "iata": ""},
    {"name": "Kalama Airstrip", "type": "Airstrip", "latitude": 0.667, "longitude": 37.467, "elevation": 7200, "icao": "HKKL", "iata": ""},
    {"name": "Borana Airstrip", "type": "Airstrip", "latitude": 0.281, "longitude": 36.874, "elevation": 6800, "icao": "HKBA", "iata": ""},
    {"name": "Lewa Downs Airstrip", "type": "Airstrip", "latitude": 0.168, "longitude": 37.417, "elevation": 6200, "icao": "HKLD", "iata": ""},
]

# Merge the data
all_data = airports_data + airstrips_data

# Define CSV file name
csv_filename = "kenya_airports_airstrips.csv"

# Define column headers
headers = ["name", "type", "latitude", "longitude", "elevation", "icao", "iata"]

# Write to CSV
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()
    writer.writerows(all_data)

print(f"CSV file '{csv_filename}' successfully created with 20 locations!")
