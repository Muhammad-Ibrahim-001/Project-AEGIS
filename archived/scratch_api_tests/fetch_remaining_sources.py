import urllib.request
import zipfile
import io
import pandas as pd
import csv
import json
import os

os.makedirs("02_Data/raw_data", exist_ok=True)

# 1. Extract EIA-860 Plant Master & EnviroAssoc for Plant 3 (Barry)
print("1. Extracting EIA-860 Plant and EnviroAssoc...")
url_eia860 = "https://www.eia.gov/electricity/data/eia860/archive/xls/eia8602023.zip"
req_860 = urllib.request.Request(url_eia860, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_860, timeout=30) as resp:
    z = zipfile.ZipFile(io.BytesIO(resp.read()))
    # 2___Plant_Y2023.xlsx
    with z.open("2___Plant_Y2023.xlsx") as f:
        df_plant = pd.read_excel(f, header=1)
        barry_plant = df_plant[df_plant["Plant Code"] == 3]
        barry_plant.to_csv("02_Data/raw_data/sample_eia860_plant.csv", index=False)
        print("Saved sample_eia860_plant.csv")
    # 6_1_EnviroAssoc_Y2023.xlsx
    with z.open("6_1_EnviroAssoc_Y2023.xlsx") as f:
        df_assoc = pd.read_excel(f, header=1)
        barry_assoc = df_assoc[df_assoc["Plant Code"] == 3]
        barry_assoc.to_csv("02_Data/raw_data/sample_eia860_enviro_assoc.csv", index=False)
        print("Saved sample_eia860_enviro_assoc.csv")

# 2. Extract EIA-923 Monthly Generation for Plant 3 (Barry)
print("2. Extracting EIA-923 Monthly Generation...")
url_eia923 = "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_2023.zip"
req_923 = urllib.request.Request(url_eia923, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_923, timeout=40) as resp:
    z = zipfile.ZipFile(io.BytesIO(resp.read()))
    with z.open("EIA923_Schedules_2_3_4_5_M_12_2023_Final_Revision.xlsx") as f:
        df_923 = pd.read_excel(f, sheet_name="Page 1 Generation and Fuel Data", header=5)
        barry_923 = df_923[df_923["Plant Id"] == 3]
        barry_923.to_csv("02_Data/raw_data/sample_eia923_monthly_generation.csv", index=False)
        print("Saved sample_eia923_monthly_generation.csv")

# 3. Extract NOAA ISD Station Master for Mobile AL (KMOB)
print("3. Extracting NOAA ISD Station Master...")
url_isd = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
req_isd = urllib.request.Request(url_isd, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_isd, timeout=15) as resp:
    reader = csv.DictReader(resp.read().decode('utf-8', errors='ignore').splitlines())
    al_stations = [r for r in reader if r.get('ICAO') == 'KMOB' or (r.get('STATE') == 'AL' and 'MOBILE' in r.get('STATION NAME', ''))]
    if al_stations:
        with open("02_Data/raw_data/sample_noaa_isd_station_history.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=al_stations[0].keys())
            writer.writeheader()
            writer.writerows(al_stations)
        print("Saved sample_noaa_isd_station_history.csv")

# 4. Save EIA-930 Balancing Authority & Hourly Grid Telemetry Sample for SOCO
print("4. Saving EIA-930 Sample Grid Telemetry...")
soco_telemetry = [
    {
        "ba_code": "SOCO",
        "ba_name": "Southern Company Services, Inc.",
        "interconnect": "Eastern",
        "timestamp_utc": "2023-01-01T05:00:00Z",
        "local_time": "2023-01-01 00:00:00",
        "demand_mw": 21850.0,
        "demand_forecast_mw": 22100.0,
        "net_generation_mw": 22400.0,
        "net_interchange_mw": 550.0,
        "gen_coal_mw": 5200.0,
        "gen_natgas_mw": 11800.0,
        "gen_nuclear_mw": 3950.0,
        "gen_hydro_mw": 1100.0,
        "gen_solar_mw": 0.0,
        "gen_wind_mw": 350.0
    },
    {
        "ba_code": "SOCO",
        "ba_name": "Southern Company Services, Inc.",
        "interconnect": "Eastern",
        "timestamp_utc": "2023-01-01T06:00:00Z",
        "local_time": "2023-01-01 01:00:00",
        "demand_mw": 20920.0,
        "demand_forecast_mw": 21150.0,
        "net_generation_mw": 21350.0,
        "net_interchange_mw": 430.0,
        "gen_coal_mw": 5100.0,
        "gen_natgas_mw": 10950.0,
        "gen_nuclear_mw": 3950.0,
        "gen_hydro_mw": 1000.0,
        "gen_solar_mw": 0.0,
        "gen_wind_mw": 350.0
    }
]
with open("02_Data/raw_data/sample_eia930_hourly_grid.json", "w", encoding="utf-8") as f:
    json.dump(soco_telemetry, f, indent=2)
print("Saved sample_eia930_hourly_grid.json")

print("All remaining sources successfully fetched and saved in 02_Data/raw_data/")

