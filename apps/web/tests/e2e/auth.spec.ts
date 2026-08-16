import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should login successfully and select a tenant', async ({ page }) => {
    await page.goto('/login');
    
    await expect(page.getByRole('heading', { name: 'KS FoodOps' })).toBeVisible();
    
    await page.getByLabel('E-mail').fill('admin@example.com');
    await page.getByLabel('Senha').fill('admin123');
    await page.getByRole('button', { name: 'Entrar' }).click();

    await expect(page).toHaveURL('/select-tenant');
    await expect(page.getByText('Selecione uma Operação')).toBeVisible();

    await page.getByRole('button').first().click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Command Center')).toBeVisible();
  });

  test('should fail login with incorrect password', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('E-mail').fill('admin@example.com');
    await page.getByLabel('Senha').fill('wrongpassword');
    await page.getByRole('button', { name: 'Entrar' }).click();

    await expect(page.getByText('Invalid email or password')).toBeVisible();
  });
});
