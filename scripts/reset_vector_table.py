import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found in .env"
    )


print("Connecting to CockroachDB...")


with psycopg.connect(
    DATABASE_URL,
    autocommit=True,
) as connection:

    with connection.cursor() as cursor:

        print(
            "Dropping old empty vector table..."
        )

        cursor.execute(
            """
            DROP TABLE IF EXISTS memory_embeddings;
            """
        )

        print(
            "Creating VECTOR(384) table..."
        )

        cursor.execute(
            """
            CREATE TABLE memory_embeddings (
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

                embedding VECTOR(384)
                    NOT NULL,

                embedding_model TEXT
                    NOT NULL,

                created_at TIMESTAMPTZ
                    NOT NULL DEFAULT now()
            );
            """
        )

        print(
            "Creating distributed vector index..."
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


print()
print("=" * 60)
print("VECTOR MEMORY RESET COMPLETE")
print("=" * 60)
print()
print("Embedding dimension: 384")
print(
    "Model: sentence-transformers/all-MiniLM-L6-v2"
)
print(
    "Vector index: memory_embeddings_vector_idx"
)