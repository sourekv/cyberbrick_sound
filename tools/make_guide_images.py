#!/usr/bin/env python3
"""Pictures for docs/user-guide.md: screenshots of web/index.html on its simulated module, written to docs/guide/.
The simulated module holds the default sets of web/demo_sets.js (made by tools/make_default_sets.py; without that file,
two small demo sets, so the pictures differ a little).

    python tools/make_guide_images.py            needs Playwright with Chromium or Edge (as tools/render_pcb.py)
"""
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PAGE = "file:///" + os.path.join(ROOT, "web", "index.html").replace("\\", "/")
OUT = os.path.join(ROOT, "docs", "guide")


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            b = p.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 1040, "height": 900}, color_scheme="light")
        pg.goto(PAGE); pg.wait_for_timeout(600)
        pg.click("#howto summary"); pg.wait_for_timeout(300)
        pg.locator("#howto").locator("xpath=..").screenshot(path=os.path.join(OUT, "01-how-it-works.png"))
        pg.click("#howto summary")
        pg.screenshot(path=os.path.join(OUT, "02-start.png"), clip={"x": 0, "y": 0, "width": 1040, "height": 260})
        pg.click("#btnSim"); pg.wait_for_timeout(1500)
        pg.locator("#setRows tr").nth(1).get_by_text("Default", exact=True).click(); pg.wait_for_timeout(500)
        pg.locator("#secSets").screenshot(path=os.path.join(OUT, "03-list.png"))
        pg.locator("#setRows tr").first.get_by_text("Copy", exact=True).click(); pg.wait_for_timeout(2500)
        pg.locator("#secEdit").screenshot(path=os.path.join(OUT, "04-editor.png"))
        pg.locator("#soundRows .sound").first.screenshot(path=os.path.join(OUT, "05-name-row.png"))
        b.close()
    print("pictures in", OUT)


if __name__ == "__main__":
    main()
