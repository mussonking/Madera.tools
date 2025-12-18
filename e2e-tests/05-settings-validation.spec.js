// MADERA MCP - Settings & Validation Page Tests
// Tests the new tabbed settings page and validation page quick-add features
const { test, expect } = require('@playwright/test');

test.describe('Settings Page - Tabbed Interface', () => {

  test('settings page loads with 5 tabs', async ({ page }) => {
    await page.goto('/settings/');

    // Check page title
    await expect(page.locator('h1')).toContainText('Training Configuration');

    // Check all 5 tabs exist
    const tabs = page.locator('.tab-btn');
    await expect(tabs).toHaveCount(5);

    // Verify tab names
    await expect(page.locator('.tab-btn[data-tab="ai-models"]')).toContainText('AI Models');
    await expect(page.locator('.tab-btn[data-tab="logo-detection"]')).toContainText('Logo Detection');
    await expect(page.locator('.tab-btn[data-tab="zone-extraction"]')).toContainText('Zone Extraction');
    await expect(page.locator('.tab-btn[data-tab="doc-classification"]')).toContainText('Classification');
    await expect(page.locator('.tab-btn[data-tab="quality-assessment"]')).toContainText('Quality');
  });

  test('tab switching works correctly', async ({ page }) => {
    await page.goto('/settings/');

    // Click Logo Detection tab
    await page.click('.tab-btn[data-tab="logo-detection"]');

    // Check Logo Detection content is visible
    await expect(page.locator('#logo-detection')).toBeVisible();

    // Click Classification tab
    await page.click('.tab-btn[data-tab="doc-classification"]');

    // Check Classification content is visible
    await expect(page.locator('#doc-classification')).toBeVisible();
  });
});

test.describe('Settings API - Logos', () => {

  test('GET /settings/api/logos returns logo list', async ({ request }) => {
    const response = await request.get('/settings/api/logos');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('logos');
    expect(Array.isArray(data.logos)).toBeTruthy();
    expect(data.logos.length).toBeGreaterThan(0);

    // Check logo structure
    const logo = data.logos[0];
    expect(logo).toHaveProperty('code');
    expect(logo).toHaveProperty('display');
    expect(logo).toHaveProperty('category');
  });

  test('POST /settings/api/logos/add creates new logo', async ({ request }) => {
    const formData = new URLSearchParams();
    formData.append('code', 'TEST_LOGO_E2E');
    formData.append('display', 'Test Logo E2E');
    formData.append('category', 'bank');

    const response = await request.post('/settings/api/logos/add', {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: formData.toString()
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBeTruthy();

    // Verify logo was added
    const logos = data.logos;
    const newLogo = logos.find(l => l.code === 'TEST_LOGO_E2E');
    expect(newLogo).toBeDefined();
    expect(newLogo.display).toBe('Test Logo E2E');
  });

  test('DELETE /settings/api/logos/{code} removes logo', async ({ request }) => {
    const response = await request.delete('/settings/api/logos/TEST_LOGO_E2E');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBeTruthy();

    // Verify logo was removed
    const logos = data.logos;
    const deletedLogo = logos.find(l => l.code === 'TEST_LOGO_E2E');
    expect(deletedLogo).toBeUndefined();
  });
});

test.describe('Settings API - Document Types', () => {

  test('GET /settings/api/doctypes returns doctype list', async ({ request }) => {
    const response = await request.get('/settings/api/doctypes');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('doctypes');
    expect(Array.isArray(data.doctypes)).toBeTruthy();
    expect(data.doctypes.length).toBeGreaterThan(0);

    // Check doctype structure
    const doctype = data.doctypes[0];
    expect(doctype).toHaveProperty('code');
    expect(doctype).toHaveProperty('label');
    expect(doctype).toHaveProperty('category');
  });

  test('POST /settings/api/doctypes/add creates new doctype', async ({ request }) => {
    const formData = new URLSearchParams();
    formData.append('code', 'test_doctype_e2e');
    formData.append('label', 'Test Doctype E2E');
    formData.append('category', 'other');

    const response = await request.post('/settings/api/doctypes/add', {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: formData.toString()
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBeTruthy();
  });

  test('DELETE /settings/api/doctypes/{code} removes doctype', async ({ request }) => {
    const response = await request.delete('/settings/api/doctypes/test_doctype_e2e');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBeTruthy();
  });
});

test.describe('Settings API - Categories', () => {

  test('GET /settings/api/categories returns category list', async ({ request }) => {
    const response = await request.get('/settings/api/categories');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('categories');
    expect(Array.isArray(data.categories)).toBeTruthy();
  });

  test('POST /settings/api/categories/add creates new category', async ({ request }) => {
    const formData = new URLSearchParams();
    formData.append('code', 'test_category');
    formData.append('label', 'Test Category');
    formData.append('icon', '🧪');

    const response = await request.post('/settings/api/categories/add', {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: formData.toString()
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBeTruthy();
  });

  test('DELETE /settings/api/categories/{code} removes category', async ({ request }) => {
    const response = await request.delete('/settings/api/categories/test_category');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBeTruthy();
  });
});

test.describe('Training Page - Mode Selection', () => {

  test('training page loads with 4 mode options', async ({ page }) => {
    await page.goto('/training/');

    // Check all 4 mode cards exist
    const modeCards = page.locator('.mode-card');
    await expect(modeCards).toHaveCount(4);

    // Check radio buttons
    await expect(page.locator('input[value="logo_detection"]')).toBeAttached();
    await expect(page.locator('input[value="zone_extraction"]')).toBeAttached();
    await expect(page.locator('input[value="document_classification"]')).toBeAttached();
    await expect(page.locator('input[value="quality_assessment"]')).toBeAttached();
  });

  test('mode selection persists when clicking card', async ({ page }) => {
    await page.goto('/training/');

    // Click on zone_extraction card
    await page.click('.mode-card:has(input[value="zone_extraction"])');

    // Wait a bit for JS to process
    await page.waitForTimeout(100);

    // Check radio is selected
    const isChecked = await page.locator('input[value="zone_extraction"]').isChecked();
    expect(isChecked).toBeTruthy();

    // Check visual feedback (selected class)
    await expect(page.locator('.mode-card:has(input[value="zone_extraction"])')).toHaveClass(/selected/);
  });
});

test.describe('Validation Page - Quick Add Features', () => {

  // Note: These tests require an active training session
  // Skip if no session available

  test.skip('validation page has quick-add buttons', async ({ page }) => {
    // This would need a real session ID
    await page.goto('/training/validate/test-session');

    // Check quick-add buttons exist
    await expect(page.locator('#add-logo-btn')).toBeVisible();
    await expect(page.locator('#add-doctype-btn')).toBeVisible();

    // Check skip entity checkbox exists
    await expect(page.locator('#skip-entity')).toBeVisible();
  });

  test.skip('quick-add logo modal opens', async ({ page }) => {
    await page.goto('/training/validate/test-session');

    // Click add logo button
    await page.click('#add-logo-btn');

    // Check modal is visible
    await expect(page.locator('#quickAddLogoModal')).toBeVisible();

    // Check form fields
    await expect(page.locator('#quick-logo-code')).toBeVisible();
    await expect(page.locator('#quick-logo-display')).toBeVisible();
    await expect(page.locator('#quick-logo-category')).toBeVisible();
  });

  test.skip('quick-add doctype modal opens', async ({ page }) => {
    await page.goto('/training/validate/test-session');

    // Click add doctype button
    await page.click('#add-doctype-btn');

    // Check modal is visible
    await expect(page.locator('#quickAddDoctypeModal')).toBeVisible();

    // Check form fields
    await expect(page.locator('#quick-doctype-code')).toBeVisible();
    await expect(page.locator('#quick-doctype-label')).toBeVisible();
    await expect(page.locator('#quick-doctype-category')).toBeVisible();
  });
});
