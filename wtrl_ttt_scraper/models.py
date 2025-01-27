import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional

from wtrl_ttt_scraper.format import format_time


@dataclass
class Rider:
    team_rank: int  # 'aa': Team rank
    rider_rank: int  # 'bb': Rider rank
    rider_name: str  # 'cc': Rider name
    rider_position: Optional[str]  # 'dd': Position (optional, can be None)
    team_name: str  # 'ee': Team name
    wkg: float  # 'ff': Watts per kilogram
    power: int  # 'gg': Power in watts
    # avg_hr: int  # 'hh': Average heart rate
    completed_laps: int  # 'ii': Laps completed
    total_time: float  # 'jj': Total time (seconds)
    time_gap: float  # 'kk': Time gap to fastest (seconds)
    avg_speed: float  # 'll': Average speed (km/h)
    distance: int  # 'mm': Distance covered (meters)

    @property
    def initials(self) -> str:
        """
        Returns the cleaned initials of the rider's name:
        - Removes everything after '|' and any text inside '[]' or '()'.
        - Normalizes whitespace to ensure no duplicate spaces.
        - Uses the first two initials from the cleaned name.
        - If the first name is a number, combines it with the first letter of the last name.

        Returns:
            str: The rider's initials.
        """
        # Remove everything after '|', and text inside '[]' or '()'
        clean_name = re.sub(r"\|.*", "", self.rider_name)  # Remove text after '|'
        clean_name = re.sub(r"\[.*?]", "", clean_name)  # Remove text inside '[]'
        clean_name = re.sub(r"\(.*?\)", "", clean_name)  # Remove text inside '()'

        # Normalize whitespace
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        # Split into parts
        name_parts = clean_name.split()

        # Handle cases where the first name is a number
        if len(name_parts) > 1 and name_parts[0].isdigit():
            return f"{name_parts[0]}{name_parts[1][0].upper()}"

        # Otherwise, take the first two initials
        return "".join(part[0].upper() for part in name_parts[:2] if part)


@dataclass
class Team:
    riders: List[Rider]  # 'a': List of riders
    rank: int  # 'b': Team rank
    total_distance: float  # 'c': Total distance (km)
    # team_rank: int  # 'd': Rank of team within coffee class
    total_power: float  # 'e': Total power output (Watts)
    zone: int  # 'f': Zone (optional, can be None)
    dropped_riders: int  # 'g': Number of riders dropped
    coffee_class: str  # 'h': Coffee class (e.g., "Espresso")
    team_time: float  # 'i': Total time for the team (seconds)
    lap_count: int  # 'j': Total laps completed
    avg_speed: float  # 'k': Average speed of team (km/h)
    total_tss: int  # 'l': Total Training Stress Score
    total_if: int  # 'm': Total Intensity Factor
    total_np: int  # 'n': Normalized Power
    team_name: str  # 'o': Team name
    # zone: Optional[int]  # 'p': Zone (optional, can be None)
    rider_count: int  # 'q': Number of racers in the team
    completed: int  # 'r': Indicator of whether the team completed
    total_time_calc: float  # 'z': Calculated total time for team (seconds)

    @property
    def average_power(self) -> float:
        """
        Calculate the average power of riders based on the number of riders in the team.
        - For teams with 5 or more riders, use rider_rank 4 and below.
        - For teams with 4 or fewer riders, use the top 3 riders.

        Returns:
            float: The average power in W/kg of the selected riders.
        """
        if len(self.riders) >= 5:
            selected_riders = [
                rider.wkg
                for rider in self.riders
                if rider.rider_rank <= 4 and rider.wkg is not None
            ]
        else:
            selected_riders = [
                rider.wkg
                for rider in sorted(self.riders, key=lambda r: r.rider_rank)[:3]
                if rider.wkg is not None
            ]
        return round(sum(selected_riders) / len(selected_riders), 2)

    @property
    def average_speed(self) -> float:
        if self.avg_speed is None:
            return 0.0
        else:
            return round(self.avg_speed, 1)

    @property
    def finish_time(self) -> str:
        return format_time(self.team_time or 0)

    def rider_initials_list(self, delimiter: str = ",") -> str:
        """
        Returns a string of rider initials in finishing order, separated by the specified delimiter.

        Args:
            delimiter (str): The delimiter to use between rider initials.

        Returns:
            str: A string of rider initials in finishing order.
        """
        return delimiter.join(
            rider.initials for rider in sorted(self.riders, key=lambda r: r.rider_rank)
        )


@dataclass
class Result:
    event: Optional[str]  # 'event': Event name (optional)
    data: List[Team]  # 'data': List of teams
    success: bool  # 'success': API call success
    loggedin: bool  # 'loggedin': User logged in

    def get_team(self, name: str) -> Optional[Team]:
        for team in self.data:
            if team.team_name == name:
                return team
        return None

    @property
    def entries(self) -> int:
        return len(self.data)

    def coffee_class_entries(self, coffee_class: str) -> int:
        entries = 0
        for team in self.data:
            if team.coffee_class == coffee_class:
                entries += 1
        return entries

    def coffee_rank(self, team: Team) -> int:
        rank = 1
        for other_team in self.data:
            if (
                team.coffee_class == other_team.coffee_class
                and team.rank > other_team.rank
            ):
                rank += 1
        return rank

    @staticmethod
    def save_to_json(result: "Result", output_file: str):
        """
        Save a WTRLResult instance to a JSON file.

        Args:
            result (Result): The WTRLResult instance to save.
            output_file (str): The path to the output JSON file.
        """
        try:
            # Convert the dataclass instance to a dictionary
            result_dict = asdict(result)

            # Serialize the dictionary to JSON
            with open(output_file, "w") as file:
                json.dump(result_dict, file, default=str, indent=4)

        except Exception as e:
            raise Exception(f"An error occurred while saving the WTRLResult: {e}")

    @staticmethod
    def load_from_json(input_file: str) -> "Result":
        """
        Load a WTRLResult instance from a JSON file.

        Args:
            input_file (str): The path to the JSON file.

        Returns:
            Result: An instance of the WTRLResult class populated with data from the JSON file.
        """
        from wtrl_ttt_scraper.parse import parse_wtrl_result

        with open(input_file, "r") as file:
            data = json.load(file)
        return parse_wtrl_result(data)


@dataclass
class Event:
    race_title: str
    course_name: str
    laps: int
    distance_km: float
    race_date: datetime
    status: str

    @property
    def is_finalised(self) -> bool:
        """
        Returns True if the event is finalised (status is 'Finalised')
        or if the race date is more than one week old.
        """
        one_week_ago = datetime.now() - timedelta(weeks=1)
        return self.status == "Finalised" or self.race_date < one_week_ago

    @staticmethod
    def save_to_json(event: "Event", output_file: str):
        """
        Save an Event instance to a JSON file.

        Args:
            event (Event): The Event instance to save.
            output_file (str): The path to the output JSON file.
        """
        try:
            # Convert the dataclass instance to a dictionary
            event_dict = asdict(event)

            # Serialize the dictionary to JSON, handling datetime fields
            with open(output_file, "w") as file:
                json.dump(event_dict, file, default=str, indent=4)

        except Exception as e:
            raise Exception(f"An error occurred while saving the Event: {e}")

    @staticmethod
    def load_from_json(input_file: str) -> "Event":
        """
        Load an Event instance from a JSON file.

        Args:
            input_file (str): The path to the JSON file.

        Returns:
            Event: An instance of the Event class populated with data from the JSON file.
        """
        # Read and parse the JSON file
        with open(input_file, "r") as file:
            data = json.load(file)

        # Convert the race_date string back to a datetime object
        data["race_date"] = datetime.fromisoformat(data["race_date"])

        # Create and return an Event instance
        return Event(**data)
