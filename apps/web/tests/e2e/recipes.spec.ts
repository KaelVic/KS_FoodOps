import { test, expect } from '@playwright/test';
import { loginAndSelectTenant } from './helpers/auth';

test.describe('Recipes Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndSelectTenant(page);
  });

  test('should view recipes and switch tabs', async ({ page }) => {
    await page.goto('/recipes');
    
    await expect(page.getByRole('heading', { name: 'Engenharia de Menu' })).toBeVisible();
    
    // Check KPIs
    await expect(page.getByText('Total de Fichas')).toBeVisible();
    await expect(page.getByText('Custo Médio / Porção')).toBeVisible();

    // Switch Tabs
    await page.getByRole('tab', { name: 'Pré-preparos (Bases)' }).click();
    await expect(page.getByRole('tab', { name: 'Pré-preparos (Bases)' })).toHaveAttribute('data-state', 'active');
    
    await page.getByRole('tab', { name: 'Itens de Menu (Pratos)' }).click();
    await expect(page.getByRole('tab', { name: 'Itens de Menu (Pratos)' })).toHaveAttribute('data-state', 'active');
  });

  test('should open new recipe modal', async ({ page }) => {
    await page.goto('/recipes');
    
    await page.getByRole('button', { name: 'Nova Ficha Técnica' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Cadastrar Ficha Técnica' })).toBeVisible();
  });
});
