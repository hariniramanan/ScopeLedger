import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found in .env"
    )


ANALYTICS_SCOPE_ID = (
    "d3914bd0-7497-4486-aa19-432890aff134"
)

DARK_MODE_SCOPE_ID = (
    "20d14092-c898-4d6d-b132-04cf9ecb340d"
)


with psycopg.connect(DATABASE_URL) as connection:

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
                "Website Redesign project not found."
            )

        project_id = project[0]

        # ---------------------------------------------
        # FIND FINAL SCOPE REVIEW MEETING
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id, meeting_date
            FROM meetings
            WHERE project_id = %s
              AND title = %s
            ORDER BY meeting_date DESC
            LIMIT 1;
            """,
            (
                project_id,
                "Website Redesign - Final Scope Review",
            ),
        )

        meeting = cursor.fetchone()

        if not meeting:
            raise ValueError(
                "Final Scope Review meeting was not found."
            )

        meeting_id = meeting[0]
        meeting_date = meeting[1]

        # ---------------------------------------------
        # ANALYTICS DASHBOARD
        # requested → deferred / Phase 2
        # ---------------------------------------------

        cursor.execute(
            """
            UPDATE scope_items
            SET
                item_text = 'Analytics dashboard',
                scope_status = 'deferred',
                impact_text = 'Moved to Phase 2.'
            WHERE id = %s
            RETURNING
                item_text,
                scope_status,
                impact_text;
            """,
            (ANALYTICS_SCOPE_ID,),
        )

        analytics_result = cursor.fetchone()

        if not analytics_result:
            raise ValueError(
                "Analytics dashboard scope row was not updated."
            )

        # Avoid duplicate change-memory rows.
        cursor.execute(
            """
            SELECT id
            FROM project_changes
            WHERE project_id = %s
              AND new_value =
                  'Analytics dashboard deferred to Phase 2'
            LIMIT 1;
            """,
            (project_id,),
        )

        existing_change = cursor.fetchone()

        if not existing_change:

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
                VALUES (
                    %s,
                    %s,
                    'scope',
                    'Analytics dashboard requested',
                    'Analytics dashboard deferred to Phase 2',
                    'Client decided that the analytics dashboard should be moved to Phase 2.',
                    0.99
                );
                """,
                (
                    project_id,
                    meeting_id,
                ),
            )

        # ---------------------------------------------
        # DARK MODE
        # requested but explicitly not approved
        # ---------------------------------------------

        cursor.execute(
            """
            UPDATE scope_items
            SET
                item_text = 'Dark mode',
                scope_status = 'requested_not_approved',
                impact_text =
                    'Not approved for the initial release.'
            WHERE id = %s
            RETURNING
                item_text,
                scope_status,
                impact_text;
            """,
            (DARK_MODE_SCOPE_ID,),
        )

        dark_mode_result = cursor.fetchone()

        if not dark_mode_result:
            raise ValueError(
                "Dark mode scope row was not updated."
            )

        connection.commit()


print()
print("=" * 60)
print("PROJECT TRUTH RECONCILED")
print("=" * 60)

print()
print(
    "Final Scope Review meeting date:",
    meeting_date,
)

print()
print("Analytics dashboard")
print("Status:", analytics_result[1])
print("Impact:", analytics_result[2])

print()
print("Dark mode")
print("Status:", dark_mode_result[1])
print("Impact:", dark_mode_result[2])