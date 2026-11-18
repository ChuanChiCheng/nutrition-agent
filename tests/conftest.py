import os
import uuid
from datetime import datetime, timezone
import pytest
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

@pytest.fixture
def store():
    from nutrition_demo.store import Store
    dsn = os.environ.get('TEST_DATABASE_URL')
    if not dsn:
        pytest.fail('TEST_DATABASE_URL required; never fall back to DATABASE_URL')
    info = conninfo_to_dict(dsn)
    if info.get('dbname') != 'nutrition_test' or info.get('host') != 'db_test':
        pytest.fail('Tests require db_test/nutrition_test')
    schema = 'case_' + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    db = Store(dsn, schema)
    try:
        db.migrate()
        yield db
    finally:
        db.close()
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))

@pytest.fixture
def clock():
    return lambda: datetime(2026, 11, 18, 7, 30, tzinfo=timezone.utc)
