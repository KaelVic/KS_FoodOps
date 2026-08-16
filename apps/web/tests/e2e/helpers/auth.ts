import { Page, expect } from '@playwright/test';

export async function loginAndSelectTenant(page: Page) {
  await page.goto('/login');
  
  // Fill login form
  await page.fill('input[name="email"]', 'admin@example.com');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('button[type="submit"]');

  // Wait for tenant selection screen
  await expect(page).toHaveURL('/select-tenant');
  
  // Click first tenant
  await page.click('button[role="menuitem"]:first-of-type');

  // Wait for dashboard redirect
  await expect(page).toHaveURL('/dashboard');
}
