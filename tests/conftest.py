"""Local, isolated Playwright test environment for the Northstar portal."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
TEST_EMAIL = "alex.morgan@example.test"
TEST_PASSWORD = "NorthstarTest2026!"


def free_port() -> int:
    # Keep the isolated test server away from the developer server on port 5000.
    return int(os.environ.get("PORTAL_TEST_PORT", "5017"))

@pytest.fixture(scope="session")
def portal_server(tmp_path_factory):
    """Run a separate app process backed by an ephemeral SQLite database."""
    work = tmp_path_factory.mktemp("hr-portal")
    database = work / "portal-test.db"
    import sqlite3

    with sqlite3.connect(database) as conn:
        conn.execute("""CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL,
            last_name TEXT NOT NULL, employee_id TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL
        )""")
        conn.execute(
            "INSERT INTO users(first_name,last_name,employee_id,email,password_hash) VALUES(?,?,?,?,?)",
            ("Alex", "Morgan", "NS-18427", TEST_EMAIL, generate_password_hash(TEST_PASSWORD)),
        )
    port = free_port()
    env = os.environ.copy()
    env.update({
        "PORTAL_DATABASE": str(database),
        "PORTAL_SECRET_KEY": "playwright-isolated-test-secret",
        "PORT": str(port),
        "PYTHONUNBUFFERED": "1",
    })
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Test portal process exited before becoming ready")
        try:
            with urlopen(base_url, timeout=0.5):
                break
        except Exception:
            time.sleep(0.1)
    else:
        process.terminate()
        raise RuntimeError("Test portal did not become ready")
    yield {"base_url": base_url, "database": database, "process": process}
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        launch_options = {"headless": True}
        chrome_path = os.environ.get("CHROME_PATH")
        if chrome_path:
            launch_options["executable_path"] = chrome_path
        browser = playwright.chromium.launch(**launch_options)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    yield page
    context.close()
