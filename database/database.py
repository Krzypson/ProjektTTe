from sqlmodel import SQLModel, create_engine
import os
from dotenv import load_dotenv

"""db_password = os.environ.get('DB_PASSWORD')

if not db_password:
    raise ValueError("No database password set!")

print("Connecting to DB...")"""
load_dotenv()

#TEMPORARY
test_db = True
if not test_db:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set!")

    engine = create_engine(
        database_url,
        echo=True,  # Set to False in production
        connect_args={
            "ssl": {
                "ca": "./ssl/DigiCertGlobalRootG2.crt.pem"
            }
        }
    )
else:
    sqlite_file_name = "database/database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(sqlite_url, echo = False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)