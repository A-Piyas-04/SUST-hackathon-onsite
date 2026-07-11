# SonarQube integration

This repository is configured as one SonarQube project containing the Next.js
frontend and FastAPI backend. Backend test coverage is imported from pytest.

## 1. Prerequisites

- Docker Engine or Docker Desktop with Compose v2.
- Node.js 18.20 or newer (Node.js 22 is used in CI).
- Python 3.12 and the backend dependencies.
- At least 4 GB of memory available to Docker; 6 GB is more comfortable.

The local stack uses SonarQube Community Build and a separate PostgreSQL
database. The application's PostgreSQL container is unrelated to this database.

## 2. Start SonarQube locally

From the repository root in PowerShell:

```powershell
Copy-Item .env.sonar.example .env.sonar
# Edit .env.sonar and replace SONAR_DB_PASSWORD.
docker compose --env-file .env.sonar -f docker-compose.sonar.yml up -d
docker compose --env-file .env.sonar -f docker-compose.sonar.yml logs -f sonarqube
```

On macOS or Linux, replace the first command with:

```bash
cp .env.sonar.example .env.sonar
```

Wait until the logs report that SonarQube is operational, then open
`http://localhost:9000`. The initial login is `admin` / `admin`; SonarQube will
require a password change.

If Linux reports an Elasticsearch bootstrap error, set the required host value
and restart the stack:

```bash
sudo sysctl -w vm.max_map_count=524288
```

For a persistent server, configure this value in `/etc/sysctl.d/` and use TLS
through a reverse proxy. Do not expose port 9000 directly to the public internet.

## 3. Create the project and token

1. In SonarQube, select **Projects > Create project > Local project**.
2. Use project key `sust-hackathon-onsite` (it must match
   `sonar-project.properties`) and set the main branch to the repository's main
   branch.
3. Select **Locally**, generate a project analysis token, and copy it once.
4. Never put the token in this repository or in `sonar-project.properties`.

## 4. Run a local analysis

Install dependencies and create the Python coverage report:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Push-Location backend
$testFile = Get-ChildItem tests -Recurse -Filter "test_*.py" -File | Select-Object -First 1
if ($testFile) {
    python -m pytest --cov=app --cov=analytics --cov-report=xml:coverage.xml
} else {
    Write-Host "No backend tests exist yet; skipping coverage generation."
}
Pop-Location

Push-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run build
Pop-Location
```

Set credentials only for the current PowerShell session, then scan from the
repository root:

```powershell
$env:SONAR_HOST_URL = "http://localhost:9000"
$env:SONAR_TOKEN = "paste-your-project-token"
npm.cmd run sonar
Remove-Item Env:SONAR_TOKEN
```

macOS/Linux equivalent:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
(
  cd backend
  if find tests -type f -name 'test_*.py' -print -quit | grep -q .; then
    python -m pytest --cov=app --cov=analytics --cov-report=xml:coverage.xml
  else
    echo 'No backend tests exist yet; skipping coverage generation.'
  fi
)
(cd frontend && npm ci && npm run lint && npm run build)
export SONAR_HOST_URL=http://localhost:9000
export SONAR_TOKEN='paste-your-project-token'
npm run sonar
unset SONAR_TOKEN
```

Open the project dashboard in SonarQube after the scanner finishes. A scan can
succeed while its quality gate fails; the dashboard explains each failed metric.

## 5. Connect GitHub Actions

The workflow at `.github/workflows/sonarqube.yml` runs tests, creates coverage,
lints and builds the frontend, scans both applications, and fails when the
quality gate fails.

In GitHub, open **Settings > Secrets and variables > Actions** and add:

- Secret `SONAR_TOKEN`: a SonarQube project token.
- Variable `SONAR_HOST_URL`: the externally reachable base URL, for example
  `https://sonarqube.example.com`.
- Optional secret `SONAR_ROOT_CERT`: the PEM root certificate when the server
  uses a private certificate authority.

The URL must be reachable from the runner. `http://localhost:9000` on your
computer is not reachable from a GitHub-hosted runner. Either host SonarQube on
a network-accessible server, or change `runs-on` to labels for a self-hosted
runner that can reach it.

Push to `main` or `master`, or run **Actions > SonarQube > Run workflow**. Then
make the `Analyze and enforce quality gate` check required in the repository's
branch protection/ruleset if merges must be blocked on a red gate.

Community Build analyzes the main branch. Pull-request and multi-branch
analysis/decoration require SonarQube Developer Edition or higher. After an
upgrade, add a `pull_request` trigger; the official scanner action detects PR
metadata automatically.

## 6. Quality gate and coverage maintenance

Start with SonarQube's built-in **Sonar way** quality gate. Prefer enforcing
strict conditions on new code rather than immediately failing on all legacy
issues. Configure the new-code definition and gate under **Project Settings**.

There are currently no frontend tests. When a frontend test runner is added:

1. Configure it to produce `frontend/coverage/lcov.info`.
2. Run it before the SonarQube scan in the workflow.
3. Uncomment `sonar.javascript.lcov.reportPaths` in
   `sonar-project.properties`.

SonarQube imports coverage reports; it does not run tests or generate coverage.

## 7. Operations and troubleshooting

Useful commands:

```powershell
# Status
docker compose --env-file .env.sonar -f docker-compose.sonar.yml ps

# Logs
docker compose --env-file .env.sonar -f docker-compose.sonar.yml logs -f sonarqube

# Stop but preserve all data
docker compose --env-file .env.sonar -f docker-compose.sonar.yml down

# Pull the configured image and recreate after intentionally updating its tag
docker compose --env-file .env.sonar -f docker-compose.sonar.yml pull
docker compose --env-file .env.sonar -f docker-compose.sonar.yml up -d
```

Do not run `down -v` unless you intentionally want to delete the SonarQube
database and all analysis history. Back up the PostgreSQL volume/database before
upgrades, read the release upgrade notes, and pin/test a newer image tag before
changing production.

Common failures:

- **Not authorized**: regenerate the project token and update `SONAR_TOKEN`.
- **Project not found**: make the UI project key match
  `sonar.projectKey=sust-hackathon-onsite`.
- **Coverage is 0%**: verify `backend/coverage.xml` exists before scanning and
  that report paths inside it resolve relative to the repository.
- **CI cannot connect**: use a runner with network access, check firewall/DNS,
  and configure a valid TLS certificate or `SONAR_ROOT_CERT`.
- **Shallow clone warning**: keep `fetch-depth: 0` in the checkout step.
