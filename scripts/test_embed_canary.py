"""Offline classification and orchestration tests; never contact browsers or ntfy."""
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import embed_canary as canary


class EmbedCanaryTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"CANARY_NOTIFY": "0", "GITHUB_STEP_SUMMARY": ""})
        self.env.start()
        self.addCleanup(self.env.stop)

    def page(self, errors=(), player=True):
        frame = MagicMock()
        frame.url = "https://www.youtube-nocookie.com/embed/test"
        error_elements = []
        for text, visible in errors:
            element = MagicMock()
            element.inner_text.return_value = text
            element.is_visible.return_value = visible
            error_elements.append(element)
        player_element = MagicMock()
        player_element.is_visible.return_value = player
        frame.query_selector_all.side_effect = [error_elements, [player_element]]
        page = MagicMock()
        page.frames = [frame]
        return page

    def run_main(self, page=None, launch_error=None):
        browser = MagicMock()
        browser.new_page.return_value = page or self.page()
        runtime = MagicMock()
        runtime.chromium.launch.return_value = browser
        runtime.chromium.launch.side_effect = launch_error
        context = MagicMock()
        context.__enter__.return_value = runtime
        module = types.ModuleType("playwright.sync_api")
        module.sync_playwright = MagicMock(return_value=context)
        with patch.dict(sys.modules, {"playwright.sync_api": module}):
            return canary.main()

    def test_visible_configuration_error_fails(self):
        self.assertEqual(self.run_main(self.page([("Error 153: Video player configuration error", True)])), 1)

    def test_bot_wall_with_embed_and_configuration_words_is_inconclusive(self):
        self.assertEqual(self.run_main(self.page([("Sign in to confirm you're not a bot. Embed configuration error", True)])), 0)
        self.assertEqual(canary.classify("Consent required before embed configuration error", False), "INCONCLUSIVE")

    def test_bare_embed_is_not_broken(self):
        self.assertEqual(canary.classify("An unusual embed issue", False), "UNUSUAL")

    def test_video_disabled_is_detected(self):
        self.assertEqual(self.run_main(self.page([("Playback on other websites has been disabled", True)])), 1)

    def test_hidden_error_is_ignored(self):
        self.assertEqual(self.run_main(self.page([("Error 153 configuration error", False)])), 0)

    def test_navigation_failure_is_monitor_error(self):
        page = self.page()
        page.goto.side_effect = TimeoutError("wrapper unreachable")
        self.assertEqual(self.run_main(page), 2)

    def test_launch_failure_is_monitor_error(self):
        self.assertEqual(self.run_main(launch_error=RuntimeError("browser unavailable")), 2)

    def test_inspection_failure_is_monitor_error(self):
        page = self.page()
        page.frames[0].query_selector_all.side_effect = RuntimeError("frame detached")
        self.assertEqual(self.run_main(page), 2)

    def test_notification_opt_out_prevents_network(self):
        with patch("urllib.request.urlopen") as request:
            canary.push("test", "test")
            request.assert_not_called()

    def test_summary_identifies_probe_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.md"
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(path)}):
                self.assertEqual(self.run_main(launch_error=RuntimeError("missing browser")), 2)
            summary = path.read_text()
            self.assertIn("MONITOR_ERROR", summary)
            self.assertIn("does not test native iOS playback", summary)


if __name__ == "__main__":
    unittest.main()
