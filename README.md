# Northstar Alumni Portal

A Python Flask app based on the screens in `Designs/`. It includes account registration and sign in, an alumni dashboard, searchable and filterable documents, previews, sample PDF downloads, and support contacts.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. Create an account with a unique former employee ID and personal email. The SQLite database (`portal.db`) is created automatically on first run.

Set `PORTAL_SECRET_KEY` to a long random value before deploying. The included records and downloadable files are sample content; connect an HR document store and account verification source before using this for real employee data.

## QA automation

Install the browser-test dependencies and Chromium once:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
python3 -m pytest -q
```

The Playwright suite launches a separate app process on port 5017 with a temporary SQLite database and a synthetic test user. Override the port with `PORTAL_TEST_PORT` if it is already in use. The suite does not create an account in `portal.db`.

See [QA_ANALYSIS.md](QA_ANALYSIS.md) for the observed workflows, rules, assumptions, coverage, and open requirement questions.

## Build and publish the container image

The GitHub Actions workflow at `.github/workflows/container.yml` runs the Playwright suite on pull requests to `main`. After tests pass, pushes to `main` and version tags such as `v1.2.3` build and publish the image to GitHub Container Registry. The workflow uses the repository-scoped `GITHUB_TOKEN`; no personal access token secret is needed. It publishes `latest` on `main`, the version tag, semantic version tags, and a commit SHA tag.

The image name is `ghcr.io/polamanasa03/hr_portal`. The first GHCR package is private by default; change package visibility in GitHub if it should be public.

To build and run it locally:

```bash
docker build -t hr-portal:local .
export PORTAL_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
docker volume create hr-portal-data
docker run --rm -p 5000:5000 \
  -e PORTAL_SECRET_KEY="$PORTAL_SECRET_KEY" \
  -v hr-portal-data:/data \
  hr-portal:local
```

The named volume stores SQLite data across container restarts. The production image refuses to start without `PORTAL_SECRET_KEY`.
