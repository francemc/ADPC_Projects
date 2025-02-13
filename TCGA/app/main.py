from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.utils.webscraper import scrape_xena_data
from app.utils.mongodb import save_gene_expression_data

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
        <html>
            <body>
                <h1>Gene Expression Data for Cancer Cohorts</h1>
                <p>Use this API to scrape and view gene expression data.</p>
            </body>
        </html>
    """

@app.get("/scrape")
def scrape_data():
    # URL of the Xena Browser cohort page to scrape
    cancer_cohort_url = 'https://xenabrowser.net/datapages/?dataset=TCGA&hub=http://xena.ucsc.edu'
    
    # Scrape gene expression data
    scrape_xena_data(cancer_cohort_url)
    
    # Optionally save to MongoDB or MinIO
    save_gene_expression_data()
    
    return {"message": "Scraping completed!"}
