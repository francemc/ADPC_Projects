import requests
from bs4 import BeautifulSoup

# Function to scrape gene expression data
def scrape_xena_data(cancer_cohort_url):
    # Send HTTP request to the Xena Browser
    response = requests.get(cancer_cohort_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the file links for IlluminaHiSeq pancan normalized gene expression data
    file_links = []
    for link in soup.find_all('a', href=True):
        if 'IlluminaHiSeq' in link['href']:
            file_links.append(link['href'])
    
    # Optionally: download the files and save them to MinIO or another storage system
    for file_link in file_links:
        download_and_save(file_link)

def download_and_save(file_link):
    # Here you can implement downloading the file from file_link
    print(f"Downloading {file_link}")
    # You can download and save files using MinIO or other storage
