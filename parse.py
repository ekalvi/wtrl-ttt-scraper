import json
from typing import Optional

from models import Rider, Team, WTRLResult


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
    if team["a"] is None:
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
def parse_wtrl_result(data: dict) -> Optional[WTRLResult]:
    if not data["data"]:
        # missing race results for some reason
        return None

    teams = []
    for _team in data["data"]:
        # sometimes the team is missing
        team = parse_team(_team)
        if team:
            teams.append(team)

    return WTRLResult(
        event=data["event"],
        data=teams,
        success=data["success"],
        loggedin=data["loggedin"],
    )


# Example usage
# Replace '<your_json_here>' with your JSON string
def load_json(json_string: str) -> WTRLResult:
    parsed_json = json.loads(json_string)
    return parse_wtrl_result(parsed_json)
