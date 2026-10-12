"""Compare two measured reports without mistaking missing coverage for a fix."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def evaluate(before: dict, after: dict) -> dict:
    b={r['id']:r for r in before['results']}
    a={r['id']:r for r in after['results']}
    if not b or not a or set(b)!=set(a):
        return {'status':'UNKNOWN','reason':'Coverage differs or empty','before_checks':len(b),'after_checks':len(a)}
    for key in b:
        if urlsplit(b[key].get('url','')).path != urlsplit(a[key].get('url','')).path:
            return {'status':'UNKNOWN','reason':f'URL path changed for {key}'}
        for field in ('locale','selector'):
            if b[key].get(field)!=a[key].get(field):
                return {'status':'UNKNOWN','reason':f'{field} changed for {key}'}
    if any(r['status']=='UNKNOWN' for r in list(b.values())+list(a.values())):
        return {'status':'UNKNOWN','reason':'Some observations are UNKNOWN'}
    if any(r['status']=='FAIL' for r in a.values()):
        return {'status':'REMAINING_DEFECTS','before_failed':sum(v['status']=='FAIL' for v in b.values()),'after_failed':sum(v['status']=='FAIL' for v in a.values())}
    old_fails=sum(v['status']=='FAIL' for v in b.values())
    return {'status':'FIX_VERIFIED_WITHIN_CHECKS' if old_fails else 'NO_REGRESSION_IN_CHECKED_REGIONS','before_failed':old_fails,'after_failed':0,'checked':len(a)}


def main(argv=None):
    p=argparse.ArgumentParser(description='Verify before/after visual gate observations')
    p.add_argument('--before',type=Path,required=True)
    p.add_argument('--after',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('comparison.json'))
    a=p.parse_args(argv)
    try:
        result=evaluate(json.loads(a.before.read_text()),json.loads(a.after.read_text()))
    except (ValueError,KeyError,FileNotFoundError) as e:
        print(f'UNKNOWN: {type(e).__name__}')
        return 2
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
    return 0 if result['status'] in ('FIX_VERIFIED_WITHIN_CHECKS','NO_REGRESSION_IN_CHECKED_REGIONS') else (1 if result['status']=='REMAINING_DEFECTS' else 2)

if __name__=='__main__':raise SystemExit(main())
