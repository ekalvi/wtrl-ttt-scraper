import json
from typing import Optional

from wtrl_ttt_scraper.format import remove_ordinal_suffix
from wtrl_ttt_scraper.models import Rider, Team, Result, Event
from datetime import datetime
from bs4 import BeautifulSoup
import re


# Helper function to parse riders
def parse_rider(rider: dict) -> Rider:
    return Rider(
        team_rank=rider["aa"],
        rider_rank=rider["bb"],
        rider_name=rider["cc"],
        rider_position=rider["dd"],
        team_name=rider["ee"],
        wkg=rider["ff"],
        power=rider["gg"],
        # avg_hr=rider['hh'],
        completed_laps=rider["ii"],
        total_time=rider["jj"],
        time_gap=rider["kk"],
        avg_speed=rider["ll"],
        distance=rider["mm"],
    )


# Helper function to parse teams
def parse_team(team: dict) -> Optional[Team]:
    if team.get("a") is None:
        return None

    riders = [parse_rider(r) for r in team["a"]]
    return Team(
        riders=riders,
        rank=team["b"],
        total_distance=team["c"],
        # team_rank=team['d'],
        total_power=team["e"],
        zone=team["f"],
        dropped_riders=team["g"],
        coffee_class=team["h"],
        team_time=team["i"],
        lap_count=team["j"],
        avg_speed=team["k"],
        total_tss=team["l"],
        total_if=team["m"],
        total_np=team["n"],
        team_name=team["o"],
        # zone=team['p'],
        rider_count=team["q"],
        completed=team["r"],
        total_time_calc=team["z"],
    )


# Parse the entire WTRL result
def parse_wtrl_result(data: dict) -> Optional[Result]:
    if not data["data"]:
        # missing race results for some reason
        return None

    teams = []
    for _team in data["data"]:
        # sometimes the team is missing
        team = parse_team(_team)
        if team:
            teams.append(team)

    return Result(
        event=data["event"],
        data=teams,
        success=data["success"],
        loggedin=data["loggedin"],
    )


# Example usage
# Replace '<your_json_here>' with your JSON string
def load_json(json_string: str) -> Result:
    parsed_json = json.loads(json_string)
    return parse_wtrl_result(parsed_json)


def get_race_soup(race_number: int) -> BeautifulSoup:
    html_file_path = f"cache/race_{race_number}.html"
    with open(html_file_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file, "html.parser")


def extract_event(html: str) -> Event:
    # Load the HTML file
    soup = BeautifulSoup(html, "html.parser")

    # Extract Race Title
    race_title = soup.find("h3", class_="text-center").get_text(strip=True)

    # Extract Course Name, Laps, and Distance
    course_info = soup.find("h5", class_="text-center", title=True)
    course_text = course_info.get_text(strip=True) if course_info else ""

    # Parse Course Name
    course_name_match = re.match(r"^(.*?)-", course_text)
    course_name = course_name_match.group(1).strip() if course_name_match else None

    # Parse Laps
    laps_match = re.search(r"-(\d+)\s*Laps", course_text)
    laps = int(laps_match.group(1)) if laps_match else 1

    # Parse Distance
    distance_match = re.search(r"\(([\d.]+)km\)", course_text)
    distance_km = float(distance_match.group(1)) if distance_match else None

    # Extract and Parse Race Date
    race_date_text = soup.find_all("h5", class_="text-center")[-1].get_text(strip=True)

    # Remove ordinal suffixes and parse date
    clean_race_date_text = remove_ordinal_suffix(race_date_text)
    race_date_match = re.search(r"(\d+\s\w+\s\d{4})", clean_race_date_text)
    race_date = (
        datetime.strptime(race_date_match.group(1), "%d %B %Y")
        if race_date_match
        else None
    )

    # Extract Status
    status_element = soup.find("h4", class_="text-center")
    raw_status = status_element.get_text(strip=True) if status_element else None

    # Clean concatenated text in status
    status_match = re.match(r"(Finalised|Provisional)", raw_status)
    status = status_match.group(1) if status_match else None

    # Return as a dataclass
    return Event(
        race_title=race_title,
        course_name=course_name,
        laps=laps,
        distance_km=distance_km,
        race_date=race_date,
        status=status,
    )
