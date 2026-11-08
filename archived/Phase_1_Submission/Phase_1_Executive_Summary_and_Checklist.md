# Phase 1 Executive Summary and Submission Checklist

**Project:** U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Warehouse
**Course:** DL3004 Data Warehousing & Business Intelligence (DWBI), Fall 2026
**Institution:** FAST National University of Computer and Emerging Sciences
**Team:** Muhammad Ibrahim (24L-2602), Rai Fahad Sultan (24L-2509), Muhammad Ayyan (24L-2568), Taha Imran (24L-2560)
**Phase:** 1 (Design), 30% of the project grade

---

## 1. Executive Summary

Generation, emissions, and weather data for the U.S. power sector are published by EIA, EPA, and NOAA in different formats, at different time grains, and with different missing-value conventions. This project designs a PostgreSQL data warehouse that integrates them so that management can answer questions such as which plants emit the most per unit of electricity, how weather affects plant load, and which grid regions have the highest renewable share.

**The design in one view**

| Element | Design |
| :--- | :--- |
| Sources | 6: EIA-860, EIA-923, EIA-930, EPA CAMPD, EPA-EIA crosswalk, NOAA ISD |
| Pipeline | 8 stages: sources, Python orchestration, Bronze, data quality and quarantine, Silver, warehouse, Gold, analytics and BI |
| Schemas | `project_staging`, `quarantine`, `project_dw`, `project_reporting` |
| Dimensions | 5: `dim_date`, `dim_plant`, `dim_generator` (SCD Type 2), `dim_balancing_authority`, `dim_weather_station` |
| Facts | 3: hourly emissions and weather (transactional, partitioned), monthly plant operations (periodic snapshot), hourly regional grid demand (aggregate grid) |
| Data quality | Sentinel handling, technology-specific heat rate bounds, EPA-versus-EIA reconciliation, quarantine table, ETL audit log |
| Analytics | `ROLLUP`, `CUBE`, window functions, three reporting views, `EXPLAIN ANALYZE` tuning |
| BI | Three-page Power BI dashboard: Executive Overview, Detailed Analysis, Decision Page |
| Stack | PostgreSQL, Python, Power BI Desktop, Draw.io, GitHub (all free) |

**What Phase 1 delivers.** A complete, documented design: business questions, source analysis, architecture, star schema, data dictionary, physical DDL, data quality rules, analytics plan, and project plan. Phase 2 builds and loads it, and Phase 3 analyzes it.

---

## 2. Phase 1 Deliverables Checklist

The course's suggested repository (`DWBI Final Project Overview.pdf`) lists three documents for `01_Project_Documentation`: Requirements, Schema, and the Data Dictionary.

### 2.1 Required by the course

- [x] **`Requirements.pdf`**: generated and verified in both `01_Project_Documentation/` and `Phase_1_Submission/`.
- [x] **`Schema.pdf`**: generated and verified in both `01_Project_Documentation/` and `Phase_1_Submission/`.
- [x] **`Data_Dictionary.xlsx`**: complete 7-tab enterprise Excel catalog (Overview & Index, Bronze Staging, Conformed Dimensions, Fact Tables, Quarantine & Audit, Reporting Views, Lineage & Code Lists), available in both `01_Project_Documentation/` and `Phase_1_Submission/`.

### 2.2 Design documents in this package

- [x] `Phase_1_Project_Proposal_and_Design_Document.md`: 8-chapter proposal with abstract, references, and appendices
- [x] `Phase_1_Architecture_and_Schema_Specification.md`: architecture, course-architecture mapping, star schema, SCD policy, validation formulas, DDL
- [x] `Phase_1_Data_Dictionary.md`: Markdown version of the data dictionary plus Bronze tables, code lists, and lineage
- [x] `Phase_1_Project_Execution_Plan.md`: team model, Git workflow, roadmap, rubric mapping, risks
- [x] `Phase_1_Executive_Summary_and_Checklist.md`: this document
- [x] `Architecture_Pipeline_Diagram.png` and `Schema_Diagram.jpg`: diagrams referenced by the documents

### 2.3 Before you submit

- [ ] Replace `[Instructor Name]` and `[Submission Date]` on the proposal title page
- [ ] Confirm the team roster and student IDs
- [ ] Push the documents to the GitHub repository and record the link
- [ ] Export the PDFs (Section 5) and open each one to check tables and images

---

## 3. Compliance Matrix

### 3.1 Course Overview Requirements

| Course requirement | Where it is addressed |
| :--- | :--- |
| Complete pipeline: source systems, ingestion, staging, cleaning and transformation, warehouse, OLAP, BI, decisions | Proposal Chapter 4; Specification Section 2 |
| Real-world business scenario with business questions | Proposal Chapter 2 |
| Free technology stack (PostgreSQL, pgAdmin, Python and pandas, Power BI Desktop, Draw.io, GitHub) | Proposal Section 4.2; Specification Section 2.2 |
| Reproducible SQL and scripts | Execution Plan Sections 3 and 4 |
| Suggested repository structure | Execution Plan Section 2 |
| Timeline and marks (30, 40, 30) | Proposal Section 8.1; Execution Plan Sections 5 and 6 |
| Requirements, Schema, and Data Dictionary in `01_Project_Documentation` | Section 2.1 of this document |
| Reference architecture (11 components) | Specification Section 3 |

### 3.2 Readiness for Phase 2 (Implementation, 40%)

| Phase 2 item | Design support |
| :--- | :--- |
| Dimension records 100+, fact records 10,000+ | Proposal Section 3.4 |
| Schemas `project_staging`, `project_dw`, `project_reporting` | Specification Sections 7 and 9 |
| Staging tables for each source | Data Dictionary Section 2; Specification Section 9.1 |
| Remove duplicates, handle nulls, standardize text, convert types | Proposal Section 6.1 |
| Dimensions with surrogate keys | Specification Section 5.1; Data Dictionary Section 7 |
| Fact loading through business key to surrogate key lookup | Proposal Section 6.2 |
| Completeness, accuracy, and integrity checks | Proposal Section 6.3; Specification Section 8 |

### 3.3 Readiness for Phase 3 (Analytics and BI, 30%)

| Phase 3 item | Design support |
| :--- | :--- |
| Aggregations and month-over-month growth | Proposal Section 7.1 |
| `ROLLUP` and `CUBE` | Proposal Section 7.1 |
| Reporting views (`vw_`) | Proposal Section 7.2; Data Dictionary Section 6 |
| `EXPLAIN ANALYZE` before and after indexes | Proposal Section 7.3 |
| Three-page dashboard ending in a decision | Proposal Section 7.4 |

---

## 4. Consistency Checks Before Submission

Tick these off while reading the final files:

- [ ] Schema names are `project_staging`, `quarantine`, `project_dw`, and `project_reporting` in every script and document
- [ ] Table and column names in the DDL match the data dictionary and the schema diagram
- [ ] The diagrams match the text (five dimensions, three facts, eight pipeline stages)
- [ ] Every figure and table renders in the exported PDF, with no cut-off columns
- [ ] The title page shows the correct names, IDs, course, instructor, and date
- [ ] References are listed in alphabetical order and each cited source appears in the list

---

## 5. Export Guide (Markdown to Word and PDF)

Run the commands from inside the `Phase_1_Submission` folder so that the image links resolve.

**Word (recommended for the proposal)**

```bash
pandoc Phase_1_Project_Proposal_and_Design_Document.md -o Phase_1_Project_Proposal_and_Design_Document.docx --toc --resource-path=.
```

Open the `.docx` in Word and apply APA 7 student-paper formatting: 12-pt Times New Roman, double-spaced body text, 1-inch margins, page numbers in the header, and a title page. Then use *File, Export, Create PDF/XPS*.

**PDF directly (needs a LaTeX engine such as MiKTeX or TeX Live)**

```bash
pandoc Phase_1_Architecture_and_Schema_Specification.md -o Phase_1_Architecture_and_Schema_Specification.pdf --pdf-engine=xelatex --resource-path=.
```

Wide tables can overflow in LaTeX. If that happens, use the Word route.

**Mermaid diagrams.** The Mermaid blocks render on GitHub and in VS Code, but not in pandoc output. The exported documents show the PNG and JPG figures, so the diagrams appear in the PDF either way.

**Naming.** Rename or copy the final files to the names the course expects: `Requirements.pdf`, `Schema.pdf`, and `Data_Dictionary.xlsx`.
