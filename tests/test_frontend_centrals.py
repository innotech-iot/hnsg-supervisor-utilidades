from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize('scenario',['dashboard','central','mapping'])
def test_central_frontend_behavior(scenario):
    binary=shutil.which('node')
    if not binary:pytest.skip('Node indisponível para regressão JS; repetir ensaio visual')
    script=Path(__file__).with_name('frontend_centrals.mjs')
    result=subprocess.run([binary,'--experimental-default-type=module',str(script),scenario],
        capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
