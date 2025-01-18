import json
from typing import Optional

import requests
import os

from config import Config
from models import WTRLResult
from parse import parse_wtrl_result

# Base URL for scraping
url_template = (
    "https://www.wtrl.racing/api/wtrlruby/?wtrlid=ttt&season={season}&action=results"
)


# Headers from the curl command
def get_headers() -> dict:
    config = Config.load()
    return {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "access-control-allow-credentials": "true",
        "access-control-allow-headers": "Accept",
        "access-control-allow-origin": "https://www.wtrl.racing",
        "authorization": "Bearer undefined",
        "cache-control": "no-cache",
        "cookie": f"wtrl_sid={config.wtrl_sid}; wtrl_ouid={config.wtrl_ouid}",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.wtrl.racing/ttt-results/",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "wtrl-api-version": "2.7",
        "wtrl-integrity": config.ctoken,
        "x-requested-with": "XMLHttpRequest",
    }


def scrape_race(
    race_number: int, refresh_cache: bool = False
) -> (Optional[WTRLResult], bool):
    """
    Reads the race data from a local file if it exists; otherwise, fetches it from the API.

    Args:
        race_number (int): The race number to scrape.
        refresh_cache (bool): Force a refresh from the web even if the file exists.

    Returns:
        WTRLResult: Parsed WTRL result object.
        bool: True if data read from cache
    """
    # Directory to save results
    cache_dir = "cache"
    filename = f"race_{race_number}.json"
    os.makedirs(cache_dir, exist_ok=True)
    output_file = os.path.join(cache_dir, filename)

    # Check if the file exists locally
    if not refresh_cache and os.path.exists(output_file):
        print(f"Reading data from local file: {output_file}")
        with open(output_file, "r") as file:
            data = json.load(file)
        return parse_wtrl_result(data), True

    # If not, fetch from the API
    url = url_template.format(season=race_number)
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        print(f"Fetching data from API for race: {race_number}")
        with open(output_file, "w") as file:
            file.write(response.text)
        return parse_wtrl_result(response.json()), False
    else:
        print(
            f"Failed to fetch data for race {race_number}. HTTP Status Code: {response.status_code}"
        )
        return None, False
