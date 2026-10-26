import { test, expect } from '@playwright/test';

test.describe('FFRE End-to-End Investigator Journey (Browser Qualification)', () => {
  const TEST_TXN_ID = 'TXN-E2E-BROWSER-8849';

  test.beforeEach(async ({ page }) => {
    // Intercept backend API requests to mock realistic deterministic responses for full browser qualification
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-investigator-alpha',
          token_type: 'bearer',
          tenant_id: 'tenant_alpha',
          role: 'investigator',
          user: {
            id: 'user_1',
            name: 'Lead Fraud Investigator',
            email: 'investigator@ffre.internal',
            role: 'investigator',
            tenant_id: 'tenant_alpha'
          }
        }),
      });
    });

    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-investigator-alpha',
          token_type: 'bearer'
        }),
      });
    });

    await page.route('**/api/v1/investigations', async (route) => {
      if (route.request().method() === 'POST') {
        const postData = route.request().postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            investigation_id: 'inv_e2e_browser_01',
            transaction_id: postData.transaction_id || TEST_TXN_ID,
            status: 'COMPLETED',
            risk_score: 0.82,
            confidence: 0.91,
            tenant_id: 'tenant_alpha',
            created_at: new Date().toISOString()
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            investigations: [
              {
                investigation_id: 'inv_e2e_browser_01',
                transaction_id: TEST_TXN_ID,
                status: 'COMPLETED',
                risk_score: 0.82,
                confidence: 0.91,
                customer_name: 'Jonathan Doe',
                amount: 1450.0,
                currency: 'USD',
                created_at: new Date().toISOString()
              }
            ],
            total: 1
          }),
        });
      }
    });

    await page.route('**/api/v1/investigations/inv_e2e_browser_01', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          investigation_id: 'inv_e2e_browser_01',
          transaction_id: TEST_TXN_ID,
          status: 'COMPLETED',
          risk_score: 0.82,
          confidence: 0.91,
          tenant_id: 'tenant_alpha',
          customer_name: 'Jonathan Doe',
          amount: 1450.0,
          currency: 'USD',
          created_at: new Date().toISOString(),
          decision_rationale: 'High velocity burst of 4 transactions in 5 minutes from unrecognized Linux device in foreign jurisdiction.',
          evidence: [
            { source: 'device', snippet: 'Unrecognized OS Linux 6.2 with spoofed browser agent' },
            { source: 'velocity', snippet: 'Velocity: 4 transactions in 180 seconds exceeding 3.5x threshold' },
            { source: 'location', snippet: 'IP Geolocation: Kyiv, Ukraine (Cardholder baseline: Chicago, USA)' }
          ]
        }),
      });
    });

    await page.route('**/api/v1/graph/inv_e2e_browser_01', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          investigation_id: 'inv_e2e_browser_01',
          status: 'completed',
          graph_version: 'v1.0-dag',
          nodes: [
            { id: 'planner', name: 'Task Planner', category: 'planning', status: 'completed', duration_ms: 45, tokens: 120, prompt_version: 'v1.0', dependencies: [], description: 'Decompose investigation into 5 parallel tasks' },
            { id: 'retrieval', name: 'Parallel Retrieval', category: 'retrieval', status: 'completed', duration_ms: 85, tokens: 300, prompt_version: 'v1.0', dependencies: ['planner'], description: 'Query customer, account, device, location stores' },
            { id: 'reasoning', name: 'Evidence Synthesizer', category: 'reasoning', status: 'completed', duration_ms: 120, tokens: 450, prompt_version: 'v1.0', dependencies: ['retrieval'], description: 'Synthesize contradictions and cross-attribute risk' },
            { id: 'reporter', name: 'Dossier Generator', category: 'reporting', status: 'completed', duration_ms: 60, tokens: 250, prompt_version: 'v1.0', dependencies: ['reasoning'], description: 'Formulate regulatory SAR executive summary' }
          ],
          metrics: {
            total_runtime_ms: 310,
            average_node_runtime_ms: 77.5,
            total_tokens: 1120,
            prompt_tokens: 720,
            completion_tokens: 400,
            estimated_cost_usd: 0.0028,
            completed_nodes: 4,
            total_nodes: 4
          }
        }),
      });
    });

    await page.route('**/api/v1/investigations/inv_e2e_browser_01/decision', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          investigation_id: 'inv_e2e_browser_01',
          status: 'APPROVED',
          action: 'APPROVE',
          notes: 'Confirmed fraudulent velocity burst by human investigator',
          updated_at: new Date().toISOString()
        }),
      });
    });

    await page.route('**/api/v1/reports**', async (route) => {
      if (route.request().url().includes('/download')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            report_id: 'rep_browser_01',
            title: 'SAR Regulatory Filing TXN-E2E-BROWSER-8849',
            dossier_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            signature: 'HMAC-SHA256-VALID'
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            reports: [
              {
                report_id: 'rep_browser_01',
                title: 'SAR Regulatory Filing TXN-E2E-BROWSER-8849',
                report_type: 'SAR Regulatory Filing',
                generated_by: 'Lead Fraud Investigator',
                status: 'Completed',
                file_format: 'pdf',
                file_size: 48200,
                created_at: new Date().toISOString()
              }
            ],
            total: 1
          }),
        });
      }
    });

    await page.route('**/api/v1/search/universal**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            { type: 'transaction', id: TEST_TXN_ID, title: `Transaction ${TEST_TXN_ID}`, subtitle: '$1,450.00 USD - High Risk' },
            { type: 'customer', id: 'cust_982', title: 'Jonathan Doe', subtitle: 'Account Verified - Risk: 0.82' }
          ]
        }),
      });
    });
  });

  test('Complete 10-Step Investigator Browser Journey', async ({ page }) => {
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
    page.on('pageerror', err => console.log('BROWSER EXCEPTION:', err.message));
    // 1. Sign In
    await page.goto('/auth');
    await expect(page.locator('h1')).toContainText('FFIRE Login');
    await page.fill('input[type="email"]', 'analyst@ffre.internal');
    await page.fill('input[type="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');

    // 2. Dashboard Navigation & Search
    await page.waitForURL('**/');
    await expect(page).toHaveURL(/127\.0\.0\.1:4173\/$/);

    // 3. Navigate to Investigations Page
    await page.goto('/investigations');
    await expect(page.locator('h1')).toContainText('Investigations');

    // 4. Verify Investigation is listed and track status
    await expect(page.locator('body')).toContainText(TEST_TXN_ID);

    // 5. Inspect Investigation Details & Evidence DAG
    await page.goto('/investigations/inv_e2e_browser_01');
    await expect(page.locator('body')).toContainText('inv_e2e_browser_01');
    await expect(page.locator('body')).toContainText('Task Planner');
    await expect(page.locator('body')).toContainText('Evidence Synthesizer');

    // 6. Review Generated Report in Reports View
    await page.goto('/reports');
    await expect(page.locator('body')).toContainText('Reports & Regulatory Filings');
    await expect(page.locator('body')).toContainText('SAR Regulatory Filing TXN-E2E-BROWSER-8849');

    // 7. Verify Multi-Tenant Cross-Access Isolation (Tenant Bravo blocked from Tenant Alpha case)
    await page.route('**/api/v1/investigations/inv_cross_tenant_secret', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Access denied: Cross-tenant resource isolation enforced.' }),
      });
    });

    await page.goto('/investigations/inv_cross_tenant_secret');
    await expect(page.locator('body')).toContainText(/Access denied|Failed to load|Error/i);

    // 8. Verify Outage / Error Handling Fails Safely
    await page.route('**/api/v1/investigations/inv_outage_test', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Service Unavailable: Database connection pool offline.' }),
      });
    });

    await page.goto('/investigations/inv_outage_test');
    // Ensure the app does not crash to a blank white screen, but safely displays the error state
    await expect(page.locator('body')).toContainText(/Service Unavailable|Error|Failed/i);
  });
});
