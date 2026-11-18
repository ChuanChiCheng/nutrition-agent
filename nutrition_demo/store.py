"""Short per-operation connections; all writes serialize on the singleton state row."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .models import decimal, dumps

TABLES = ('profile', 'inventory', 'cooking_runs', 'cooking_ingredients', 'batches',
          'batch_ingredients', 'batch_addons', 'events', 'inventory_movements',
          'previews', 'operations', 'workflow_sessions', 'agent_runs')


def jsonb(value):
    return Jsonb(value, dumps=dumps)


class Store:
    def __init__(self, dsn: str, schema='public'):
        if not dsn or not schema or '\x00' in schema:
            raise ValueError('Database URL and schema required')
        self.dsn, self.schema = dsn, schema

    @contextmanager
    def transaction(self, *, lock=False):
        with psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5) as c:
            c.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(self.schema)))
            if lock:
                c.execute('SELECT version FROM state_meta WHERE id=1 FOR UPDATE').fetchone()
            yield c

    def _migrations(self):
        return {p.name: (sha256(p.read_bytes()).hexdigest(), p.read_text())
                for p in sorted((Path(__file__).parent / 'migrations').glob('*.sql'))}

    def _check(self, c):
        known = self._migrations()
        rows = c.execute('SELECT * FROM schema_migrations').fetchall()
        if any(r['version'] not in known or known[r['version']][0] != r['checksum'] for r in rows):
            raise ValueError('Unknown or modified migration; restore matching application version')
        return {r['version'] for r in rows}

    def migrate(self):
        with self.transaction() as c:
            # Serialize initialization even before state_meta exists.
            c.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('nutrition-migrate:' + self.schema,))
            c.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, checksum TEXT NOT NULL)')
            applied = self._check(c)
            for version, (checksum, statement) in self._migrations().items():
                if version not in applied:
                    c.execute(statement)
                    c.execute('INSERT INTO schema_migrations VALUES (%s,%s)', (version, checksum))

    def check_schema(self):
        with self.transaction() as c:
            try:
                applied = self._check(c)
            except psycopg.errors.UndefinedTable:
                raise ValueError('Schema not initialized; run --init-db') from None
            if set(self._migrations()) != applied:
                raise ValueError('Pending migration; run --init-db')

    def info(self):
        self.check_schema()
        conn = conninfo_to_dict(self.dsn)
        with self.transaction() as c:
            return {'database': conn.get('dbname'), 'host': conn.get('host'), 'schema': self.schema,
                    'versions': [r['version'] for r in c.execute('SELECT version FROM schema_migrations ORDER BY version')],
                    'counts': {t: c.execute(sql.SQL('SELECT count(*) n FROM {}').format(sql.Identifier(t))).fetchone()['n'] for t in TABLES}}

    def seed(self, values):
        if values.get('synthetic') is not True:
            raise ValueError('Seed must explicitly declare synthetic=true')
        with self.transaction(lock=True) as c:
            if any(c.execute(sql.SQL('SELECT EXISTS(SELECT 1 FROM {}) present').format(sql.Identifier(t))).fetchone()['present'] for t in TABLES):
                raise ValueError('Seed requires an empty schema')
            if 'profile' in values:
                c.execute('INSERT INTO profile VALUES (1,%s)', (jsonb(values['profile']),))
            for item in values.get('inventory', []):
                qty = decimal(item['quantity'])
                c.execute('INSERT INTO inventory VALUES (%s,%s,%s,%s,%s)',
                          (item['ingredient_id'], qty, item['unit'], item['state'], jsonb(item.get('source', {'status': 'synthetic'}))))
            c.execute('UPDATE state_meta SET version=version+1 WHERE id=1')

    def close(self):
        # Connections belong to transaction() and are always closed there.
        pass
