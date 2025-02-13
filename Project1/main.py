import psycopg2
import json
import os
import shutil
from minio import Minio
from minio.error import S3Error
import requests

# Database connection details
DB_HOST = 'royally-beautiful-conger.data-1.use1.tembo.io'
DB_PORT = '5432'
DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = 'Os2ZoGMqD0GIoVwD'  # Use the password from Tembo

MINIO_ENDPOINT = "localhost:9000"  # Change for cloud-based MinIO
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
BUCKET_NAME = "packages"

# Establishing a connection to the PostgreSQL database
def connect_to_db():
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

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True for HTTPS
)

# Ensure the bucket exists
def ensure_bucket():
    found = minio_client.bucket_exists(BUCKET_NAME)
    if not found:
        minio_client.make_bucket(BUCKET_NAME)

# Upload package artifact to MinIO
def upload_to_minio(file_path, package_name, version):
    ensure_bucket()
    file_name = os.path.basename(file_path)
    object_name = f"{package_name}/{version}/{file_name}"
    
    try:
        minio_client.fput_object(BUCKET_NAME, object_name, file_path)
        print(f"Uploaded {file_name} to MinIO as {object_name}")
        return f"http://{MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"
    except S3Error as e:
        print(f"MinIO upload error: {e}")
        return None

# Create a new repository
def create_repository(name):
    conn = connect_to_db()
    if conn:
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
            conn.close()

# List all packages in a given repository
def list_packages(repo_name):
    conn = connect_to_db()
    if conn:
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
            conn.close()

# Publish a package (add a new package to the repository)

# Publish a package
def publish_package(directory):
    json_path = os.path.join(directory, "publish.json")

    if not os.path.exists(json_path):
        print("Error: publish.json file not found.")
        return

    with open(json_path, "r") as f:
        package_data = json.load(f)

    package_name = package_data.get("package_name")
    description = package_data.get("description")
    version = package_data.get("version")
    author = package_data.get("author")
    artifact_path = package_data.get("artifact_path")

    if not all([package_name, version, artifact_path]):
        print("Error: Missing required fields in publish.json.")
        return

    minio_url = upload_to_minio(artifact_path, package_name, version)
    if not minio_url:
        print("Error: Failed to upload artifact.")
        return

    conn = connect_to_db()
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
        conn.close()

# Validate version format (x.y.z)
def validate_version(version):
    return bool(re.match(r'^\d+\.\d+\.\d+$', version))

# Get repository ID by its name
def get_repository_id(repo_name):
    conn = connect_to_db()
    if conn:
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
            conn.close()

def info(package_name):
    conn = connect_to_db()
    if conn:
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
            conn.close()

def get_installation_path():
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'installation_path';")
            path = cursor.fetchone()
            return path[0] if path else "/usr/local/packages/"  # Default fallback
        except Exception as e:
            print("Error fetching installation path:", e)
            return "/usr/local/packages/"  # Default fallback
        finally:
            cursor.close()
            conn.close()
def install_package(package_name):
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()

            # Get latest version and MinIO URL
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

            installation_path = get_installation_path()
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
            conn.close()


def find(query):
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()

            # SQL query to search for packages
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
            conn.close()

def config():
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()

            # Fetch configuration settings
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
            conn.close()




# Main function to handle command-line arguments
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Package management system.")
    parser.add_argument('command', choices=['list', 'publish', 'info', 'install', 'find', 'config'], help="Command to run")
    parser.add_argument('param', help="Parameter for the command (e.g., repo name, package name, directory)")
    args = parser.parse_args()

    if args.command == 'list':
        list_packages(args.param)
    elif args.command == 'publish':
        publish_package(args.param)
    elif args.command == 'info':
        info(args.param)
    elif args.command == 'install':
        install(args.param)
    elif args.command == 'find':
        find(args.param)
    elif args.command == 'config':
       config

if __name__ == '__main__':
    main()
