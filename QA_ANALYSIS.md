# Northstar Alumni Portal — QA Analysis

## Scope and observed application behavior

Reviewed the nine supplied design images, the running sign-in and registration screens, and the Flask routes, templates, and client JavaScript. The current product is an **alumni self-service portal**. It does not expose an HR staff or administrator workflow.

### Modules and workflows

| Module | Observed behavior | Dependencies |
|---|---|---|
| Authentication | Sign-in with personal email/password; account registration with first/last name, former employee ID, email, password and confirmation; sign-out | SQLite `users` table, Werkzeug password hashing, Flask session cookie |
| Overview | Welcome header, four category cards/counts, former-manager contact, document list, support section, profile menu | Authenticated session; static demo document and contact data |
| Documents | Category filters; query search over name, description and category; click a document to open preview; download sample PDF | Authenticated session; static document catalog; download endpoint |
| Support | Email/telephone contact links for alumni support, People Operations and help desk | Static contact data; external mail/telephone handlers when activated |
| Navigation | Overview, Documents and Support links; document/support links jump to dashboard anchors | Authenticated session |

### Business rules found in code/UI

- Email and password are required by the sign-in browser form.
- Registration requires names, former employee ID, personal email, password and confirmation.
- The server requires at least 8 password characters and exact password confirmation.
- Email is checked for a basic `@` and dotted domain server-side; the browser also uses `type=email`.
- Employee IDs are uppercased before insert; email uniqueness is case-insensitive. Duplicate email or employee ID returns an inline error.
- A valid sign-in establishes a session; protected pages redirect to sign-in when unauthenticated.
- The demo catalog contains six documents across Employment (2), Tax (1), Payroll (1) and Benefits (2).
- Search and category filters can be combined. Empty results show a message.
- Downloads are generated sample PDFs, not official employee records.

## Requirements inventory

### Functional requirements

1. Users can register using employment identity data and a personal email.
2. Users can sign in and sign out; protected pages require a session.
3. Authenticated users can view their overview and employee-specific welcome/profile details.
4. Users can filter the document list by category and search across document name, description and category.
5. Users can open and close a document preview and inspect its category, type, size, date and document ID.
6. Users can download a PDF for a listed document.
7. Users can reach the provided former-manager and support contact channels.

### Positive scenarios

- Correct credentials open the dashboard for the matching user.
- Each category filter lists only its documents; All documents restores all six.
- Search returns matching documents; search plus category applies both constraints.
- Preview content and metadata correspond to the selected document; close button, backdrop and Escape dismiss it.
- A listed document download returns an attachment named for that document with a PDF signature.
- Sign-out clears access; subsequent protected-route requests return to sign-in.

### Negative and boundary scenarios

- Unknown email, wrong password and blank credentials do not authenticate.
- Registration rejects missing fields, malformed email, password shorter than 8, mismatched confirmation and duplicate email/employee ID.
- Search with no matches displays the empty state; category with no matching term is also empty.
- Unknown document download ID returns 404; unauthenticated download redirects to sign-in.
- IDs and names with leading/trailing whitespace; email case variants; employee ID case variants; unusually long values; password exactly 7, 8 and more than 8 characters.
- Unknown category query parameter; special characters and Unicode in names/search terms; repeated session requests after sign-out.

### Validation and integration dependencies

- There are no JSON/REST API routes in the current app. All observed workflows use HTML pages, query parameters, form posts, and file-download responses; consequently the automated suite covers these HTTP flows through the browser rather than a nonexistent API contract.
- Persistence: SQLite; authentication: Werkzeug hash functions and Flask signed session cookies.
- No external HRIS, identity verification, payroll, tax, document-management or email service integration is implemented.
- Document rows and support contacts are static Python data; generated PDFs are sample records.
- The registration form has browser `required`, `type=email` and `minlength=8` constraints. Server-side checks cover required names/ID, basic email syntax, minimum password length and confirmation.

## Assumptions (kept separate)

- The screenshots define the intended visual and user-visible scope; no separate product requirements or API contract were supplied.
- The current demo account and document contents are fixtures only. No official HR records should be inferred from them.
- Tests use a disposable SQLite database and a synthetic account; they do not mutate the developer's portal database.
- Successful registration is not submitted during this run because the UI says registration constitutes agreement to portal terms. Invalid registration validation is safe to exercise; account creation requires explicit action-time confirmation.

## Missing or ambiguous requirements

- Employee ID format, normalization rules beyond uppercase, and the authoritative system for verifying former employees.
- Email ownership verification, forgotten-password recovery, account lockout/rate limits, MFA, session lifetime and revocation policy.
- Password complexity/rotation rules, whether leading/trailing spaces are meaningful, and whether password manager/autofill is supported.
- Exact allowed name/email/ID lengths and Unicode handling.
- Whether an employee can change profile details, access dependents/beneficiaries, or request corrected documents.
- Official document source, authorization per document, audit trail, retention/deletion, generation/signature, and download access logging.
- Required behavior for unsupported categories/IDs, pagination, sort order, empty categories, and whether search is case/accent-insensitive.
- Support service hours/time zone, response SLA, and whether contacts are live or placeholders.
- Accessibility target, supported browsers/devices, performance/security requirements, deployment configuration and production secret management.

## Defects and risks observed from implementation review

- **Demo document IDs are fixed to `MP-1234` while the signed-in user is arbitrary.** Preview metadata may not match the user identity displayed on the generated PDF. Treat catalog IDs as demo-only until data is user-scoped.
- **Email validation is intentionally basic** (`@` plus a dot after it). It is not a complete email syntax or ownership check.
- **The app uses a development secret fallback and Flask debug mode.** Production must supply a strong secret and disable debug mode.
- **No CSRF protection, rate limiting, or account recovery is present.** These are production hardening gaps, not requirements inferred from the designs.
- The help button and nav links jump to sections on the same page; there are no distinct support or document pages.

## Automated coverage

`tests/test_portal_e2e.py` uses Playwright for Python and pytest. It covers protected-route redirects, bad sign-in, registration validation, dashboard content, combined category/search behavior, document preview/download, and sign-out. Successful registration is not exercised because of the terms notice described above.
