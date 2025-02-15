## Structure 

Project1/
│── alembic/
│   │── __pycache__/
│   │── versions/
│   │── env.py
│   │── README
│── minio-data/
│   │── .minio.sys/
│   │── format.json
│── packages/
│── publish.json
│── myapp/
│   │── __pycache__/
│   │── __init__.py
│   │── main.py
│   │── models.py

This is a console-based package management system that interacts with a PostgreSQL database and MinIO object storage to store, retrieve, and manage software packages.

### Key Functionalities
#### Environment Configuration
Loads environment variables from a .env file to configure database and MinIO settings.

#### Database Connection Management
Establishes a connection with PostgreSQL using psycopg2.
Functions handle interactions such as inserting, updating, and retrieving package and repository data.

#### MinIO Integration
Connects to a MinIO storage server to upload and retrieve package artifacts.
Ensures that the necessary buckets exist before uploading.

#### Package Management Operations
Publish a package: Reads package details from publish.json, uploads the artifact to MinIO, and saves metadata in the database.
List packages: Retrieves and displays all packages stored in a given repository.
Show package information: Fetches details about a package, including its dependencies.
Find packages: Searches for packages based on a user query.
Install a package: Downloads the latest version of a package from MinIO and saves it to the local system.

#### Repository Management

Create a repository: Adds a new repository entry to the database.
Retrieve repository details: Queries database for repository-related data.

#### Versioning and Dependencies
Uses semantic versioning (x.y.z) for package releases.
Stores and retrieves dependencies between packages.

#### User Interaction via CLI
Prompts the user to choose an action from a list of commands.
Calls the appropriate function based on user input.

#### Data Integrity and Error Handling
Ensures that connections to external services (database, MinIO) are closed properly.

#### Migration for New Column (package_tag)
If a new attribute (e.g., package_tag) needs to be added to the packages table:
Alembic (a database migration tool) can be used to modify the schema without losing existing data.
After applying the migration, publish.json and database queries should be updated to include the new field.
