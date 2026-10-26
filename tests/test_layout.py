"""CSS layout regression, optional system Chromium. No external navigation."""
from pathlib import Path
import shutil
import pytest

@pytest.mark.parametrize('width',[390,768,1600])
def test_workspace_occupies_visible_column(width):
    binary=shutil.which('chromium') or shutil.which('chromium-browser')
    if not binary:pytest.skip('Chromium de sistema não instalado; repetir verify_ui no alvo')
    sync=pytest.importorskip('playwright.sync_api')
    css=(Path(__file__).resolve().parents[1]/'static/styles.css').read_text()
    with sync.sync_playwright() as p:
        browser=p.chromium.launch(executable_path=binary,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':width,'height':900})
        page.set_content('<style>'+css+'</style><div class="app-shell expanded"><aside class="sidebar">Menu</aside><div class="workspace"><header class="topbar">HNSG</header><main class="content">Teste</main></div></div>')
        box=page.locator('.workspace').bounding_box()
        try:assert box['width']>=width-1,box
        finally:browser.close()
