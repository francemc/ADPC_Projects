import os
import time
import io
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from minio import Minio
from minio.error import S3Error
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "gene-expression-data"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

FILENAME = "TCGA_clinical_survival_data.tsv"
OBJECT_NAME = FILENAME 


def ensure_bucket(bucket_name):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' creado.")
    else:
        print(f"Bucket '{bucket_name}' already exists.")


def upload_stream_to_minio(response, bucket_name, object_name):
    try:
        data = io.BytesIO(response.content)
        size = len(response.content)
        minio_client.put_object(bucket_name, object_name, data, length=size)
        print(f"☑️ Sucessfully upload to MinIO: {bucket_name}/{object_name}")
    except S3Error as e:
        print(f" ⚠️ Error uploading to MinIO: {e}")

def scrape_xena_and_download():
    url_base = "https://xenabrowser.net/datapages/"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url_base)
    time.sleep(3)

    cohorts = driver.find_elements(By.XPATH, '//ul/li/a')
    print(f"{len(cohorts)} cohorts found.")

    tcga_cohorts = []
    for c in cohorts:
        cohort_name = c.text.strip()
        href = c.get_attribute("href")
        if cohort_name.startswith("TCGA") and href:
            full_href = href if not href.startswith("?") else url_base + href
            tcga_cohorts.append({"name": cohort_name, "href": full_href})

    print(f"{len(tcga_cohorts)} cohorts TCGA found.")

    ensure_bucket(BUCKET_NAME)

    for cohort in tcga_cohorts:
        cohort_name = cohort["name"]
        cohort_url = cohort["href"]

        print(f"⏳ Entering: {cohort_name} ")
        try:
            driver.get(cohort_url)
            time.sleep(3)

            # Buscar el enlace "IlluminaHiSeq pancan normalized"
            illumina_link = None
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for a in all_links:
                if "IlluminaHiSeq pancan normalized" in a.text:
                    illumina_link = a
            
            if not illumina_link:
                print(f" 🚫 There is not IlluminaHiSeq pancan normalized")
                continue

            illumina_href = illumina_link.get_attribute("href")
            illumina_url = illumina_href if not illumina_href.startswith("?") else url_base + illumina_href

            driver.get(illumina_url)
            time.sleep(3)

            wait = WebDriverWait(driver, 10) 
            # fin <span> with .gz 
            spans = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Datapages-module__value___3k05o")))
            gz_url = None
            for span in spans:
                inner_links = span.find_elements(By.TAG_NAME, "a")
                for l in inner_links:
                    href = l.get_attribute("href")
                    if href and href.endswith(".gz"):
                        gz_url = href
                        break
                if gz_url:
                    break

            if gz_url:
                filename = f"{cohort_name.replace(' ', '_')}_{gz_url.split('/')[-1]}"
                print(f"📥 Downloading file")

                try:
                    response = requests.get(gz_url, stream=True)
                    if response.status_code == 200:
                        upload_stream_to_minio(response, BUCKET_NAME, filename)
                    else:
                        print(f"❌ Error HTTP: {response.status_code}")
                except Exception as e:
                    print(f" ❌ Error downloanding: {e}")

            else:
                print(f" 🚫 file.gz doesnt existis in {cohort_name}")


        except Exception as e:
            print(f"⚠️ Error charging cohort {cohort_name}: {e}")

    driver.quit()

def upload_survival_file():
    ensure_bucket(BUCKET_NAME)

    if not os.path.exists(FILENAME):
        print(f"❌ '{FILENAME}'  doesn´t exist.")
        return

    try:
        with open(FILENAME, "rb") as file_data:
            file_size = os.stat(FILENAME).st_size
            minio_client.put_object(BUCKET_NAME, OBJECT_NAME, file_data, file_size)
            print(f"☑️  Sucessfully upload to MinIO:'{OBJECT_NAME}'.")
    except S3Error as e:
        print(f"❌ Error uploading to  MinIO: {e}")

def main():
    scrape_xena_and_download()
    upload_survival_file()

if __name__ == "__main__":
    main()
