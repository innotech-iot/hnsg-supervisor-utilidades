import shutil
import subprocess
from pathlib import Path

import pytest


def test_mixed_chart_uses_local_resolution():
    node=shutil.which('node')
    if not node:pytest.skip('Node indisponível para teste de módulo nativo')
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([node,str(root/'tests/history_mixed.mjs')],cwd=root,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('scenario',['tag','profile'])
def test_fan_authorization_in_profile_only(scenario):
    node=shutil.which('node')
    if not node:pytest.skip('Node indisponível')
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([node,str(root/'tests/frontend_fan.mjs'),scenario],cwd=root,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
