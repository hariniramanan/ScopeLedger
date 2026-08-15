import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found in .env"
    )


with psycopg.connect(
    DATABASE_URL,
    autocommit=True,
) as connection:

    with connection.cursor() as cursor:

        print(
            "Creating project_id index..."
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                memory_embeddings_project_idx
            ON memory_embeddings (
                project_id
            )
            STORING (
                memory_type,
                memory_text,
                embedding
            );
            """
        )

        print(
            "Refreshing table statistics..."
        )

        cursor.execute(
            """
            ANALYZE memory_embeddings;
            """
        )


print()
print("Vector demo indexes ready.")