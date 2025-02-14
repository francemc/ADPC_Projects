from sqlalchemy.orm import sessionmaker
from myapp.models import engine,Repository

# Create a session
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    # Add a test repository
    new_repo = Repository(name="TestRepo")
    session.add(new_repo)
    session.commit()  # Committing to the database

    # Check if it was added successfully
    repos = session.query(Repository).all()
    print(f"Repositories in DB: {[repo.name for repo in repos]}")

except Exception as e:
    print(f"Error: {e}")

finally:
    session.close()  # Always close the session when done
