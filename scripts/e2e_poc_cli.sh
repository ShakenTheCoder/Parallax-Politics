#!/usr/bin/env bash
set -euo pipefail

PWCLI="/Users/ioan_andrei/.codex/skills/playwright/scripts/playwright_cli.sh"
SESSION="parallax-poc-final"
BASE_URL="${E2E_BASE_URL:-http://127.0.0.1:3000}"

mkdir -p output/playwright
bash "$PWCLI" -s="$SESSION" open "$BASE_URL"
bash "$PWCLI" -s="$SESSION" cookie-set parallax.session_token e2e
bash "$PWCLI" -s="$SESSION" cookie-set parallax.session active
bash "$PWCLI" -s="$SESSION" goto "$BASE_URL/brief"
bash "$PWCLI" -s="$SESSION" snapshot
bash "$PWCLI" -s="$SESSION" run-code "async (page) => { await page.setViewportSize({ width: 390, height: 844 }); await page.getByRole('heading', { name: 'Maria Santos' }).waitFor(); await page.getByRole('heading', { name: 'Watchlist ratings' }).waitFor(); await page.getByRole('heading', { name: 'Public media appearances' }).waitFor(); await page.getByRole('heading', { name: 'Latest opinion about you' }).waitFor(); for (const removed of ['Who am I?', 'Awaiting data', 'Brief · 30 second view']) { if (await page.getByText(removed, { exact: true }).count()) throw new Error('Removed label is still visible: ' + removed); } const opinions = await page.locator('article').count(); if (opinions !== 4) throw new Error('Expected current plus three previous opinions, got ' + opinions); await page.screenshot({ path: 'output/playwright/brief-mobile.png', fullPage: true }); }"
bash "$PWCLI" -s="$SESSION" console error
bash "$PWCLI" -s="$SESSION" close
echo "Brief mobile browser smoke test passed."
