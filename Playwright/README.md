# ai-hackathon

Playwright-powered browser automation project.

## Setup

```bash
pip install -r requirements.txt
playwright install
```

## Run

```bash
python main.py
```

## Playwright Paths

- **playwright.exe**: `C:\Users\Saw\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\playwright.exe`
- **Browsers**: `C:\Users\Saw\AppData\Local\ms-playwright\`

## Key APIs

```python
from playwright.sync_api import sync_playwright  # synchronous
from playwright.async_api import async_playwright  # async

# Browsers available: chromium, firefox, webkit
```
