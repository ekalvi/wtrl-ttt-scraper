"""Refresh results in Chrome, then publish all configured Netlify dashboards."""

import argparse
import os
from pathlib import Path

from config import Config
from run_browser import main as refresh_results
from wtrl_ttt_scraper.deploy import DeployError, NetlifyPublisher, deploy_all_sites


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Read-only preflight of existing output and site access; no browser or uploads",
    )
    mode.add_argument(
        "--existing",
        "--publish",
        dest="existing",
        action="store_true",
        help="Publish existing local results without refreshing (legacy alias: --publish)",
    )
    args = parser.parse_args(argv)
    os.chdir(Path(__file__).resolve().parent)
    try:
        config = Config.load("config.secret.json")
        if args.check:
            deploy_all_sites(config)
            return
        publisher = NetlifyPublisher(config.netlify_auth_token)
        if not args.existing:
            # Fail on bad credentials before asking the user to log in and scrape.
            if not config.clubs:
                raise DeployError("No clubs configured.")
            for club in config.clubs:
                publisher.site(club.site_id)
            print(
                "Netlify access verified. Refreshing results before publishing all configured clubs."
            )
            refresh_results(config)
        deploy_all_sites(config, publish=True, publisher=publisher)
    except (RuntimeError, FileNotFoundError, ValueError, KeyError) as error:
        parser.exit(1, f"Publishing stopped: {error}\n")


if __name__ == "__main__":
    main()
