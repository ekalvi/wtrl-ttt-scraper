
# WTRL TTT Scraper

## Project Overview
The **WTRL TTT Scraper** is a Python-based project designed to scrape, process, and visualize time trial results from the WTRL website. It provides detailed data analysis for multiple teams and riders, generates dashboards with sortable tables and charts, and outputs static HTML files.

---

## Features
- Fetches and parses race data from the WTRL website.
- Supports multiple team configurations with aliases.
- Outputs sortable and filterable DataTables with visualizations.
- Generates static HTML files for team dashboards and a central index.
- Files can be hosted on [Netlify](https://www.netlify.com/) or similar static hosting platforms.

---

## Setup and Configuration

### 1. Install Dependencies
- Ensure you have Python 3.8 or higher installed.
- Install required packages using:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Configuration
- A configuration file named `config.secret.json` is required in the project root.
- Start by copying the template:
  ```bash
  cp config.json config.secret.json
  ```
- Fill in the necessary fields in `config.secret.json`:
  ```json
  {
      "club_name": "Waterloo Cycling Club (WCC)",
      "wtrl_sid": "your_sid_here",
      "wtrl_ouid": "your_ouid_here",
      "ctoken": "your_ctoken_here",
      "teams": [
          {
              "team_name": "Waterloo Ones",
              "aliases": ["WCC Butter Tarts"]
          },
          {
              "team_name": "Waterloo Threes",
              "aliases": ["WCC Coureur des Bois"]
          }
      ]
  }
  ```

### 3. Extract Required Tokens
- Use your browser’s **Developer Tools** to extract the required values:
  - **`wtrl_sid`** and **`wtrl_ouid`**: Found under `Application > Cookies > https://www.wtrl.racing`.
  - **`ctoken`**: Found under `Application > Session Storage > https://www.wtrl.racing`.

---

## File Structure
```
WTRL-TTT-Scraper/
├── cache/                   # Contains cached race results in JSON format
├── config.json              # Template configuration file
├── config.secret.json       # User-filled configuration file (not tracked in Git)
├── main.py                  # Main script to scrape and process data
├── models.py                # Data models for teams, riders, and results
├── parse.py                 # Functions for parsing WTRL API responses
├── format.py                # Utility functions for formatting and calculations
├── results/                 # Generated HTML files (team dashboards and index)
└── README.md                # Documentation (this file)
```

---

## Usage

### 1. Run the Scraper
- Execute the main script to scrape data and generate dashboards:
  ```bash
  python main.py
  ```

### 2. Access Results
- Generated HTML files will be saved in the `results/` directory:
  - `index.html`: Central index file with links to all team dashboards.
  - `[team_name].html`: Individual dashboards for each team.

### 3. Publish Results
- Host the `results/` directory on a static hosting service:
  - [Netlify](https://www.netlify.com/): Drag and drop the `results/` folder into Netlify’s interface.
  - [GitHub Pages](https://pages.github.com/): Push the `results/` directory to a GitHub repository and enable GitHub Pages.

---

## Notes
- Make sure your `config.secret.json` file is excluded from version control (via `.gitignore`).
- The `cache/` directory stores race results in JSON format for caching purposes.
- Ensure you keep the extracted tokens (`wtrl_sid`, `wtrl_ouid`, `ctoken`) secure, as they are tied to your account.

---

## Contributing
Feel free to submit issues or pull requests to improve the project. Contributions are welcome!
