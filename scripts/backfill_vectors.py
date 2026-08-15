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


print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
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


print("Connecting to CockroachDB...")


with psycopg.connect(
    DATABASE_URL
) as connection:

    with connection.cursor() as cursor:

        # ---------------------------------------------
        # FIND OUR DEMO PROJECT
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
        # CLEAR ANY PREVIOUS VECTOR MEMORIES
        # ---------------------------------------------

        cursor.execute(
            """
            DELETE FROM memory_embeddings
            WHERE project_id = %s;
            """,
            (project_id,),
        )

        # ---------------------------------------------
        # LOAD EVIDENCE
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT
                e.id,
                e.meeting_id,
                e.evidence_type,
                e.evidence_text,
                m.title,
                m.meeting_date
            FROM evidence AS e
            JOIN meetings AS m
              ON m.id = e.meeting_id
            WHERE e.project_id = %s
            ORDER BY
                m.meeting_date,
                e.created_at;
            """,
            (project_id,),
        )

        evidence_rows = (
            cursor.fetchall()
        )

        print(
            f"Found {len(evidence_rows)} "
            "evidence records."
        )

        inserted = 0

        for row in evidence_rows:

            (
                evidence_id,
                meeting_id,
                evidence_type,
                evidence_text,
                meeting_title,
                meeting_date,
            ) = row

            # Add a little context to the text
            # before embedding it.
            memory_text = (
                f"Meeting: {meeting_title}. "
                f"Date: {meeting_date}. "
                f"Evidence type: "
                f"{evidence_type}. "
                f"{evidence_text}"
            )

            embedding = model.encode(
                memory_text,
                normalize_embeddings=True,
            )

            vector_sql = vector_to_sql(
                embedding
            )

            cursor.execute(
                """
                INSERT INTO memory_embeddings (
                    project_id,
                    meeting_id,
                    evidence_id,
                    memory_type,
                    memory_text,
                    embedding,
                    embedding_model
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CAST(%s AS VECTOR(384)),
                    %s
                );
                """,
                (
                    project_id,
                    meeting_id,
                    evidence_id,
                    evidence_type,
                    memory_text,
                    vector_sql,
                    MODEL_NAME,
                ),
            )

            inserted += 1

            print(
                f"Embedded {inserted}: "
                f"{evidence_type}"
            )

        connection.commit()


print()
print("=" * 60)
print("VECTOR BACKFILL COMPLETE")
print("=" * 60)
print(
    "Stored semantic memories:",
    inserted
)