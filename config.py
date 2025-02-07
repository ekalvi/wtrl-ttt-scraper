from dataclasses import dataclass
from typing import List, Optional
import json
import os

from wtrl_ttt_scraper.format import slugify

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Root directory of the project
CACHE_DIR = os.path.join(BASE_DIR, "cache")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CONFIG = None


@dataclass
class TeamConfig:
    team_name: str
    aliases: List[str]


@dataclass
class ClubConfig:
    club_name: str
    site_id: str
    teams: List[TeamConfig]

    @property
    def club_results_dir(self) -> str:
        """Returns the path where results for this club are stored."""
        return os.path.join(RESULTS_DIR, slugify(self.club_name))


@dataclass
class Config:
    netlify_auth_token: str
    wtrl_sid: str
    wtrl_ouid: str
    ctoken: str
    clubs: List[ClubConfig]
    file_path: str = None

    @staticmethod
    def load(file_path: str = "config.json") -> "Config":
        """Loads the configuration file and initializes a Config instance."""
        global CONFIG

        try:
            with open(file_path, "r") as file:
                data = json.load(file)

            CONFIG = Config(
                netlify_auth_token=data["netlify_auth_token"],
                wtrl_sid=data["wtrl_sid"],
                wtrl_ouid=data["wtrl_ouid"],
                ctoken=data["ctoken"],
                clubs=[
                    ClubConfig(
                        club_name=club["club_name"],
                        site_id=club["site_id"],
                        teams=[
                            TeamConfig(
                                team_name=team["team_name"], aliases=team["aliases"]
                            )
                            for team in club["teams"]
                        ],
                    )
                    for club in data["clubs"]
                ],
                file_path=file_path,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file '{file_path}' not found.")
        except json.JSONDecodeError:
            raise ValueError(
                f"Error parsing JSON in '{file_path}'. Ensure valid formatting."
            )
        except KeyError as e:
            raise KeyError(f"Missing required key in config file: {e}")

        return CONFIG

    @staticmethod
    def get() -> Optional["Config"]:
        """Returns the globally loaded configuration or raises an error if not loaded."""
        if CONFIG is None:
            raise ValueError("Configuration not loaded. Call load() first.")
        return CONFIG

    def save_credentials(self, new_credentials: dict) -> "Config":
        """Updates the global WTRL credentials and saves them to the file."""
        if not self.file_path:
            raise ValueError(
                "Cannot save credentials. Configuration file path is missing."
            )

        try:
            with open(self.file_path, "r") as file:
                config = json.load(file)

            # Update the global WTRL credentials
            config["wrtl_sid"] = new_credentials.get("wrtl_sid", config["wrtl_sid"])
            config["wrtl_ouid"] = new_credentials.get("wrtl_ouid", config["wrtl_ouid"])
            config["ctoken"] = new_credentials.get("ctoken", config["ctoken"])

            with open(self.file_path, "w") as file:
                # noinspection PyTypeChecker
                json.dump(config, file, indent=4)

            print(
                f"✅ Updated WTRL credentials in '{self.file_path}'. Reloading config..."
            )

            # Reload the updated configuration
            return Config.load(self.file_path)

        except FileNotFoundError:
            raise FileNotFoundError(f"Config file '{self.file_path}' not found.")
        except json.JSONDecodeError:
            raise ValueError(
                f"Error decoding JSON in '{self.file_path}'. Verify the format."
            )
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")
