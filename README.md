# Eurosender AI SEO Content Auditor — v1.3

Independent candidate portfolio project; **not affiliated with Eurosender**.

A public-URL SEO auditor with bilingual UI, grounded Gemini suggestions, and formatted XLSX export.

## What's new in v1.3

- **Gemini 3.5 Flash-Lite is the primary (only) AI model.** Avoids switching back to Gemini 3.8 Flash, whose free daily quota was exhausted.
- **24-hour shared Streamlit cache** of successful AI responses for *identical observed page content, same language and model*. Re-running a changed page or a different language may produce a new AI request. Cached responses are lost on certain Cloud restarts.
- **Maximum 3 new AI page analyses per run** (all other pages still get rule-based SEO results).
- **Best-effort per-process limits: 12 real Gemini API attempts per UTC day and 8 per minute.** Retries count as API attempts. When the limit is reached, SEO checks and Excel exports continue to work.
- **503:** one retry on the same Flash-Lite model, counted against local quota; **429:** do not retry/fallback automatically.
- Model results are labeled AI suggestions, not verified SEO issues.

## Update an existing deployment (v1.2 → v1.3)

In the GitHub repository root, replace the two existing files and upload one new file:

1. `streamlit_app.py` — replace
2. `ai_engine.py` — replace
3. `usage_guard.py` — add (new)

Click **Commit changes**. Streamlit Community Cloud should redeploy from `main`. No change to `requirements.txt` or your Streamlit Secrets is required. Confirm that the GitHub commit has been recorded before testing the public link.

**Do not upload** `.env`, `.venv`, or `.streamlit/secrets.toml` with real credentials.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Gemini key (Streamlit Cloud > App settings > Secrets):

```toml
GEMINI_API_KEY = "your-secret-key"
```

You can run deterministic SEO checks and download XLSX without any AI key.

## Limits to explain honestly at the interview

- The included throttling is **in-memory per Streamlit server process**, not a durable project-wide or per-user billing cap. Restart/redeployment resets it; multiple processes could have separate counters. Google's real rate limits and costs still apply. For public production use, add authentication, durable shared quotas and API-side budget controls.
- The cached AI output is **not refreshed** for unchanged observed inputs for up to 24 hours. The app still fetches the live HTML to compute SEO signals on every audit.
- The system analyzes downloaded public HTML, not Search Console, rankings, traffic, JS-rendered content, or actual business impact.
- Decorative images legitimately can have empty alt attributes and always need human review before treating a flag as an SEO issue.
- Site changes and content suggestions aren't automatically published.

## Test

```bash
python -m unittest discover -s tests -v
```
