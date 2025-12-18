// Playwright configuration for MADERA MCP
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e-tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Run tests serially (training workflow is stateful)
  reporter: 'html',

  use: {
    baseURL: 'http://192.168.2.71:8004',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'cd /home/mad/madera-mcp && docker compose up madera-web',
    url: 'http://192.168.2.71:8004/health',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
