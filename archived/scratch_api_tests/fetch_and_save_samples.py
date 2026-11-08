import urllib.request
import json
import csv
import io
import zipfile
import pandas as pd
import os

os.makedirs("02_Data/raw_data", exist_ok=True)

# 1. Fetch EPA CAMPD Hourly Emissions for Plant 3 (Barry)
print("1. Fetching EPA CAMPD Hourly Emissions...")
api_key = 'KzaPdgeUgdnuuqCcanmoXKnVuiyYAHKFcmqNrd3u'
url_epa = f'https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly?beginDate=2023-01-01&endDate=2023-01-01&stateCode=AL&facilityId=3'
headers_epa = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'x-api-key': api_key,
    'Origin': 'https://campd.epa.gov',
    'Referer': 'https://campd.epa.gov/'
}
req_epa = urllib.request.Request(url_epa, headers=headers_epa)
with urllib.request.urlopen(req_epa, timeout=15) as resp:
    epa_data = json.loads(resp.read().decode())
    with open("02_Data/raw_data/sample_epa_hourly_emissions.json", "w", encoding="utf-8") as f:
        json.dump(epa_data[:20], f, indent=2)
    print(f"Saved {len(epa_data[:20])} EPA CAMPD sample records.")

# 2. Fetch EPA-EIA Crosswalk for Plant 3 (Barry)
print("2. Fetching EPA-EIA Crosswalk...")
url_xwalk = 'https://raw.githubusercontent.com/USEPA/camd-eia-crosswalk/master/epa_eia_crosswalk.csv'
req_xwalk = urllib.request.Request(url_xwalk, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req_xwalk, timeout=15) as resp:
    reader = csv.DictReader(resp.read().decode('utf-8').splitlines())
    barry_xwalk = [r for r in reader if r.get('CAMD_PLANT_ID') == '3']
    if barry_xwalk:
        with open("02_Data/raw_data/sample_epa_eia_crosswalk.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=barry_xwalk[0].keys())
            writer.writeheader()
            writer.writerows(barry_xwalk)
        print(f"Saved {len(barry_xwalk)} EPA-EIA Crosswalk sample records.")

# 3. Fetch NOAA Weather Observations (Station KMOB near Barry)
print("3. Fetching NOAA Weather Observations...")
url_noaa = 'https://api.weather.gov/stations/KMOB/observations?limit=20'
req_noaa = urllib.request.Request(url_noaa, headers={'User-Agent': 'DWBI-Student-Project/1.0 (student@university.edu)'})
with urllib.request.urlopen(req_noaa, timeout=15) as resp:
    noaa_data = json.loads(resp.read().decode())
    features = noaa_data.get('features', [])
    clean_noaa = [feat['properties'] for feat in features]
    with open("02_Data/raw_data/sample_noaa_isd_weather.json", "w", encoding="utf-8") as f:
        json.dump(clean_noaa, f, indent=2)
    print(f"Saved {len(clean_noaa)} NOAA Weather sample records.")

# 4. Extract EIA-860 Generator Inventory for Plant 3 (Barry)
print("4. Fetching EIA-860 Generator Inventory...")
url_eia860 = "https://www.eia.gov/electricity/data/eia860/archive/xls/eia8602023.zip"
req_eia860 = urllib.request.Request(url_eia860, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
with urllib.request.urlopen(req_eia860, timeout=30) as resp:
    zip_bytes = io.BytesIO(resp.read())
    with zipfile.ZipFile(zip_bytes) as z:
        with z.open("3_1_Generator_Y2023.xlsx") as f:
            df_gen = pd.read_excel(f, header=1)
            barry_gen = df_gen[df_gen["Plant Code"] == 3]
            barry_gen.to_csv("02_Data/raw_data/sample_eia860_generator.csv", index=False)
            print(f"Saved {len(barry_gen)} EIA-860 Generator sample records.")

print("All source samples successfully saved in 02_Data/raw_data/")
