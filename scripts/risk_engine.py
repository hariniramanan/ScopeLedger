import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row



# LOAD DATABASE CONNECTION


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL was not found in .env")


print("Connecting to ScopeLedger memory...")



# READ PROJECT MEMORY


with psycopg.connect(
    DATABASE_URL,
    row_factory=dict_row
) as connection:

    with connection.cursor() as cursor:

        # Get our project.
        cursor.execute(
            """
            SELECT
                id,
                name,
                client_name,
                original_budget,
                current_budget,
                original_deadline,
                current_deadline,
                currency
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
            raise ValueError("Demo project was not found.")

        project_id = project["id"]

        # Get scope changes.
        cursor.execute(
            """
            SELECT
                pc.change_type,
                pc.old_value,
                pc.new_value,
                pc.reason,
                m.title,
                m.meeting_date
            FROM project_changes pc
            JOIN meetings m
              ON pc.meeting_id = m.id
            WHERE pc.project_id = %s
              AND pc.change_type = 'scope'
            ORDER BY m.meeting_date DESC;
            """,
            (project_id,),
        )

        scope_changes = cursor.fetchall()

        # Find schedule-impact evidence.
        cursor.execute(
            """
            SELECT
                e.evidence_text,
                m.title,
                m.meeting_date
            FROM evidence e
            JOIN meetings m
              ON e.meeting_id = m.id
            WHERE e.project_id = %s
              AND e.evidence_type = 'schedule_impact'
            ORDER BY m.meeting_date DESC;
            """,
            (project_id,),
        )

        schedule_impacts = cursor.fetchall()



# DETERMINE CURRENT CONDITIONS


budget_unchanged = (
    project["original_budget"] == project["current_budget"]
)

deadline_unchanged = (
    project["original_deadline"] == project["current_deadline"]
)

scope_changed = len(scope_changes) > 0

schedule_impact_exists = len(schedule_impacts) > 0



# SIMPLE DETERMINISTIC RISK RULE


risk_detected = (
    scope_changed
    and schedule_impact_exists
    and budget_unchanged
    and deadline_unchanged
)



# DISPLAY RESULT


print()
print("=" * 65)
print("SCOPELEDGER DELIVERY RISK ANALYSIS")
print("=" * 65)

print()
print("PROJECT")
print(project["name"], "-", project["client_name"])

print()
print("CURRENT CONDITIONS")

print(
    "Budget:",
    f"{project['current_budget']} {project['currency']}"
)

print(
    "Deadline:",
    project["current_deadline"]
)

print(
    "Scope change detected:",
    "YES" if scope_changed else "NO"
)

print(
    "Schedule impact detected:",
    "YES" if schedule_impact_exists else "NO"
)

print(
    "Budget unchanged:",
    "YES" if budget_unchanged else "NO"
)

print(
    "Deadline unchanged:",
    "YES" if deadline_unchanged else "NO"
)


print()
print("-" * 65)


if risk_detected:

    print("RISK LEVEL: HIGH")
    print()

    print(
        "Reason: Approved project scope has increased and "
        "additional development time has been identified, "
        "while the agreed budget and deadline remain unchanged."
    )

    print()
    print("EVIDENCE")

    for change in scope_changes:

        print()
        print(
            f"[{change['meeting_date']}] "
            f"{change['old_value']} -> {change['new_value']}"
        )

        print(
            "Reason:",
            change["reason"]
        )

    for impact in schedule_impacts:

        print()
        print(
            f"[{impact['meeting_date']}] "
            f"{impact['evidence_text']}"
        )

    print()
    print("RECOMMENDED PM ACTION")

    print(
        "Review the delivery plan with the client. "
        "Consider increasing capacity, extending the deadline, "
        "or reducing/defering scope."
    )

else:

    print("RISK LEVEL: LOW / NOT DETECTED")
    print()
    print(
        "The current deterministic rules did not identify "
        "a scope-versus-delivery conflict."
    )


print()
print("=" * 65)