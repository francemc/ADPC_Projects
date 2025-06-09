# processor.py
import io
import gzip
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
    "collection": "gene_expression"
}

# Connections
minio_client = Minio(
    MINIO["endpoint"],
    access_key=MINIO["access_key"],
    secret_key=MINIO["secret_key"],
    secure=False
)

mongo_client = MongoClient(MONGO["uri"])
mongo_col = mongo_client[MONGO["db"]][MONGO["collection"]]

def process():
    for obj in minio_client.list_objects(MINIO["bucket"], recursive=True):
        if not obj.object_name.endswith(".gz"):
            continue

        cohort = obj.object_name.split("_")[0]
        print(f"Loading {obj.object_name}...")

        response = minio_client.get_object(MINIO["bucket"], obj.object_name)
        with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
            df = pd.read_csv(gz, sep="\t", index_col=0)

        df = df[df.index.isin(GENES)].transpose()

        docs = []
        for patient_id, row in df.iterrows():
            # Evita duplicados antes de insertar
            if mongo_col.find_one({"patient_id": patient_id, "cancer_cohort": cohort}):
                continue  # ya existe, lo salta

            docs.append({
                "patient_id": patient_id,
                "cancer_cohort": cohort,
                "gene_expression": row.dropna().to_dict()
            })

        if docs:
            mongo_col.insert_many(docs)
            print(f" {len(docs)} registros insertados.")
        else:
            print("⚠ No se encontraron datos válidos.")

if __name__ == "__main__":
    process()
