import { test, expect } from '@playwright/test';
import { loginAndSelectTenant } from './helpers/auth';

test.describe('Inventory Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndSelectTenant(page);
  });

  test('should view inventory radar and critical items', async ({ page }) => {
    await page.goto('/inventory');
    
    await expect(page.getByRole('heading', { name: 'Radar de Estoque' })).toBeVisible();
    
    // Check KPIs
    await expect(page.getByText('Itens Críticos')).toBeVisible();
    await expect(page.getByText('Capital Alocado')).toBeVisible();
    await expect(page.getByText('Risco Teórico')).toBeVisible();

    // Check Data Table
    await expect(page.getByRole('table')).toBeVisible();
  });

  test('should open inventory session modal', async ({ page }) => {
    await page.goto('/inventory');
    
    await page.getByRole('button', { name: 'Nova Contagem' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Nova Sessão de Contagem')).toBeVisible();
  });
});
