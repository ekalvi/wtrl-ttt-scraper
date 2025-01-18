import re
from datetime import datetime


def format_percent(percent: float) -> str:
    """
    Calculate the percentile as a percentage to one decimal place.

    Args:
        percent (float): Percent as a float

    Returns:
        str: The percent as a formatted string (e.g., '85.7%').
    """
    return f"{percent:.1f}%"


def format_time(seconds: float) -> str:
    """
    Converts a time value in seconds to the format MM:SS.mmm.

    Args:
        seconds (float): Time in seconds.

    Returns:
        str: Formatted time string in MM:SS.mmm.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds_remainder:05.2f}"
    else:
        return f"{minutes:02}:{seconds_remainder:05.2f}"


def slugify(val: str) -> str:
    """
    Converts a team name to a slugified filename using underscores.

    Args:
        val (str): The string to convert.

    Returns:
        str: A slugified filename with underscores, in lowercase.
    """
    # Remove special characters and replace spaces with underscores
    slug = re.sub(r"[^\w\s]", "", val)  # Remove non-alphanumeric characters
    slug = re.sub(r"\s+", "_", slug)  # Replace spaces with underscores
    return slug.lower()


def iso_8601_format(date_obj: datetime) -> str:
    """
    Formats a datetime object into a sortable and display-friendly format for DataTable.

    Args:
        date_obj (datetime): A datetime object to format.

    Returns:
        str: sortable format (ISO 8601)
    """
    return date_obj.strftime("%Y-%m-%d")  # ISO 8601 format
