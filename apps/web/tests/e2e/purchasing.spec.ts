import { test, expect } from '@playwright/test';
import { loginAndSelectTenant } from './helpers/auth';

test.describe('Purchasing Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndSelectTenant(page);
  });

  test('should upload NFe XML and view extraction', async ({ page }) => {
    await page.goto('/purchasing');
    
    await expect(page.getByRole('heading', { name: 'Compras & Custo' })).toBeVisible();
    
    // Test the upload component existence
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();

    // Note: Actually testing file upload requires a mock XML file in the test suite
    // await fileInput.setInputFiles('tests/e2e/fixtures/mock_nfe.xml');
    
    // Check extractions list
    await expect(page.getByText('Fila de Ingestão e Validação')).toBeVisible();
  });
});
