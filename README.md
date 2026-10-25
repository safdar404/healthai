# HealthAssist · Agentic Health Platform v2

A broader **Python / Streamlit workspace** built around the HealthAssist preview, with a context-aware, tool-calling agent. The previous companion chatbot has been expanded into an 11-section platform. This is still a research and educational implementation, not a clinically validated medical device or a production EHR.

## Working modules

| Module | Implemented behavior |
|---|---|
| Overview | Session metrics derived from actual records, fictional training data loader and encounter table. |
| Patient Intake | Five-section form: demographics, reported symptoms/onset, history, medicines/allergies and recording permission. |
| Patient Registry | Alias/ID/district/concern search, record selection, editing, explicit removal and JSON export. |
| Clinical Workspace | Measured vital signs, date/time entry, longitudinal charts, arithmetic trends, lab records, editable SOAP review notes and encounter summary. |
| AI Care Agent | Patient/doctor styles; English/Urdu; OpenAI/Gemini; bounded model-selected tools; opt-in encounter/document context; visible tool results; source excerpts; draft downloads; optional OpenAI speech transcription. |
| Care Tasks | User-created follow-up/appointment-preparation tasks, responsibility, planned date and status. No notifications or real booking. |
| Facilities & GIS | User-maintained facility/clinician directory, filtering, optional external map, CSV export. No verified clinician network, live capacity or automated referral. |
| Calculators | BMI, pulse pressure, estimated MAP, glucose-unit and temperature-unit conversions. Arithmetic only. |
| References & Models | Official reference links and an honest component/method registry. No fabricated ML risk scores or regulatory compliance claims. |
| Reports & Backup | Printable Unicode HTML (browser Print → PDF), per-encounter JSON, observation/directory/activity CSV and v2 workspace backup. Patient backup restoration validates fields before replacement. |
| Settings | Provider/model configuration, clear/reset controls, implementation boundaries and deployment help. |

The layout is fluid and readable, with a teal healthcare identity and custom assets. If the page appears extremely small, reset browser zoom with **Ctrl+0**; browser zoom is independent of Streamlit layout.

## Seven actual agent tools

1. `get_selected_patient_context`: only the opt-in selected de-identified encounter, not the whole registry.
2. `compare_recorded_vitals`: chronological numerical differences; no diagnosis or clinical improvement inference.
3. `search_documents`: keyword retrieval from included PDF/DOCX/TXT/Markdown text with source IDs.
4. `calculate_bmi`: validated arithmetic from supplied measurements.
5. `prepare_handoff`: unreviewed facts/questions draft; nothing sent.
6. `draft_review_note`: unreviewed SOAP-style draft; no signature or automatic save.
7. `draft_care_checklist`: preparation/discussion draft; no booking, notifications or prescriptions.

The model selects tools, Python executes allowed functions, results return to the model, and the loop stops within four rounds. Unknown tools are blocked. There is no hidden network-search, messaging or booking tool.

Selected-context sharing is **off by default**. Patient alias, ID, district and coordinates are excluded. Only the last 30 observations, 15 lab entries and 5 review notes are available, along with reported history. This is partial history; the agent is instructed to state uncertainty. Changing the selected encounter resets chat and uploaded documents, avoiding accidental reuse across patients.

## Important boundaries

- Doctor mode is self-selected and does not verify identity. User-marked review is not a digital medical signature.
- No diagnosis, medication prescribing/dose adjustment, validated triage, CVD/eGFR risk engine, medication interaction database, emergency dispatch, live clinician chat or certified EHR integration is included.
- Urgency text screening is conservative, unvalidated and incomplete; historical or negated descriptions can trigger it. A negative screen never means someone is safe.
- No autonomous clinical decision or guaranteed “best treatment” is supplied. Discuss options with qualified professionals.
- Records, tasks and activity are session-local on the Streamlit server. No multi-user database or durable server storage is implied. Export backups before the session ends.
- Reports and backups are unencrypted. Activity logs are not tamper-proof compliance logs. Use de-identified training data unless a separately reviewed deployment meets your clinical/privacy requirements.
- The facility directory is user supplied and not professionally verified. The optional map fetches external map tiles after opt-in.
- Uploaded document text is extracted on the server. Scans/images need OCR elsewhere. Retrieval is keyword based, not vector search, and sources may be incomplete or outdated.
- API/transcription usage is billed by your selected provider. The app has no access to real doctors, hospitals or messaging credentials.

## 1. Run in VS Code / Windows PowerShell

Install **Python 3.12** (recommended), VS Code and its Microsoft Python extension. Extract the ZIP and open the `HealthAssist_Agentic_Platform` folder in VS Code. Open Terminal → New Terminal:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the localhost address printed by Streamlit, usually http://localhost:8501. These commands do not require PowerShell activation, avoiding execution-policy issues. Or double-click `run_windows.bat`. Select `.venv` as the VS Code interpreter; the included launch configuration supports F5 when Python Debugger is installed.

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

## 2. Add YOUR API key

**Easiest:** choose OpenAI or Gemini in the sidebar and enter your key in the password field. It is used only in the session and is never written to the project. The key is sent to its selected provider for authentication. Do not paste keys in chat messages, GitHub, screenshots or documents.

Alternatively copy `.env.example` to `.env` locally. Set the matching key and a strong `APP_ACCESS_PASSWORD` to enable the private workspace gate and shared server key. Without a gate, server keys are intentionally ignored by default. Public BYOK mode (each visitor provides a key) needs no server key.

OpenAI and Gemini keys are different. Use the corresponding provider. The default model IDs are editable; access depends on your provider account, region, billing and model availability. ChatGPT subscriptions are separate from API billing. The app does not require both providers.

## 3. Upload to GitHub

Create an empty repository, for example `healthassist-agentic-streamlit`. From this extracted folder:

```bash
git init
git add .
git commit -m "Add HealthAssist agentic Streamlit app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/healthassist-agentic-streamlit.git
git push -u origin main
```

Replace `YOUR_USERNAME`. Or use GitHub's Upload files interface, including the `src`, `assets` and `.streamlit/config.toml` files. Never upload `.venv`, `.env` or `.streamlit/secrets.toml`. Included `.gitignore` protects these paths. Verify the staged files before pushing; Git cannot automatically hide a secret once committed. The included GitHub Actions workflow runs tests on push.

## 4. Deploy on Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ with your GitHub account.
2. Select **Create app**, the repository and branch `main`.
3. Set main file path to **`app.py`** (if files are inside a subfolder, use `HealthAssist_Agentic_Platform/app.py`).
4. Advanced settings: select **Python 3.12**.
5. In Secrets, paste settings from `.streamlit/secrets.toml.example` and replace placeholders. For private shared-key use, set a strong `APP_ACCESS_PASSWORD` and the matching provider key. Keep `ALLOW_SHARED_KEY = "false"`.
6. Deploy. For public BYOK use, leave server API keys blank; visitors supply their own sidebar key.

A public shared key without authentication exposes your API budget. `ALLOW_SHARED_KEY = "true"` is an explicit opt-in for trusted environments; leave it false for public apps. The password gate is a simple shared workspace password, not enterprise identity or verified clinician authentication. Community Cloud is not being represented as an approved host for identifiable clinical records. Configure appropriate access, policies and infrastructure before any real clinical use.

## 5. Use the agent

1. Select role, language, provider and model; enter your key.
2. For document questions, process files in **Document knowledge**. Inspect extraction. Scanned files need OCR first.
3. Tick **Include loaded documents** if wanted and review the data-sharing consent.
4. Ask a focused question, e.g. “I am preparing a doctor visit. What details should I bring?”
5. For a tool demonstration: “Calculate BMI for 70 kg and 170 cm,” or “Prepare a handoff draft from these facts…”
6. Expand tool activity to review the results and source excerpts. Citations reflect retrieved text, not verified clinical authority. The model may still make errors; inspect them.
7. Export Markdown/JSON. Nothing is automatically sent to a doctor. Downloaded files are not encrypted.

Uploaded documents are processed in the Streamlit server session. Included, retrieved excerpts and up to the last 16 chat messages can be sent to the chosen provider. Previously shared excerpts may also be summarized in retained assistant messages. Switching off document inclusion does not remove prior conversation: clear the session to start fresh. Clearing resets application state; it is not a certified deletion mechanism for server memory or provider logs. Provider retention and privacy policies apply. No analytics, database, cloud file sync or cross-user cache is implemented by this package.

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover tool validation, extraction, retrieval, escalation, multi-step tool calling using a fake provider, Streamlit startup, and the password gate. No paid API calls are made. A real API key is required to verify live model responses, quota and audio transcription.

## Troubleshooting

- `ModuleNotFoundError`: install requirements using the same `.venv` Python used to launch Streamlit.
- `401`: wrong key/provider or revoked key. `429`: check provider credits/rate limits.
- Model not found: enter a tool-calling model available to your account.
- No document evidence: inspect extracted text and ask using relevant terms; retrieval is keyword based.
- Voice unavailable: use OpenAI, permit microphone access, record a short message, accept consent, then transcribe.
- Port busy: `python -m streamlit run app.py --server.port 8502`.
- Reboot after dependencies change in Streamlit Cloud. Do not use Python 3.15 for this package; use the tested Python series.

## References and design boundaries

- OpenAI function calling: https://developers.openai.com/api/docs/guides/function-calling
- Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai/
- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit audio input: https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input
- NHS chest-pain escalation information: https://www.nhs.uk/symptoms/chest-pain/
- WHO governance of health AI: https://www.who.int/publications/i/item/9789240084759

Sources inform implementation boundaries; this app is not endorsed by these organizations. No clinical guideline corpus is bundled, and general model knowledge may be outdated. Review before real use.


## Expanded source tree

```text
app.py                          # Root Streamlit launcher (Cloud main file)
src/app.py                      # Main platform navigation and access gate
src/healthassist/
  agent.py                      # Provider clients, seven tools and agent loop
  core.py                       # Extraction, retrieval, handoff, BMI and text screening
  workspace.py                  # Records, trends, backup validation and printable reports
  pages.py                      # Dashboard, intake, registry, clinical UI, maps, tasks, reports
  chat.py                       # API conversation, documents, voice, traces and exports
  style.css                     # Fluid healthcare styling
  __init__.py
assets/                         # Custom logo + AI-generated clinician image
tests/                          # Automated core, agent, workspace and page-flow checks
.streamlit/                     # Theme configuration + secrets example
.github/workflows/tests.yml     # CI checks on push
.vscode/launch.json             # VS Code F5 launcher
requirements.txt
requirements-dev.txt
.env.example
FEATURE_GUIDE.md
README.md
```

Upload ALL source and asset folders. Keep `app.py` as the Streamlit Cloud main file. Do not upload `.env`, real `secrets.toml`, `.venv` or exported patient data. This ZIP is a new v2 package; it is not automatically deployed or pushed to a remote repository.
