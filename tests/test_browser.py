import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from main import main_scraper_logic

from wtrl_ttt_scraper.browser import BrowserSource


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.driver = Mock()
        self.source = BrowserSource(self.driver)
        sleeper = patch("wtrl_ttt_scraper.browser.time.sleep")
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def respond(self, status=200, text='{"loggedin":true,"success":true}'):
        self.driver.execute_async_script.return_value = {"status": status, "text": text}

    def test_authenticated(self):
        self.respond()
        self.assertTrue(self.source.is_authenticated())
        args = self.driver.execute_async_script.call_args.args
        self.assertIn(f"season={self.source.latest}", args[1])
        self.assertEqual(args[2:], ("GET", None))

    def test_server_error_does_not_trigger_login_or_print_body(self):
        self.respond(520, "PRIVATE RESPONSE")
        with self.assertRaisesRegex(RuntimeError, "HTTP 520") as caught:
            self.source.is_authenticated()
        self.assertNotIn("PRIVATE", str(caught.exception))

    def test_invalid_json(self):
        self.respond(text="<html>Login</html>")
        with self.assertRaisesRegex(RuntimeError, "non-JSON"):
            self.source.is_authenticated()

    def test_rejected_session(self):
        self.respond(text='{"loggedin":false}')
        with self.assertRaisesRegex(RuntimeError, "browser session"):
            self.source.is_authenticated()

    def test_authenticated_without_latest_results(self):
        self.respond(text='{"loggedin":true,"success":false}')
        self.assertTrue(self.source.is_authenticated())

    def test_missing_latest_results_does_not_block_history(self):
        self.source.latest = 2
        unavailable = {"status": 200, "text": '{"loggedin":true,"success":false}'}
        available = {"status": 200, "text": '{"loggedin":true,"success":true}'}
        self.driver.execute_async_script.side_effect = [
            unavailable,
            unavailable,
            available,
        ]
        event = SimpleNamespace(is_finalised=True, is_recent=False)
        with tempfile.TemporaryDirectory() as directory, patch(
            "main.latest_race", return_value=2
        ), patch.object(self.source, "scrape_event", return_value=(event, True)), patch(
            "wtrl_ttt_scraper.scrape.CACHE_DIR", directory
        ), patch(
            "wtrl_ttt_scraper.scrape.parse_wtrl_result", return_value=None
        ) as parse, patch(
            "wtrl_ttt_scraper.scrape.Result.save_to_json"
        ), patch(
            "builtins.print"
        ):
            main_scraper_logic(SimpleNamespace(clubs=[]), source=self.source)
        parse.assert_called_once_with({"loggedin": True, "success": True})
        urls = [
            call.args[1] for call in self.driver.execute_async_script.call_args_list
        ]
        self.assertIn("season=2", urls[1])
        self.assertIn("season=1", urls[2])

    def test_browser_error(self):
        self.driver.execute_async_script.return_value = {
            "error": "Browser request failed"
        }
        with self.assertRaisesRegex(RuntimeError, "Browser request failed"):
            self.source.is_authenticated()

    def test_event_post(self):
        self.respond(text="<html>synthetic event</html>")
        response = self.source.fetch_event(394)
        self.assertEqual(response.text, "<html>synthetic event</html>")
        args = self.driver.execute_async_script.call_args.args
        self.assertEqual(args[1:], ("/ttt/TTT-Results-beta.php", "POST", "wtrlid=394"))

    def test_latest_forces_refresh(self):
        with patch("wtrl_ttt_scraper.browser.scrape.scrape_result") as scrape_result:
            self.source.scrape_result(self.source.latest)
            self.assertTrue(scrape_result.call_args.kwargs["refresh_cache"])
            self.assertEqual(
                scrape_result.call_args.kwargs["fetcher"], self.source.fetch_result
            )
        with patch("wtrl_ttt_scraper.browser.scrape.scrape_event") as scrape_event:
            self.source.scrape_event(self.source.latest)
            self.assertTrue(scrape_event.call_args.kwargs["refresh_cache"])

    def test_history_keeps_cache(self):
        with patch("wtrl_ttt_scraper.browser.scrape.scrape_result") as scrape_result:
            self.source.scrape_result(self.source.latest - 1)
            self.assertFalse(scrape_result.call_args.kwargs["refresh_cache"])


if __name__ == "__main__":
    unittest.main()
