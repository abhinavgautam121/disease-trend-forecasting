"""Check a running local dashboard and capture actual browser screenshots."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    screenshots = ROOT / "reports/figures"
    screenshots.mkdir(exist_ok=True)
    checks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1500, "height": 1500}, device_scale_factor=1)
        page.goto(args.url, wait_until="networkidle")
        page.get_by_text("A forecast is a range of possibilities").wait_for(timeout=45000)
        assert page.locator('[data-testid="stException"]').count() == 0
        page.screenshot(path=str(screenshots / "dashboard.png"), full_page=True)
        checks.append("Archive forecast rendered without visible exception")

        for tab in ["Model comparison", "Data observatory", "Method & limitations"]:
            page.get_by_role("tab", name=tab, exact=True).click()
            assert page.locator('[data-testid="stException"]').count() == 0
            if tab == "Model comparison":
                page.screenshot(path=str(screenshots / "model_comparison.png"), full_page=True)
            checks.append(f"{tab} tab opened")

        page.get_by_role("tab", name="Forecast studio", exact=True).click()
        page.get_by_text("Backtest explorer", exact=True).click()
        page.get_by_text("Historical forecast origin", exact=True).wait_for(timeout=30000)
        page.get_by_role("combobox").nth(0).click()
        page.get_by_role("option", name="Random Forest", exact=True).click()
        page.get_by_text("Historical forecast origin", exact=True).wait_for(timeout=30000)
        assert page.locator('[data-testid="stException"]').count() == 0
        checks.append("Backtest explorer and Random Forest model controls work")
        page.screenshot(path=str(screenshots / "backtest.png"), full_page=True)
        with page.expect_download() as download:
            page.get_by_role("button", name="↓ Download this forecast").click()
        assert download.value.suggested_filename.endswith(".csv")
        checks.append("Forecast CSV download initiated successfully")
        browser.close()
    (ROOT / "reports/browser_checks.json").write_text(
        json.dumps(
            {
                "tool": "Playwright Chromium",
                "checks_passed": checks,
            },
            indent=2,
        )
        + "\n"
    )
    print("\n".join(checks))


if __name__ == "__main__":
    main()
