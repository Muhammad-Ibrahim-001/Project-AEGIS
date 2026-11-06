# 01_Project_Documentation

This directory contains the foundational specifications, official deliverables, and academic guidelines for the **DL3004 Data Warehousing & Business Intelligence (DWBI)** Final Project: *U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Lakehouse / Warehouse*.

---

## Directory Overview

### 1. Official Course Deliverables (Strict University Layout)
These three primary deliverables match the exact university repository layout:
* **[`Requirements.pdf`](Requirements.pdf)**: Formal project specification, problem statement, and scope document.
* **[`Schema.pdf`](Schema.pdf)**: Visual Kimball Star Schema entity-relationship blueprint (Draw.io export).
* **[`Data_Dictionary.xlsx`](Data_Dictionary.xlsx)**: Authoritative 7-tab enterprise data catalog:
  1. `Overview & Table Index`
  2. `Bronze_Staging_Tables` (`project_staging`)
  3. `Conformed_Dimensions` (`project_dw`)
  4. `Fact_Tables` (`project_dw`)
  5. `Quarantine_and_Audit` (`quarantine`)
  6. `Reporting_Views` (`project_reporting`)
  7. `Lineage_and_Code_Lists`

### 2. Architectural Diagrams & Design Sources
* **[`Architecture.pdf`](Architecture.pdf) / [`Architecture.png`](Architecture.png)**: Visual 8-stage / 11-stage end-to-end pipeline architecture.
* **[`Schema.pdf`](Schema.pdf) / [`Schema.png`](Schema.png)**: Visual Kimball Star Schema blueprint and raster export.
* **[`schema_diagram_mermaid.md`](schema_diagram_mermaid.md)**: Verified Mermaid ERD code blocks for Draw.io (`app.diagrams.net`).
* **[`Requirements.md`](Requirements.md)**: Markdown summary linking to the formal Phase 1 proposal and deliverables in `Phase_1_Submission/`.

### 3. Subdirectories
* **[`course_requirements/`](course_requirements/) — ⚠️ MANDATORY REFERENCE:**  
  Official university syllabus, phase grading rubrics (`DWBI Lab Phase 2.pdf`, `DWBI Lab Phase 3.pdf`), and reference architecture diagram. **All code and schema implementations must adhere strictly to these rubrics.**
* **[`Team_Guides/`](Team_Guides/) — 👥 HUMAN ONBOARDING ONLY:**  
  Formatted Microsoft Word guides (`.docx`) detailing the 4-person work packages (WP1–WP4) for human team members.

