import json
from typing import Optional

import requests
import os

from requests import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import CACHE_DIR
from config import Config
from wtrl_ttt_scraper.models import WTRLResult
from wtrl_ttt_scraper.parse import parse_wtrl_result

# Base URL for scraping
url_template = (
    "https://www.wtrl.racing/api/wtrlruby/?wtrlid=ttt&season={season}&action=results"
)


class AuthenticationError(Exception):
    """Raised when there is an authentication error."""

    pass


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


def get_race(race_number: int) -> Response:
    url = url_template.format(season=race_number)
    return requests.get(url, headers=get_headers())


def is_authenticated(response: Response = None) -> bool:
    if not response:
        response = get_race(1)
    data = response.json()
    return (
        response.status_code == 200
        and data.get("loggedin", False)
        and data.get("success", False)
    )


def get_authentication_credentials() -> dict:
    credentials = dict()

    # Initialize the browser driver
    driver = webdriver.Chrome()  # Replace with your browser driver

    # Open the WTRL login page
    driver.get("https://www.wtrl.racing/login/")

    print("Please log in manually...")

    try:
        # Wait for a specific element that appears after login
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, "//a[text()='Logout']"))
        )
        print("Login detected!")

        # Save cookies after manual login
        cookies = driver.get_cookies()  # Get all cookies
        for cookie in cookies:
            if cookie["name"] in ["wtrl_ouid", "wtrl_sid"]:
                credentials[cookie["name"]] = cookie["value"]

        # Execute JavaScript to retrieve the value of ctoken
        ctoken = driver.execute_script("return sessionStorage.getItem('ctoken');")
        if ctoken:
            credentials["ctoken"] = ctoken
        else:
            raise AuthenticationError("ctoken not found in sessionStorage")

    except Exception as e:
        print(f"Error detecting login: {e}")

    finally:
        # Close the browser
        driver.quit()

    return credentials


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
    filename = f"race_{race_number}.json"
    os.makedirs(CACHE_DIR, exist_ok=True)
    output_file = os.path.join(CACHE_DIR, filename)

    # Check if the file exists locally
    if not refresh_cache and os.path.exists(output_file):
        print(f"Reading data from local file: {output_file}")
        with open(output_file, "r") as file:
            data = json.load(file)
        return parse_wtrl_result(data), True

    # If not, fetch from the API
    response = get_race(race_number)
    if is_authenticated(response):
        print(f"Fetching data from API for race: {race_number}")
        with open(output_file, "w") as file:
            file.write(response.text)
        return parse_wtrl_result(response.json()), False
    else:
        raise AuthenticationError(
            f"Failed to fetch data for race {race_number}. HTTP Status Code: {response.status_code}"
        )
