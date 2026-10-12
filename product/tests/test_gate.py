import json
import tempfile
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright
from lrg.core import DETECTOR_JS, load_config, main, safe_url, url_for

BASE=Path(__file__).parent.parent

def measure(file):
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        pg=b.new_page(viewport={'width':320,'height':760})
        pg.set_content((BASE/'tests'/'fixtures'/file).read_text(),wait_until='load')
        r=pg.evaluate(DETECTOR_JS,{'rootSelector':'[data-lrg-critical]','minTextLength':2,'ignoreSelector':'[data-lrg-ignore]','maxNodes':200,'minOverlapPixels':2})
        b.close()
        return r

def test_bad_detects_ellipsis_and_overlap():
    r=measure('bad.html')
    types={x['type'] for x in r['findings']}
    assert r['state']=='OK' and r['nodes']>=3
    assert 'TEXT_CLIPPED' in types
    assert 'TEXT_ICON_OVERLAP' in types

def test_good_passes():
    r=measure('good.html')
    assert r['state']=='OK',r
    assert not r['findings'],r['findings']

def test_missing_target_never_green():
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        pg=b.new_page();pg.set_content('<h1>hello</h1>')
        r=pg.evaluate(DETECTOR_JS,{'rootSelector':'#missing','minTextLength':2,'ignoreSelector':'[data-lrg-ignore]','maxNodes':200,'minOverlapPixels':2})
        assert r['state']=='MISSING_TARGET'
        b.close()

def test_url_auth_redaction():
    assert safe_url('https://u:password@host.tld:345/a?token=123#secret')=='https://host.tld:345/a'

def test_config_validation():
    a=load_config(BASE/'examples'/'offline.json')
    assert a['schema_version']=='1'
    assert url_for(a['base_url'],a['locales'][0],a['pages'][0]).endswith('/fr/bad')
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'bad.json';path.write_text('{"schema_version":"1","base_url":"file:///etc/passwd"}')
        with pytest.raises(ValueError): load_config(path)

def test_cli_bad_exit_and_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)/'out'
        status=main(['--config',str(BASE/'examples'/'offline.json'),'--fixture-mode','--chromium','/usr/bin/chromium','--output',str(dest)])
        report=json.loads((dest/'report.json').read_text())
        assert status==1 and report['status']=='FAIL'
        assert (dest/'report.html').exists() and list(dest.glob('*.png'))

def test_cli_good_exit():
    cfg=json.loads((BASE/'examples'/'offline.json').read_text());cfg['pages'][0]['fixture']='good.html'
    with tempfile.TemporaryDirectory() as tmp:
        cfgpath=Path(tmp)/'cfg.json';cfg['fixture_root']=str(BASE/'tests'/'fixtures')
        cfgpath.write_text(json.dumps(cfg))
        out=Path(tmp)/'out'
        assert main(['--config',str(cfgpath),'--fixture-mode','--chromium','/usr/bin/chromium','--output',str(out)])==0

def test_cli_unknown_missing_target():
    cfg=json.loads((BASE/'examples'/'offline.json').read_text());cfg['critical_selectors']=['#nothing'];cfg['fixture_root']=str(BASE/'tests'/'fixtures')
    with tempfile.TemporaryDirectory() as tmp:
        cfgpath=Path(tmp)/'cfg.json';cfgpath.write_text(json.dumps(cfg))
        assert main(['--config',str(cfgpath),'--fixture-mode','--chromium','/usr/bin/chromium','--output',str(Path(tmp)/'out')])==2

from lrg.compare import evaluate

def test_comparison_fix_and_regression_and_unknown():
    original={'results':[{'id':'a','locale':'fr','selector':'nav','status':'FAIL'}]}
    fixed={'results':[{'id':'a','locale':'fr','selector':'nav','status':'PASS'}]}
    assert evaluate(original,fixed)['status']=='FIX_VERIFIED_WITHIN_CHECKS'
    assert evaluate(original,original)['status']=='REMAINING_DEFECTS'
    assert evaluate(fixed,fixed)['status']=='NO_REGRESSION_IN_CHECKED_REGIONS'
    assert evaluate(original,{'results':[]})['status']=='UNKNOWN'
    assert evaluate(original,{'results':[{'id':'a','locale':'de','selector':'nav','status':'PASS'}]})['status']=='UNKNOWN'
    assert evaluate(original,{'results':[{'id':'a','locale':'fr','selector':'nav','status':'UNKNOWN'}]})['status']=='UNKNOWN'

def test_missing_locale_signal_rejected():
    obj=json.loads((BASE/'examples'/'offline.json').read_text())
    obj['locales'][0].pop('require_text')
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'cfg.json';path.write_text(json.dumps(obj))
        with pytest.raises(ValueError,match='require_text'):
            load_config(path)
