#!/usr/bin/env python3
"""Seed a dedicated DEMO database; run collector with the same environment."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from filelock import FileLock
from app.config import Settings
from app.database import Database
from app.runtime import Runtime


def main():
    parser = argparse.ArgumentParser(description='Popular 16 equipamentos sintéticos em banco DEMO separado.')
    parser.add_argument('--hours', type=float, default=3)
    parser.add_argument('--scenario', choices=['normal', 'faults'], default='normal')
    args = parser.parse_args()
    settings = Settings.from_env()
    if settings.mode != 'demo':
        parser.error('Recusado: HNSG_MODE precisa ser demo; nenhum dado LIVE será simulado.')
    if not 0 <= args.hours <= 168:
        parser.error('--hours deve estar entre 0 e 168')
    settings.demo_full = True
    settings.demo_scenario = args.scenario
    settings.seed_hours = args.hours
    db = Database(settings)
    try:
        with FileLock(str(settings.data_dir / 'collector.lock'), timeout=0):
            Runtime(db, settings).initialize()
        print('DEMO preparada. Histórico inicial criado somente se o banco não tinha amostras.')
        print('Para aquisição contínua: DEMO_FULL=true e DEMO_SCENARIO=' + args.scenario)
        print('Execute um único worker de app.main:app com o MESMO ambiente e banco.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
