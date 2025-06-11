# clinical_loader.py
from pymongo import MongoClient

MONGO = {
    "uri": "mongodb://localhost:27017",
    "db": "genomics",
    "gene_collection": "gene_expression",
    "survival_collection": "survival_data",
    "merged_collection": "merged_patient_data"
}

client = MongoClient(MONGO["uri"])
db = client[MONGO["db"]]
gene_col = db[MONGO["gene_collection"]]
surv_col = db[MONGO["survival_collection"]]
merged_col = db[MONGO["merged_collection"]]

def merge_data():

    # Optional: clean previous results
    merged_col.delete_many({})

    
    total = 0
    matched = 0
    missing = 0

    # Load all gene expression docs
    for gene_doc in gene_col.find():
        full_patient_id = gene_doc["patient_id"]
        cohort = gene_doc["cancer_cohort"]
        total += 1

        patient_id = "-".join(full_patient_id.split("-")[:3])

        # Try to find matching survival data
        surv_doc = surv_col.find_one({"patient_id": patient_id})

        merged_doc = {
            "patient_id": full_patient_id,
            "cancer_cohort": cohort,
            "gene_expression": gene_doc.get("gene_expression", {})
           
        }

        if surv_doc:
            matched += 1

            # Copy relevant survival fields
            for field in ["DSS", "OS", "clinical_stage"]:
                if field in surv_doc:
                    merged_doc[field] = surv_doc[field]
            print(f"matched+")
            merged_col.insert_one(merged_doc)


        else:
            missing += 1
            print(f"[WARN] No survival data for {patient_id} in cohort '{cohort}'")


    print("✅ Merging complete. Check 'merged_patient_data' collection.")
    print(f"  Total patients:  {total}")
    print(f"  Matched survival: {matched}")
    print(f"  Missing survival: {missing}")
    print("  -> Check collection: merged_patient_data")

if __name__ == "__main__":
    merge_data()
