"""Preflight by default; --publish explicitly promotes all configured dashboards."""

import argparse
import os
from pathlib import Path

from config import Config
from wtrl_ttt_scraper.deploy import DeployError, deploy_all_sites


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Upload and publish all configured clubs after preflight succeeds",
    )
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parent)
    try:
        config = Config.load("config.secret.json")
        deploy_all_sites(config, publish=args.publish)
    except (DeployError, FileNotFoundError, ValueError, KeyError) as error:
        parser.exit(1, f"Publishing stopped: {error}\n")


if __name__ == "__main__":
    main()
