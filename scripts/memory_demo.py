import os
from datetime import date

import psycopg
from dotenv import load_dotenv

# Load the CockroachDB connection string from .env

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL was not found in .env")

# Create first demo project memory

print("Connecting to CockroachDB...")
print("Saving demo project memory...")


with psycopg.connect(database_url) as connection:

    with connection.cursor() as cursor:

        # safely run this demo multiple times.
        cursor.execute(
            """
            DELETE FROM projects
            WHERE name = %s
              AND client_name = %s;
            """,
            (
                "Website Redesign",
                "Acme Corp",
            ),
        )


        # PROJECT

        cursor.execute(
            """
            INSERT INTO projects (
                name,
                client_name,
                original_budget,
                current_budget,
                currency,
                original_deadline,
                current_deadline
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                "Website Redesign",
                "Acme Corp",
                10000,
                10000,
                "USD",
                date(2026, 9, 30),
                date(2026, 9, 30),
            ),
        )

        project_id = cursor.fetchone()[0]


        # MEETING

        meeting_notes = """
Meeting: Website Redesign
Date: August 7, 2026

Client confirmed the project budget remains $10,000.

The website must launch by September 30, 2026.

John agreed to complete authentication by September 5, 2026.

The client requested CSV export.

Sarah explained that CSV export could add three days to development.

Mobile support was discussed but has not been approved.
""".strip()

        cursor.execute(
            """
            INSERT INTO meetings (
                project_id,
                title,
                meeting_date,
                raw_notes
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (
                project_id,
                "Website Redesign - Project Meeting",
                date(2026, 8, 7),
                meeting_notes,
            ),
        )

        meeting_id = cursor.fetchone()[0]

        # DECISIONS

        cursor.execute(
            """
            INSERT INTO decisions (
                project_id,
                meeting_id,
                decision_text,
                confidence
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                project_id,
                meeting_id,
                "Project budget remains $10,000.",
                0.99,
            ),
        )

        cursor.execute(
            """
            INSERT INTO decisions (
                project_id,
                meeting_id,
                decision_text,
                confidence
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                project_id,
                meeting_id,
                "Website launch deadline is September 30, 2026.",
                0.99,
            ),
        )

        # COMMITMENT

        cursor.execute(
            """
            INSERT INTO commitments (
                project_id,
                meeting_id,
                commitment_text,
                owner_name,
                due_date,
                status,
                confidence
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                project_id,
                meeting_id,
                "Complete authentication.",
                "John",
                date(2026, 9, 5),
                "open",
                0.98,
            ),
        )

        # SCOPE ITEM: CSV EXPORT

        cursor.execute(
            """
            INSERT INTO scope_items (
                project_id,
                meeting_id,
                item_text,
                scope_status,
                impact_text,
                confidence
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                project_id,
                meeting_id,
                "CSV export",
                "requested",
                "Could add approximately three development days.",
                0.96,
            ),
        )


        # SCOPE ITEM: MOBILE SUPPORT

        cursor.execute(
            """
            INSERT INTO scope_items (
                project_id,
                meeting_id,
                item_text,
                scope_status,
                impact_text,
                confidence
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                project_id,
                meeting_id,
                "Mobile support",
                "discussed_not_approved",
                "No approved schedule or budget impact yet.",
                0.97,
            ),
        )

        # EVIDENCE

        evidence_items = [
            (
                "budget",
                "Client confirmed the project budget remains $10,000.",
            ),
            (
                "deadline",
                "The website must launch by September 30, 2026.",
            ),
            (
                "commitment",
                "John agreed to complete authentication by September 5, 2026.",
            ),
            (
                "scope",
                "The client requested CSV export.",
            ),
            (
                "schedule_impact",
                "Sarah explained that CSV export could add three days to development.",
            ),
            (
                "scope",
                "Mobile support was discussed but has not been approved.",
            ),
        ]

        for evidence_type, evidence_text in evidence_items:

            cursor.execute(
                """
                INSERT INTO evidence (
                    project_id,
                    meeting_id,
                    evidence_type,
                    evidence_text
                )
                VALUES (%s, %s, %s, %s);
                """,
                (
                    project_id,
                    meeting_id,
                    evidence_type,
                    evidence_text,
                ),
            )

        connection.commit()


print()
print("Memory saved.")
print("Closing database connection...")
print()


# Open a new connection


print("Opening a fresh connection...")
print("Asking CockroachDB what ScopeLedger remembers...")
print()


with psycopg.connect(database_url) as connection:

    with connection.cursor() as cursor:

        # Find the project again from the database.
        cursor.execute(
            """
            SELECT
                id,
                name,
                client_name,
                current_budget,
                currency,
                current_deadline
            FROM projects
            WHERE name = %s
              AND client_name = %s;
            """,
            (
                "Website Redesign",
                "Acme Corp",
            ),
        )

        project = cursor.fetchone()

        project_id = project[0]

        # Get decisions.
        cursor.execute(
            """
            SELECT decision_text
            FROM decisions
            WHERE project_id = %s
            ORDER BY created_at;
            """,
            (project_id,),
        )

        decisions = cursor.fetchall()

        # Get commitments.
        cursor.execute(
            """
            SELECT
                commitment_text,
                owner_name,
                due_date,
                status
            FROM commitments
            WHERE project_id = %s
            ORDER BY created_at;
            """,
            (project_id,),
        )

        commitments = cursor.fetchall()

        # Get scope.
        cursor.execute(
            """
            SELECT
                item_text,
                scope_status,
                impact_text
            FROM scope_items
            WHERE project_id = %s
            ORDER BY created_at;
            """,
            (project_id,),
        )

        scope_items = cursor.fetchall()

        # Get evidence.
        cursor.execute(
            """
            SELECT
                evidence_type,
                evidence_text
            FROM evidence
            WHERE project_id = %s
            ORDER BY created_at;
            """,
            (project_id,),
        )

        evidence = cursor.fetchall()


# Display what CockroachDB remembered

print("=" * 60)
print("SCOPELEDGER PROJECT MEMORY")
print("=" * 60)

print()
print("PROJECT")
print("Name:", project[1])
print("Client:", project[2])
print("Budget:", f"{project[3]} {project[4]}")
print("Deadline:", project[5])

print()
print("DECISIONS")

for decision in decisions:
    print("-", decision[0])

print()
print("COMMITMENTS")

for commitment in commitments:
    print(
        f"- {commitment[1]}: {commitment[0]} "
        f"(Due {commitment[2]}, Status: {commitment[3]})"
    )

print()
print("SCOPE")

for item in scope_items:
    print(f"- {item[0]}")
    print(f"  Status: {item[1]}")
    print(f"  Impact: {item[2]}")

print()
print("EVIDENCE")

for item in evidence:
    print(f"- [{item[0]}] {item[1]}")

print()
print("=" * 60)
print("Persistent memory test successful.")
print("=" * 60)