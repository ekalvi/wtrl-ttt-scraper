import requests
import os

from requests import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from config import CACHE_DIR
from config import Config
from wtrl_ttt_scraper.models import Result, Event
from wtrl_ttt_scraper.parse import parse_wtrl_result, extract_event

# Base URL for scraping
url_template = (
    "https://www.wtrl.racing/api/wtrlruby/?wtrlid=ttt&season={season}&action=results"
)


class AuthenticationError(Exception):
    """Raised when there is an authentication error."""

    pass


# Headers from the curl command
def get_headers() -> dict:
    config = Config.get()
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


def fetch_result(race_number: int) -> Response:
    url = url_template.format(season=race_number)
    return requests.get(url, headers=get_headers())


def is_authenticated(response: Response = None) -> bool:
    if not response:
        response = fetch_result(1)
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
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//a[text()='Logout']")
            )
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


def scrape_result(race_number: int, refresh_cache: bool = False) -> (Result, bool):
    """
    Reads the race data from a local file if it exists; otherwise, fetches it from the API.

    Args:
        race_number (int): The race number to scrape.
        refresh_cache (bool): Force a refresh from the web even if the file exists.

    Returns:
        Result: Parsed WTRL result object.
        bool: True if data read from cache
    """
    # Directory to save results
    filename = f"race_{race_number}.json"
    os.makedirs(CACHE_DIR, exist_ok=True)
    output_file = os.path.join(CACHE_DIR, filename)

    # Check if the file exists locally
    if not refresh_cache and os.path.exists(output_file):
        result = Result.load_from_json(output_file)
        return result, True

    # If not, fetch from the API
    response = fetch_result(race_number)
    if is_authenticated(response):
        result = parse_wtrl_result(response.json())
        Result.save_to_json(result, output_file)
        return result, False

    else:
        raise AuthenticationError(
            f"Failed to fetch data for race {race_number}. HTTP Status Code: {response.status_code}"
        )


def scrape_event(race_number: int, refresh_cache: bool = False) -> (Event, bool):
    config = Config.get()

    # Directory to save the cache
    os.makedirs(CACHE_DIR, exist_ok=True)

    # File path for the cached HTML
    output_file = os.path.join(CACHE_DIR, f"event_{race_number}.json")

    # Check if the file exists locally
    if not refresh_cache and os.path.exists(output_file):
        return Event.load_from_json(output_file), True

    # Base URL and POST data
    url = "https://www.wtrl.racing/ttt/TTT-Results-beta.php"
    data = {"wtrlid": str(race_number)}

    # Headers (replace with actual values as needed)
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": f"wtrl_sid={config.wtrl_sid}; wtrl_ouid={config.wtrl_ouid}",
        "origin": "https://www.wtrl.racing",
        "priority": "u=0, i",
        "referer": "https://www.wtrl.racing/ttt/TTT-Results-beta.php",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Raise exception for HTTP errors
        event = extract_event(response.text)
        Event.save_to_json(event, output_file)
        return event, False

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching race #{race_number}: {e}")
