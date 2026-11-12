# Eurosender SEO Content Auditor — candidate portfolio project

**Independent project; not affiliated with Eurosender.** A repeatable marketing task: take public Eurosender page URLs, perform deterministic on-page checks, optionally use Gemini to formulate grounded optimization suggestions, and export an Excel-ready CSV plus a JSON audit trail.

## Features
- Live public HTTPS URLs on `eurosender.com`, `www.eurosender.com`, `blog.eurosender.com` only (max 10/run).
- Redirect and public-DNS restrictions, response size/time limits and content-type checks.
- Extracts HTML title, meta description, H1, canonical, robots, alt text, internal links, main visible text.
- Priority-ranked rules; **checklist score is not a Google SEO score**.
- Optional Gemini-generated recommendations grounded in extracted evidence; clear warnings if AI unavailable.
- Excel-compatible UTF-8 BOM CSV + structured JSON exports.
- Clearly labeled synthetic fixture for a guaranteed reproducible demonstration.

## Run locally (Windows PowerShell)

Install Python 3.11/3.12, unzip project and open a terminal **inside** the project directory:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Open the localhost address printed in the terminal (normally `http://localhost:8501`). If PowerShell blocks activating venv, run `.venv\Scripts\python.exe -m pip install -r requirements.txt` followed by `.venv\Scripts\python.exe -m streamlit run streamlit_app.py`.

### AI credentials
Generate your own Gemini key at https://aistudio.google.com/app/apikey . Set it in Streamlit's sidebar for a personal local session, or set an environment variable `GEMINI_API_KEY`. For Community Cloud deployment, place it in **App > Settings > Secrets** in TOML form:

```toml
GEMINI_API_KEY = "your-key-here"
```

Do not commit `.streamlit/secrets.toml` or publish your key in a GitHub repository. The app can do rule-based scans without a key, **but AI recommendations require the API**. Gemini calls may incur fees or quota limits depending on your account and model availability.

## Deploy to a public Streamlit URL

1. Create a GitHub account and a **new public repository**, e.g. `eurosender-seo-auditor`.
2. Upload the **contents** of the extracted project into the repository root (`streamlit_app.py` must be at the root), not a wrapping directory. Never upload secrets.
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Choose **Create app > Yup, I have an app**. Select the repository, `main` branch, `streamlit_app.py` entrypoint.
5. Open **Advanced settings**, pick Python 3.12, optionally add `GEMINI_API_KEY = "..."` to secrets, then deploy.
6. Copy the allocated `*.streamlit.app` URL for the application. Without configured Gemini credentials, AI remains off but rule-based checks and demo mode run.
7. Test the live URL in an incognito window. Run the **Synthetic demo page** first, then 1 or 2 actual Eurosender URLs, then export the CSV.

**Public app key security:** if you configure a secret Gemini key in a public app, anyone with access to the app may trigger requests billed/charged to your account. For interview deployment, consider running with AI disabled by default, setting quotas, limiting usage or keeping AI-enabled deployment private. A key typed into the sidebar remains session-local.

## Recommended 75-second screen recording

1. Show `Eurosender SEO Content Auditor` homepage and explain input (10s).
2. Switch to synthetic demo, click **Run SEO audit**, show factual findings (15s).
3. Switch to a Eurosender live URL, run the scan and show true extracted signals (20s).
4. If API configured, toggle Gemini AI, rerun and show suggestions (15s).
5. Export CSV, open it in Excel, explain limitations (15s).

## Interview description (English)

> Marketing teams regularly review SEO landing pages, spending time copying HTML metadata, noting missing elements and manually compiling action lists. I built a Streamlit app that audits public Eurosender pages, prioritizes on-page SEO checklist findings, uses Gemini to draft evidence-grounded improvement suggestions, and exports an Excel-ready report. It requires no internal access and can be rerun on a new URL list. This is an independent candidate prototype, not a representation of Eurosender’s existing internal tooling.

### What was tricky and what I'd improve

- Some websites block scripted HTML requests or inject content with JavaScript; the app reports a fetch error instead of inventing data.
- HTML extraction cannot establish Google indexing, search demand, ranking performance or Core Web Vitals. Heuristic thresholds generate review flags rather than definite SEO failures.
- Gemini output can fail due to unavailable credentials, quotas or imperfect JSON. The scan remains usable even when AI is unavailable.
- Future: scheduled change detection with page diffing, consented Search Console integration, robots.txt-aware crawling and human approval workflow.

## Testing

```bash
python -m unittest discover -s tests -v
```

No external API is contacted by unit tests; Gemini behavior is tested with a mock client.


### API availability handling (v1.1)
The app automatically retries transient Gemini HTTP 503 responses once after a short delay, then attempts `gemini-3.5-flash-lite` as fallback. Other errors (including authentication and quota failures) are surfaced rather than masked. Availability and free-tier access vary by API key.
