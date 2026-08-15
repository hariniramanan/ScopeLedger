import os
from datetime import date

import psycopg
from dotenv import load_dotenv


# LOAD DATABASE CONNECTION


load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL was not found in .env")


print("Connecting to CockroachDB...")


with psycopg.connect(database_url) as connection:

    with connection.cursor() as cursor:

        
        # FIND OUR EXISTING PROJECT
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
                "Website Redesign project was not found. "
                "Run memory_demo.py first."
            )

        project_id = project[0]

        
        # PREVENT DUPLICATES
        

        cursor.execute(
            """
            SELECT id
            FROM meetings
            WHERE project_id = %s
              AND title = %s
            LIMIT 1;
            """,
            (
                project_id,
                "Website Redesign - Scope Review",
            ),
        )

        existing_meeting = cursor.fetchone()

        if existing_meeting:
            print()
            print("Meeting #2 already exists.")
            print("Nothing new was added.")
            raise SystemExit

        
        # MEETING #2
        

        meeting_notes = """
Meeting: Website Redesign - Scope Review
Date: August 14, 2026

The client confirmed that CSV export must be included in the initial release.

Sarah confirmed that implementing CSV export is expected to require
approximately three additional development days.

The client confirmed that the total project budget should remain $10,000.

The client also confirmed that the September 30, 2026 launch deadline
should remain unchanged.

Mobile support will be considered for a later phase and is not included
in the current release.

John reported that authentication work is progressing as planned.
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
                "Website Redesign - Scope Review",
                date(2026, 8, 14),
                meeting_notes,
            ),
        )

        meeting_id = cursor.fetchone()[0]

        
        # DECISIONS FROM MEETING #2
        

        decisions = [
            (
                "CSV export is approved for the initial release.",
                0.99,
            ),
            (
                "Project budget remains $10,000.",
                0.99,
            ),
            (
                "Launch deadline remains September 30, 2026.",
                0.99,
            ),
            (
                "Mobile support is deferred to a later phase.",
                0.98,
            ),
        ]

        for decision_text, confidence in decisions:

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
                    decision_text,
                    confidence,
                ),
            )

        
        # NEW SCOPE MEMORY
        

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
                "approved",
                "Expected to require approximately three additional development days.",
                0.99,
            ),
        )

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
                "deferred",
                "Not included in the current release.",
                0.98,
            ),
        )

        
        # PROJECT CHANGE MEMORY
        #
        # Important:
        # Scope changed even though budget/deadline did not.
        

        cursor.execute(
            """
            INSERT INTO project_changes (
                project_id,
                meeting_id,
                change_type,
                old_value,
                new_value,
                reason,
                confidence
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                project_id,
                meeting_id,
                "scope",
                "CSV export requested",
                "CSV export approved",
                "Client confirmed CSV export must be included in the initial release.",
                0.99,
            ),
        )

        
        # EVIDENCE
        

        evidence_items = [
            (
                "scope",
                "The client confirmed that CSV export must be included in the initial release.",
            ),
            (
                "schedule_impact",
                "Sarah confirmed that implementing CSV export is expected to require approximately three additional development days.",
            ),
            (
                "budget",
                "The client confirmed that the total project budget should remain $10,000.",
            ),
            (
                "deadline",
                "The client also confirmed that the September 30, 2026 launch deadline should remain unchanged.",
            ),
            (
                "scope",
                "Mobile support will be considered for a later phase and is not included in the current release.",
            ),
            (
                "progress",
                "John reported that authentication work is progressing as planned.",
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
print("Meeting #2 saved successfully!")
print("ScopeLedger now remembers multiple meetings.")