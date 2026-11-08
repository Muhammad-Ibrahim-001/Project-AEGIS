# Phase 1 Project Execution Plan

**Project:** U.S. Bulk Power Generation, Smokestack Air Emissions, and Synoptic Weather Warehouse
**Course:** DL3004 Data Warehousing & Business Intelligence (DWBI), Fall 2026
**Institution:** FAST National University of Computer and Emerging Sciences
**Phase:** 1 (Design)

---

## 1. Team and Collaboration Model

| Member | Student ID |
| :--- | :--- |
| Muhammad Ibrahim | 24L-2602 |
| Rai Fahad Sultan | 24L-2509 |
| Muhammad Ayyan | 24L-2568 |
| Taha Imran | 24L-2560 |

The team uses a cross-functional agile model. Every member contributes to data engineering, dimensional modeling, data quality, OLAP, and Power BI reporting, and no one is limited to a single role. To keep work visible and avoid overlap:

- Work is tracked as GitHub Issues. Each issue has **one assignee** and **one reviewer** who is a different member.
- Issues are claimed at a short weekly planning session and checked in a mid-week sync.
- Every member must be able to explain the whole pipeline, so reviewers rotate across workstreams.

---

## 2. Repository Structure

The structure follows the course guideline (`DWBI Final Project Overview.pdf`) and adds a few project-specific files.

```text
DWBI-Final-Project/
├── 01_Project_Documentation/
│   ├── Requirements.pdf
│   ├── Schema.pdf
│   ├── Data_Dictionary.xlsx
│   └── course_requirements/          # Course PDFs and reference architecture
├── 02_Data/
│   ├── raw_data/                     # Downloaded EIA, EPA, NOAA files (or samples)
│   └── cleaned_data/                 # Silver output ready for bulk load
├── 03_ETL/
│   ├── staging.sql
│   ├── dimensions.sql
│   ├── facts.sql
│   ├── quality_checks.sql
│   └── 00_master_orchestrator.py
├── 04_Data_Warehouse/
│   ├── warehouse.sql
│   └── partitioning_indexes.sql
├── 05_Analytics/
│   ├── OLAP.sql
│   ├── Views.sql
│   └── performance_explain.sql
├── 06_Dashboard/
│   └── PowerBI.pbix
├── Phase_1_Submission/               # Phase 1 documents
└── README.md
```

---

## 3. Git Workflow

| Topic | Convention |
| :--- | :--- |
| Branches | `main` holds submitted, working code. `dev` is the integration branch. Work happens on `feature/<short-name>` branches created from `dev` |
| Pull requests | A feature branch merges into `dev` through a pull request that another member reviews. `dev` merges into `main` at the end of each phase |
| Commit messages | Short imperative subject with a scope, for example `etl: add EIA-923 header detection` or `dw: add dim_generator SCD2 load` |
| Tags | `phase-1-design`, `phase-2-implementation`, `phase-3-analytics` on the submitted commit |
| Large files | Raw downloads that are too large for GitHub are not committed. A download script and a short note in `02_Data/raw_data` explain how to fetch them. A small sample is committed so the pipeline can be tested |
| Secrets | Database passwords are read from environment variables or a local `.env` file that is listed in `.gitignore` |
| Reproducibility | Every table, load, and report is created by a script in the repository, so a reviewer can rebuild the warehouse from scratch |

---

## 4. Environment Setup

| Item | Setup |
| :--- | :--- |
| Database | PostgreSQL 16+ on `localhost:5432`, database `dwbi_power_grid`, managed with pgAdmin |
| Python | 3.10+ in a virtual environment; packages `pandas`, `openpyxl`, `requests`, `psycopg2` (or `sqlalchemy`) pinned in `requirements.txt` |
| BI | Microsoft Power BI Desktop connected to PostgreSQL |
| Diagrams | Draw.io for visuals; Mermaid source kept in the specification |
| Order of first run | Create schemas (`warehouse.sql`), create Bronze tables (`staging.sql`), run the orchestrator, run `quality_checks.sql`, load dimensions then facts |

---

## 5. Eight-Week Roadmap

| Week | Phase | Milestone | Main outputs |
| :-: | :-: | :--- | :--- |
| 1 | 1 | Requirements and source profiling | Business questions, source inventory, data challenges list |
| 2 | 1 | Architecture and dimensional model | Pipeline architecture, star schema, grain and bus matrix |
| 3 | 1 | Documentation and review | Data dictionary, diagrams, proposal, execution plan, team review, **Phase 1 submission** |
| 4 | 2 | Physical warehouse | Schemas and DDL for staging, dimensions, and facts; Bronze landing scripts; sample data loaded |
| 5 | 2 | ETL and data quality | Silver transformations, quarantine rules, dimension loads (SCD Type 1 and 2), audit logging |
| 6 | 2 | Fact loading and validation | Surrogate-key fact loads, completeness, accuracy, and integrity checks, cleaning report and data quality report, **Phase 2 submission** |
| 7 | 3 | Analytics and tuning | Analytical SQL, `ROLLUP` and `CUBE`, reporting views, `EXPLAIN ANALYZE` before and after indexes |
| 8 | 3 | BI and presentation | Three-page Power BI dashboard, screenshots, business insights report, final presentation, **Phase 3 submission** |

---

## 6. Deliverables and Marks by Phase

### Phase 1: Design (30%)

| Deliverable | File |
| :--- | :--- |
| Project requirements | `Requirements.pdf` (from the proposal) |
| Schema diagram | `Schema.pdf` (from `Schema_Diagram.jpg`) |
| Data dictionary | `Data_Dictionary.xlsx` |
| Architecture and design write-up | Proposal and specification documents |

### Phase 2: Implementation (40%)

| Rubric item | Marks | Evidence |
| :--- | :-: | :--- |
| Database implementation | 10 | Staging, warehouse, and reporting schema scripts |
| ETL pipeline | 15 | ETL scripts (SQL and Python), dimension load scripts, fact load scripts, data cleaning report (PDF) |
| Surrogate key implementation | 5 | `*_key` columns and business-key lookup in fact loads |
| Data quality validation | 10 | Completeness, accuracy, and integrity checks, data quality report (PDF) |

The submission also includes the GitHub repository link.

### Phase 3: Analytics and BI (30%)

| Rubric item | Marks | Evidence |
| :--- | :-: | :--- |
| Analytical SQL | 10 | Aggregations, growth query, reporting views, indexing report (PDF) |
| OLAP implementation | 5 | `ROLLUP` and `CUBE` queries |
| Dashboard | 10 | `PowerBI.pbix` and screenshots (PDF) |
| Business insights | 5 | Business insights report (PDF) and final presentation (PPT) |

---

## 7. Workstreams and Task Breakdown

| Workstream | Phase | Tasks |
| :--- | :-: | :--- |
| Source profiling | 1 | Download samples, record formats, grains, header rows, sentinels, and key overlap |
| Dimensional design | 1 | Declare grain, choose dimensions and facts, define SCD policy, draw the star schema |
| Architecture | 1 | Draw the pipeline, map it to the course reference architecture |
| Documentation | 1 | Data dictionary, proposal, execution plan, checklist, PDF exports |
| Database build | 2 | Create schemas, tables, constraints, and partitions |
| Ingestion | 2 | Extractors for Excel, JSON, CSV, and fixed-width files; header discovery; batch IDs |
| Cleaning and quality | 2 | Deduplication, null handling, text standardization, type conversion, quarantine rules, reports |
| Dimension and fact loads | 2 | Dimension loads with SCD logic; fact loads with surrogate-key lookup; reconciliation |
| Analytics | 3 | Analytical SQL, OLAP, views, index tuning |
| Dashboard and insights | 3 | Power BI model and pages, screenshots, insights report, presentation |

---

## 8. Definition of Done

A task is done when all of the following are true:

1. The script or document is committed on a feature branch and merged through a reviewed pull request.
2. SQL and Python scripts run from a clean database without manual edits.
3. Row counts, rejected-row counts, and reconciliation results are logged in `etl_run_log` or reported in the relevant report.
4. Names match the data dictionary (schemas, tables, and columns).
5. The README or the relevant document is updated if behavior changed.

---

## 9. Risks and Contingency

| Risk | Likelihood | Contingency |
| :--- | :-: | :--- |
| Source files change layout | Medium | Header discovery; keep a copy of every raw file used |
| Hourly files exceed local hardware | Medium | Restrict to selected states and date ranges; load in monthly batches |
| API limits or downtime (EIA-930, EPA CAMPD) | Medium | Download once, store in `02_Data/raw_data`, and load from the stored files |
| A member is unavailable | Medium | Shared ownership, rotating reviewers, and documented scripts |
| Phase 2 volume requirements not met | Low | Extend the date range or add states; the hourly facts are large |
| Power BI cannot reach the database | Low | Export the reporting views to CSV as a fallback data source |
