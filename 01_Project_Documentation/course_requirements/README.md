# Course Requirements & Reference Specifications

This folder contains the official university course specifications and architecture blueprints for **DL3004 Data Warehousing & Business Intelligence (DWBI)**:

1. **`DWBI Final Project Overview.pdf`:**  
   Overall project introduction, timeline (Weeks 1–8), 3 phases, zero-cost local technology stack (PostgreSQL, Python, Power BI Desktop), and repository structure guidelines.
2. **`DWBI Lab Phase 2.pdf` (Phase 2: 40% Marks):**  
   Detailed rubric for physical DW implementation & ETL pipeline:
   * Minimum data volume: **100+ dimension rows**, **10,000+ fact rows**.
   * Exact PostgreSQL schemas required: `project_staging`, `project_dw`, `project_reporting`.
   * Staging transformations: deduplication, null-handling, text standardization, data type conversions.
   * Surrogate key implementation (`dim_xxx_key`) and business-key lookup mapping.
   * Data quality checks: Completeness, Accuracy, and Referential Integrity.
3. **`DWBI Lab Phase 3.pdf` (Phase 3: 30% Marks):**  
   Detailed rubric for OLAP, Query Optimization & BI:
   * Analytical SQL queries (`SUM`, `AVG`, `COUNT`, month-over-month growth).
   * Multi-dimensional OLAP queries (`ROLLUP` and `CUBE`).
   * Reporting Views (`vw_xxx`).
   * Performance optimization: `EXPLAIN ANALYZE` before & after index creation.
   * 3-Page Power BI Dashboard (`PowerBI.pbix`): Executive Overview, Detailed Analysis, and Business Decision Page.
4. **`Sample Project Architecture Diagram.png`:**  
   The official 11-stage end-to-end architecture flowchart (Bronze $\to$ Data Quality/Quarantine $\to$ Silver $\to$ Kimball Star Schema $\to$ Gold Marts $\to$ Power BI $\to$ Audit & Lineage).

