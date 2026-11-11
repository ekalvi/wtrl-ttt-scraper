"""Run locally through Chrome, with manual login and no Netlify deployment."""

import os
from pathlib import Path

from selenium import webdriver
from main import load_config, main_scraper_logic
from wtrl_ttt_scraper.browser import BrowserSource


def main():
    os.chdir(Path(__file__).resolve().parent)
    config = load_config()
    driver = webdriver.Chrome()
    try:
        driver.get("https://www.wtrl.racing/ttt-results/")
        print("\nLog into WTRL in the NEW Chrome window.")
        print(
            "Open https://www.wtrl.racing/ttt-results/ and wait until you see results."
        )
        input("Then return here and press Enter (leave Chrome open): ")
        source = BrowserSource(driver)
        main_scraper_logic(config, source=source)
        print("\nLocal HTML generated under results/. Nothing was published.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
