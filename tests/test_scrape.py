import tempfile
import unittest
from unittest.mock import Mock, patch

from main import load_config
from wtrl_ttt_scraper import scrape


class AuthenticationTests(unittest.TestCase):
    def response(self, status=200, **data):
        response = Mock(status_code=status)
        response.json.return_value = data
        return response

    def test_unavailable_race_is_not_failed_login(self):
        self.assertTrue(
            scrape.is_authenticated(self.response(loggedin=True, success=False))
        )

    def test_logged_out(self):
        self.assertFalse(scrape.is_authenticated(self.response(loggedin=False)))

    def test_http_error_is_not_failed_login(self):
        with self.assertRaisesRegex(RuntimeError, "HTTP 520"):
            scrape.is_authenticated(self.response(status=520))

    def test_non_json_stops(self):
        response = self.response()
        response.json.side_effect = ValueError()
        with self.assertRaisesRegex(RuntimeError, "non-JSON"):
            scrape.is_authenticated(response)

    def test_unavailable_results_have_separate_exception(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            scrape, "CACHE_DIR", directory
        ):
            with self.assertRaises(scrape.ResultsUnavailableError):
                scrape.scrape_result(
                    123, fetcher=lambda _: self.response(loggedin=True, success=False)
                )

    def test_no_secret_config_does_not_fall_back_to_template(self):
        with patch("main.os.path.exists", return_value=False), patch(
            "main.Config.load"
        ) as load:
            with self.assertRaisesRegex(FileNotFoundError, "Copy config.json"):
                load_config()
            load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
