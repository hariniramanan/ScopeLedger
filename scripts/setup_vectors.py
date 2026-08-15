import os

import psycopg
from dotenv import load_dotenv


# ---------------------------------------------------------
# LOAD DATABASE CONNECTION
# ---------------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL was not found in .env")


print("Connecting to CockroachDB...")


# ---------------------------------------------------------
# IMPORTANT:
# autocommit=True means each SQL statement runs on its own,
# instead of Psycopg wrapping everything in one transaction.
# ---------------------------------------------------------

with psycopg.connect(
    DATABASE_URL,
    autocommit=True
) as connection:

    with connection.cursor() as cursor:

        # -------------------------------------------------
        # ENABLE COCKROACHDB VECTOR INDEXING
        # -------------------------------------------------

        print("Enabling vector indexing...")

        cursor.execute(
            """
            SET CLUSTER SETTING
                feature.vector_index.enabled = true;
            """
        )

        print("Vector indexing enabled.")

        # -------------------------------------------------
        # CREATE SEMANTIC MEMORY TABLE
        # -------------------------------------------------

        print("Creating semantic memory table...")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_embeddings (

                id UUID PRIMARY KEY
                    DEFAULT gen_random_uuid(),

                project_id UUID NOT NULL
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                meeting_id UUID
                    REFERENCES meetings(id)
                    ON DELETE CASCADE,

                evidence_id UUID
                    REFERENCES evidence(id)
                    ON DELETE CASCADE,

                memory_type TEXT NOT NULL,

                memory_text TEXT NOT NULL,

                embedding VECTOR(256),

                embedding_model TEXT,

                created_at TIMESTAMPTZ
                    NOT NULL DEFAULT now()
            );
            """
        )

        print("Semantic memory table ready.")

        # -------------------------------------------------
        # CHECK IF VECTOR INDEX ALREADY EXISTS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT index_name
            FROM [SHOW INDEX FROM memory_embeddings]
            WHERE index_name = 'memory_embeddings_vector_idx'
            LIMIT 1;
            """
        )

        existing_index = cursor.fetchone()

        # -------------------------------------------------
        # CREATE COSINE VECTOR INDEX
        # -------------------------------------------------

        if existing_index:

            print("Vector index already exists.")

        else:

            print(
                "Creating CockroachDB cosine vector index..."
            )

            cursor.execute(
                """
                CREATE VECTOR INDEX
                    memory_embeddings_vector_idx
                ON memory_embeddings (
                    embedding vector_cosine_ops
                );
                """
            )

            print("Vector index created.")

        # -------------------------------------------------
        # VERIFY COLUMNS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_name = 'memory_embeddings'
            ORDER BY ordinal_position;
            """
        )

        columns = cursor.fetchall()

        # -------------------------------------------------
        # VERIFY INDEXES
        # -------------------------------------------------

        cursor.execute(
            """
            SHOW INDEX FROM memory_embeddings;
            """
        )

        indexes = cursor.fetchall()


# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

print()
print("=" * 60)
print("SCOPELEDGER VECTOR MEMORY SETUP")
print("=" * 60)

print()
print("memory_embeddings table ready.")

print()
print("Columns:")

for column in columns:
    print(
        "-",
        column[0],
        ":",
        column[1]
    )

print()
print("Indexes:")

index_names = set()

for index in indexes:
    index_names.add(index[1])

for index_name in sorted(index_names):
    print("-", index_name)

print()
print("=" * 60)
print("Vector memory foundation ready.")
print("=" * 60)