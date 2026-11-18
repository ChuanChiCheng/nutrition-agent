import pytest
import psycopg


def test_profile_survives_reopen(store):
    from nutrition_demo.store import Store
    store.seed({'synthetic': True, 'profile': {'timezone': 'America/Los_Angeles'}, 'inventory': []})
    other = Store(store.dsn, store.schema)
    assert other.info()['counts']['profile'] == 1
    with other.transaction() as c:
        assert c.execute('SELECT data FROM profile').fetchone()['data']['timezone'] == 'America/Los_Angeles'
    other.close()


def test_migrations_repeat_safely(store):
    store.seed({'synthetic': True, 'profile': {'timezone': 'America/Los_Angeles'}})
    before = store.info()
    store.migrate()
    assert store.info() == before


def test_unknown_schema_version(store):
    with store.transaction() as c:
        c.execute("INSERT INTO schema_migrations VALUES ('999_future.sql', 'unknown')")
    with pytest.raises(ValueError, match='migration'):
        store.check_schema()


def test_foreign_keys(store):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with store.transaction() as c:
            c.execute("INSERT INTO batches(id,cooking_run_id,name,total_boxes,remaining_boxes, data) VALUES ('b','missing','test',1,1,'{}')")


def test_seed_rejects_nonempty(store):
    store.seed({'synthetic': True, 'profile': {'timezone': 'America/Los_Angeles'}})
    with pytest.raises(ValueError, match='empty'):
        store.seed({'synthetic': True, 'profile': {}})
    assert store.info()['counts']['profile'] == 1


def test_seed_failure_rolls_back(store):
    with pytest.raises((ValueError, psycopg.Error)):
        store.seed({'synthetic': True, 'profile': {'timezone': 'America/Los_Angeles'}, 'inventory': [
            {'ingredient_id': 'x', 'quantity': '1', 'unit': 'g', 'state': 'raw'},
            {'ingredient_id': 'y', 'quantity': '-1', 'unit': 'g', 'state': 'raw'}]})
    assert store.info()['counts']['profile'] == 0
    assert store.info()['counts']['inventory'] == 0


def test_migration_checksum_checked(store):
    with store.transaction() as c:
        c.execute("UPDATE schema_migrations SET checksum='bad'")
    with pytest.raises(ValueError, match='migration'):
        store.migrate()
