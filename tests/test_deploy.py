import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from wtrl_ttt_scraper.deploy import (
    DeployError,
    NetlifyPublisher,
    dashboard_files,
    deploy_all_sites,
)


def response(data=None, status=200):
    result = Mock(status_code=status)
    result.json.return_value = data or {}
    return result


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.publisher = NetlifyPublisher(
            "synthetic-token", self.session, poll_attempts=1
        )

    def test_unauthorized_sanitized(self):
        self.session.request.return_value = response({"secret": "DO NOT PRINT"}, 401)
        with self.assertRaisesRegex(DeployError, "HTTP 401") as caught:
            self.publisher.site("site-a")
        self.assertNotIn("DO NOT PRINT", str(caught.exception))
        kwargs = self.session.request.call_args.kwargs
        self.assertEqual(kwargs["timeout"], 30)
        self.assertFalse(kwargs["allow_redirects"])

    def test_uploads_only_required_hash_once_and_creates_draft(self):
        content = b"<html>synthetic</html>"
        sha = hashlib.sha1(content).hexdigest()
        self.session.request.side_effect = [
            response({"id": "deploy-a", "required": [sha]}),
            response(),
            response({"state": "ready"}),
        ]
        self.assertEqual(
            self.publisher.prepare(
                "site-a",
                {
                    "index.html": content,
                    "duplicate.html": content,
                    "cached.html": b"cached",
                },
            ),
            "deploy-a",
        )
        calls = self.session.request.call_args_list
        self.assertTrue(calls[0].kwargs["json"]["draft"])
        self.assertEqual([c.args[0] for c in calls], ["POST", "PUT", "GET"])

    def test_upload_failure_stops_before_promotion(self):
        content = b"synthetic"
        self.session.request.side_effect = [
            response(
                {"id": "deploy-a", "required": [hashlib.sha1(content).hexdigest()]}
            ),
            response(status=500),
        ]
        with self.assertRaisesRegex(DeployError, "HTTP 500"):
            self.publisher.prepare("site-a", {"index.html": content})
        self.assertEqual(self.session.request.call_count, 2)

    def test_prepare_timeout_does_not_retry_post(self):
        self.session.request.side_effect = requests.Timeout("sensitive detail")
        with self.assertRaisesRegex(DeployError, "No write was retried") as caught:
            self.publisher.prepare("site-a", {"index.html": b"x"})
        self.assertNotIn("sensitive", str(caught.exception))
        self.assertEqual(self.session.request.call_count, 1)

    def test_restore_timeout_reconciles_without_retry(self):
        self.session.request.side_effect = [
            requests.Timeout(),
            response(
                {
                    "published_deploy": {"id": "deploy-a"},
                    "ssl_url": "https://example.test",
                }
            ),
        ]
        self.assertEqual(
            self.publisher.publish("site-a", "deploy-a"), "https://example.test"
        )
        self.assertEqual(
            [c.args[0] for c in self.session.request.call_args_list], ["POST", "GET"]
        )

    def test_restore_timeout_unconfirmed(self):
        self.session.request.side_effect = [
            requests.Timeout(),
            response({"published_deploy": {"id": "old"}}),
        ]
        with self.assertRaisesRegex(DeployError, "unconfirmed"):
            self.publisher.publish("site-a", "deploy-a")

    @patch("wtrl_ttt_scraper.deploy.time.sleep")
    def test_ready_timeout(self, sleep):
        self.session.request.side_effect = [
            response({"id": "deploy-a", "required": []}),
            response({"state": "uploading"}),
        ]
        with self.assertRaisesRegex(DeployError, "not ready"):
            self.publisher.prepare("site-a", {"index.html": b"x"})

    def test_failed_deploy(self):
        self.session.request.side_effect = [
            response({"id": "deploy-a", "required": []}),
            response({"state": "error"}),
        ]
        with self.assertRaisesRegex(DeployError, "failed"):
            self.publisher.prepare("site-a", {"index.html": b"x"})


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        (root / "index.html").write_text("<html>synthetic</html>")
        self.root = root
        self.config = SimpleNamespace(
            netlify_auth_token="synthetic-token",
            clubs=[
                SimpleNamespace(club_name=name, site_id=name, club_results_dir=root)
                for name in ("club-a", "club-b")
            ],
        )
        self.publisher = Mock()
        self.publisher.site.return_value = {"ssl_url": "https://example.test"}
        self.publisher.prepare.side_effect = ["deploy-a", "deploy-b"]
        self.publisher.publish.return_value = "https://example.test"

    def test_preflight_is_read_only(self):
        self.assertEqual(deploy_all_sites(self.config, publisher=self.publisher), [])
        self.assertEqual(self.publisher.site.call_count, 2)
        self.publisher.prepare.assert_not_called()
        self.publisher.publish.assert_not_called()

    def test_all_preflights_before_any_writes(self):
        self.publisher.site.side_effect = [
            {"url": "https://example.test"},
            DeployError("401"),
        ]
        with self.assertRaises(DeployError):
            deploy_all_sites(self.config, publish=True, publisher=self.publisher)
        self.publisher.prepare.assert_not_called()

    def test_all_drafts_before_any_promotion(self):
        result = deploy_all_sites(self.config, publish=True, publisher=self.publisher)
        self.assertEqual(len(result), 2)
        self.assertEqual(
            [c[0] for c in self.publisher.mock_calls],
            [
                "site",
                "site",
                "prepare",
                "prepare",
                "publish",
                "publish",
            ],
        )

    def test_second_upload_failure_leaves_production_alone(self):
        self.publisher.prepare.side_effect = ["deploy-a", DeployError("upload failed")]
        with self.assertRaises(DeployError):
            deploy_all_sites(self.config, publish=True, publisher=self.publisher)
        self.publisher.publish.assert_not_called()

    def test_partial_publish_is_reported(self):
        self.publisher.publish.side_effect = [
            "https://example.test",
            DeployError("failed"),
        ]
        with patch("builtins.print") as output, self.assertRaises(DeployError):
            deploy_all_sites(self.config, publish=True, publisher=self.publisher)
        self.assertTrue(any("1/2" in str(c) for c in output.call_args_list))

    def test_reject_unexpected_files_before_network(self):
        (self.root / "config.secret.json").write_text("{}")
        with self.assertRaisesRegex(DeployError, "Unexpected file"):
            deploy_all_sites(self.config, publish=True, publisher=self.publisher)
        self.publisher.site.assert_not_called()

    def test_reject_symlink(self):
        (self.root / "link.html").symlink_to(self.root / "index.html")
        with self.assertRaisesRegex(DeployError, "symlinks"):
            dashboard_files(self.root)

    def test_missing_index(self):
        (self.root / "index.html").unlink()
        with self.assertRaisesRegex(DeployError, "index.html"):
            dashboard_files(self.root)

    def test_duplicate_site_ids(self):
        self.config.clubs[1].site_id = "club-a"
        with self.assertRaisesRegex(DeployError, "distinct"):
            deploy_all_sites(self.config, publisher=self.publisher)
        self.publisher.site.assert_not_called()


if __name__ == "__main__":
    unittest.main()
