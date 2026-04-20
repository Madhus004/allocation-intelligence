from app.db import create_db_and_tables
import app.models  # noqa: F401


if __name__ == "__main__":
    create_db_and_tables()
    print("Database and tables created successfully.")