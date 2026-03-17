# Local Watsonx Embed Test

Standalone local page for testing the watsonx Orchestrate embed without changing the main app.

## Run

```powershell
cd D:\codex\wson_ai\ai-hackathon\embed-local
..\backend\.venv\Scripts\python.exe serve.py
```

Then open `http://127.0.0.1:8787`.

## Notes

- This page does not use or expose your API key.
- It only uses the embed identifiers and the official loader.
