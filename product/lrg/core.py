"""Localization Visual Gate. Browser measurements are evidence, not proof of universal visual correctness."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright, Error as PlaywrightError

SUPPORTED_VERSION = '1'
DETECTOR_JS = (Path(__file__).parent / 'detector.js').read_text(encoding='utf-8')


def safe_url(raw: str) -> str:
    """Never serialize credentials, query strings or fragments to reports."""
    try:
        p=urlsplit(raw)
        return urlunsplit((p.scheme, p.hostname + ((':'+str(p.port)) if p.port else '') if p.hostname else '',p.path,'',''))
    except (ValueError, TypeError):
        return '[redacted]'


def load_config(path: Path) -> dict:
    obj=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj,dict) or obj.get('schema_version')!=SUPPORTED_VERSION:
        raise ValueError('config.schema_version must be "1"')
    base=obj.get('base_url')
    if not isinstance(base,str) or urlsplit(base).scheme not in ('http','https') or not urlsplit(base).hostname:
        raise ValueError('base_url must be http(s) with hostname')
    locales=obj.get('locales'); pages=obj.get('pages'); viewports=obj.get('viewports')
    for name,items in [('locales',locales),('pages',pages),('viewports',viewports)]:
        if not isinstance(items,list) or not items or len(items)>20:
            raise ValueError(f'{name} must have 1 to 20 items')
    for key, items in [('locales',locales),('pages',pages),('viewports',viewports)]:
        names=[x.get('name') for x in items if isinstance(x,dict)]
        if len(names)!=len(items) or len(set(names))!=len(names):
            raise ValueError(f'{key} entries require unique names')
    for x in locales:
        if not isinstance(x,dict) or not re.fullmatch(r'[A-Za-z0-9_-]{2,25}',x.get('name','')):
            raise ValueError('Each locale needs short name')
        if 'path_prefix' not in x and 'cookie' not in x and 'query_param' not in x:
            raise ValueError('Each locale needs path_prefix, query_param, or cookie')
        if not isinstance(x.get('require_text'),str) or not x['require_text'].strip():
            raise ValueError('Each locale requires require_text proving that locale is actually rendered')
        if 'cookie' in x and (not isinstance(x['cookie'],dict) or not x['cookie'].get('name') or 'value' not in x['cookie']):
            raise ValueError('locale.cookie requires name and value')
        if 'query_param' in x and (not isinstance(x['query_param'],dict) or not x['query_param'].get('name') or 'value' not in x['query_param']):
            raise ValueError('locale.query_param requires name and value')
    for x in pages:
        if not isinstance(x,dict) or not isinstance(x.get('path'),str) or not x['path'].startswith('/') or x['path'].startswith('//'):
            raise ValueError('Each page needs a relative absolute path starting with /')
        if not isinstance(x.get('name'),str) or not re.fullmatch(r'[\w-]{1,55}',x['name']):
            raise ValueError('Each page needs a safe slug name')
    for v in viewports:
        if not isinstance(v,dict) or not re.fullmatch(r'[\w-]{1,45}',v.get('name','')):
            raise ValueError('Each viewport needs safe name')
        if not all(isinstance(v.get(key),int) and not isinstance(v.get(key),bool) and 240<=v[key]<=3840 for key in ('width','height')):
            raise ValueError('Viewport dimensions must be integer 240..3840')
    selectors=obj.get('critical_selectors')
    if not isinstance(selectors,list) or not selectors or not all(isinstance(s,str) and s.strip() for s in selectors):
        raise ValueError('critical_selectors must have at least one CSS selector')
    if len(locales)*len(pages)*len(viewports)*len(selectors)>300:
        raise ValueError('Too many configured checks: max 300')
    auth=obj.get('storage_state')
    if auth is not None and not isinstance(auth,str):raise ValueError('storage_state must be file path')
    return obj


def url_for(base: str, locale: dict, page: dict) -> str:
    prefix=locale.get('path_prefix','')
    if not isinstance(prefix,str) or (prefix and (not prefix.startswith('/') or prefix.startswith('//'))):
        raise ValueError('path_prefix must start with /')
    path=(prefix.rstrip('/')+page['path']) if prefix else page['path']
    parsed=urlsplit(base)
    from urllib.parse import urlencode, parse_qsl
    q=dict(parse_qsl(parsed.query,keep_blank_values=True))
    qp=locale.get('query_param')
    if qp:q[qp['name']]=str(qp['value'])
    return urlunsplit((parsed.scheme,parsed.netloc,path,urlencode(q),'')).strip()


def check_page(page, spec: dict, cfg: dict) -> dict:
    selector=spec['selector']
    return page.evaluate(DETECTOR_JS, {
        'rootSelector': selector,
        'minTextLength':int(cfg.get('min_text_length',2)),
        'ignoreSelector': cfg.get('ignore_selector','[data-lrg-ignore]'),
        'maxNodes':int(cfg.get('max_text_nodes',200)),
        'minOverlapPixels':float(cfg.get('min_overlap_pixels',2)),
    })


def render_report(report: dict) -> str:
    css='''body{font:15px/1.6 system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 18px;color:#15202b}header{border-bottom:2px solid #d8e0e7}h1{font-size:28px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #d8e0e7;text-align:left;padding:10px;vertical-align:top}th{background:#f1f5f9}.bad{color:#a20f20;font-weight:700}.ok{color:#146933;font-weight:700}.unknown{color:#9e5500;font-weight:700}code{font-size:12px}a{color:#1269a3}small{color:#566}'''
    status=report['status']; rows=[]
    for entry in report['results']:
        link=html.escape(entry.get('screenshot',''))
        href=f'<a href="{link}">Screenshot</a>' if link else '—'
        finds='<ul>'+''.join(f'<li><code>{html.escape(f["type"])}</code>: {html.escape(f.get("text", ""))}</li>' for f in entry.get('findings',[]))+'</ul>' if entry.get('findings') else '—'
        rows.append(f'<tr><td>{html.escape(entry["id"])}</td><td class="{entry["status"].lower()}">{entry["status"]}</td><td>{len(entry.get("findings",[]))}</td><td>{finds}</td><td>{href}</td></tr>')
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Localization Visual Gate Report</title><style>{css}</style><body><header><h1>Localization Visual Gate</h1><p>Independent browser evidence, not a guarantee of visual correctness.</p><strong class="{status.lower()}">{status}</strong> &mdash; {len(report['results'])} checks</header><main><p>PASS: {report['summary']['pass']} &nbsp; FAIL: {report['summary']['fail']} &nbsp; UNKNOWN: {report['summary']['unknown']}</p><table><thead><tr><th>Page / locale / viewport / selector</th><th>Verdict</th><th>Findings</th><th>Detected defects</th><th>Evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p><small>FAIL indicates a detected issue. UNKNOWN includes navigation errors, missing elements and insufficient coverage; it must never be treated as PASS. Review screenshots before shipping.</small></p></main></body></html>'''


def scan(config_path: Path, output: Path, executable: str | None = None, fixture_mode: bool = False) -> dict:
    cfg=load_config(config_path)
    output.mkdir(parents=True,exist_ok=True)
    output=output.resolve(); results=[]
    fixture_root=(config_path.parent / cfg.get('fixture_root','')).resolve() if fixture_mode else None
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'] if executable else None)
        try:
            for locale in cfg['locales']:
                for entry in cfg['pages']:
                    for viewport in cfg['viewports']:
                        ident='-'.join((entry['name'],locale['name'],viewport['name']))
                        context=browser.new_context(viewport={'width':viewport['width'],'height':viewport['height']},storage_state=str(config_path.parent/cfg['storage_state']) if cfg.get('storage_state') else None)
                        page=context.new_page()
                        try:
                            url=url_for(cfg['base_url'],locale,entry)
                            c=locale.get('cookie')
                            if c:context.add_cookies([{'name':c['name'],'value':str(c['value']),'url':cfg['base_url']}])
                            if fixture_mode:
                                rel=entry.get('fixture')
                                if not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:
                                    raise ValueError('Fixture path must be relative and under fixture_root')
                                doc=(fixture_root/rel).resolve()
                                if not doc.is_relative_to(fixture_root):raise ValueError('Invalid fixture path')
                                page.set_content(doc.read_text(encoding='utf-8'),wait_until='load',timeout=20000)
                            else:
                                response=page.goto(url,wait_until='domcontentloaded',timeout=int(cfg.get('timeout_ms',20000)))
                                if not response or response.status>=400:raise RuntimeError(f'HTTP_ERROR:{response.status if response else "NO_RESPONSE"}')
                            page.wait_for_timeout(int(cfg.get('settle_ms',350)))
                            if not page.get_by_text(locale['require_text'],exact=False).count():
                                raise RuntimeError('LOCALE_TEXT_NOT_FOUND')
                            filename=f'{ident}.png';page.screenshot(path=str(output/filename),full_page=True)
                            for index,selector in enumerate(cfg['critical_selectors']):
                                rid=f'{ident}-s{index+1}'
                                try:
                                    measured=check_page(page,{'selector':selector},cfg)
                                    state=measured.get('state')
                                    status='UNKNOWN' if state!='OK' or measured.get('nodes',0)==0 else ('FAIL' if measured.get('findings') else 'PASS')
                                    results.append({'id':rid,'locale':locale['name'],'url':safe_url(url),'selector':selector,'status':status,'screenshot':filename,'findings':measured.get('findings',[]),'metrics':measured.get('metrics',{}),'error':state if status=='UNKNOWN' else None})
                                except Exception as err:
                                    results.append({'id':rid,'locale':locale['name'],'url':safe_url(url),'selector':selector,'status':'UNKNOWN','findings':[],'error':type(err).__name__})
                        except Exception as err:
                            for index,selector in enumerate(cfg['critical_selectors']):
                                results.append({'id':f'{ident}-s{index+1}','locale':locale['name'],'url':safe_url(url_for(cfg['base_url'],locale,entry)),'selector':selector,'status':'UNKNOWN','findings':[],'error':str(err).split('\n')[0][:180]})
                        finally:
                            context.close()
        finally:
            browser.close()
    summary={s.lower():sum(x['status']==s for x in results) for s in ('PASS','FAIL','UNKNOWN')}
    status='FAIL' if summary['fail'] else ('UNKNOWN' if summary['unknown'] else 'PASS')
    report={'tool':'Localization Visual Gate','schema_version':'1','status':status,'summary':summary,'results':results}
    (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    (output/'report.html').write_text(render_report(report),encoding='utf-8')
    return report


def main(argv=None) -> int:
    p=argparse.ArgumentParser(prog='lrg',description='Localization QA for running sites. Detect clipping and control/icon collisions.')
    p.add_argument('--config',required=True,type=Path)
    p.add_argument('--output',default='lrg-report',type=Path)
    p.add_argument('--chromium',help='Chromium binary path (optional)')
    p.add_argument('--fixture-mode',action='store_true',help='Offline demo with local HTML fixtures, not production verification')
    a=p.parse_args(argv)
    try:
        r=scan(a.config,a.output,a.chromium,a.fixture_mode)
    except (ValueError,FileNotFoundError,PlaywrightError) as e:
        print(f'CONFIG_OR_RUNTIME_ERROR: {e}',file=sys.stderr)
        return 2
    print(f"{r['status']}: {r['summary']} — {a.output}/report.html")
    return {'PASS':0,'FAIL':1,'UNKNOWN':2}[r['status']]

if __name__=='__main__':raise SystemExit(main())
