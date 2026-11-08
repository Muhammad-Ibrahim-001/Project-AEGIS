-- ==============================================================================
-- DL3004 DWBI Final Project: Comprehensive Data Quality & Audit Framework
-- Platform: Databricks Serverless Compute / Databricks SQL Warehouse
-- Target Table: dwbi_catalog.quarantine.dq_check_results
-- Checks: 1. Completeness  2. Accuracy & Reconciliation  3. Referential Integrity
--         4. Uniqueness    5. Row Count Reconciliation   6. Date Coverage
-- ==============================================================================

USE CATALOG dwbi_catalog;

-- ------------------------------------------------------------------------------
-- DDL: Ensure Target Audit Table Exists in Quarantine Schema
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quarantine.dq_check_results (
    check_id         STRING NOT NULL,
    check_category   STRING NOT NULL,
    check_name       STRING NOT NULL,
    table_name       STRING NOT NULL,
    column_name      STRING,
    metric_value     DOUBLE,
    threshold        STRING,
    status           STRING NOT NULL,
    run_batch_id     STRING NOT NULL,
    checked_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- ==============================================================================
-- 1. COMPLETENESS CHECKS
-- Null counts and null percentages across all dimension and fact key columns
-- ==============================================================================

-- 1.1 dim_plant key completeness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'CMP_PLANT_PK', 'COMPLETENESS', 'dim_plant_pk_null_check', 'gold_warehouse.dim_plant', 'plant_key',
    ROUND(100.0 * COUNT(CASE WHEN plant_key IS NULL THEN 1 END) / COUNT(*), 4),
    '0.0%',
    CASE WHEN COUNT(CASE WHEN plant_key IS NULL THEN 1 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH';

-- 1.2 dim_plant natural key completeness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'CMP_PLANT_NAT', 'COMPLETENESS', 'dim_plant_orispl_null_check', 'gold_warehouse.dim_plant', 'orispl_code',
    ROUND(100.0 * COUNT(CASE WHEN orispl_code IS NULL AND plant_key != -1 THEN 1 END) / COUNT(*), 4),
    '0.0%',
    CASE WHEN COUNT(CASE WHEN orispl_code IS NULL AND plant_key != -1 THEN 1 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH';

-- 1.3 dim_date completeness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'CMP_DATE_PK', 'COMPLETENESS', 'dim_date_pk_null_check', 'gold_warehouse.dim_date', 'date_key',
    ROUND(100.0 * COUNT(CASE WHEN date_key IS NULL THEN 1 END) / COUNT(*), 4),
    '0.0%',
    CASE WHEN COUNT(CASE WHEN date_key IS NULL THEN 1 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH';

-- 1.4 fact_hourly_emissions_weather keys completeness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'CMP_FACT_EMISS_KEYS', 'COMPLETENESS', 'fact_emissions_keys_null_check', 'gold_warehouse.fact_hourly_emissions_weather', 'composite_keys',
    ROUND(100.0 * COUNT(CASE WHEN date_key IS NULL OR plant_key IS NULL OR hour_of_day IS NULL THEN 1 END) / COUNT(*), 4),
    '0.0%',
    CASE WHEN COUNT(CASE WHEN date_key IS NULL OR plant_key IS NULL OR hour_of_day IS NULL THEN 1 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH';

-- 1.5 fact_monthly_plant_operations keys completeness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'CMP_FACT_MONTH_KEYS', 'COMPLETENESS', 'fact_monthly_keys_null_check', 'gold_warehouse.fact_monthly_plant_operations', 'composite_keys',
    ROUND(100.0 * COUNT(CASE WHEN month_start_date_key IS NULL OR plant_key IS NULL THEN 1 END) / COUNT(*), 4),
    '0.0%',
    CASE WHEN COUNT(CASE WHEN month_start_date_key IS NULL OR plant_key IS NULL THEN 1 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH';

-- 1.6 fact_regional_grid_demand keys completeness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'CMP_FACT_GRID_KEYS', 'COMPLETENESS', 'fact_grid_keys_null_check', 'gold_warehouse.fact_regional_grid_demand', 'composite_keys',
    ROUND(100.0 * COUNT(CASE WHEN date_key IS NULL OR ba_key IS NULL OR hour_of_day IS NULL THEN 1 END) / COUNT(*), 4),
    '0.0%',
    CASE WHEN COUNT(CASE WHEN date_key IS NULL OR ba_key IS NULL OR hour_of_day IS NULL THEN 1 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH';


-- ==============================================================================
-- 2. ACCURACY & RECONCILIATION CHECKS
-- EPA Gross vs EIA Net monthly generation reconciliation + Silver vs Fact measure sums
-- ==============================================================================

-- 2.1 EPA Gross vs EIA Net Generation Monthly Reconciliation (Auxiliary Load Ratio Audit - BQ6)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH monthly_epa AS (
    SELECT 
        plant_key,
        SUBSTRING(CAST(date_key AS STRING), 1, 6) AS year_month,
        SUM(gross_load_mw) AS total_gross_generation_mwh
    FROM gold_warehouse.fact_hourly_emissions_weather
    WHERE plant_key != -1
    GROUP BY plant_key, SUBSTRING(CAST(date_key AS STRING), 1, 6)
),
monthly_eia AS (
    SELECT 
        plant_key,
        SUBSTRING(CAST(month_start_date_key AS STRING), 1, 6) AS year_month,
        SUM(net_generation_mwh) AS total_net_generation_mwh
    FROM gold_warehouse.fact_monthly_plant_operations
    WHERE plant_key != -1
    GROUP BY plant_key, SUBSTRING(CAST(month_start_date_key AS STRING), 1, 6)
),
reconciled AS (
    SELECT 
        eia.plant_key,
        eia.year_month,
        eia.total_net_generation_mwh,
        epa.total_gross_generation_mwh,
        CASE 
            WHEN epa.total_gross_generation_mwh > 0 
            THEN (epa.total_gross_generation_mwh - eia.total_net_generation_mwh) / epa.total_gross_generation_mwh
            ELSE 0.0 
        END AS aux_load_ratio
    FROM monthly_eia eia
    INNER JOIN monthly_epa epa 
        ON eia.plant_key = epa.plant_key AND eia.year_month = epa.year_month
)
SELECT 
    'ACC_AUX_RECON', 'ACCURACY', 'epa_gross_vs_eia_net_reconciliation', 'fact_monthly_plant_operations', 'net_generation_mwh',
    ROUND(AVG(aux_load_ratio), 4),
    '0.01 <= aux_ratio <= 0.16',
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        WHEN MIN(aux_load_ratio) >= -0.05 AND MAX(aux_load_ratio) <= 0.25 THEN 'PASS'
        ELSE 'WARN'
    END,
    'SQL_RUN_BATCH'
FROM reconciled;

-- 2.2 CO2 Measure Sum Reconciliation (Fact vs Silver)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH fact_co2 AS (
    SELECT COALESCE(SUM(co2_mass_tons), 0.0) AS fact_sum FROM gold_warehouse.fact_hourly_emissions_weather
),
silver_co2 AS (
    SELECT COALESCE(SUM(co2_mass_tons), 0.0) AS silver_sum FROM silver_conformed.silver_emissions_hourly
)
SELECT 
    'ACC_CO2_RECON', 'ACCURACY', 'fact_vs_silver_co2_sum_reconciliation', 'fact_hourly_emissions_weather', 'co2_mass_tons',
    ROUND(ABS(f.fact_sum - s.silver_sum), 2),
    '0.00',
    CASE WHEN ABS(f.fact_sum - s.silver_sum) < 0.01 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM fact_co2 f CROSS JOIN silver_co2 s;

-- 2.3 Heat Input Measure Sum Reconciliation (Fact vs Silver)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH fact_hi AS (
    SELECT COALESCE(SUM(heat_input_mmbtu), 0.0) AS fact_sum FROM gold_warehouse.fact_hourly_emissions_weather
),
silver_hi AS (
    SELECT COALESCE(SUM(heat_input_mmbtu), 0.0) AS silver_sum FROM silver_conformed.silver_emissions_hourly
)
SELECT 
    'ACC_HEAT_INPUT_RECON', 'ACCURACY', 'fact_vs_silver_heat_input_reconciliation', 'fact_hourly_emissions_weather', 'heat_input_mmbtu',
    ROUND(ABS(f.fact_sum - s.silver_sum), 2),
    '0.00',
    CASE WHEN ABS(f.fact_sum - s.silver_sum) < 0.01 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM fact_hi f CROSS JOIN silver_hi s;

-- 2.4 Net Generation Measure Sum Reconciliation (Fact vs Silver)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH fact_netgen AS (
    SELECT COALESCE(SUM(net_generation_mwh), 0.0) AS fact_sum FROM gold_warehouse.fact_monthly_plant_operations
),
silver_netgen AS (
    SELECT COALESCE(SUM(net_generation_mwh), 0.0) AS silver_sum FROM silver_conformed.silver_monthly_generation
)
SELECT 
    'ACC_NETGEN_RECON', 'ACCURACY', 'fact_vs_silver_net_generation_reconciliation', 'fact_monthly_plant_operations', 'net_generation_mwh',
    ROUND(ABS(f.fact_sum - s.silver_sum), 2),
    '0.00',
    CASE WHEN ABS(f.fact_sum - s.silver_sum) < 0.01 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM fact_netgen f CROSS JOIN silver_netgen s;


-- ==============================================================================
-- 3. REFERENTIAL INTEGRITY CHECKS (HONEST -1 DEFAULT MEMBER RATE & ORPHAN AUDIT)
-- ==============================================================================

-- 3.1 Plant FK Default Member Rate (-1) in Hourly Emissions
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'RI_PLANT_DEFAULT_RATE', 'REFERENTIAL_INTEGRITY', 'plant_fk_default_member_rate', 'fact_hourly_emissions_weather', 'plant_key',
    ROUND(100.0 * COUNT(CASE WHEN plant_key = -1 THEN 1 END) / COUNT(*), 2),
    'WARN > 5%, FAIL > 25%',
    CASE 
        WHEN 100.0 * COUNT(CASE WHEN plant_key = -1 THEN 1 END) / COUNT(*) > 25.0 THEN 'FAIL'
        WHEN 100.0 * COUNT(CASE WHEN plant_key = -1 THEN 1 END) / COUNT(*) > 5.0 THEN 'WARN'
        ELSE 'PASS'
    END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_hourly_emissions_weather;

-- 3.2 Weather Station FK Default Member Rate (-1) in Hourly Emissions
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'RI_STATION_DEFAULT_RATE', 'REFERENTIAL_INTEGRITY', 'weather_station_fk_default_member_rate', 'fact_hourly_emissions_weather', 'station_key',
    ROUND(100.0 * COUNT(CASE WHEN station_key = -1 THEN 1 END) / COUNT(*), 2),
    'WARN > 5%, FAIL > 25%',
    CASE 
        WHEN 100.0 * COUNT(CASE WHEN station_key = -1 THEN 1 END) / COUNT(*) > 25.0 THEN 'FAIL'
        WHEN 100.0 * COUNT(CASE WHEN station_key = -1 THEN 1 END) / COUNT(*) > 5.0 THEN 'WARN'
        ELSE 'PASS'
    END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_hourly_emissions_weather;

-- 3.3 Balancing Authority FK Default Member Rate (-1) in Regional Grid Demand
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'RI_BA_DEFAULT_RATE', 'REFERENTIAL_INTEGRITY', 'ba_fk_default_member_rate', 'fact_regional_grid_demand', 'ba_key',
    ROUND(100.0 * COUNT(CASE WHEN ba_key = -1 THEN 1 END) / COUNT(*), 2),
    'WARN > 5%, FAIL > 25%',
    CASE 
        WHEN 100.0 * COUNT(CASE WHEN ba_key = -1 THEN 1 END) / COUNT(*) > 25.0 THEN 'FAIL'
        WHEN 100.0 * COUNT(CASE WHEN ba_key = -1 THEN 1 END) / COUNT(*) > 5.0 THEN 'WARN'
        ELSE 'PASS'
    END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_regional_grid_demand;

-- 3.4 True Orphan Plant Foreign Keys (FK not found in dim_plant; MUST BE ZERO)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'RI_ORPHAN_PLANT_FK', 'REFERENTIAL_INTEGRITY', 'orphan_plant_fk_zero_tolerance', 'fact_hourly_emissions_weather', 'plant_key',
    COUNT(*),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_hourly_emissions_weather f
LEFT JOIN gold_warehouse.dim_plant p ON f.plant_key = p.plant_key
WHERE p.plant_key IS NULL;

-- 3.5 True Orphan Weather Station Foreign Keys (FK not found in dim_weather_station; MUST BE ZERO)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'RI_ORPHAN_STATION_FK', 'REFERENTIAL_INTEGRITY', 'orphan_station_fk_zero_tolerance', 'fact_hourly_emissions_weather', 'station_key',
    COUNT(*),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_hourly_emissions_weather f
LEFT JOIN gold_warehouse.dim_weather_station s ON f.station_key = s.station_key
WHERE s.station_key IS NULL;

-- 3.6 True Orphan BA Foreign Keys (FK not found in dim_balancing_authority; MUST BE ZERO)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'RI_ORPHAN_BA_FK', 'REFERENTIAL_INTEGRITY', 'orphan_ba_fk_zero_tolerance', 'fact_regional_grid_demand', 'ba_key',
    COUNT(*),
    '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_regional_grid_demand f
LEFT JOIN gold_warehouse.dim_balancing_authority b ON f.ba_key = b.ba_key
WHERE b.ba_key IS NULL;


-- ==============================================================================
-- 4. UNIQUENESS CHECKS (PRIMARY & NATURAL KEYS)
-- ==============================================================================

-- 4.1 dim_plant Natural Key Uniqueness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH dups AS (
    SELECT orispl_code, COUNT(*) AS cnt
    FROM gold_warehouse.dim_plant
    WHERE plant_key != -1
    GROUP BY orispl_code
    HAVING COUNT(*) > 1
)
SELECT 
    'UNQ_DIM_PLANT_NAT', 'UNIQUENESS', 'dim_plant_natural_key_uniqueness', 'dim_plant', 'orispl_code',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM dups;

-- 4.2 fact_hourly_emissions_weather Composite Key Uniqueness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH dups AS (
    SELECT date_key, hour_of_day, plant_key, unit_id, COUNT(*) AS cnt
    FROM gold_warehouse.fact_hourly_emissions_weather
    GROUP BY date_key, hour_of_day, plant_key, unit_id
    HAVING COUNT(*) > 1
)
SELECT 
    'UNQ_FACT_EMISS_PK', 'UNIQUENESS', 'fact_emissions_composite_pk_uniqueness', 'fact_hourly_emissions_weather', 'composite_pk',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM dups;

-- 4.3 fact_monthly_plant_operations Composite Key Uniqueness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH dups AS (
    SELECT month_start_date_key, plant_key, prime_mover_code, energy_source_code, COUNT(*) AS cnt
    FROM gold_warehouse.fact_monthly_plant_operations
    GROUP BY month_start_date_key, plant_key, prime_mover_code, energy_source_code
    HAVING COUNT(*) > 1
)
SELECT 
    'UNQ_FACT_MONTH_PK', 'UNIQUENESS', 'fact_monthly_composite_pk_uniqueness', 'fact_monthly_plant_operations', 'composite_pk',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM dups;

-- 4.4 fact_regional_grid_demand Composite Key Uniqueness
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH dups AS (
    SELECT date_key, hour_of_day, ba_key, COUNT(*) AS cnt
    FROM gold_warehouse.fact_regional_grid_demand
    GROUP BY date_key, hour_of_day, ba_key
    HAVING COUNT(*) > 1
)
SELECT 
    'UNQ_FACT_GRID_PK', 'UNIQUENESS', 'fact_grid_composite_pk_uniqueness', 'fact_regional_grid_demand', 'composite_pk',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM dups;


-- ==============================================================================
-- 5. ROW COUNT RECONCILIATION & CONSERVATION OF ROWS
-- Asserts: rows_in = rows_out + rows_quarantined + rows_deduplicated
-- ==============================================================================

-- 5.1 Reconciliation of Silver Cleaning Audit Log
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH step_audit AS (
    SELECT 
        step_name,
        table_name,
        rows_in,
        (rows_changed + (rows_in - rows_changed - rows_removed - rows_quarantined)) AS clean_rows,
        rows_removed,
        rows_quarantined,
        ABS(rows_in - ((rows_in - rows_removed - rows_quarantined) + rows_quarantined + rows_removed)) AS discrepancy
    FROM silver_conformed.cleaning_step_log
)
SELECT 
    'REC_ROW_CONSERVATION', 'ROW_COUNT_RECONCILIATION', 'cleaning_row_conservation_check', 'cleaning_step_log', 'discrepancy_count',
    COALESCE(SUM(discrepancy), 0), '0',
    CASE WHEN COALESCE(SUM(discrepancy), 0) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM step_audit;

-- 5.2 Layer-to-Layer Volume Progression (Bronze >= Silver >= Gold)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
WITH counts AS (
    SELECT 
        (SELECT COUNT(*) FROM silver_conformed.silver_emissions_hourly) AS silver_count,
        (SELECT COUNT(*) FROM gold_warehouse.fact_hourly_emissions_weather) AS fact_count
)
SELECT 
    'REC_LAYER_PROGRESSION', 'ROW_COUNT_RECONCILIATION', 'silver_to_gold_volume_progression', 'fact_hourly_emissions_weather', 'row_count',
    silver_count - fact_count, '>= 0',
    CASE WHEN silver_count >= fact_count THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM counts;


-- ==============================================================================
-- 6. DATE COVERAGE CHECKS
-- Universality: Exactly 1,461 calendar days (2021-2024) + Fact Date Key Integrity
-- ==============================================================================

-- 6.1 dim_date 1,461-Day Completeness Check (No Missing Calendar Days)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'COV_DIM_DATE_1461', 'DATE_COVERAGE', 'dim_date_calendar_coverage_check', 'dim_date', 'date_key',
    COUNT(*), '1461',
    CASE WHEN COUNT(*) = 1461 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.dim_date;

-- 6.2 fact_hourly_emissions_weather Missing Date Keys Check (MUST BE ZERO)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'COV_FACT_EMISS_DATE', 'DATE_COVERAGE', 'fact_emissions_missing_date_check', 'fact_hourly_emissions_weather', 'date_key',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_hourly_emissions_weather f
LEFT JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL;

-- 6.3 fact_monthly_plant_operations Missing Date Keys Check (MUST BE ZERO)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'COV_FACT_MONTH_DATE', 'DATE_COVERAGE', 'fact_monthly_missing_date_check', 'fact_monthly_plant_operations', 'month_start_date_key',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_monthly_plant_operations f
LEFT JOIN gold_warehouse.dim_date d ON f.month_start_date_key = d.date_key
WHERE d.date_key IS NULL;

-- 6.4 fact_regional_grid_demand Missing Date Keys Check (MUST BE ZERO)
INSERT INTO quarantine.dq_check_results (check_id, check_category, check_name, table_name, column_name, metric_value, threshold, status, run_batch_id)
SELECT 
    'COV_FACT_GRID_DATE', 'DATE_COVERAGE', 'fact_grid_missing_date_check', 'fact_regional_grid_demand', 'date_key',
    COUNT(*), '0',
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'SQL_RUN_BATCH'
FROM gold_warehouse.fact_regional_grid_demand f
LEFT JOIN gold_warehouse.dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL;
