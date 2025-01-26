
# WTRL TTT Scraper

## Project Overview
The **WTRL TTT Scraper** is a Python-based project designed to scrape, process, and visualize time trial results from the WTRL website. It provides detailed data analysis for multiple teams and riders, generates dashboards with sortable tables and charts, and outputs static HTML files.

The results are found here (requires a WTRL account): https://www.wtrl.racing/ttt-results/ 

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
  - **`ctoken`**: Found under `Application > Session Storage > https://www.wtrl.racing`. This will need to be refreshed after being signed out.

---

## File Structure
```
WTRL-TTT-Scraper/
├── cache/                   # Contains cached race results in JSON format
├── results/                 # Contains generated HTML files for dashboards and index
├── wtrl/                    # Core package for the scraper
│   ├── __init__.py          # Package init
│   ├── scrape.py            # Scraping logic
│   ├── render.py            # HTML rendering
│   ├── models.py            # Data models
│   ├── format.py            # Formatting utilities
│   ├── parse.py             # Parsing utilities
│   ├── calculate.py         # Calculations (e.g., percentiles)
├── main.py                  # Entry point for the scraper
├── config.py            # Configuration logic
├── requirements.txt         # Python dependencies
├── README.md                # Documentation
├── LICENSE.md               # License file
└── scripts.sh               # Utility scripts for automation
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
  
### 4. Format COde
- Ensure Python code is formatted using [Black](https://black.readthedocs.io/en/latest/)
  ```bash
  black .
  ```

---

## Notes
- Make sure your `config.secret.json` file is excluded from version control (via `.gitignore`).
- The `cache/` directory stores race results in JSON format for caching purposes.
- Ensure you keep the extracted tokens (`wtrl_sid`, `wtrl_ouid`, `ctoken`) secure, as they are tied to your account.

---

## Contributing
Feel free to submit issues or pull requests to improve the project. Contributions are welcome!
