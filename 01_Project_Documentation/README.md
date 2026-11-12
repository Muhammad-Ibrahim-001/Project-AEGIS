# 01_Project_Documentation

This directory contains the official Phase 1 deliverables, federal data source engineering specifications, and academic grading guidelines for the **DL3004 Data Warehousing & Business Intelligence (DWBI)** Final Project: *U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Lakehouse*.

---

## Directory Overview

### 1. Official Phase 1 Deliverables (`DWBI Lab Phase 1.pdf`)
1. **[`01_Project_Proposal.pdf`](01_Project_Proposal.pdf)**: 8-chapter project proposal, Medallion architecture blueprint, Kimball dimensional design, and execution roadmap.
2. **[`02_Business_Requirements_Document.pdf`](02_Business_Requirements_Document.pdf)**: Enterprise Business Requirements Document (stakeholder personas, FR1–FR12, NFR1–NFR8, SLAs, governance).
3. **[`03_10_Business_Questions.pdf`](03_10_Business_Questions.pdf)**: 12 analytical business questions (BQ1–BQ12) with mathematical metric formulas, ANSI SQL sketches, and Power BI visual mappings.
4. **[`04_Fact_and_Dimension_Identification.pdf`](04_Fact_and_Dimension_Identification.pdf)**: Kimball Dimensional Bus Matrix, 5 conformed dimensions (including `dim_generator` SCD Type 2), and 3 multi-grain fact tables.
5. **[`05_Grain_Definition_Document.pdf`](05_Grain_Definition_Document.pdf)**: Atomic grain declarations, measure additivity classification rules, and physical unit standardization.
6. **[`06_Schema_Diagrams.pdf`](06_Schema_Diagrams.pdf)**: 3-tier modeling diagrams (Conceptual Model, Logical Kimball Star Schema, and Physical Delta Lake DDL Model with Liquid Clustering).
7. **[`07_Data_Dictionary.xlsx`](07_Data_Dictionary.xlsx)**: Authoritative 7-tab enterprise data catalog:
   * `Overview & Table Index`
   * `Bronze_Staging_Tables` (`bronze_staging`)
   * `Conformed_Dimensions` (`gold_warehouse`)
   * `Fact_Tables` (`gold_warehouse`)
   * `Quarantine_and_Audit` (`quarantine`)
   * `Reporting_Views` (`gold_marts`)
   * `Lineage_and_Code_Lists`

*(Source scripts and 300-DPI diagram PNGs for Phase 1 reside in [`../archived/Phase_1_Submission/`](../archived/Phase_1_Submission/).)*

### 2. Architecture Diagrams & ETL Specifications
* **[`Architecture.pdf`](Architecture.pdf) / [`Architecture.png`](Architecture.png)**: End-to-end 8-stage pipeline architecture diagram.
* **[`DATA_SOURCES_MASTER_SPECIFICATION.md`](DATA_SOURCES_MASTER_SPECIFICATION.md)**: 633-line master technical specification for all 6 federal datasets (EIA-860/923/930, EPA CAMPD, EPA–EIA Crosswalk, NOAA ISD).
* **[`column_removal_map.md`](column_removal_map.md)**: Source-by-source Silver $\longrightarrow$ Gold column pruning reference (343 raw physical columns across 10 datasets).

### 3. Subdirectories
* **[`course_requirements/`](course_requirements/) — ⚠️ MANDATORY REFERENCE:**  
  Official university syllabus, phase grading rubrics (`DWBI Lab Phase 1.pdf`, `DWBI Lab Phase 2.pdf`, `DWBI Lab Phase 3.pdf`), and reference architecture diagram. **All code and schema implementations must adhere strictly to these rubrics.**
* **[`Team_Guides/`](Team_Guides/) — 👥 HUMAN ONBOARDING ONLY:**  
  Formatted Microsoft Word guides (`.docx`) detailing the 4-person work packages (WP1–WP4) for human team members. *(Strictly off-limits to AI agents per [`AGENTS.md`](../AGENTS.md).)*
