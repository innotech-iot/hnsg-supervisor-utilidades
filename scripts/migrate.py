#!/usr/bin/env python3
"""Inspect by default; apply explicit revision with the application stopped."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from filelock import FileLock, Timeout
from app.config import Settings
from app.database import Database
from app.migrations import schema_status, migrate_database


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Aplicar migração; exige backup e aplicação parada')
    args=parser.parse_args()
    settings=Settings.from_env()
    db=Database(settings)
    try:
        with FileLock(str(settings.data_dir/'collector.lock'),timeout=0):
            result=migrate_database(db) if args.apply else schema_status(db)
        print(json.dumps(result,ensure_ascii=False))
        return 0
    except (RuntimeError,Timeout) as exc:
        print('Migração bloqueada: '+('Aplicação em execução; pare antes de migrar' if isinstance(exc,Timeout) else str(exc)),file=sys.stderr)
        return 2
    finally:db.close()


if __name__=='__main__':raise SystemExit(main())
