import { expect, test } from '@playwright/test';

/**
 * Target-side continuous visual regression example.
 *
 * For Legacy-vs-Target migration comparison use:
 * scripts/visual/visual_harness.mjs
 */
test('target visual regression', async ({ page }) => {
  await page.goto('/users');
  await expect(page.locator('table')).toBeVisible();
  await expect(page).toHaveScreenshot('USER-LIST-default.png', {
    fullPage: true,
    animations: 'disabled',
  });
});
