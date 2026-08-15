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


print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
)


question = (
    "What did the client say "
    "about the launch timeline?"
)


print()
print("Question:")
print(question)
print()


query_embedding = model.encode(
    question,
    normalize_embeddings=True,
)

query_vector = vector_to_sql(
    query_embedding
)


print("Connecting to CockroachDB...")


with psycopg.connect(
    DATABASE_URL
) as connection:

    with connection.cursor() as cursor:

        # ---------------------------------------------
        # FIND PROJECT
        # ---------------------------------------------

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

        project = cursor.fetchone()

        if not project:
            raise ValueError(
                "Website Redesign project "
                "was not found."
            )

        project_id = project[0]

        # ---------------------------------------------
        # SEMANTIC VECTOR SEARCH
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT
                memory_type,
                memory_text,
                embedding
                    <=> CAST(%s AS VECTOR(384))
                    AS cosine_distance
            FROM memory_embeddings
            WHERE project_id = %s
            ORDER BY
                embedding
                    <=> CAST(%s AS VECTOR(384))
            LIMIT 5;
            """,
            (
                query_vector,
                project_id,
                query_vector,
            ),
        )

        results = cursor.fetchall()


print()
print("=" * 70)
print("SEMANTIC SEARCH RESULTS")
print("=" * 70)


for index, row in enumerate(
    results,
    start=1,
):

    memory_type = row[0]
    memory_text = row[1]
    distance = float(row[2])

    similarity = (
        1 - distance
    )

    print()
    print(
        f"RESULT #{index}"
    )

    print(
        "Memory type:",
        memory_type,
    )

    print(
        "Cosine similarity:",
        round(
            similarity,
            4,
        ),
    )

    print(
        "Memory:"
    )

    print(
        memory_text
    )

    print(
        "-" * 70
    )