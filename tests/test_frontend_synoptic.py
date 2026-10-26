from pathlib import Path
import shutil
import subprocess

import pytest


def test_isometric_synoptic_contract():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node indisponível')
    result = subprocess.run(
        [node, '--experimental-default-type=module', '--input-type=module', '-e', '''
import assert from 'node:assert/strict';
import {utaSynoptic} from './static/synoptic.js';
const html=utaSynoptic();
assert.ok(html.includes('role="img"'));
assert.ok(html.includes('viewBox="0 0 1000 560"'));
for(const id of ['fan-device','heater-device']) assert.equal(html.split(`id="${id}"`).length,2);
for(const metric of ['cooling','heating']) assert.ok(html.includes(`data-detail-value="${metric}"`));
assert.ok(html.includes('ilustrativa'));
assert.equal((html.match(/class="uta-callout /g)||[]).length,3);
assert.equal((html.match(/data-proportional-valve=/g)||[]).length,2);
assert.ok(html.includes('data-detail-value="fan_speed"'));
assert.ok(html.includes('uta-leaders'));
assert.ok(html.includes('uta-fan-support'));
assert.ok(html.includes('id="uta-airflow"'));
assert.ok(html.includes('data-water-circuit="chilled"'));
assert.ok(html.includes('data-water-circuit="hot"'));
assert.ok(!html.includes('<animate')&&!html.includes('onclick'));
'''], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
