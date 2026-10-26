import os
import subprocess
import sys

import pytest

from sqlalchemy import select

from app.config import Settings
from app.database import Database
from app.equipment import catalog_for
from app.models import Sample
from app.runtime import Runtime


def test_full_demo_populates_all_equipment_and_history(tmp_path):
    settings = Settings(data_dir=tmp_path, seed_hours=0.05)
    settings.demo_full = True
    db = Database(settings)
    rt = Runtime(db, settings)
    try:
        rt.initialize()
        assert len(rt.latest) == 16
        for aid, row in rt.latest.items():
            assert row['source'] == 'demo' and row['quality'] == 'good'
            assert set(row['data']) == set(catalog_for(rt.asset_kinds[aid]))
            assert all(v is not None for v in row['data'].values())
        cold, hot = rt.latest[15]['data'], rt.latest[16]['data']
        assert 5 <= cold['supply_temperature'] <= 10
        assert 2 <= cold['return_temperature'] - cold['supply_temperature'] <= 7
        assert 40 <= hot['supply_temperature'] <= 60
        assert 2 <= hot['supply_temperature'] - hot['return_temperature'] <= 8
        rt.persist()
        with db.session() as s:
            for aid in range(1, 17):
                assert len(s.scalars(select(Sample).where(Sample.asset_id == aid)).all()) >= 6
        old = rt.latest[1]['data'].copy()
        rt.overrides[1] = {'mode': 0}
        rt.demo_tick()
        off = rt.latest[1]['data']
        assert old['fan_speed'] > 0
        assert off['fan_speed'] == off['airflow'] == off['pressure'] == off['cooling'] == 0
        assert off['fan_feedback'] == off['fan_command'] == 0
    finally:
        db.close()


def test_full_demo_never_supplies_live_data(tmp_path):
    settings = Settings(mode='live', data_dir=tmp_path, run_collector=False)
    settings.demo_full = True
    db = Database(settings)
    rt = Runtime(db, settings)
    try:
        rt.initialize()
        assert not rt.latest
        assert all(a['quality'] == 'unknown' for a in rt.snapshot()['assets'])
        with pytest.raises(RuntimeError, match='somente em DEMO'):
            rt.demo_tick()
        with pytest.raises(RuntimeError, match='somente em DEMO'):
            rt.seed()
    finally:
        db.close()


def test_fault_scenario_preserves_invalid_data_and_physical_ranges():
    from app.demo_plant import plant_values
    for stamp in range(0, 86400, 60):
        for aid in range(1, 15):
            data, quality = plant_values(aid, 'uta', stamp)
            assert quality == 'good'
            assert 0 <= data['cooling'] <= 100 and 0 <= data['fan_speed'] <= 100
            assert 0 <= data['humidity'] <= 100 and data['airflow'] > 0
    data, quality = plant_values(11, 'uta', 1000, scenario='faults')
    assert quality == 'bad' and all(v is None for v in data.values())
    data, quality = plant_values(3, 'uta', 1000, scenario='faults')
    assert data['temperature'] - data['temp_sp'] > 2 and data['cooling'] > 95


def test_population_script_rejects_live_before_creating_database(tmp_path):
    result = subprocess.run([sys.executable, 'scripts/populate_demo.py'],
        env=os.environ | {'HNSG_MODE': 'live', 'HNSG_DATA_DIR': str(tmp_path / 'untouched')},
        capture_output=True, text=True)
    assert result.returncode == 2 and 'Recusado' in result.stderr
    assert not (tmp_path / 'untouched').exists()
