from dataclasses import dataclass, field
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
class Config:
    club_name: str
    wtrl_sid: str
    wtrl_ouid: str
    ctoken: str
    teams: List[TeamConfig] = field(default_factory=list)

    @property
    def club_results_dir(self) -> str:
        return os.path.join(RESULTS_DIR, slugify(self.club_name))

    @staticmethod
    def load(file_path: str = "config.secret.json") -> "Config":
        """
        Load configuration from a JSON file and set globally.

        Args:
            file_path (str): Path to the configuration file.

        Returns:
            Config: A populated Config instance.
        """
        with open(file_path, "r") as file:
            data = json.load(file)

        global CONFIG
        CONFIG = Config(
            club_name=data["club_name"],
            wtrl_sid=data["wtrl_sid"],
            wtrl_ouid=data["wtrl_ouid"],
            ctoken=data["ctoken"],
            teams=[
                TeamConfig(team_name=team["team_name"], aliases=team["aliases"])
                for team in data["teams"]
            ],
        )
        return Config.get()

    @staticmethod
    def get() -> Optional["Config"]:
        """
        Retrieve the globally loaded configuration.

        Returns:
            Config: The loaded configuration object.
        """
        if CONFIG is None:
            raise ValueError("Configuration not loaded. Call load() first.")

        return CONFIG

    @staticmethod
    def save_credentials(new_credentials: dict, file_path: str = "config.secret.json"):
        try:
            # Load the current configuration
            with open(file_path, "r") as file:
                config = json.load(file)

            # Update the credentials
            config["wtrl_sid"] = new_credentials.get("wtrl_sid", config.get("wtrl_sid"))
            config["wtrl_ouid"] = new_credentials.get(
                "wtrl_ouid", config.get("wtrl_ouid")
            )
            config["ctoken"] = new_credentials.get("ctoken", config.get("ctoken"))

            # Save the updated configuration
            with open(file_path, "w") as file:
                json.dump(config, file, indent=4)

            print("config.secret.json has been updated successfully.")

        except FileNotFoundError:
            print(f"{file_path} not found. Ensure the file exists.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON in {file_path}. Verify the file's format.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
