#!/usr/bin/env python3
import json, sys
from pathlib import Path
before=json.loads(Path(sys.argv[1]).read_text())
after=json.loads(Path(sys.argv[2]).read_text())
b={x['href']:x for x in before['labels']}
a={x['href']:x for x in after['labels']}
paired=[{'href':k,'text_before':v['label'],'text_after':a[k]['label'],'clipped_before':v['clipped'],'clipped_after':a[k]['clipped']} for k,v in b.items() if k in a]
result={'status':'UNKNOWN','app':'getarcaneapp/arcane@v2.10.2','issue':3899,'real_backend':True,'html_lang_before':before['language'],'html_lang_after':after['language'],'clipped_before':before['clippedCount'],'clipped_after':after['clippedCount'],'paired':paired}
if any('Tableau de bord' in x['label'] for x in before['labels']) and any('Tableau de bord' in x['label'] for x in after['labels']) and len(paired)>=3:
    if before['clippedCount']>0 and after['clippedCount']==0: result['status']='RUNTIME_FIX_SUPPORTED'
    elif before['clippedCount']==0: result['status']='BASELINE_BUG_NOT_REPRODUCED'
    else: result['status']='RUNTIME_FIX_NOT_ESTABLISHED'
print(json.dumps(result, ensure_ascii=False, indent=2))
