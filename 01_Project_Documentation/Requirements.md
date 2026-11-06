# DL3004 DWBI Project Requirements & Formal Specification

> **Official Phase 1 Deliverables Location:**  
> The complete academic Phase 1 proposal and design artifacts conforming to APA 7th Edition are located in the [Phase_1_Submission/](../Phase_1_Submission/) directory:
> 1. [Phase_1_Project_Proposal_and_Design_Document.md](../Phase_1_Submission/Phase_1_Project_Proposal_and_Design_Document.md) – The master 8-chapter academic project proposal.
> 2. [Data_Dictionary.xlsx](../Phase_1_Submission/Data_Dictionary.xlsx) – Authoritative multi-tab Excel data dictionary (4 schemas).
> 3. [Phase_1_Data_Dictionary.md](../Phase_1_Submission/Phase_1_Data_Dictionary.md) – Formatted markdown data dictionary specification.
> 4. [Architecture_Pipeline_Diagram.png](../Phase_1_Submission/Architecture_Pipeline_Diagram.png) – Visual 8-stage pipeline architecture flowchart.
> 5. [Schema_Diagram.jpg](../Phase_1_Submission/Schema_Diagram.jpg) – Visual Kimball Star Schema entity-relationship blueprint.
> 6. [Phase_1_Architecture_and_Schema_Specification.md](../Phase_1_Submission/Phase_1_Architecture_and_Schema_Specification.md) – 11-stage pipeline blueprint, validation formulas, and DDL.
> 7. [Phase_1_Project_Execution_Plan.md](../Phase_1_Submission/Phase_1_Project_Execution_Plan.md) – Team collaboration framework, Git workflow, and 8-week roadmap.
> 8. [Phase_1_Executive_Summary_and_Checklist.md](../Phase_1_Submission/Phase_1_Executive_Summary_and_Checklist.md) – Compliance audit matrix and docx/pdf export guide.

---

## 1. Project Title and Metadata
* **Project Name:** U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Lakehouse / Warehouse
* **Course:** DL3004 Data Warehousing & Business Intelligence (DWBI)
* **Institution:** FAST National University of Computer and Emerging Sciences
* **Academic Term:** Fall 2026

## 2. Project Team Members & Collaborative Structure
* **Muhammad Ibrahim [24L-2602]**
* **Rai Fahad Sultan [24L-2509]**
* **Muhammad Ayyan [24L-2568]**
* **Taha Imran [24L-2560]**

*Collaboration Model:* Cross-functional agile collaboration. All members participate equally and flexibly across all data engineering, dimensional modeling, data quality, OLAP, and Power BI reporting tasks without rigid role boundaries.

## 3. Technology Stack (Databricks Serverless Cloud Lakehouse)
* **Lakehouse Platform:** Databricks Serverless Compute (Photon Engine) + Databricks SQL Warehouse.
* **Storage & Governance:** Delta Lake + Unity Catalog (`dwbi_catalog` schemas: `bronze_staging`, `silver_conformed`, `gold_warehouse`, `gold_marts`, `quarantine`).
* **ETL & Data Engineering:** Apache Spark / PySpark & Databricks SQL (Delta `MERGE INTO`).
* **Visualization & BI:** Microsoft Power BI Desktop (`PowerBI.pbix` via Native Databricks DirectQuery).
* **Modeling & Architecture:** Draw.io & Markdown.

## 4. Summary of Data Sources
* **EIA-860:** Generator asset inventory and boiler-generator environmental associations.
* **EIA-923:** Monthly net electrical generation, fuel consumed, and thermal heat rates.
* **EIA-930:** Hourly regional grid electrical demand and fuel mix telemetry.
* **EPA CAMPD:** Continuous Emission Monitoring System (CEMS) gross MW, heat input, $\text{SO}_2, \text{NO}_x, \text{CO}_2$ emissions.
* **EPA-EIA Crosswalk:** Official federal bipartite crosswalk bridging boilers to generators.
* **NOAA ISD:** Hourly synoptic surface weather observations (ambient temperature, wind speed).

