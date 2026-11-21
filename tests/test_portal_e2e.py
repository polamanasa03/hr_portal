"""Browser-level functional coverage for observed Northstar portal workflows."""
from __future__ import annotations

import re

from conftest import TEST_EMAIL, TEST_PASSWORD


def sign_in(page, base_url):
    page.goto(f"{base_url}/auth?mode=signin")
    page.get_by_label("Email address").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in securely").click()
    page.get_by_role("heading", name="Welcome back, Alex").wait_for()


def test_unauthenticated_protected_routes_redirect_to_sign_in(page, portal_server):
    base = portal_server["base_url"]
    for route in ("/dashboard", "/documents", "/support", "/documents/form-16/download"):
        response = page.goto(base + route)
        assert response is not None and response.status == 200
        assert page.url.startswith(base + "/auth?mode=signin")
        assert page.get_by_role("heading", name="Sign in to your portal").is_visible()


def test_sign_in_rejects_unknown_account(page, portal_server):
    page.goto(portal_server["base_url"] + "/auth?mode=signin")
    page.get_by_label("Email address").fill("missing@example.test")
    page.get_by_label("Password").fill("WrongPassword123!")
    page.get_by_role("button", name="Sign in securely").click()
    assert page.get_by_text("Email or password is incorrect. Please try again.").is_visible()
    assert page.get_by_role("heading", name="Sign in to your portal").is_visible()


def test_registration_validation_rejects_password_mismatch(page, portal_server):
    page.goto(portal_server["base_url"] + "/auth?mode=register")
    page.get_by_label("First name").fill("Test")
    page.get_by_label("Last name").fill("Alumni")
    page.get_by_label("Former employee ID").fill("NS-INVALID-01")
    page.get_by_label("Personal email").fill("mismatch@example.test")
    page.get_by_label("Create password").fill("NorthstarTest2026!")
    page.get_by_label("Confirm password").fill("DifferentPassword2026!")
    page.get_by_role("button", name="Create account & continue").click()
    assert page.get_by_text("Your passwords do not match.").is_visible()
    assert page.get_by_role("heading", name="Create your account").is_visible()


def test_registration_html_constraints_cover_required_and_minimum_password(page, portal_server):
    page.goto(portal_server["base_url"] + "/auth?mode=register")
    assert page.locator('input[name="first_name"]').get_attribute("required") is not None
    assert page.locator('input[name="password"]').get_attribute("minlength") == "8"
    assert page.locator('input[name="email"]').get_attribute("type") == "email"


def test_dashboard_shows_summary_documents_and_support(page, portal_server):
    sign_in(page, portal_server["base_url"])
    assert page.get_by_text("Employment", exact=True).count() >= 1
    assert page.get_by_text("Your documents", exact=True).is_visible()
    assert page.get_by_role("button", name=re.compile("Experience Certificate")).is_visible()
    assert page.get_by_text("Maya Patel", exact=True).is_visible()
    assert page.get_by_text("Portal & alumni support", exact=True).is_visible()


def test_category_filter_and_search_compose(page, portal_server):
    sign_in(page, portal_server["base_url"])
    page.get_by_role("link", name=re.compile("Tax")).first.click()
    page.get_by_text("FY 2023–24 Form 16", exact=True).wait_for()
    assert page.get_by_text("Experience Certificate", exact=True).count() == 0
    search = page.get_by_placeholder("Search documents")
    search.fill("Form 16")
    search.press("Enter")
    assert page.get_by_text("FY 2023–24 Form 16", exact=True).is_visible()
    assert page.get_by_text("No documents match your search.", exact=False).count() == 0


def test_document_preview_metadata_and_sample_pdf_download(page, portal_server):
    sign_in(page, portal_server["base_url"])
    page.get_by_role("button", name=re.compile("Experience Certificate")).click()
    assert page.get_by_text("Document details", exact=True).is_visible()
    assert page.get_by_text("NS-EMP-MP-1234", exact=True).is_visible()
    with page.expect_download() as download_info:
        page.get_by_role("link", name=re.compile("Download document")).click()
    download = download_info.value
    assert download.suggested_filename == "experience-certificate.pdf"
    path = download.path()
    assert path is not None
    assert open(path, "rb").read(8).startswith(b"%PDF-1.")
    page.get_by_role("button", name="Close preview").click()
    assert not page.get_by_text("Document details", exact=True).is_visible()


def test_profile_menu_sign_out_returns_to_sign_in(page, portal_server):
    sign_in(page, portal_server["base_url"])
    page.get_by_role("button", name=re.compile("Alex Morgan")).click()
    assert page.get_by_text(TEST_EMAIL, exact=True).is_visible()
    page.get_by_role("button", name=re.compile("Sign out")).click()
    page.get_by_role("heading", name="Sign in to your portal").wait_for()
    response = page.goto(portal_server["base_url"] + "/dashboard")
    assert response is not None and page.url.startswith(portal_server["base_url"] + "/auth?mode=signin")
