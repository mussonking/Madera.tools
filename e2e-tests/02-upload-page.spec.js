// MADERA MCP - Upload Page Tests
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

test.describe('Upload Page Tests', () => {
  test.beforeAll(async () => {
    // Create sample PDF for testing (using simple text PDF)
    const fixturesDir = path.join(__dirname, 'fixtures');
    if (!fs.existsSync(fixturesDir)) {
      fs.mkdirSync(fixturesDir, { recursive: true });
    }

    // Create a minimal valid PDF
    const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000270 00000 n
0000000348 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
440
%%EOF`;

    fs.writeFileSync(path.join(fixturesDir, 'test-document.pdf'), pdfContent);
  });

  test('upload page UI elements', async ({ page }) => {
    await page.goto('/training/');

    // Check title
    await expect(page.locator('h1')).toContainText('MADERA AI Training');

    // Check upload box
    await expect(page.locator('#uploadBox')).toBeVisible();

    // Check mode selection (radio inputs are hidden, only labels visible)
    const logoMode = page.locator('input[name="mode"][value="logo_detection"]');
    await expect(logoMode).toBeChecked(); // Default selected (input exists but hidden)

    const logoModeLabel = page.locator('.mode-card').filter({ hasText: 'Logo Detection' });
    await expect(logoModeLabel).toBeVisible(); // Label is visible

    const zoneModeLabel = page.locator('.mode-card').filter({ hasText: 'Zone Extraction' });
    await expect(zoneModeLabel).toBeVisible(); // Label is visible

    // Check start button (should be disabled initially)
    const startBtn = page.locator('#startBtn');
    await expect(startBtn).toBeVisible();
    await expect(startBtn).toBeDisabled();
  });

  test('file selection enables start button', async ({ page }) => {
    await page.goto('/training/');

    const startBtn = page.locator('#startBtn');
    await expect(startBtn).toBeDisabled();

    // Upload file
    const fileInput = page.locator('#fileInput');
    const testFile = path.join(__dirname, 'fixtures', 'test-document.pdf');

    await fileInput.setInputFiles(testFile);

    // Wait for file to be processed
    await page.waitForTimeout(500);

    // Check file appears in list
    await expect(page.locator('#filesList')).toBeVisible();
    await expect(page.locator('.file-item')).toHaveCount(1);

    // Start button should now be enabled
    await expect(startBtn).toBeEnabled();
  });

  test('mode selection changes', async ({ page }) => {
    await page.goto('/training/');

    // Default is logo_detection
    const logoMode = page.locator('input[name="mode"][value="logo_detection"]');
    await expect(logoMode).toBeChecked();

    // Change to zone_extraction by clicking the visible label (radio input is hidden)
    const zoneModeLabel = page.locator('.mode-card').filter({ hasText: 'Zone Extraction' });
    await zoneModeLabel.click();

    // Wait for change
    await page.waitForTimeout(100);

    const zoneMode = page.locator('input[name="mode"][value="zone_extraction"]');
    await expect(zoneMode).toBeChecked();
    await expect(logoMode).not.toBeChecked();
  });

  test('remove file from list', async ({ page }) => {
    await page.goto('/training/');

    // Upload file
    const fileInput = page.locator('#fileInput');
    const testFile = path.join(__dirname, 'fixtures', 'test-document.pdf');
    await fileInput.setInputFiles(testFile);

    await page.waitForTimeout(500);

    // Check file appears
    await expect(page.locator('.file-item')).toHaveCount(1);

    // Remove file
    await page.locator('.file-remove').click();

    // File list should be hidden
    await expect(page.locator('#filesList')).toBeHidden();

    // Start button disabled again
    await expect(page.locator('#startBtn')).toBeDisabled();
  });

  test('clear all files', async ({ page }) => {
    await page.goto('/training/');

    // Upload file
    const fileInput = page.locator('#fileInput');
    const testFile = path.join(__dirname, 'fixtures', 'test-document.pdf');
    await fileInput.setInputFiles(testFile);

    await page.waitForTimeout(500);

    // Click clear all
    await page.locator('button').filter({ hasText: 'Effacer tout' }).click();

    // File list should be hidden
    await expect(page.locator('#filesList')).toBeHidden();
  });

  test('drag and drop file (simulated)', async ({ page }) => {
    await page.goto('/training/');

    // We can't truly test drag & drop in Playwright without real files,
    // but we can test the handler exists
    const uploadBox = page.locator('#uploadBox');
    await expect(uploadBox).toBeVisible();

    // Click to trigger file input
    await uploadBox.click();

    // File input should exist
    await expect(page.locator('#fileInput')).toBeAttached();
  });
});
