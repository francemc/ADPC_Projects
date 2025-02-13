from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['tcga_db']
collection = db['gene_expression_data']

# Function to save gene expression data to MongoDB
def save_gene_expression_data():
    # You can add logic here to format the scraped data and insert it into MongoDB
    data = {
        "patient_id": "TCGA-XX-XXXX",
        "cancer_cohort": "TCGA-COHORT-01",
        "gene_expression": {
            "C6orf150": 123.45,
            "CCL5": 67.89,
            # other genes...
        }
    }
    
    collection.insert_one(data)
    print("Gene expression data saved to MongoDB!")
