import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: '.',
  testMatch: 'lrg_runtime.spec.ts',
  timeout: 90000,
  expect: { timeout: 20000 },
  workers: 1,
  retries: 0,
  reporter: [['line'], ['json', { outputFile: process.env.PW_JSON || 'lrg-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:3000',
    ...devices['Desktop Chrome'],
    viewport: { width: 320, height: 760 },
    serviceWorkers: 'block',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure'
  }
});
