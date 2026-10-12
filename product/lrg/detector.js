({ rootSelector, minTextLength, ignoreSelector, maxNodes, minOverlapPixels }) => {
  const root = document.querySelector(rootSelector);
  if (!root) return { state:'MISSING_TARGET', rootSelector, nodes:0, findings:[], metrics: {} };
  const box = r => ({ x:r.x, y:r.y, width:r.width, height:r.height, left:r.left, right:r.right, top:r.top, bottom:r.bottom });
  const overlap = (a,b) => ({w: Math.max(0, Math.min(a.right,b.right)-Math.max(a.left,b.left)), h:Math.max(0, Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)) });
  const clipX = v => ['hidden','clip'].includes(v);
  const clipY = v => ['hidden','clip'].includes(v);
  const visible = el => {
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    if (cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0||r.width<1||r.height<1) return false;
    if (el.closest('[aria-hidden="true"], [hidden], [inert]')) return false;
    if (ignoreSelector && el.closest(ignoreSelector)) return false;
    return true;
  };
  const nodes=[];
  const walk=document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {acceptNode(n) {
    const el=n.parentElement;
    if (!el || !visible(el)) return NodeFilter.FILTER_REJECT;
    if (['SCRIPT','STYLE','NOSCRIPT','TEXTAREA','OPTION','SVG','TITLE'].includes(el.tagName)) return NodeFilter.FILTER_REJECT;
    if ((n.textContent||'').trim().length < minTextLength) return NodeFilter.FILTER_REJECT;
    return NodeFilter.FILTER_ACCEPT;
  }});
  while (nodes.length<maxNodes && walk.nextNode()) nodes.push(walk.currentNode);
  const findings=[];
  const seen=new Set();
  const emit=(type,el,details={})=>{
    const text=(el.textContent||'').trim().replace(/\s+/g,' ').slice(0,110);
    const key=[type,text,el.tagName,details.ancestor || ''].join('|');
    if(seen.has(key)) return;
    seen.add(key);
    findings.push({type,severity:'error',text,tag:el.tagName.toLowerCase(),testId:el.getAttribute('data-testid'),details});
  };
  for (const n of nodes) {
    const el=n.parentElement; if(!el)continue;
    const range=document.createRange();range.selectNodeContents(n);
    const rects=Array.from(range.getClientRects()).filter(r=>r.width>0.5&&r.height>0.5);
    const cs=getComputedStyle(el);
    const elRect=el.getBoundingClientRect();
    if ((clipX(cs.overflowX) && el.scrollWidth > el.clientWidth+1 && cs.whiteSpace==='nowrap') ||
       ((cs.textOverflow==='ellipsis' || cs.textOverflow==='clip') && el.scrollWidth>el.clientWidth+1 && clipX(cs.overflowX))) {
      emit('TEXT_CLIPPED',el,{source:'element-scrollwidth',scrollWidth:el.scrollWidth,clientWidth:el.clientWidth});
    }
    for (const r of rects) {
      if (r.left < -1 || r.right > innerWidth+1) {
        const amount=Math.max(0,-r.left,r.right-innerWidth);
        if (amount>minOverlapPixels) emit('TEXT_OUTSIDE_VIEWPORT',el,{amount,rect:box(r)});
      }
      let cur=el;
      while(cur && cur instanceof Element) {
        const st=getComputedStyle(cur), br=cur.getBoundingClientRect();
        const dx = clipX(st.overflowX) ? Math.max(0,br.left-r.left,r.right-br.right) : 0;
        const dy = clipY(st.overflowY) ? Math.max(0,br.top-r.top,r.bottom-br.bottom) : 0;
        if(dx > minOverlapPixels || dy>minOverlapPixels) emit('TEXT_CLIPPED',el,{source:'ancestor',ancestor:cur.tagName.toLowerCase(),clippedPixels:Math.max(dx,dy)});
        if(cur===root)break;
        cur=cur.parentElement;
      }
    }
    // Overlapping icons within one interactive control are visible to humans despite no CSS overflow.
    const control=el.closest('a,button,[role="button"]');
    if (control && root.contains(control)) {
      for(const icon of control.querySelectorAll('svg, img, [data-lrg-icon]')) {
        if(icon.contains(el)) continue;
        const iconStyle=getComputedStyle(icon);
        if(iconStyle.display==='none' || iconStyle.visibility==='hidden' || Number(iconStyle.opacity)===0) continue;
        const ir=icon.getBoundingClientRect();
        for(const r of rects){const cross=overlap(ir,r);
          if(cross.w > minOverlapPixels && cross.h > minOverlapPixels)emit('TEXT_ICON_OVERLAP',el,{icon:icon.tagName.toLowerCase(),pixels:Math.round(cross.w*cross.h),textRect:box(r),iconRect:box(ir)});
        }
      }
    }
  }
  const interactive=Array.from(root.querySelectorAll('a,button,[role="button"]')).filter(visible);
  for(let i=0;i<interactive.length;i++){
    for(let j=i+1;j<interactive.length;j++){
      const a=interactive[i],b=interactive[j];if(a.contains(b)||b.contains(a))continue;
      const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect(); const cross=overlap(ar,br);
      if (cross.w>minOverlapPixels && cross.h>minOverlapPixels && cross.w*cross.h>25) {
        emit('CONTROL_OVERLAP',a,{against:(b.getAttribute('aria-label')||b.textContent||'').trim().slice(0,60),pixels:Math.round(cross.w*cross.h),rect:box(ar),otherRect:box(br)});
      }
    }
  }
  return {state:'OK',rootSelector, nodes:nodes.length,findings,metrics:{textNodes:nodes.length,interactiveControls:interactive.length,rootBox:box(root.getBoundingClientRect())}};
}
