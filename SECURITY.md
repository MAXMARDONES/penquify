# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Reporting a Vulnerability

Email **max@getsmartup.ai** with:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment

Do NOT open a public issue for security vulnerabilities. You will receive a response within 48 hours.

## API Key Safety

Penquify uses the Gemini API which requires an API key. **Never:**
- Commit API keys to the repository
- Include keys in Docker images
- Log keys in output files
- Pass keys as CLI arguments (use env vars)

**Always:**
- Use environment variables: `GEMINI_API_KEY`
- Use Kubernetes secrets for deployments
- Use `.env` files locally (`.env` is in `.gitignore`)
- Rotate keys if exposed

## Supply Chain Security

### Dependencies
- We pin major versions in `pyproject.toml`
- Playwright is installed separately (`playwright install chromium`) — not bundled
- We use only well-known packages: `google-genai`, `Pillow`, `Jinja2`, `FastAPI`
- No post-install scripts

### Docker
- Base image: `python:3.12-slim` (official)
- No root processes in container
- No secrets baked into images
- Secrets injected via environment variables at runtime

### CI/CD
- GitHub Actions workflows use pinned action versions
- No third-party actions with write permissions
- Docker builds verified in CI before merge

## Merge Policy

- **All PRs require review from @MAXMARDONES** before merge
- No direct pushes to `main` (branch protection enabled)
- Dependabot enabled for dependency updates
- No force pushes allowed

## Responsible AI Use

Penquify generates synthetic document images. Users are responsible for:
- Not generating documents that impersonate real organizations
- Not using generated images for fraud or deception
- Clearly labeling synthetic data as synthetic
- Complying with local laws regarding document generation
