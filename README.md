# WTRL TTT Scraper

## Project Overview
The **WTRL TTT Scraper** is a Python-based project designed to scrape, process, and visualize time trial results from the WTRL website. It provides detailed data analysis for multiple teams and riders, generates dashboards with sortable tables and charts, and outputs static HTML files.

The results are found here (requires a WTRL account):  
🔗 [WTRL TTT Results](https://www.wtrl.racing/ttt-results/)

---

## Features
- Fetches and parses race data from the WTRL website.
- Supports **multiple clubs** with multiple teams and aliases.
- Outputs sortable and filterable DataTables with visualizations.
- Generates **static HTML dashboards** for each team and an index for each club.
- Files can be hosted on [Netlify](https://www.netlify.com/) or similar static hosting platforms.

---

## Setup and Configuration

### **1. Install Dependencies**
- Ensure you have **Python 3.8 or higher** installed.
- Install required packages using:
  ```bash
  pip install -r requirements.txt
  ```

### **2. Configuration**
- A configuration file named `config.secret.json` is required in the project root.
- Start by copying the template:
  ```bash
  cp config.json config.secret.json
  ```
- **Configuration Format** (`config.secret.json`):
  ```json
  {
    "netlify_auth_token": "your_global_netlify_auth_token",
    "wtrl_sid": "your_wtrl_sid",
    "wtrl_ouid": "your_wtrl_ouid",
    "ctoken": "your_ctoken",
    "clubs": [
      {
        "club_name": "Waterloo Cycling Club",
        "site_id": "your_wcc_site_id",
        "teams": [
          {
            "team_name": "Waterloo Ones",
            "aliases": ["WCC Butter Tarts"]
          },
          {
            "team_name": "Waterloo Twos",
            "aliases": ["WCC Canucks"]
          }
        ]
      },
      {
        "club_name": "SISU Racing",
        "site_id": "your_sisu_site_id",
        "teams": [
          {
            "team_name": "SISU Racing Grit",
            "aliases": []
          },
          {
            "team_name": "SISU Racing Mokki",
            "aliases": []
          }
        ]
      }
    ]
  }
  ```

---

### **3. Extract Required Tokens**
- Running `main.py` will open a browser for you to log in to WTRL.  
  The tokens will automatically be extracted and inserted into `config.secret.json`.  
- **[Optional] Manually extract tokens using Developer Tools:**
  - **`wtrl_sid`** and **`wtrl_ouid`**: Found under `Application > Cookies > https://www.wtrl.racing`.
  - **`ctoken`**: Found under `Application > Session Storage > https://www.wtrl.racing` (refresh after logout).

---

## File Structure
```
WTRL-TTT-Scraper/
├── cache/                   # Cached race results in JSON format
├── results/                 # Generated HTML files for clubs and teams
│   ├── waterloo-cycling-club/  # Results for Waterloo Cycling Club
│   │   ├── index.html         # Index for all WCC teams
│   │   ├── waterloo-ones.html # Results for Waterloo Ones
│   │   ├── waterloo-twos.html # Results for Waterloo Twos
│   ├── sisu-racing/           # Results for SISU Racing
│   │   ├── index.html         # Index for SISU teams
│   │   ├── sisu-racing-grit.html  # Results for SISU Racing Grit
│   │   ├── sisu-racing-mokki.html # Results for SISU Racing Mokki
├── wtrl/                    # Core package for the scraper
│   ├── __init__.py          # Package init
│   ├── scrape.py            # Scraping logic
│   ├── render.py            # HTML rendering
│   ├── models.py            # Data models
│   ├── format.py            # Formatting utilities
│   ├── parse.py             # Parsing utilities
│   ├── calculate.py         # Calculations (e.g., percentiles)
├── main.py                  # Entry point for the scraper
├── config.py                 # Configuration logic
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── LICENSE.md                # License file
└── scripts.sh                # Utility scripts for automation
```

---

## **Usage**

### **1. Run the Scraper**
- Execute the main script to scrape data and generate results:
  ```bash
  python main.py
  ```
- The script will automatically:
  - Load **`config.secret.json`** (or fallback to `config.json`).
  - Authenticate with WTRL.
  - Scrape **all configured clubs and teams**.
  - Save results in **`results/[club_name]/`**.

### **2. Access Results**
- Generated HTML files will be saved in the **`results/` directory**, structured per club:
  - **`results/[club_name]/index.html`** → Central index for the club.
  - **`results/[club_name]/[team_name].html`** → Individual dashboards.

### **3. Publish Results**
- Host the `results/` directory on a **static hosting service**:
  - **[Netlify](https://www.netlify.com/)** → Drag and drop `results/` into Netlify’s UI.
  - **[GitHub Pages](https://pages.github.com/)** → Push `results/` to GitHub and enable Pages.
  
### **4. Format Code**
- Ensure Python code is formatted using **[Black](https://black.readthedocs.io/en/latest/)**
  ```bash
  black .
  ```

---

## **Notes**
- Make sure your **`config.secret.json`** file is excluded from version control (`.gitignore`).
- The **`cache/` directory** stores JSON-formatted race results for caching.
- Keep your **extracted tokens (`wtrl_sid`, `wtrl_ouid`, `ctoken`) secure**, as they are tied to your account.

---

## **Contributing**
Feel free to **submit issues or pull requests** to improve the project. Contributions are always welcome! 🚀
