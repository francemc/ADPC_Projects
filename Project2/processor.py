# processor.py
import io
import gzip
import re
import pandas as pd
from pymongo import MongoClient
from minio import Minio

# Settings
GENES = [
    "C6orf150", "CCL5", "CXCL10", "TMEM173", "CXCL9", "CXCL11",
    "NFKB1", "IKBKE", "IRF3", "TREX1", "ATM", "IL6", "CXCL8"
]

MINIO = {
    "endpoint": "localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "bucket": "gene-expression-data"
}

MONGO = {
    "uri": "mongodb://localhost:27017",
    "db": "genomics",
    "collection": "gene_expression",
    "survival_collection": "survival_data"
}

# Connections
minio_client = Minio(
    MINIO["endpoint"],
    access_key=MINIO["access_key"],
    secret_key=MINIO["secret_key"],
    secure=False
)

mongo_client = MongoClient(MONGO["uri"])
mongo_gene_col = mongo_client[MONGO["db"]][MONGO["collection"]]
mongo_surv_col = mongo_client[MONGO["db"]][MONGO["survival_collection"]]

def process():
    for obj in minio_client.list_objects(MINIO["bucket"], recursive=True):
        if obj.object_name.endswith(".gz"):
            

            match = re.search(r'TCGA_(.*?)_\(', obj.object_name)
            cohort = match.group(1).replace("_", " ") if match else "Unknown"
            print(f" [GENE] Loading {cohort}...")

            response = minio_client.get_object(MINIO["bucket"], obj.object_name)
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                df = pd.read_csv(gz, sep="\t", index_col=0)

            df = df[df.index.isin(GENES)].transpose()
            for patient_id, row in df.iterrows():
                doc = {
                    "patient_id": patient_id,
                    "cancer_cohort": cohort,
                    "gene_expression": row.dropna().to_dict()
                }
                mongo_gene_col.replace_one(
                    {"patient_id": patient_id, "cancer_cohort": cohort},
                    doc,
                    upsert=True
                )

         
        elif obj.object_name.endswith(".tsv"):
            print(f"[SURVIVAL] Processing file - {obj.object_name}")

            response = minio_client.get_object(MINIO["bucket"], obj.object_name)
            df = pd.read_csv(io.BytesIO(response.read()), sep="\t")


            # Normalize int values
            for col in ["DSS", "OS"]:
                if col in df.columns:
                    df[col] = df[col].fillna(0).astype(int)

            # Validation of columns
            required_columns = ["bcr_patient_barcode", "DSS", "OS", "histological_type", "clinical_stage"]
            df = df[[col for col in required_columns if col in df.columns]]
            df = df.dropna(subset=["bcr_patient_barcode", "histological_type"], how="any")

            # group by cancer type 
            grouped = df.groupby("histological_type")

            for cohort, group_df in grouped:
                inserted = 0
                for _, row in group_df.iterrows():
                    patient_id = row["bcr_patient_barcode"]

                    doc = {
                        "patient_id": patient_id,
                        "cancer_cohort": cohort,
                        "DSS": row.get("DSS", 0),
                        "OS": row.get("OS", 0),
                        "clinical_stage": row.get("clinical_stage", "[Not Available]")
                    }

                    mongo_surv_col.replace_one(
                        {"patient_id": patient_id, "cancer_cohort": cohort},
                        doc,
                        upsert=True
                    )
                    inserted += 1

                print(f"-> {inserted} survival docs for cohort {cohort}")
            else:
                    continue  
    
if __name__ == "__main__":
    process()
