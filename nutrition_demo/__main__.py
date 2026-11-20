import argparse
import json
import os
import sys
from .models import dumps
from .store import Store


def main():
    parser = argparse.ArgumentParser(description='Nutrition Agent Python V1')
    parser.add_argument('--init-db', action='store_true')
    parser.add_argument('--db-info', action='store_true')
    parser.add_argument('--seed')
    parser.add_argument('--scripted', action='store_true')
    parser.add_argument('--model')
    args = parser.parse_args()
    try:
        store = Store(os.environ.get('DATABASE_URL', ''), os.environ.get('DATABASE_SCHEMA', 'public'))
        if args.init_db:
            store.migrate()
            print('Database initialized.')
            return 0
        store.check_schema()
        if args.seed:
            with open(args.seed) as f:
                store.seed(json.load(f))
            print('Synthetic demonstration data loaded.')
        if args.db_info:
            print(dumps(store.info()))
            return 0
        if args.scripted:
            from .scenario import run_scripted
            print(dumps(run_scripted(store)))
            return 0
        from .agent import interactive
        return interactive(store, args.model)
    except Exception as exc:
        # Never print DSNs, credentials, request payloads, or upstream raw errors.
        if isinstance(exc, ValueError):
            print('Configuration/data error: ' + str(exc), file=sys.stderr)
        else:
            print('Operation failed (' + type(exc).__name__ + '); check connectivity and settings, then retry with the same request_id.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
