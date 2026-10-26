from pathlib import Path
import shutil
import subprocess
import pytest


def test_register_selection_units_and_missing_fan_speed():
    binary=shutil.which('node')
    if not binary:
        pytest.skip('Node indisponível')
    result=subprocess.run([binary,'--input-type=module','-e','''
import assert from 'node:assert/strict';
import {registers,selectedSeries} from './static/registers.js';
assert.equal(registers.fan_speed.unit,'%');
assert.equal(registers.fan_command,undefined); // Digital/enum aggregates must not look like analog states.
assert.deepEqual(selectedSeries(['temperature','temp_sp'],'°C').map(s=>s.key),['temperature','temp_sp']);
assert.deepEqual(selectedSeries(['temperature','humidity','unknown'],'°C').map(s=>s.key),['temperature']);
assert.deepEqual(selectedSeries([],'%'),[]);
assert.ok(selectedSeries(['fan_speed'],'%')[0].label.includes('%'));
'''],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stdout+result.stderr
