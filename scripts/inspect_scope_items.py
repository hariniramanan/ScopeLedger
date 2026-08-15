import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL was not found in .env"
    )


with psycopg.connect(DATABASE_URL) as connection:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                si.id,
                si.item_text,
                si.scope_status,
                si.impact_text,
                m.title,
                m.meeting_date
            FROM scope_items AS si
            LEFT JOIN meetings AS m
                ON m.id = si.meeting_id
            JOIN projects AS p
                ON p.id = si.project_id
            WHERE p.name = %s
              AND p.client_name = %s
            ORDER BY
                m.meeting_date,
                si.created_at;
            """,
            (
                "Website Redesign",
                "Acme Corp",
            ),
        )

        rows = cursor.fetchall()


print()
print("=" * 70)
print("CURRENT SCOPE ITEMS")
print("=" * 70)

for row in rows:
    print()
    print("ID:", row[0])
    print("Item:", repr(row[1]))
    print("Status:", row[2])
    print("Impact:", row[3])
    print("Meeting:", row[4])
    print("Date:", row[5])
    print("-" * 70)

print()
print("Total scope rows:", len(rows))