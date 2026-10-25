# HealthAssist · Agentic Care Companion

A self-contained **Python / Streamlit edition** for educational doctor–patient conversations using your own OpenAI or Gemini API key. This is a new companion app, not a full port of the previous React/AI Studio clinical platform. It does not include the original hospital registry, GIS surveillance, prescription engine or biometric login.

## What works

- Separate patient and doctor conversation styles; English, Urdu or bilingual replies.
- Genuine bounded agent loop: the model chooses permitted tools; Python runs them and returns results before the final answer.
- Tools: keyword document retrieval, BMI arithmetic, and an unreviewed clinician handoff draft.
- PDF / DOCX / TXT / Markdown extraction with PDF page references and visible retrieval excerpts.
- Typed questions; optional microphone recording → OpenAI transcription → user-reviewed text → chatbot. Replies are text, not spoken audio. Microphone requires browser permission and HTTPS or localhost.
- Tool activity, source excerpts, conversation exports, local care-preparation forms.
- Conservative keyword escalation warnings, plus model instructions to recognize urgent situations. The keyword screen is NOT validated triage and can miss urgent situations or flag historical/negated mentions.
- Teal healthcare dashboard, custom logo and AI-generated clinician illustration.

No real physician messaging, appointment booking, email, live medical web search, OCR, vector embeddings, EHR integration or clinical validation is included. Do not use it to diagnose, prescribe, adjust medication or manage an emergency. Human clinicians must verify any suggestions. Doctor mode is a self-selected audience preference, not verified medical identity.

## 1. Run in VS Code / Windows PowerShell

Install **Python 3.12** (recommended), VS Code and its Microsoft Python extension. Extract the ZIP and open the `HealthAssist_Agentic_Streamlit` folder in VS Code. Open Terminal → New Terminal:

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
3. Set main file path to **`app.py`** (if files are inside a subfolder, use `HealthAssist_Agentic_Streamlit/app.py`).
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

## Source files for GitHub

Upload the **contents** of this folder to your repository root (not just app.py). The complete Python source is in src/. This Python Streamlit edition uses Python modules rather than the original React application's TSX components.

```text
app.py                         # Streamlit launcher; Cloud main file
src/
  app.py                       # Complete Streamlit UI
  healthassist/
    __init__.py
    agent.py                   # Provider clients and tool-calling loop
    core.py                    # Retrieval, extraction, escalation and tools
    style.css                  # Healthcare styling
assets/                        # Logo and clinician image
tests/                         # Automated tests + source path setup
.streamlit/config.toml         # Streamlit theme and upload limits
.streamlit/secrets.toml.example # Template only; never commit actual secrets
.env.example                   # Local key template
.github/workflows/tests.yml    # GitHub Actions checks
.vscode/launch.json            # VS Code F5 configuration
requirements.txt
requirements-dev.txt
run_windows.bat
run_macos_linux.sh
```

On Streamlit Cloud choose **app.py**, not src/app.py, so the launcher configures the source path.
