"""
Playwright browser launcher for ai-hackathon.

Opens the EduTrivia app at localhost:8000 in a non-headless browser
so you can view the UI alongside the code.

Run the FastAPI server first:
    cd backend && uvicorn app.main:app --reload --port 8000

Then in a separate terminal:
    cd Playwright && python main.py
"""

import time
from playwright.sync_api import sync_playwright


APP_URL = "http://localhost:8000"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--window-size=1280,900"],
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print(f"Opening EduTrivia at {APP_URL} ...")
        page.goto(APP_URL)
        print(f"Title: {page.title()}")
        print("Browser is open. Close the browser window to exit.")

        # Keep the browser open until the window is closed
        try:
            while True:
                time.sleep(1)
                if not browser.is_connected():
                    break
        except KeyboardInterrupt:
            pass
        finally:
            browser.close()


if __name__ == "__main__":
    run()
