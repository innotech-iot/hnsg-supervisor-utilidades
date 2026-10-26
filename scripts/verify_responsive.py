"""Read-only UI checks against an explicitly selected DEMO server."""
import argparse
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

SIZES=[(360,800),(390,844),(768,1024),(820,1180),(844,390),(1024,768),(1440,1000)]


async def route_to(page,route):
    await page.evaluate('''route=>new Promise(resolve=>{location.hash=route;
        requestAnimationFrame(()=>requestAnimationFrame(resolve));})''',route)
    await page.wait_for_function('''()=>!document.querySelector('#content .loading-view')&&
        !!document.querySelector('#content .page-head, #content .error-view')''')
    assert not await page.locator('.error-view').count(),route


async def layout_check(page,width,route):
    overflows=await page.evaluate("""()=>['.content','.topbar','.compact-nav'].filter(s=>{
        const e=document.querySelector(s);return e.offsetParent!==null&&e.scrollWidth>e.clientWidth+2;
    })""")
    assert not overflows,(width,route,overflows)
    clipped=await page.evaluate("""()=>[...document.querySelectorAll('.panel input,.panel select,.panel textarea,.panel .button')].filter(e=>{
        if(!e.getClientRects().length||e.closest('.table-scroll'))return false;
        const r=e.getBoundingClientRect(),p=e.closest('.panel').getBoundingClientRect();
        return r.left<p.left-2||r.right>p.right+2;
    }).map(e=>e.id||e.name||e.className)""")
    assert not clipped,(width,route,clipped)
    if width<=1024:
        tiny=await page.evaluate("""()=>[...document.querySelectorAll('#app input,#app select,#app textarea')].filter(e=>
            e.getClientRects().length&&e.type!=='checkbox'&&e.type!=='radio'&&parseFloat(getComputedStyle(e).fontSize)<16
        ).map(e=>e.id||e.name)""")
        assert not tiny,(width,route,tiny)


async def run(args):
    password=os.environ.get('HNSG_UI_PASSWORD')
    if not password:raise SystemExit('Defina HNSG_UI_PASSWORD')
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path=args.chromium)
        page=await browser.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        await page.goto(args.url)
        assert await page.locator('.login-story img').count()==1,'Logo Innotech ausente'
        title=' '.join((await page.locator('.login-copy h1').inner_text()).split())
        assert title.casefold()=='Hospital Nossa Senhora das Graças'.casefold(),title
        for width,height in SIZES:
            await page.set_viewport_size({'width':width,'height':height})
            assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
            assert await page.locator('.login-story img').evaluate('(e)=>e.complete&&e.naturalWidth>0')
            if width<=1024:
                assert await page.locator('#login-form input').first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)>=16')
            await page.screenshot(path=str(output/f'login-{width}.png'))
        await page.locator('#login-form [name=password]').fill(password)
        async with page.expect_response(lambda r:r.url.endswith('/api/auth/login')) as response:
            await page.locator('#login-form button[type=submit]').click()
        assert (await (await response.value).json())['mode']=='demo','Somente demo autorizada para ensaio'
        await page.locator('.asset-card').first.wait_for()
        routes=['dashboard','uta/1','central/16','history','alarms','shift','maintenance','rooms','ai','health',
                'config/controllers','config/points','config/profiles','audit']
        for theme in ('dark','light'):
            await page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
            for width,height in SIZES:
                await page.set_viewport_size({'width':width,'height':height})
                for route in routes:
                    await route_to(page,route)
                    await layout_check(page,width,route)
                if await page.locator('#mobile-menu').is_visible():
                    button=page.locator('#mobile-menu');box=await button.bounding_box()
                    assert box['width']>=44 and box['height']>=44,(width,box)
                    await button.click();await page.locator('#sidebar-logout').wait_for(state='visible')
                    assert await page.locator('#sidebar-nav').evaluate('(e)=>e.clientHeight>=44')
                    assert await page.locator('#sidebar-logout').evaluate('(e)=>{let r=e.getBoundingClientRect();return r.bottom<=innerHeight&&r.top>=0;}')
                    await page.screenshot(path=str(output/f'menu-{theme}-{width}.png'))
                    await button.click()
                await route_to(page,'config/profiles')
                await page.locator('[data-profile="1"]').click()
                await page.locator('#profile-form').wait_for(state='visible')
                assert await page.locator('#dialog-body').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
                await page.locator('#dialog-close').click()
                await page.locator('#expand-button').click()
                await page.locator('#compact-nav').wait_for(state='visible')
                await page.locator('#quick-nav').select_option('uta/1')
                await page.locator('#detail-period').wait_for(state='visible')
                await layout_check(page,width,'expanded uta')
                await page.locator('#adjust-button').click()
                await page.locator('#adjust-form').wait_for(state='visible')
                assert await page.locator('#dialog-body').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
                await page.screenshot(path=str(output/f'dialog-{theme}-{width}.png'))
                await page.locator('#dialog-close').click()
                await page.locator('#expand-button').click()
                await route_to(page,'dashboard')
                await page.screenshot(path=str(output/f'app-{theme}-{width}.png'))
                checks.append({'theme':theme,'width':width,'routes':len(routes)})
        assert not errors,errors
        report={'checks':checks,'javascript_errors':errors,'mode':'demo','browser':'Chrome',
            'limitations':['Viewport emulado; dispositivos físicos, Safari e teclado virtual não testados.']}
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False));await browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8001')
    parser.add_argument('--chromium',required=True)
    parser.add_argument('--output',default='docs/screenshots/2026-10-15-responsivo')
    asyncio.run(run(parser.parse_args()))
