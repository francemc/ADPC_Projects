# 🧬 TCGA Gene Expression & Clinical Data Pipeline

This project is a complete pipeline to extract, store, process, and merge gene expression and clinical survival data from [UCSC Xena](https://xenabrowser.net/). The data is stored in **MinIO** and processed into **MongoDB** collections for further analysis or modeling.

---

## 📂 Project Structure

### `scraper.py` – Data Scraper & Uploader to MinIO

This script automates the download of **gene expression data** from UCSC Xena and uploads it to MinIO.

- Uses Selenium to:
  - Access the TCGA datasets from UCSC Xena.
  - Look for `"IlluminaHiSeq pancan normalized"` datasets.
- Downloads `.gz` files containing gene expression matrices.
- Uploads a local clinical survival file (`TCGA_clinical_survival_data.tsv`) to MinIO.
- Avoids duplicates and replaces any existing files in MinIO.
- Creates the MinIO bucket automatically if it doesn't exist.

### `processor.py` – Data Processor: MinIO → MongoDB

This script processes the files in MinIO and populates MongoDB with structured data.

#### Functionality:

- **Gene Expression Data (`.gz` files)**:
  - Extracts expression values for a predefined list of immune-related genes.
  - Transposes the expression matrix to a patient-centric structure.
  - Inserts or updates each patient’s gene data into MongoDB (`gene_expression` collection).
  - Prevents duplicates 

- **Clinical Survival Data (`.tsv` file)**:
  - Reads the survival TSV file uploaded to MinIO.
  - Validates and normalizes fields like `DSS`, `OS`, `clinical_stage`.
  - Groups by  cancer cohort.
  - Inserts or updates one document per patient into MongoDB (`survival_data` collection).

### `clinical_loader.py` – Gene + Survival Data Merger

This utility script merges already stored gene expression data with survival data in MongoDB:

- Reads all documents from:
  - `gene_expression` collection
  - `survival_data` collection
- Joins records based on `patient_id` and `cancer_cohort`
- Creates merged patient-level documents in the `merged_patient_data` collection.
- Prints detailed stats on matched vs unmatched cases.

---

## ⚙️ Technologies Used

- 🐍 Python 3
- 🧬 UCSC Xena Browser (data source)
- 🧰 Selenium (automated web scraping)
- 🗃️ MinIO (S3-compatible object storage)
- 🍃 MongoDB (NoSQL database)
- 🧪 pandas (for tabular data manipulation)

---
