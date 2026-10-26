"""Read-only demo UI check; password supplied through HNSG_UI_PASSWORD."""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    output=Path('docs/screenshots/2026-10-16-uta-layout')
    output.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
        page=await browser.new_page()
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        await page.goto('http://127.0.0.1:8001')
        await page.locator('input[name=username]').fill('admin')
        await page.locator('input[name=password]').fill(os.environ['HNSG_UI_PASSWORD'])
        await page.locator('#login-form button[type=submit]').click()
        await page.locator('.asset-card').first.wait_for()
        assert await page.evaluate("async()=>{const {ctx}=await import('/static/core.js');return ctx.state.mode}")=='demo'
        await page.evaluate("location.hash='uta/1'")
        await page.locator('#register-live').wait_for()
        checks=[]
        for theme in ['dark','light']:
            await page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
            for width in [360,768,1440,1920]:
                await page.set_viewport_size({'width':width,'height':1100})
                assert await page.evaluate("document.querySelector('.content').scrollWidth<=document.querySelector('.content').clientWidth+2")
                operation=await page.locator('.uta-operation-grid').bounding_box()
                if width>=1440:
                    syn=await page.locator('.uta-operation-grid>.panel').first.bounding_box()
                    live=await page.locator('[data-chart-panel=register-live]').bounding_box()
                    assert syn['x']+syn['width']<=live['x']+1
                    assert await page.locator('.uta-scene-scroll').evaluate('e=>e.scrollWidth<=e.clientWidth+2')
                history=await page.locator('[data-chart-panel=register-history]').bounding_box()
                assert history['y']>=operation['y']+operation['height']
                await page.locator('.uta-operation-grid').screenshot(path=str(output/f'{theme}-{width}.png'))
                checks.append({'theme':theme,'width':width})
        await page.locator('#register-live-unit').select_option('%')
        assert await page.locator('#register-live-points input').count()==3
        for key in ['heating','fan_speed']:
            await page.locator(f'#register-live-points input[value={key}]').check()
        state=await page.evaluate("async()=>{const {ctx}=await import('/static/core.js');const r=ctx.charts.find(r=>r.id==='register-live');return {keys:r.chart.options.series.map(s=>s.key),unit:r.chart.options.unit,fan:ctx.state.assets[0].data.fan_speed??null}}")
        assert state=={'keys':['cooling','heating','fan_speed'],'unit':'%','fan':None},state
        for key in state['keys']:
            await page.locator(f'#register-live-points input[value={key}]').uncheck()
        assert 'Selecione' in await page.locator('[data-register-legend=register-live]').inner_text()
        await page.locator('#register-history-unit').select_option('m³/h')
        await page.locator('#detail-period').select_option('24')
        await page.locator('#register-live-points input[value=fan_speed]').check()
        await page.locator('[data-expand-chart=register-live]').click()
        await page.locator('#expanded-chart').wait_for()
        assert 'Velocidade' in await page.locator('#expanded-chart').get_attribute('aria-label')
        await page.locator('#modal-asset').select_option('2')
        await page.locator('#modal-hours').select_option('24')
        await page.locator('#modal-unit').select_option('% UR')
        await page.locator('#modal-points input[value=humidity_sp]').check()
        await page.locator('#reset-zoom').click()
        assert 'Umidade' in await page.locator('#expanded-chart').get_attribute('aria-label')
        await page.locator('#dialog-close').click()
        assert not errors,errors
        (output/'report.json').write_text(json.dumps({'checks':checks,'errors':errors,'selection':state,
            'empty_selection':True,'expand':True,'history_period':True,'mode':'demo'},indent=2),encoding='utf-8')
        print('8 viewport/theme checks; multi-selection, unit filtering, missing speed, empty selection, expansion and history period passed.')
        await browser.close()


if __name__=='__main__':
    asyncio.run(main())
