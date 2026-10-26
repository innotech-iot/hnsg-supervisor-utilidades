import json
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec=importlib.util.spec_from_file_location('hnsg_postgres_runner',Path(__file__).resolve().parents[1]/'scripts/verify_postgres.py')
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize('endpoint',['ssh://remote.invalid','tcp://127.0.0.1:2375','npipe:////server/pipe/docker_engine',''])
def test_postgres_runner_refuses_nonlocal_context(endpoint):
    with pytest.raises(ValueError,match='local'):runner.require_local_endpoint(endpoint)


@pytest.mark.parametrize('endpoint',['unix:///var/run/docker.sock','npipe:////./pipe/dockerDesktopLinuxEngine'])
def test_postgres_runner_accepts_local_socket(endpoint):
    runner.require_local_endpoint(endpoint)


@pytest.mark.parametrize('test_exit',[0,1])
def test_postgres_runner_cleans_own_project_and_sanitizes_artifacts(tmp_path,monkeypatch,test_exit):
    commands=[]
    project=[]
    password=[]
    def run(command,**kwargs):
        commands.append(command)
        if 'buildx' in command:return SimpleNamespace(returncode=0,stdout='Name: desktop-linux\nDriver: docker\n',stderr='')
        if 'inspect' in command:return SimpleNamespace(returncode=0,stdout='npipe:////./pipe/dockerDesktopLinuxEngine\n',stderr='')
        if 'up' in command:
            env=kwargs['env'];password.append(env['HNSG_PGTEST_PASSWORD'])
            assert env['BUILDX_BUILDER']=='desktop-linux'
            assert env['COMPOSE_BAKE']=='false'
            assert 'BUILDKIT_HOST' not in env and 'BUILDX_CONFIG' not in env
            project.append(command[command.index('--project-name')+1])
            output=Path(env['HNSG_PGTEST_ARTIFACTS'])
            (output/'pytest-postgres.xml').write_text(f'<testsuites><testsuite tests="5" failures="{test_exit}" errors="0" skipped="0"/></testsuites>')
            (output/'postgres-environment.json').write_text(json.dumps({'postgresql':'16-fixture','unexpected':password[0]}))
            return SimpleNamespace(returncode=test_exit,stdout='fixture secret: '+password[0],stderr='')
        return SimpleNamespace(returncode=0,stdout='',stderr='')
    monkeypatch.setenv('DATABASE_URL','postgresql://operational.invalid/never-use')
    monkeypatch.setenv('DOCKER_HOST','tcp://remote.invalid:2375')
    monkeypatch.setenv('BUILDX_BUILDER','fixture-remote-builder')
    monkeypatch.setenv('BUILDKIT_HOST','tcp://remote-builder.invalid:1234')
    monkeypatch.setenv('BUILDX_CONFIG','fixture-remote-config')
    monkeypatch.setenv('COMPOSE_BAKE','true')
    monkeypatch.setattr(runner.shutil,'which',lambda _: 'fixture-docker')
    monkeypatch.setattr(runner.subprocess,'run',run)
    output=tmp_path/'artifacts'
    assert runner.run_validation('desktop-linux',output)==test_exit
    downs=[c for c in commands if 'down' in c]
    assert len(downs)==1 and project[0] in downs[0]
    assert not any('prune' in c for c in commands)
    for path in output.iterdir():
        assert password[0] not in path.read_text()
        assert 'operational.invalid' not in path.read_text()
    report=json.loads((output/'report.json').read_text())
    assert report['tests']==5 and report['failures']==test_exit
    assert report['cleanup_succeeded'] is True


def test_postgres_runner_refuses_existing_output_directory(tmp_path):
    existing=tmp_path/'existing';existing.mkdir()
    keep=existing/'keep.txt';keep.write_text('preservar')
    with pytest.raises(FileExistsError):runner.run_validation('desktop-linux',existing)
    assert keep.read_text()=='preservar'


def test_postgres_runner_refuses_incomplete_offline_cache(tmp_path):
    output=tmp_path/'artifacts'
    cache=tmp_path/'packages';cache.mkdir()
    with pytest.raises(ValueError,match='cache'):runner.run_validation('desktop-linux',output,package_cache=cache)


def test_postgres_runner_rejects_non_docker_builder_before_compose(tmp_path,monkeypatch):
    commands=[]
    def run(command,**kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0,stdout='Driver: cloud\n' if 'buildx' in command else 'unix:///var/run/docker.sock\n',stderr='')
    monkeypatch.setattr(runner.shutil,'which',lambda _: 'fixture-docker')
    monkeypatch.setattr(runner.subprocess,'run',run)
    with pytest.raises(ValueError,match='builder'):runner.run_validation('default',tmp_path/'artifacts')
    assert not any('up' in command for command in commands)
