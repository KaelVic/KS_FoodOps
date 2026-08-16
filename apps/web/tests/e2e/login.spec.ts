import { test, expect } from '@playwright/test';

test.describe('Login & Tenant Selection Flow', () => {
  test('should login successfully and select a tenant', async ({ page }) => {
    // Navigate to the login page
    await page.goto('/login');

    // Check if the title is visible
    await expect(page.locator('text=KS FoodOps')).toBeVisible();

    // Fill in credentials
    await page.fill('input[type="email"]', 'admin@ksfoodops.com');
    await page.fill('input[type="password"]', 'admin123');

    // Click submit
    await page.click('button[type="submit"]');

    // Assert that we are redirected to tenant selection
    await expect(page).toHaveURL('/select-tenant');
    await expect(page.locator('text=Selecione a sua Operação')).toBeVisible();

    // Select the first tenant available
    const firstTenantButton = page.locator('button').filter({ hasText: 'Acessar Operação' }).first();
    await firstTenantButton.click();

    // Assert that we are redirected to the dashboard (root or sales/recipes)
    await expect(page).toHaveURL('/');
    // Check for a dashboard element
    await expect(page.locator('text=Visão Geral da Operação')).toBeVisible();
  });
});
