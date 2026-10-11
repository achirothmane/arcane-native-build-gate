import { test, expect } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const output = process.env.EVIDENCE_DIR || '/tmp/lrg-evidence';
const variant = process.env.VARIANT || 'unknown';

test('running Arcane: French mobile navigation before and after candidate', async ({ page }) => {
  mkdirSync(output, { recursive: true });
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Username').fill('arcane');
  await page.getByLabel('Password').fill('arcane-admin');
  await page.getByRole('button', { name: 'Sign in to Arcane', exact: true }).click();
  await page.waitForURL('**/dashboard', { timeout: 25000 });
  const modal = page.getByRole('dialog', { name: 'Change Default Password' });
  if (await modal.isVisible().catch(() => false)) {
    await modal.getByRole('textbox', { name: 'Current Password' }).fill('arcane-admin');
    await modal.getByRole('textbox', { name: 'New Password', exact: true }).fill('Test-password-123');
    await modal.getByRole('textbox', { name: 'Confirm New Password' }).fill('Test-password-123');
    await modal.getByRole('button', { name: 'Change Password' }).click();
    await expect(modal).toBeHidden({ timeout: 15000 });
  }
  await page.context().addCookies([{ name: 'locale', value: 'fr', url: 'http://127.0.0.1:3000/' }]);
  await page.goto('/containers', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1200);
  const nav = page.locator('[data-testid="mobile-floating-nav"], [data-testid="mobile-docked-nav"]');
  await expect(nav).toBeVisible({ timeout: 20000 });
  const anchors = nav.locator('[data-testid="mobile-nav-item"]');
  await expect(anchors.first()).toBeVisible();
  const info = await anchors.evaluateAll(nodes => nodes.map((node: any) => {
    const label = node.querySelector('span:not(.sr-only)');
    if (!label) return null;
    const rect = label.getBoundingClientRect();
    const overflow = label.scrollWidth > label.clientWidth + 1 || label.scrollHeight > label.clientHeight + 1;
    const range = document.createRange();
    range.selectNodeContents(label);
    const fragments = [...range.getClientRects()].map(b => ({left:b.left,right:b.right,top:b.top,bottom:b.bottom}));
    const visibleTextOutside = fragments.some(b => b.left < rect.left - 2 || b.right > rect.right + 2 || b.top < rect.top - 2 || b.bottom > rect.bottom + 2);
    return {
      label: label.textContent?.trim() || '',
      href: node.getAttribute('href'),
      clipped: overflow || visibleTextOutside,
      textOverflow: getComputedStyle(label).textOverflow,
      clientWidth: label.clientWidth,
      scrollWidth: label.scrollWidth,
      clientHeight: label.clientHeight,
      scrollHeight: label.scrollHeight,
      box: {x:rect.x,y:rect.y,width:rect.width,height:rect.height},
      fragments
    };
  }).filter(Boolean)) as any[];
  const language = await page.locator('html').getAttribute('lang');
  const navBox = await nav.boundingBox();
  const result = {variant,language,url:page.url(),navBox,viewport:{width:320,height:760},labels:info,clippedCount:info.filter(x=>x.clipped).length,capturedAt:new Date().toISOString()};
  const base = join(output, variant + '-french-mobile');
  writeFileSync(base + '.json', JSON.stringify(result, null, 2));
  await page.screenshot({path:base + '.png',fullPage:true});
  console.log('LIVE_ARCANE_EVIDENCE ' + JSON.stringify({variant,language,clippedCount:result.clippedCount,labels:info.map(x=>({label:x.label,clipped:x.clipped,clientWidth:x.clientWidth,scrollWidth:x.scrollWidth}))}));
  expect(language, 'French locale must be active').toBe('fr');
  expect(info.some(x => /Tableau|Conteneurs|Projets|Images/i.test(x.label)), 'Actual French labels must be present').toBe(true);
  expect(info.length).toBeGreaterThanOrEqual(3);
  expect(navBox!.x).toBeGreaterThanOrEqual(-2);
  expect(navBox!.x + navBox!.width).toBeLessThanOrEqual(322);
  const target = nav.locator('a[href="/containers"]');
  await expect(target).toBeVisible();
  await target.click();
  await expect(page).toHaveURL(/\/containers$/);
});
