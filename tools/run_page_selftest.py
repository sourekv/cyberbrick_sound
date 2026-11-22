#!/usr/bin/env python3
"""Runs the self-test of the sound sets page (web/index.html#selftest) in headless Edge with Playwright and prints it.

The page tests itself against its simulated module (no hardware): list, copy, edit, write, delete, CRC, layered sets.
Needs: pip install playwright (the browser is the installed Microsoft Edge, no download).

    python tools/run_page_selftest.py
Exit status 1 when a check fails or the page does not finish.
"""
import functools, http.server, os, socketserver, sys, threading, time
from playwright.sync_api import sync_playwright

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    text, errs = "", []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        pg = b.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/index.html#selftest" % port)
        t0 = time.time()
        while time.time() - t0 < 120:
            try:
                text = pg.inner_text("#selftest", timeout=3000)
            except Exception:
                text = ""
            if "DONE" in text:
                break
            time.sleep(1)
        b.close()
    srv.shutdown()
    print(text)
    if errs:
        print("page errors:", errs[:5])
    ok = "DONE" in text and "FAIL" not in text and not errs
    print("all checks passed" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
