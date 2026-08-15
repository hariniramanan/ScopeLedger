import os

import psycopg
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found in .env"
    )


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


def vector_to_sql(vector):
    return (
        "["
        + ",".join(
            str(float(value))
            for value in vector
        )
        + "]"
    )


model = SentenceTransformer(
    MODEL_NAME
)


question = (
    "What did the client say "
    "about the launch timeline?"
)


embedding = model.encode(
    question,
    normalize_embeddings=True,
)


query_vector = vector_to_sql(
    embedding
)


with psycopg.connect(
    DATABASE_URL
) as connection:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT id
            FROM projects
            WHERE name = %s
              AND client_name = %s
            LIMIT 1;
            """,
            (
                "Website Redesign",
                "Acme Corp",
            ),
        )

        project_id = cursor.fetchone()[0]

        cursor.execute(
            """
            EXPLAIN
            SELECT
                memory_type,
                memory_text
            FROM memory_embeddings
            WHERE project_id = %s
            ORDER BY
                embedding
                <=> CAST(%s AS VECTOR(384))
            LIMIT 5;
            """,
            (
                project_id,
                query_vector,
            ),
        )

        rows = cursor.fetchall()


print()
print("=" * 70)
print("COCKROACHDB QUERY PLAN")
print("=" * 70)
print()

for row in rows:
    print(row[0])