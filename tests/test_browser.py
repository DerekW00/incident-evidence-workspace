import os
import subprocess
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.skipif(
    os.environ.get("RUN_BROWSER") != "1",
    reason="Run browser gate separately against seeded private server",
)
def test_saved_timeline_review_and_cancellation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        page.goto("http://127.0.0.1:8103/login/")
        page.get_by_label("Username").fill("engineer")
        page.get_by_label("Password").fill("synthetic-demo")
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("link", name="INVESTIGATE").click()
        page.get_by_role("button", name="Start investigation").click()
        page.reload()
        assert page.get_by_role("button", name="Cancel investigation").is_visible()
        subprocess.run(
            ["uv", "run", "python", "manage.py", "worker", "--once"], check=True
        )
        page.reload()
        assert page.get_by_text("Contradictory observations", exact=True).is_visible()
        page.get_by_label("Engineer assessment").fill(
            "Deployment correlation is weakened. Check missing metrics before assigning cause."
        )
        page.get_by_role("button", name="Save incident brief").click()
        assert page.get_by_role(
            "link", name="Download saved brief", exact=False
        ).is_visible()
        with page.expect_download() as download_event:
            page.get_by_role("link", name="Download saved brief", exact=False).click()
        downloaded = download_event.value
        assert downloaded.suggested_filename == "synthetic-incident-brief.txt"
        assert (
            "Deployment correlation is weakened" in Path(downloaded.path()).read_text()
        )
        dest = Path(
            "/Users/dw/code/portfolio-python/python-evidence/incident-evidence-workspace"
        )
        page.screenshot(path=str(dest / "timeline-browser.png"), full_page=True)
        page.screenshot(path=str(dest / "workflow-review.jpg"), type="jpeg", quality=70)
        page.goto("http://127.0.0.1:8103/")
        page.get_by_role("link", name="INVESTIGATE").click()
        page.get_by_role("button", name="Start investigation").click()
        page.get_by_role("button", name="Cancel investigation").click()
        page.reload()
        assert page.get_by_text("cancelled", exact=True).first.is_visible()
        assert not page.get_by_role("button", name="Cancel investigation").count()
        page.screenshot(path=str(dest / "cancelled-browser.png"), full_page=True)
        browser.close()
