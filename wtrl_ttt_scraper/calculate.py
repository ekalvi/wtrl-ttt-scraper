from datetime import datetime, timedelta


def calculate_percentile(rank, total_entries) -> float:
    """
    Calculate the percentile as a percentage to one decimal place.

    Args:
        rank (int): The team's rank.
        total_entries (int): The total number of teams.

    Returns:
        float: The percentile as a float (e.g., 0.857).
    """
    return round((1 - rank / total_entries) * 100, 1)


def race_to_date(race_number: int) -> datetime:
    """
    Converts a race number to its corresponding date.

    Args:
        race_number (int): The race number.

    Returns:
        datetime: The date of the race.
    """
    # The date of Race #300
    base_race = 300
    base_date = datetime(2025, 1, 16)  # Thursday, January 16, 2025

    # Calculate the offset in weeks
    week_difference = race_number - base_race
    race_date = base_date + timedelta(weeks=week_difference)

    return race_date


def date_to_race(date: datetime) -> int:
    """
    Converts a given date to the most recent race number.

    Args:
        date (datetime): The date to calculate the race number for.

    Returns:
        int: The most recent race number.
    """
    # Base race and date
    base_race = 300
    base_date = datetime(2025, 1, 16)  # Thursday, January 16, 2025

    # Calculate the difference in weeks
    days_difference = (date - base_date).days
    weeks_difference = days_difference // 7

    # Calculate the race number
    race_number = base_race + weeks_difference
    return race_number


def latest_race():
    return date_to_race(datetime.now())
