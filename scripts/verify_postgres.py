#!/usr/bin/env python3
"""Run a disposable local PostgreSQL integration harness; never uses DATABASE_URL."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def require_local_endpoint(endpoint):
    endpoint=endpoint.strip()
    if not (endpoint.startswith('unix:///') or endpoint.startswith('npipe:////./pipe/')):
        raise ValueError('Ensaio exige contexto Docker local por socket/pipe; endpoint remoto/TCP recusado')


def redact(text,values):
    for value in values:text=text.replace(value,'[REDACTED]')
    return text


def run_validation(context,output_dir,package_cache=None):
    output=Path(output_dir).resolve()
    output.mkdir(parents=True,exist_ok=False)
    if package_cache is not None:
        package_cache=Path(package_cache).resolve()
        if not (package_cache/'packages/repositories').is_file() or not (package_cache/'wheels').is_dir():
            raise ValueError('cache offline incompleto: requer packages/repositories e wheels')
    binary=shutil.which('docker')
    if not binary:raise ValueError('Docker/Compose local não disponível')
    env=os.environ.copy()
    # Explicit context overrides endpoints; inherited connection overrides are removed.
    for name in ['DATABASE_URL','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH',
                 'BUILDX_BUILDER','BUILDX_CONFIG','BUILDKIT_HOST','COMPOSE_BAKE','COMPOSE_DOCKER_CLI_BUILD']:
        env.pop(name,None)
    for name in list(env):
        if name.startswith('HNSG_PGTEST_'):env.pop(name)
    if context is None:
        result=subprocess.run([binary,'context','show'],env=env,capture_output=True,text=True,timeout=30)
        if result.returncode:raise ValueError('Não foi possível identificar contexto Docker local')
        context=result.stdout.strip()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,80}',context):raise ValueError('Nome de contexto inválido')
    result=subprocess.run([binary,'context','inspect',context,'--format','{{.Endpoints.docker.Host}}'],
        env=env,capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('Contexto Docker não encontrado')
    require_local_endpoint(result.stdout)
    # Engine locality alone does not constrain a cloud/remote Buildx builder.
    env.update(BUILDX_BUILDER=context,COMPOSE_BAKE='false',DOCKER_BUILDKIT='1')
    result=subprocess.run([binary,'--context',context,'buildx','inspect',context],
        env=env,capture_output=True,text=True,timeout=30)
    if result.returncode or not re.search(r'^Driver:\s+docker\s*$',result.stdout,re.MULTILINE):
        raise ValueError('Ensaio exige builder Docker integrado ao contexto local; builder externo recusado')
    project='hnsg-pgtest-'+secrets.token_hex(8)
    credentials=[secrets.token_urlsafe(32) for _ in range(3)]
    env.update(HNSG_PGTEST_PASSWORD=credentials[0],HNSG_PGTEST_ADMIN_PASSWORD=credentials[1],
        HNSG_PGTEST_TOKEN=credentials[2],HNSG_PGTEST_SOURCE=ROOT.as_posix(),HNSG_PGTEST_ARTIFACTS=output.as_posix())
    if package_cache is not None:
        env.update(HNSG_PGTEST_PACKAGE_CACHE=package_cache.as_posix(),
            HNSG_PGTEST_DOCKERFILE='tests/postgres/Dockerfile.offline')
    compose=[binary,'--context',context,'compose','--project-name',project,
        '--file',str(ROOT/'tests/postgres/compose.yml')]
    exit_code=2;cleanup_ok=False;logs=[]
    try:
        result=subprocess.run(compose+['up','--build','--abort-on-container-exit','--exit-code-from','tests'],
            env=env,capture_output=True,text=True,timeout=1200)
        logs.extend([result.stdout,result.stderr]);exit_code=result.returncode
    except subprocess.TimeoutExpired as exc:
        logs.append('Timeout do ensaio PostgreSQL')
        for value in [exc.stdout,exc.stderr]:
            if value:logs.append(value.decode(errors='replace') if isinstance(value,bytes) else value)
    finally:
        try:
            result=subprocess.run(compose+['down','--volumes','--remove-orphans','--rmi','local'],
                env=env,capture_output=True,text=True,timeout=60)
            logs.extend([result.stdout,result.stderr]);cleanup_ok=result.returncode==0
        except (OSError,subprocess.TimeoutExpired):logs.append('Falha ao remover recursos do projeto '+project)
        (output/'compose.log').write_text(redact('\n'.join(logs),credentials),encoding='utf-8')
        for name in ['pytest-postgres.xml','postgres-environment.json']:
            path=output/name
            if path.exists():path.write_text(redact(path.read_text(encoding='utf-8'),credentials),encoding='utf-8')
        counts={'tests':0,'failures':0,'errors':0,'skipped':0}
        junit=output/'pytest-postgres.xml'
        if junit.exists():
            try:
                suites=ET.parse(junit).getroot().iter('testsuite')
                for suite in suites:
                    for key in counts:counts[key]+=int(suite.get(key,'0'))
            except (ET.ParseError,ValueError):counts['errors']+=1
        ok=exit_code==0 and counts['tests']>0 and not any(counts[key] for key in ['failures','errors','skipped']) and cleanup_ok
        report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'context':context,'project':project,
            **counts,'compose_exit_code':exit_code,'cleanup_succeeded':cleanup_ok,'passed':ok,
            'operational_database_used':False,'ports_published':False,'plcs_connected':False,
            'notice':'Contêiner descartável; não valida ARM64/Raspberry, disco independente ou instalação hospitalar.'}
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    print('Artefatos: '+str(output))
    if not ok:
        print(redact('\n'.join(logs),credentials)[-6000:],file=sys.stderr)
    return 0 if ok else exit_code or 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context',help='Contexto Docker local; padrão: contexto atual sem DOCKER_HOST')
    parser.add_argument('--output-dir',type=Path,help='Diretório novo e exclusivo para evidências')
    parser.add_argument('--package-cache',type=Path,help='Cache opcional de APKs assinados e wheels para build sem rede')
    args=parser.parse_args()
    output=args.output_dir or ROOT/'docs/postgres-tests'/('run-'+secrets.token_hex(8))
    try:return run_validation(args.context,output,args.package_cache)
    except (ValueError,FileExistsError,OSError) as exc:
        print('Ensaio bloqueado: '+str(exc),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
