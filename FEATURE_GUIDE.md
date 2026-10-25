# HealthAssist v2 · Practical walkthrough

## First launch without an API key

1. Open Overview and load the fictional records. Their aliases start with DEMO.
2. Choose a record under Active encounter in the sidebar.
3. Open Clinical Workspace. The first fictional record has three synthetic BP/pulse/SpO2/temperature observations. Plot a single measurement series so units remain meaningful.
4. Add only measurements actually recorded; check the relevant fields before saving. Empty/unchecked measurements are not invented.
5. Record a laboratory result and laboratory-supplied unit/reference interval if available.
6. Write a SOAP note. Its review checkbox records a user statement, not professional verification.
7. Add care-preparation tasks and update their status. Planned dates do not create reminder notifications.
8. Download the printable report, open it in a browser, then Print → Save as PDF.
9. Export a workspace backup. Test restoration using a second browser session. The importer restores patient records, observations, labs, notes and tasks; directory/activity fields are exported for reference but not automatically restored.

## Connect your AI provider

1. Open AI Care Agent; expand API connection in the sidebar.
2. Choose OpenAI or Gemini and supply your matching API key.
3. Select a tool-calling model available to your account. Defaults are editable.
4. Choose Patient/Doctor and reply language.
5. Explicitly include selected encounter context if you want record-specific answers.
6. Optionally process documents in the agent's Document knowledge tab, and include them in retrieval.
7. Accept data-sharing consent only after checking/redacting context.
8. Ask a focused question. Example: “Review the included encounter, list missing context, compare the recorded blood-pressure readings numerically and draft questions for the appointment. Do not infer a diagnosis.”
9. Review the tool trace and evidence. Download any AI draft; verify it before pasting it into review notes. Draft tools never automatically write clinical notes or tasks.

## Example prompts

- Patient: “Help me explain my reported concern clearly to my doctor and list questions to ask.”
- Doctor: “Organize the included record into reported facts, documented observations and missing information. Prepare an unreviewed SOAP draft without inventing findings.”
- Documents: “Search the included document for follow-up instructions. Quote and cite supporting excerpts; say if none are found.”
- Trends: “Compare the recorded pulse and blood-pressure readings. Explain arithmetic differences without deciding whether they indicate improvement.”
- Care preparation: “Draft a checklist of documents and questions to bring to a follow-up visit. Do not book or contact anyone.”

## Session scope and privacy

This is not the original AI Studio backend. No hospital APIs or external clinician roster are connected. Facility names and locations are added by the user and require independent verification. Shared-password access is optional; professional modes are not authenticated roles. Public deployment should use de-identified training data and each user's API key unless access and data handling have been independently reviewed.

The context sent to the model omits alias, record ID, district and coordinates. Free-text history or notes may still contain identifiers if a user enters them; remove identifiers before granting sharing consent. Switching providers sends retained chat to the newly selected provider when a request is submitted. Chat and uploaded documents reset on encounter change. Clearing the app does not delete provider retention or downloaded exports.

## Compared with the earlier companion package

The v2 package adds the registry, five-section intake, observations and charts, lab records, SOAP review workflow, patient-context tools, numerical trend tools, care tasks, facilities/map, reference/method registry, printable reports, validated patient-backup import and session activity history. It does not claim to reproduce unverified clinical predictions, autonomous prescribing or regulatory certifications from the previous interface.
