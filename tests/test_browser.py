import unittest
from unittest.mock import Mock, patch

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

    def test_no_results(self):
        self.respond(text='{"loggedin":true,"success":false}')
        with self.assertRaisesRegex(RuntimeError, "no successful results"):
            self.source.is_authenticated()

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
