import os
import json
import shutil
import requests
import psycopg2
from minio import Minio
from minio.error import S3Error
import re
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
def load_dotenv_variables():
    load_dotenv()  # This loads variables from .env to the environment

    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DATABASE_URL = os.getenv('DATABASE_URL')

    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    BUCKET_NAME = os.getenv('BUCKET_NAME')

    print(f"MINIO_ENDPOINT: {MINIO_ENDPOINT}")
    print(f"MINIO_ACCESS_KEY: {MINIO_ACCESS_KEY}")
    print(f"MINIO_SECRET_KEY: {MINIO_SECRET_KEY}")
    print(f"BUCKET_NAME: {BUCKET_NAME}")

    return {
        'DB_HOST': DB_HOST,
        'DB_PORT': DB_PORT,
        'DB_NAME': DB_NAME,
        'DB_USER': DB_USER,
        'DB_PASSWORD': DB_PASSWORD,
        'DATABASE_URL': DATABASE_URL,
        'MINIO_ENDPOINT': MINIO_ENDPOINT,
        'MINIO_ACCESS_KEY': MINIO_ACCESS_KEY,
        'MINIO_SECRET_KEY': MINIO_SECRET_KEY,
        'BUCKET_NAME': BUCKET_NAME,
    }

# Establish a connection to the PostgreSQL database
def connect_to_db(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        return None

# MinIO Client Setup
def get_minio_client(config):
    return Minio(
        config['MINIO_ENDPOINT'],
        access_key=config['MINIO_ACCESS_KEY'],
        secret_key=config['MINIO_SECRET_KEY'],
        secure=False  # Set to True for HTTPS
    )

# Ensure the bucket exists in MinIO
def ensure_bucket(minio_client, BUCKET_NAME):
    found = minio_client.bucket_exists(BUCKET_NAME)
    if not found:
        minio_client.make_bucket(BUCKET_NAME)

def upload_to_minio(minio_client, artifact_path, package_name, version, BUCKET_NAME, config):
    ensure_bucket(minio_client, BUCKET_NAME)
    file_name = os.path.basename(artifact_path)
    object_name = f"{package_name}/{version}/{file_name}"
    
    try:
        minio_client.fput_object(BUCKET_NAME, object_name, artifact_path)
        print(f"Uploaded {file_name} to MinIO as {object_name}")
        return f"http://{config['MINIO_ENDPOINT']}/{BUCKET_NAME}/{object_name}"  # URL del archivo en MinIO
    except S3Error as e:
        print(f"MinIO upload error: {e}")
        return None



# Create a new repository in the database
def create_repository(conn, name):
    try:
        cursor = conn.cursor()
        query = "INSERT INTO repositories (name) VALUES (%s) RETURNING id;"
        cursor.execute(query, (name,))
        repo_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Repository '{name}' created with ID {repo_id}.")
    except Exception as e:
        print("Error creating repository:", e)
    finally:
        cursor.close()

# List all packages in a repository
def list_packages(conn, repo_name):
    try:
        cursor = conn.cursor()
        query = """
            SELECT p.name, p.version
            FROM packages p
            JOIN repositories r ON p.repository_id = r.id
            WHERE r.name = %s;
        """
        cursor.execute(query, (repo_name,))
        packages = cursor.fetchall()

        if packages:
            print(f"Packages in repository '{repo_name}':")
            for package in packages:
                print(f"{package[0]} - Version: {package[1]}")
        else:
            print(f"No packages found in repository '{repo_name}'.")
    except Exception as e:
        print("Error listing packages:", e)
    finally:
        cursor.close()

def publish_package(conn, directory, minio_client, BUCKET_NAME, config):
    json_path = os.path.join(directory, "publish.json")
    if not os.path.exists(json_path):
        print("Error: publish.json file not found.")
        return

    try:
        with open(json_path, "r") as f:
            package_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading publish.json: {e}")
        return

    package_name = package_data.get("package_name")
    description = package_data.get("description")
    version = package_data.get("version")
    author = package_data.get("author")
    artifact_path = package_data.get("artifact_path")

    if not all([package_name, version, artifact_path]):
        print("Error: Missing required fields in publish.json.")
        return

    minio_url = upload_to_minio(minio_client, artifact_path, package_name, version, BUCKET_NAME, config)
    if not minio_url:
        print("Error: Failed to upload artifact.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO packages (name, description, version, author, minio_url)
               VALUES (%s, %s, %s, %s, %s)""",
            (package_name, description, version, author, minio_url)
        )
        conn.commit()
        print(f"Package {package_name} (v{version}) published successfully!")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()

# Validate version format (x.y.z)
def validate_version(version):
    return bool(re.match(r'^\d+\.\d+\.\d+$', version))

# Get repository ID by its name
def get_repository_id(conn, repo_name):
    try:
        cursor = conn.cursor()
        query = "SELECT id FROM repositories WHERE name = %s;"
        cursor.execute(query, (repo_name,))
        repo_id = cursor.fetchone()
        if repo_id:
            return repo_id[0]
        else:
            return None
    except Exception as e:
        print("Error fetching repository ID:", e)
    finally:
        cursor.close()

# Get package information
def info(conn, package_name):
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, name, version, description, author, created_at
            FROM packages
            WHERE name = %s
            ORDER BY created_at DESC;
        """
        cursor.execute(query, (package_name,))
        package_versions = cursor.fetchall()

        if not package_versions:
            print(f"No package found with name '{package_name}'.")
            return

        print(f"Package: {package_name}")
        print("=" * 40)

        for package in package_versions:
            package_id, name, version, description, author, created_at = package
            print(f"Version: {version}")
            print(f"Description: {description}")
            print(f"Author: {author}")
            print(f"Created At: {created_at}")

            # Get dependencies
            query_dependencies = """
                SELECT p2.name, p2.version
                FROM dependencies d
                JOIN packages p2 ON d.dependent_package_id = p2.id
                WHERE d.package_id = %s;
            """
            cursor.execute(query_dependencies, (package_id,))
            dependencies = cursor.fetchall()

            if dependencies:
                print("Dependencies:")
                for dep_name, dep_version in dependencies:
                    print(f"  - {dep_name} (Version: {dep_version})")
            else:
                print("Dependencies: None")

            print("-" * 40)
    except Exception as e:
        print("Error fetching package info:", e)
    finally:
        cursor.close()

# Install a package
def install(conn, package_name, installation_path, minio_client, BUCKET_NAME):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT name, version, minio_url FROM packages 
               WHERE name = %s ORDER BY version DESC LIMIT 1""",
            (package_name,)
        )
        package = cursor.fetchone()

        if not package:
            print(f"No package found with name '{package_name}'.")
            return

        name, version, minio_url = package

        if not minio_url:
            print(f"No MinIO artifact found for {name} v{version}.")
            return

        os.makedirs(installation_path, exist_ok=True)

        # Download the file from MinIO
        local_file = os.path.join(installation_path, os.path.basename(minio_url))
        with requests.get(minio_url, stream=True) as r:
            with open(local_file, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        print(f"Package '{name}' (version {version}) installed successfully at {local_file}")
    except Exception as e:
        print("Error installing package:", e)
    finally:
        cursor.close()

# Find packages
def find(conn, query):
    try:
        cursor = conn.cursor()
        query_find = """
            SELECT name, MAX(version) AS latest_version
            FROM packages
            WHERE name ILIKE %s
            GROUP BY name
            ORDER BY name;
        """
        cursor.execute(query_find, (f"%{query}%",))
        results = cursor.fetchall()

        if not results:
            print(f"No packages found matching '{query}'.")
            return

        print("Matching Packages:")
        print("=" * 30)
        for name, version in results:
            print(f"{name} (Latest Version: {version})")
    except Exception as e:
        print("Error finding package:", e)
    finally:
        cursor.close()

# Get configuration settings
def config(conn):
    try:
        cursor = conn.cursor()
        query_config = "SELECT key, value FROM config;"
        cursor.execute(query_config)
        results = cursor.fetchall()

        if not results:
            print("No configuration settings found.")
            return

        print("Current Configuration:")
        print("=" * 30)
        for key, value in results:
            print(f"{key}: {value}")
    except Exception as e:
        print("Error retrieving configuration:", e)
    finally:
        cursor.close()

# Main function to handle command-line arguments
def main():
    print("Starting script execution...")

    # Load environment variables
    config = load_dotenv_variables()

    # Get database connection details
    DB_HOST = config['DB_HOST']
    DB_PORT = config['DB_PORT']
    DB_NAME = config['DB_NAME']
    DB_USER = config['DB_USER']
    DB_PASSWORD = config['DB_PASSWORD']
    
    # Connect to database
    conn = connect_to_db(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    print("Connection ok")

    # Initialize MinIO client
    minio_client = get_minio_client(config)

    # Asking for user input to choose a command
    print("\nPlease choose a command to execute:")
    print("1. Publish a package")
    print("2. List packages")
    print("3. Show package info")
    print("4. Find packages")
    print("5. Install a package")
    print("6. Create a repository")

    # User input for selecting command
    command = input("Enter the number of the command you want to execute: ")

    # Handle commands based on user input
    if command == "1":
        # Ask for additional parameters for 'publish'
        directory = input("Enter the directory containing publish.json: ")
        publish_package(conn, directory, minio_client, config['BUCKET_NAME'],config)
    
    elif command == "2":
        # Ask for repository name to list packages
        repo_name = input("Enter the repository name: ")
        list_packages(conn, repo_name)
    
    elif command == "3":
        # Ask for package name to show info
        package_name = input("Enter the package name: ")
        info(conn, package_name)
    
    elif command == "4":
        # Ask for search query to find packages
        query = input("Enter your search query: ")
        find(conn, query)
    
    elif command == "5":
        # Ask for package name and installation path to install
        package_name = input("Enter the package name to install: ")
        installation_path = input("Enter the installation path: ")
        install(conn, package_name, installation_path, minio_client, config['BUCKET_NAME'])
    
    elif command == "6":
        # Ask for repository name to create it
        repo_name = input("Enter the repository name: ")
        create_repository(conn, repo_name)
    
    else:
        print("Invalid command choice!")

    # Close database connection
    conn.close()

if __name__ == "__main__":
    main()
