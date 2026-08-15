import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL was not found in .env")


print("Connecting to CockroachDB...")


with psycopg.connect(DATABASE_URL) as connection:

    with connection.cursor() as cursor:

        # ---------------------------------------------
        # CREATE PROJECT PLANNING TABLE
        # ---------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_planning (
                project_id UUID PRIMARY KEY
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                baseline_remaining_work_days DECIMAL(8, 2)
                    NOT NULL,

                available_capacity_days DECIMAL(8, 2)
                    NOT NULL,

                engineer_day_cost DECIMAL(14, 2)
                    NOT NULL,

                planning_notes TEXT,

                updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT now()
            );
            """
        )

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
                "Website Redesign project was not found."
            )

        project_id = project[0]

        # ---------------------------------------------
        # STORE DEMO PLANNING ASSUMPTIONS
        # ---------------------------------------------
        #
        # baseline_remaining_work_days:
        # Core remaining work before newly approved additions.
        #
        # available_capacity_days:
        # Remaining team capacity before agreed deadline.
        #
        # engineer_day_cost:
        # Cost of purchasing one additional engineering day.
        # ---------------------------------------------

        cursor.execute(
            """
            INSERT INTO project_planning (
                project_id,
                baseline_remaining_work_days,
                available_capacity_days,
                engineer_day_cost,
                planning_notes
            )
            VALUES (%s, %s, %s, %s, %s)

            ON CONFLICT (project_id)
            DO UPDATE SET
                baseline_remaining_work_days =
                    excluded.baseline_remaining_work_days,

                available_capacity_days =
                    excluded.available_capacity_days,

                engineer_day_cost =
                    excluded.engineer_day_cost,

                planning_notes =
                    excluded.planning_notes,

                updated_at = now();
            """,
            (
                project_id,
                10,
                10,
                400,
                (
                    "Demo assumptions for hackathon. "
                    "Baseline work excludes newly approved "
                    "scope additions."
                ),
            ),
        )

        connection.commit()

        # ---------------------------------------------
        # VERIFY
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT
                baseline_remaining_work_days,
                available_capacity_days,
                engineer_day_cost,
                planning_notes
            FROM project_planning
            WHERE project_id = %s;
            """,
            (project_id,),
        )

        planning = cursor.fetchone()


print()
print("=" * 60)
print("SCOPELEDGER PLANNING MEMORY")
print("=" * 60)

print(
    "Baseline remaining work:",
    planning[0],
    "days"
)

print(
    "Available team capacity:",
    planning[1],
    "days"
)

print(
    "Extra engineering cost:",
    "$" + str(planning[2]),
    "per day"
)

print()
print("Planning assumptions saved.")