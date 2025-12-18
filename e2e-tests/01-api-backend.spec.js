// MADERA MCP - API Backend Tests
const { test, expect } = require('@playwright/test');

test.describe('API Backend Tests', () => {
  test('health check endpoint', async ({ request }) => {
    const response = await request.get('/health');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('service', 'madera-web');
    expect(data).toHaveProperty('version');
  });

  test('dashboard loads correctly', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page.locator('h1')).toContainText('Dashboard');

    // Check stats cards
    await expect(page.locator('.stat-card')).toHaveCount(6);
  });

  test('tools page lists all MCP tools', async ({ page }) => {
    await page.goto('/tools');

    await expect(page.locator('h1')).toContainText('MCP Tools');

    // Wait for tools to load
    await page.waitForSelector('.tool-card', { timeout: 5000 });

    const toolCards = await page.locator('.tool-card').count();
    expect(toolCards).toBeGreaterThanOrEqual(40); // 40 base + visual-ai tools
  });

  test('templates page loads', async ({ page }) => {
    await page.goto('/templates');

    await expect(page.locator('h1')).toContainText('Trained Templates');
  });

  test('MCP tools API endpoint', async ({ request }) => {
    const response = await request.get('/api/tools');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();

    // API returns object with tools array, not direct array
    expect(data).toHaveProperty('tools');
    expect(Array.isArray(data.tools)).toBeTruthy();
    expect(data.tools.length).toBeGreaterThanOrEqual(40); // 40 base + visual-ai tools

    // Check first tool structure
    const firstTool = data.tools[0];
    expect(firstTool).toHaveProperty('name');
    expect(firstTool).toHaveProperty('description');
    expect(firstTool).toHaveProperty('category');
  });

  test('training page loads', async ({ page }) => {
    await page.goto('/training/');

    await expect(page.locator('h1')).toContainText('MADERA AI Training');

    // Check upload box exists
    await expect(page.locator('#uploadBox')).toBeVisible();

    // Check mode selection exists (radio inputs are hidden, labels are visible)
    const logoModeInput = page.locator('input[name="mode"][value="logo_detection"]');
    await expect(logoModeInput).toBeChecked(); // Input exists and is checked

    const logoModeLabel = page.locator('.mode-card').filter({ hasText: 'Logo Detection' });
    await expect(logoModeLabel).toBeVisible(); // Label is visible

    const zoneModeLabel = page.locator('.mode-card').filter({ hasText: 'Zone Extraction' });
    await expect(zoneModeLabel).toBeVisible();
  });
});
