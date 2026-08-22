#!/usr/bin/env python3
"""
MarkSave — YouTube EMBED PLAYER canary.

Companion to the API canary in the markSave repo (scripts/yt-canary/), which
watches the stream-extraction endpoint. THIS one watches the other half — the
embed player itself, i.e. the path that broke with "Error 153". It loads the
hidden wrapper page on wystoneapps.com (same iframe markup + same referer origin
the app uses) in headless Chromium and inspects the player that renders.

Philosophy (same as the API canary): quiet unless it's a REAL break.
    HEALTHY       player UI rendered, no error overlay            -> silent
    INCONCLUSIVE  bot-wall / consent / timeout on datacenter IP   -> silent
    UNUSUAL       error overlay we don't recognize                -> low-prio ntfy
    BROKEN        config/embed error (the 153 class)              -> ALERT + exit 1
                  (exit 1 fails the workflow, so GitHub also emails as backup)

Env: NTFY_TOPIC (default Marksave_YT_alerts), NTFY_SERVER, CANARY_URL.
Exit: 0 healthy/inconclusive/unusual, 1 broken, 2 canary internal error.
"""

import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "Marksave_YT_alerts")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
CANARY_URL = os.environ.get(
    "CANARY_URL",
    "https://wystoneapps.com/x/0fd359011beb91c1fdfb11a7f3e50e2e/",
)

# Error texts that mean the embed pipeline is genuinely broken for the app.
BROKEN_PATTERNS = re.compile(
    r"configuration error|error\s*153|not available on this (site|website)|"
    r"playback on other websites has been disabled|embed",
    re.IGNORECASE,
)
# Error texts that are datacenter-IP noise, not a product break.
QUIET_PATTERNS = re.compile(r"sign in|confirm|not a bot|try again later", re.IGNORECASE)


def push(title: str, body: str, priority: str = "high") -> None:
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=body.encode(),
        headers={"Title": title, "Priority": priority, "Tags": "rotating_light,tv"},
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:  # alerting must never crash the canary
        print(f"ntfy push failed: {e}", file=sys.stderr)


def main() -> int:
    from playwright.sync_api import sync_playwright

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        try:
            page.goto(CANARY_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            # Our own page failed to load — monitoring is blind, tell Roger quietly.
            push("MarkSave canary needs attention",
                 f"Embed canary page failed to load ({e.__class__.__name__}). "
                 f"Monitoring is blind until fixed. {now}", priority="default")
            return 2
        page.wait_for_timeout(8000)

        frame = next((f for f in page.frames if "youtube-nocookie.com/embed" in f.url), None)
        if frame is None:
            print("INCONCLUSIVE: no embed iframe rendered (CDN/consent quirk)")
            return 0

        try:
            error_el = frame.query_selector(".ytp-error")
            error_text = (error_el.inner_text() or "").strip() if error_el else ""
            has_player = frame.query_selector("video, .ytp-large-play-button, .html5-video-player") is not None
        except Exception as e:
            print(f"INCONCLUSIVE: frame inspection failed ({e})")
            return 0

        if error_text:
            if BROKEN_PATTERNS.search(error_text):
                push("MarkSave ALERT: YouTube embed player BROKEN",
                     f"The in-app YouTube player path is showing a config/embed error:\n"
                     f"“{error_text}”\n{now}\nUsers are seeing the fallback message. "
                     f"Open Cowork and get a fix shipped.")
                print(f"BROKEN: {error_text}")
                return 1
            if QUIET_PATTERNS.search(error_text):
                print(f"INCONCLUSIVE (bot-wall class): {error_text}")
                return 0
            push("MarkSave: unusual YouTube embed error",
                 f"Embed canary saw an error it doesn't recognize:\n“{error_text}”\n{now}",
                 priority="default")
            print(f"UNUSUAL: {error_text}")
            return 0

        if has_player:
            print("HEALTHY: player rendered, no error overlay")
            return 0

        print("INCONCLUSIVE: no player UI and no error (slow render?)")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"canary internal error: {e}", file=sys.stderr)
        sys.exit(2)
