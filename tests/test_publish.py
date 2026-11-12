import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import publish
from wtrl_ttt_scraper.deploy import DeployError


class PublishCommandTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            netlify_auth_token="synthetic-token",
            clubs=[
                SimpleNamespace(site_id="site-a"),
                SimpleNamespace(site_id="site-b"),
            ],
        )
        self.patches = [
            patch("publish.Config.load", return_value=self.config),
            patch("publish.NetlifyPublisher"),
            patch("publish.refresh_results"),
            patch("publish.deploy_all_sites"),
            patch("publish.os.chdir"),
        ]
        self.load, self.publisher, self.refresh, self.deploy, _ = [
            p.start() for p in self.patches
        ]
        for p in self.patches:
            self.addCleanup(p.stop)

    def test_default_checks_access_refreshes_then_publishes(self):
        order = Mock()
        order.attach_mock(self.publisher.return_value.site, "site")
        order.attach_mock(self.refresh, "refresh")
        order.attach_mock(self.deploy, "deploy")
        publish.main([])
        self.assertEqual(
            [c[0] for c in order.mock_calls], ["site", "site", "refresh", "deploy"]
        )
        self.refresh.assert_called_once_with(self.config)
        self.deploy.assert_called_once_with(
            self.config, publish=True, publisher=self.publisher.return_value
        )

    def test_check_is_read_only_and_does_not_open_browser(self):
        publish.main(["--check"])
        self.refresh.assert_not_called()
        self.publisher.assert_not_called()
        self.deploy.assert_called_once_with(self.config)

    def test_existing_skips_refresh(self):
        publish.main(["--existing"])
        self.refresh.assert_not_called()
        self.deploy.assert_called_once_with(
            self.config, publish=True, publisher=self.publisher.return_value
        )

    def test_legacy_publish_flag_still_publishes_existing(self):
        publish.main(["--publish"])
        self.refresh.assert_not_called()
        self.assertTrue(self.deploy.call_args.kwargs["publish"])

    def test_bad_token_stops_before_browser_or_upload(self):
        self.publisher.return_value.site.side_effect = DeployError("HTTP 401")
        with self.assertRaises(SystemExit) as caught:
            publish.main([])
        self.assertEqual(caught.exception.code, 1)
        self.refresh.assert_not_called()
        self.deploy.assert_not_called()

    def test_scrape_failure_never_publishes_stale_output(self):
        self.refresh.side_effect = RuntimeError("scrape failed")
        with self.assertRaises(SystemExit):
            publish.main([])
        self.deploy.assert_not_called()

    def test_interrupt_never_publishes(self):
        self.refresh.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            publish.main([])
        self.deploy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
