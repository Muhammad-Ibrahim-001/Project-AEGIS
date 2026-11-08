-- ==============================================================================
-- DL3004 DWBI Final Project: Data Quality & Quarantine Validation Rules
-- Platform: Databricks Serverless Compute / Databricks SQL Warehouse
-- Catalog: dwbi_catalog
-- ==============================================================================

USE CATALOG dwbi_catalog;

-- ------------------------------------------------------------------------------
-- 1. QUARANTINE SENTINELS & UNPARSEABLE STRINGS FROM EIA-923
-- ------------------------------------------------------------------------------
-- Identifies records where numeric columns contain '.' or 'NM' string sentinels
INSERT INTO quarantine.rejected_records (
    batch_id,
    source_system,
    source_table,
    source_row_identifier,
    rejection_reason,
    raw_payload_json
)
SELECT 
    batch_id,
    'EIA-923',
    'dwbi_catalog.bronze_staging.raw_eia923_monthly_generation',
    plant_id,
    'NUMERIC_FIELD_CONTAINS_STRING_SENTINEL',
    to_json(named_struct('plant_id', plant_id, 'quantity_january', quantity_january, 'netgen_january', netgen_january))
FROM bronze_staging.raw_eia923_monthly_generation
WHERE TRIM(quantity_january) IN ('.', 'NM', '*', '')
   OR TRIM(netgen_january) IN ('.', 'NM', '*', '');

-- ------------------------------------------------------------------------------
-- 2. QUARANTINE NOAA WEATHER SENSOR DROPOUTS (-9999)
-- ------------------------------------------------------------------------------
INSERT INTO quarantine.rejected_records (
    batch_id,
    source_system,
    source_table,
    source_row_identifier,
    rejection_reason,
    raw_payload_json
)
SELECT 
    batch_id,
    'NOAA-ISD',
    'dwbi_catalog.bronze_staging.raw_noaa_isd_weather',
    CONCAT(station_id, '_', timestamp_utc),
    'NOAA_SENTINEL_SENSOR_DROPOUT',
    to_json(named_struct('station_id', station_id, 'timestamp_utc', timestamp_utc, 'air_temp', air_temperature_c, 'wind_speed', wind_speed_mps))
FROM bronze_staging.raw_noaa_isd_weather
WHERE air_temperature_c = '-9999'
   OR wind_speed_mps = '-9999';

-- ------------------------------------------------------------------------------
-- 3. THERMODYNAMIC HEAT RATE BOUNDARY AUDIT (TECHNOLOGY-SPECIFIC)
-- ------------------------------------------------------------------------------
-- Flags plants whose Heat Rate violates realistic engineering bounds
-- (CCGT: 5,000 - 14,000 Btu/kWh | Coal: 8,500 - 18,000 Btu/kWh | Peakers: 9,000 - 22,000 Btu/kWh)
INSERT INTO quarantine.rejected_records (
    batch_id,
    source_system,
    source_table,
    source_row_identifier,
    rejection_reason,
    raw_payload_json
)
SELECT 
    uuid(),
    'EIA-923-CALCULATED',
    'dwbi_catalog.gold_warehouse.fact_monthly_plant_operations',
    CAST(f.plant_key AS STRING),
    CASE 
        WHEN f.prime_mover_code IN ('CA', 'CT', 'CS', 'CC') AND (f.avg_heat_rate_btu_kwh < 5000 OR f.avg_heat_rate_btu_kwh > 14000)
            THEN 'CCGT_HEAT_RATE_OUT_OF_BOUNDS'
        WHEN f.prime_mover_code = 'ST' AND (f.avg_heat_rate_btu_kwh < 8500 OR f.avg_heat_rate_btu_kwh > 18000)
            THEN 'COAL_ST_HEAT_RATE_OUT_OF_BOUNDS'
        WHEN f.prime_mover_code = 'GT' AND (f.avg_heat_rate_btu_kwh < 9000 OR f.avg_heat_rate_btu_kwh > 22000)
            THEN 'PEAKER_GT_HEAT_RATE_OUT_OF_BOUNDS'
    END,
    to_json(named_struct('plant_key', f.plant_key, 'prime_mover', f.prime_mover_code, 'heat_rate', f.avg_heat_rate_btu_kwh))
FROM gold_warehouse.fact_monthly_plant_operations f
WHERE (f.prime_mover_code IN ('CA', 'CT', 'CS', 'CC') AND (f.avg_heat_rate_btu_kwh < 5000 OR f.avg_heat_rate_btu_kwh > 14000))
   OR (f.prime_mover_code = 'ST' AND (f.avg_heat_rate_btu_kwh < 8500 OR f.avg_heat_rate_btu_kwh > 18000))
   OR (f.prime_mover_code = 'GT' AND (f.avg_heat_rate_btu_kwh < 9000 OR f.avg_heat_rate_btu_kwh > 22000));
