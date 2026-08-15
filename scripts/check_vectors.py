import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found in .env"
    )


with psycopg.connect(DATABASE_URL) as connection:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                column_name,
                data_type,
                udt_name
            FROM information_schema.columns
            WHERE table_name = 'memory_embeddings'
            ORDER BY ordinal_position;
            """
        )

        columns = cursor.fetchall()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM memory_embeddings;
            """
        )

        count = cursor.fetchone()[0]


print("memory_embeddings columns:")
print()

for column in columns:
    print(column)

print()
print(
    "Stored vector memories:",
    count
)