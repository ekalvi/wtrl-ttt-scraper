from dataclasses import dataclass, field
from typing import List
import json
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Root directory of the project
CACHE_DIR = os.path.join(BASE_DIR, "cache")
RESULTS_DIR = os.path.join(BASE_DIR, "results")


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

    @staticmethod
    def load(file_path: str = "config.secret.json") -> "Config":
        """
        Load configuration from a JSON file.

        Args:
            file_path (str): Path to the configuration file.

        Returns:
            Config: A populated Config instance.
        """
        with open(file_path, "r") as file:
            data = json.load(file)
        return Config(
            club_name=data["club_name"],
            wtrl_sid=data["wtrl_sid"],
            wtrl_ouid=data["wtrl_ouid"],
            ctoken=data["ctoken"],
            teams=[
                TeamConfig(team_name=team["team_name"], aliases=team["aliases"])
                for team in data["teams"]
            ],
        )
