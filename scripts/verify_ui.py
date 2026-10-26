#!/usr/bin/env python3
"""Exercise DEMO UI. Default: normal HTTP browser. --dom-harness tests DOM/modules via API bridge.
The harness does not validate browser cookie transport, HTTP navigation, TLS or native fullscreen.
It exists for environments whose managed browser blocks all URL navigation. It changes no policy.
"""
from __future__ import annotations
import argparse,asyncio,json,os,re
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]

async def run(args):
    password=os.getenv(args.password_env)
    if not password:raise SystemExit('Defina a senha de teste em '+args.password_env)
    output=Path(args.screenshots);output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[];delay={'controllers':False}
    async with httpx.AsyncClient(base_url=args.url,timeout=45) as http:
        auth=await http.post('/api/auth/login',json={'username':args.username,'password':password})
        auth.raise_for_status()
        if auth.json()['mode']!='demo':raise SystemExit('Testes de UI recusados: execute apenas DEMO isolada.')
        async def bridge(url,init):
            if delay['controllers'] and url=='/api/controllers':await asyncio.sleep(1)
            headers=dict(init.get('headers',{}));headers['Origin']=args.url.rstrip('/')
            r=await http.request(init.get('method','GET'),url,headers=headers,content=init.get('body'))
            return {'body':r.text,'status':r.status_code,'headers':dict(r.headers)}
        # UI starts unauthenticated, including when an API bridge is used.
        http.cookies.clear()
        async with async_playwright() as p:
            opts={'headless':True}
            if args.chromium:opts['executable_path']=args.chromium
            if os.name!='nt' and getattr(os,'geteuid',lambda:1)()==0:opts['args']=['--no-sandbox']
            browser=await p.chromium.launch(**opts)
            page=await browser.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
            page.on('pageerror',lambda e:errors.append(str(e)))
            if args.dom_harness:
                await page.expose_function('__localTestTransport',bridge)
                html=(ROOT/'static/index.html').read_text(encoding='utf-8')
                html=re.sub(r'<script[^>]*src=.*?</script>','',html,flags=re.S)
                html=re.sub(r'<link[^>]+>','',html)
                html=html.replace('</head>','<style>'+(ROOT/'static/styles.css').read_text()+'</style></head>')
                await page.set_content(html)
                await page.evaluate('''() => {
                    const store=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k)}});
                    window.fetch=async(url,init={})=>{const r=await window.__localTestTransport(String(url),init);return new Response(r.body,{status:r.status,headers:r.headers});};
                }''')
                sources={f.name:f.read_text(encoding='utf-8') for f in (ROOT/'static').glob('*.js')}
                await page.evaluate(r'''async sources=>{
                    const cache={};function make(name){if(cache[name])return cache[name];let code=sources[name];code=code.replace(/from ['"]\.\/([^'"]+)['"]/g,(_,dep)=>`from '${make(dep)}'`);return cache[name]=URL.createObjectURL(new Blob([code],{type:'text/javascript'}));}
                    await import(make('theme.js'));await import(make('app.js'));
                }''',sources)
            else:await page.goto(args.url)
            await page.locator('#login-form [name=username]').fill(args.username)
            await page.locator('#login-form [name=password]').fill(password)
            await page.locator('#login-form button[type=submit]').click()
            await page.locator('.asset-card').first.wait_for(timeout=20000)
            assert await page.locator('.asset-card').count()==14
            assert await page.locator('.central-card').count()==2
            checks.append('Login, 14 UTAs e duas centrais')
            await page.screenshot(path=str(output/'01-dashboard-escuro.png'))
            await page.locator('#expand-button').click()
            assert 'expanded' in await page.locator('#app').get_attribute('class')
            await page.screenshot(path=str(output/'02-dashboard-expandido.png'))
            for aid,name in [(15,'CAG'),(16,'CAQ')]:
                await page.locator('#quick-nav').select_option(f'central/{aid}')
                await page.locator('#central-quality').wait_for()
                assert await page.locator('#central-quality').inner_text()=='Desconhecida'
                assert await page.locator('#content canvas').count()==2
                assert await page.locator('#adjust-button').count()==0
                assert 'expanded' in await page.locator('#app').get_attribute('class')
                await page.screenshot(path=str(output/f'central-{name.lower()}-escuro.png'))
            await page.locator('#next-uta').click()
            await page.locator('#register-live').wait_for()
            assert await page.locator('#quick-nav').input_value()=='uta/1'
            checks.append('CAG/CAQ desconhecidas, dois gráficos e navegação expandida circular')
            await page.locator('#quick-nav').select_option('uta/3')
            await page.locator('#register-live').wait_for()
            await page.wait_for_timeout(1500)
            assert await page.locator('#content canvas').count()==2
            assert 'expanded' in await page.locator('#app').get_attribute('class')
            checks.append('Troca de UTA preserva expansão; dois gráficos selecionáveis')
            await page.screenshot(path=str(output/'03-uta-detalhe.png'))
            await page.locator('[data-pause=register-live]').click()
            assert 'pausada' in await page.locator('[data-chart-status=register-live]').inner_text()
            await page.locator('[data-pause=register-live]').click()
            checks.append('Pausa e retomada apenas da visualização')
            await page.locator('[data-expand-chart=register-history]').click()
            await page.locator('#modal-asset').select_option('2')
            await page.wait_for_timeout(600)
            assert await page.locator('#modal-asset').input_value()=='2'
            assert 'expanded' in await page.locator('#app').get_attribute('class')
            await page.screenshot(path=str(output/'06-grafico-ampliado.png'))
            await page.locator('#dialog-close').click()
            checks.append('Gráfico ampliado com navegação entre UTAs')
            await page.locator('#theme-button').click()
            assert await page.locator('html').get_attribute('data-theme')=='light'
            await page.wait_for_timeout(300)
            await page.screenshot(path=str(output/'04-uta-claro.png'))
            await page.locator('#adjust-button').click()
            await page.locator('#adjust-form [name=value]').fill('23')
            await page.locator('#adjust-form [name=reason]').fill('Teste de interface em demonstração isolada')
            await page.locator('#adjust-form button[type=submit]').click()
            await page.locator('#confirm-command').wait_for()
            assert 'UTA 03' in await page.locator('#dialog-body').inner_text()
            await page.locator('#confirm-command').click()
            await page.locator('#dialog-overlay').wait_for(state='hidden')
            checks.append('Comando DEMO em duas etapas, destino e confirmação')
            async def route(name):
                await page.evaluate('(name)=>location.hash=name',name)
                await page.wait_for_timeout(600)
                assert await page.locator('.error-view').count()==0,name
            await route('maintenance')
            await page.locator('#new-ticket').click()
            await page.locator('#ticket-form [name=title]').fill('Verificação automatizada de bancada')
            await page.locator('#ticket-form [name=owner]').fill('Equipe de desenvolvimento')
            await page.locator('#ticket-form [name=details]').fill('Registro sintético criado pelo teste de UI.')
            await page.locator('#ticket-form button[type=submit]').click()
            await page.locator('#dialog-overlay').wait_for(state='hidden')
            checks.append('Registro de manutenção pela interface')
            await route('config/import')
            await page.locator('#import-form [name=controller_id]').select_option('3')
            await page.locator('#import-form [name=address_base]').select_option('0')
            await page.locator('#protocol-file').set_input_files(str(ROOT/'samples/protocolo-contrato-demo.txt'))
            await page.locator('#import-form button[type=submit]').click()
            await page.locator('#activate-map').wait_for()
            await page.locator('#activate-map [name=confirmation]').fill('CONFIRMO MAPA DE LEITURA')
            await page.locator('#activate-map button[type=submit]').click()
            await page.wait_for_timeout(800)
            assert 'Parâmetros' in await page.locator('#content').inner_text()
            checks.append('Importação e ativação de mapa fictício no CLP 3 sem escrita')
            for name in ['history','alarms','rooms','shift','ai','health','config/controllers','config/points','config/profiles','config/knowledge','config/users','audit']:
                await route(name)
            checks.append('12 rotas adicionais sem erro de renderização')
            await route('config/controllers')
            assert await page.locator('.controller-form').count()==3
            await route('config/profiles')
            await page.locator('[data-profile="16"]').click()
            await page.locator('#central-metadata-form').wait_for()
            assert await page.locator('#dialog-body [name=temperature_tolerance]').count()==0
            await page.locator('#central-metadata-form [name=sector]').fill('Setor fictício de bancada')
            await page.locator('#central-metadata-form [name=reason]').fill('Revisão de cadastro em demo temporária')
            await page.locator('#central-metadata-form button[type=submit]').click()
            await page.locator('#dialog-overlay').wait_for(state='hidden')
            checks.append('Três CLPs e cadastro da CAQ sem perfil de ventilação')
            await route('config/points')
            await page.locator('[data-tag]').first.click()
            await page.locator('#tag-form').wait_for()
            assert await page.locator('#tag-form [name=fan_confirmation_validated]').count()==0
            await page.locator('#dialog-close').click()
            await route('config/profiles')
            await page.locator('[data-profile="1"]').click()
            checkbox=page.locator('#profile-form [name=fan_confirmation_validated]')
            assert not await checkbox.is_checked()
            await checkbox.check()
            await page.locator('#profile-form [name=reason]').fill('Fixture: relação comando e retorno revisada em demo')
            async with page.expect_response(lambda r:'/api/assets/1' in r.url and r.request.method=='PUT') as response:
                await page.locator('#profile-form button[type=submit]').click()
            result=await (await response.value).json()
            assert result['profile']['fan_confirmation_validated'] is True
            await page.locator('#dialog-overlay').wait_for(state='hidden')
            checks.append('Comando/retorno: opt-in no perfil UTA, gravação e editor de tag preservado')
            if args.dom_harness:
                delay['controllers']=True
                await page.evaluate("location.hash='config/controllers'")
                await page.wait_for_timeout(150)
                await page.evaluate("location.hash='dashboard'")
                await page.wait_for_timeout(1500)
                assert await page.locator('.asset-card').count()==14
                delay['controllers']=False
                checks.append('Resposta atrasada não sobrescreve a tela atual')
            await route('ai')
            await page.locator('#ai-form button[type=submit]').click()
            await page.locator('#ai-answer .ai-result').wait_for(timeout=45000)
            checks.append('Diagnóstico consultivo na interface')
            await page.locator('#ai-form [name=history_hours]').select_option('24')
            await page.locator('#ai-form [name=history_metric]').select_option('temperature')
            async with page.expect_response(lambda r:'/api/ai/explain' in r.url and r.request.method=='POST') as response:
                await page.locator('#ai-form button[type=submit]').click()
            result=await (await response.value).json()
            assert result['evidence']['history']['hours']==24
            assert result['evidence']['history']['metrics']['temperature']['count']>0
            await page.locator('#ai-history-summary').wait_for()
            await page.screenshot(path=str(output/'ai-historico.png'))
            await page.locator('#ai-form [name=asset_id]').select_option('16')
            assert await page.locator('#ai-form [name=history_metric]').input_value()=='supply_temperature'
            async with page.expect_response(lambda r:'/api/ai/explain' in r.url and r.request.method=='POST') as response:
                await page.locator('#ai-form button[type=submit]').click()
            result=await (await response.value).json()
            assert result['evidence']['history']['metrics']['supply_temperature']['mean'] is None
            checks.append('Assistente histórico: período explícito, estatísticas UTA e CAQ sem valores inventados')
            await page.set_viewport_size({'width':390,'height':844})
            await route('dashboard')
            assert not await page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
            box=await page.locator('.workspace').bounding_box();assert box['width']>=389
            assert (await page.locator('.asset-card').first.bounding_box())['width']>120
            await page.locator('#mobile-menu').click()
            assert await page.locator('.sidebar').is_visible()
            await page.locator('#mobile-menu').click()
            await page.screenshot(path=str(output/'05-celular.png'))
            checks.append('Layout de 390 px sem transbordamento horizontal')
            await route('central/16')
            await page.locator('#central-quality').wait_for()
            assert not await page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
            await page.screenshot(path=str(output/'central-caq-celular.png'))
            checks.append('CAQ no celular sem transbordamento horizontal')
            if args.evidence_fixture:
                await page.set_viewport_size({'width':1400,'height':1000})
                await route('alarms')
                await page.locator('#alarm-state').select_option('all')
                await page.locator('tr',has_text='Evidence UI fixture').locator('[data-inspect]').click()
                await page.locator('#evidence-samples').click()
                await page.locator('#evidence-next').wait_for()
                assert 'stale' in await page.locator('#incident-snapshots').inner_text()
                await page.locator('#evidence-next').click()
                await page.locator('#evidence-next').wait_for(state='detached')
                assert '2 snapshot(s)' in await page.locator('#incident-snapshots').inner_text()
                await page.locator('#evidence-points').click()
                await page.wait_for_function("document.querySelector('#incident-snapshots')?.textContent.includes('fixture')")
                assert '1 snapshot(s)' in await page.locator('#incident-snapshots').inner_text()
                await page.screenshot(path=str(output/'evidence-dialog.png'))
                checks.append('Evidências: 102 amostras em duas páginas, nulos/stale e pontos do CLP')
            if args.mixed_fixture:
                await page.set_viewport_size({'width':1400,'height':1000})
                await route('history')
                await page.locator('#history-filter [name=hours]').select_option('720')
                async with page.expect_response(lambda r:'/api/assets/1/history?hours=720' in r.url) as response:
                    await page.locator('#history-filter button[type=submit]').click()
                result=await (await response.value).json()
                assert result['aggregation']=='mixed'
                assert {'hourly','raw'}<={r['aggregation'] for r in result['rows']}
                assert all(a['ts']<=b['ts'] for a,b in zip(result['rows'],result['rows'][1:]))
                await page.wait_for_timeout(300)
                await page.screenshot(path=str(output/'historico-misto.png'))
                checks.append('Histórico misto: agregado antigo e snapshots recentes no mesmo gráfico')
            assert not errors,errors
            report={'mode':'dom-harness' if args.dom_harness else 'http-browser','checks':checks,'javascript_errors':errors,
                    'native_fullscreen_validated':False,'tls_validated':False,
                    'notice':'Harness não valida cookies/navegação HTTP do navegador; testes de API verificam autenticação/CSRF separadamente.' if args.dom_harness else 'Ensaios em demo; hardware real não foi exercitado.'}
            (output/'ui-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(report,ensure_ascii=False,indent=2))
            await browser.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:8000');p.add_argument('--username',default='admin')
    p.add_argument('--password-env',default='HNSG_UI_PASSWORD');p.add_argument('--chromium')
    p.add_argument('--screenshots',default=str(ROOT/'docs/screenshots'));p.add_argument('--dom-harness',action='store_true')
    p.add_argument('--evidence-fixture',action='store_true',help='Exige ocorrência fictícia Evidence UI fixture com 102 amostras e um snapshot do CLP')
    p.add_argument('--mixed-fixture',action='store_true',help='Exige agregado antigo e snapshots recentes da UTA 1')
    asyncio.run(run(p.parse_args()))
