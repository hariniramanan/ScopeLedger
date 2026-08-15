import os

import psycopg
from dotenv import load_dotenv


# Load DATABASE_URL from .env
load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL was not found in .env")


# Each item below is one database table.
tables = [

    """
    CREATE TABLE IF NOT EXISTS projects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        name TEXT NOT NULL,
        client_name TEXT,

        status TEXT NOT NULL DEFAULT 'active',

        original_budget DECIMAL(14, 2),
        current_budget DECIMAL(14, 2),
        currency TEXT DEFAULT 'USD',

        original_deadline DATE,
        current_deadline DATE,

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS meetings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        project_id UUID NOT NULL
            REFERENCES projects(id)
            ON DELETE CASCADE,

        title TEXT,
        meeting_date DATE,

        raw_notes TEXT NOT NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS decisions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        project_id UUID NOT NULL
            REFERENCES projects(id)
            ON DELETE CASCADE,

        meeting_id UUID
            REFERENCES meetings(id)
            ON DELETE CASCADE,

        decision_text TEXT NOT NULL,

        reasoning TEXT,

        status TEXT NOT NULL DEFAULT 'active',

        confidence DECIMAL(4, 3),

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS commitments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        project_id UUID NOT NULL
            REFERENCES projects(id)
            ON DELETE CASCADE,

        meeting_id UUID
            REFERENCES meetings(id)
            ON DELETE CASCADE,

        commitment_text TEXT NOT NULL,

        owner_name TEXT,

        due_date DATE,

        status TEXT NOT NULL DEFAULT 'open',

        estimated_cost DECIMAL(14, 2),

        estimated_days DECIMAL(8, 2),

        confidence DECIMAL(4, 3),

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS scope_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        project_id UUID NOT NULL
            REFERENCES projects(id)
            ON DELETE CASCADE,

        meeting_id UUID
            REFERENCES meetings(id)
            ON DELETE CASCADE,

        item_text TEXT NOT NULL,

        scope_status TEXT NOT NULL,

        impact_text TEXT,

        confidence DECIMAL(4, 3),

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS project_changes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        project_id UUID NOT NULL
            REFERENCES projects(id)
            ON DELETE CASCADE,

        meeting_id UUID
            REFERENCES meetings(id)
            ON DELETE CASCADE,

        change_type TEXT NOT NULL,

        old_value TEXT,

        new_value TEXT,

        reason TEXT,

        confidence DECIMAL(4, 3),

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS evidence (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        project_id UUID NOT NULL
            REFERENCES projects(id)
            ON DELETE CASCADE,

        meeting_id UUID
            REFERENCES meetings(id)
            ON DELETE CASCADE,

        evidence_type TEXT,

        evidence_text TEXT NOT NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """
]


print("Connecting to CockroachDB...")

with psycopg.connect(database_url) as connection:

    with connection.cursor() as cursor:

        print("Creating ScopeLedger memory tables...")

        for table_sql in tables:
            cursor.execute(table_sql)

        connection.commit()

        # Check which tables now exist.
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
        )

        rows = cursor.fetchall()


print()
print("ScopeLedger database initialized!")
print()
print("Tables:")

for row in rows:
    print("-", row[0])