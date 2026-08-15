import os

import psycopg
from dotenv import load_dotenv


# Load private values from .env
load_dotenv()


database_url = os.getenv("DATABASE_URL")


# Make sure we actually found the connection string.
if not database_url:
    raise ValueError("DATABASE_URL was not found in the .env file")


print("Connecting to CockroachDB...")


# Connect to CockroachDB
with psycopg.connect(database_url) as connection:

    # Create a database cursor.
    with connection.cursor() as cursor:

        # Ask CockroachDB which database and user we connected as.
        cursor.execute(
            """
            SELECT
                current_database(),
                current_user,
                version();
            """
        )

        result = cursor.fetchone()


print()
print("CockroachDB connection successful!")
print()
print("Database:", result[0])
print("User:", result[1])
print("Database version:")
print(result[2])