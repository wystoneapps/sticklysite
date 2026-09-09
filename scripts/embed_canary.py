#!/usr/bin/env python3
"""Probe the hosted YouTube embed fallback, not native iOS video playback.

Exit: 0 healthy/inconclusive/unusual, 1 visible config/embed error,
2 monitoring infrastructure failure. CANARY_NOTIFY=0 disables external alerts.
Other env: NTFY_TOPIC, NTFY_SERVER, CANARY_URL, GITHUB_STEP_SUMMARY.
"""

import html
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "Marksave_YT_alerts")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
CANARY_URL = os.environ.get(
    "CANARY_URL", "https://wystoneapps.com/x/0fd359011beb91c1fdfb11a7f3e50e2e/",
)
BROKEN_PATTERNS = re.compile(
    r"configuration error|error\s*153|not available on this (site|website)|"
    r"playback on other websites has been disabled", re.IGNORECASE,
)
QUIET_PATTERNS = re.compile(
    r"sign in|confirm|not a bot|try again later|consent|accept (all )?cookies",
    re.IGNORECASE,
)


def push(title: str, body: str, priority: str = "high") -> None:
    if os.environ.get("CANARY_NOTIFY", "1") == "0":
        return
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}", data=body.encode(),
        headers={"Title": title, "Priority": priority, "Tags": "rotating_light,tv"},
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as exc:
        print(f"ntfy push failed: {exc}", file=sys.stderr)


def result(status: str, detail: str, code: int) -> int:
    print(f"{status}: {detail}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as output:
                output.write(
                    f"### MarkSave embed canary: {status}\n\n"
                    "Hosted embed-only probe; does not test native iOS playback. "
                    "A monitoring failure provides no player-health result.\n\n"
                    f"<pre>{html.escape(detail[:1000])}</pre>\n"
                )
        except OSError as exc:
            print(f"Could not write workflow summary: {exc}", file=sys.stderr)
    return code


def classify(error_text: str, has_player: bool) -> str:
    # A bot/consent wall can mention an embed or configuration error incidentally.
    if error_text and QUIET_PATTERNS.search(error_text):
        return "INCONCLUSIVE"
    if error_text and BROKEN_PATTERNS.search(error_text):
        return "BROKEN"
    if error_text:
        return "UNUSUAL"
    return "HEALTHY" if has_player else "INCONCLUSIVE"


def inspect(page, now: str) -> int:
    page.goto(CANARY_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(8000)
    frame = next((f for f in page.frames if "youtube-nocookie.com/embed" in f.url), None)
    if frame is None:
        return result("INCONCLUSIVE", "No embed iframe rendered; no playback conclusion.", 0)
    # Hidden error templates are normal player markup, not a failed video.
    error_text = "\n".join(
        (element.inner_text() or "").strip()
        for element in frame.query_selector_all(".ytp-error") if element.is_visible()
    ).strip()
    has_player = any(element.is_visible() for element in frame.query_selector_all(
        "video, .ytp-large-play-button, .html5-video-player"
    ))
    status = classify(error_text, has_player)
    if status == "BROKEN":
        push("MarkSave ALERT: YouTube embed probe failed",
             f"Hosted test video shows a visible config/embed error:\n{error_text}\n{now}\n"
             "This tests the embed fallback only. Native app playback may still work; "
             "video-specific restrictions may also apply.")
    elif status == "UNUSUAL":
        push("MarkSave: unusual YouTube embed error",
             f"Hosted embed probe saw an unrecognized visible error:\n{error_text}\n{now}",
             priority="default")
    detail = error_text or ("Player UI rendered with no visible error; playback not proven."
                            if has_player else "No visible player UI or error; result inconclusive.")
    return result(status, detail, 1 if status == "BROKEN" else 0)


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                return inspect(page, now)
            finally:
                browser.close()
    except Exception as exc:
        detail = f"Monitoring failed ({exc.__class__.__name__}: {exc}); player health unknown."
        push("MarkSave canary needs attention", f"{detail} {now}", priority="default")
        return result("MONITOR_ERROR", detail, 2)


if __name__ == "__main__":
    sys.exit(main())
