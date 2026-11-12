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
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
  ```

### **2. Configuration**
- A configuration file named `config.secret.json` is required in the project root.
- Start by copying the template:
  ```bash
  (umask 077; cp -n config.json config.secret.json)
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
- Recommended: run `.venv/bin/python run_browser.py` to keep authentication inside Chrome (see below). No manual token extraction is needed.
- The legacy `main.py` transport will open a browser for you to log in to WTRL.
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
├── wtrl_ttt_scraper/        # Core package for the scraper
│   ├── __init__.py          # Package init
│   ├── calculate.py         # Percentile calculations
│   ├── deploy.py            # Automates deployment to Netlify
│   ├── format.py            # Formatting utilities
│   ├── models.py            # Data models
│   ├── parse.py             # Parsing utilities
│   ├── render.py            # HTML rendering
│   ├── scrape.py            # Scraping logic
├── .gitignore               # Ignore sensitive files
├── config.json              # Default configuration
├── config.secret.json       # User-specific configuration (ignored in Git)
├── LICENSE.md               # License file
├── main.py                  # Entry point for scraping
├── README.md                # Documentation
├── requirements.txt         # Python dependencies
└── scripts.sh               # Utility scripts for automation
```

---

## **Usage**

### Happy path: refresh and publish

```bash
.venv/bin/python publish.py
```

This checks Netlify access first, opens Chrome for you to log into WTRL, refreshes
results, then publishes **all configured clubs**. Once the results page has loaded
in the new Chrome window, press Enter in the terminal. No additional publish flag
or second command is needed. Missing results for the newest race are skipped;
completed historical results still generate dashboards.

For a local-only refresh, use `.venv/bin/python run_browser.py` instead.

### **1. Run the Scraper**
- Execute the main script to scrape data and generate results:
  ```bash
  python main.py
  ```
- The script will automatically:
  - Load **`config.secret.json`** (required; credentials are never written into the tracked template).
  - Authenticate with WTRL.
  - Scrape **all configured clubs and teams**.
  - Save results in **`results/[club_name]/`**.

### Browser-based local run (alternative to copied session cookies)

If results work in Chrome but Python requests fail, run from the project root:

```bash
.venv/bin/python run_browser.py
```

This uses the existing Selenium dependency and requires Chrome. Log in manually
in the new Chrome window, open the TTT results page, and press Enter in the
terminal only once results are visible. Leave Chrome open during scraping.
Cookies and the integrity token stay inside that temporary browser session;
they are not copied to Python or saved by this runner. Existing team configuration
is still loaded. The runner refreshes the latest race and uses historical caches.
It generates local HTML only and **never calls Netlify deployment**.

This is an alternative transport, not a guarantee that WTRL's current response
format still matches the parsers. HTTP, session, or parsing failures stop or are
reported; no challenge or access restriction is bypassed automatically.

Synthetic tests (no login or network):

```bash
.venv/bin/python -m unittest discover -s tests -v
```

### **2. Access Results**
- Generated HTML files will be saved in the **`results/` directory**, structured per club:
  - **`results/[club_name]/index.html`** → Central index for the club.
  - **`results/[club_name]/[team_name].html`** → Individual dashboards.

### **3. Publish Results**

Scraping is local-only: neither `main.py` nor `run_browser.py` publishes anything.
The publish command refreshes and publishes **all configured Netlify sites**:

```bash
# Happy path: check access, refresh via Chrome, then publish.
.venv/bin/python publish.py

# Optional: read-only preflight of existing output; no browser or uploads.
.venv/bin/python publish.py --check

# Optional: publish already-generated results without refreshing.
.venv/bin/python publish.py --existing
```

The previous `--publish` flag remains an alias for `--existing`.

Set `netlify_auth_token` and each club's `site_id` in the ignored
`config.secret.json`. HTTP 401/403 means the token or site access needs attention;
do not paste credentials into logs, issues, or chat.

Publishing snapshots only HTML files under each club's results directory and
rejects unexpected files, symlinks, duplicate site IDs, and a missing index.
It preflights **every site before any upload**, uploads draft deploys using only
Netlify's required hashes, waits for **all drafts** to be ready, then promotes
each and verifies the site's live deploy ID. Draft URLs are externally accessible;
running `publish.py` (unless `--check` is used) uploads them and replaces production.

Cross-site publication is not atomic. If a later promotion fails, already-published
sites are reported and remain live. HTTP calls have timeouts, writes are never
automatically retried, and uncertain promotion outcomes are checked with a read.
If a run stops, inspect the printed deploy IDs in Netlify before rerunning to
avoid duplicate uploads. A rerun creates new drafts; it is not a resume command.

A failed or interrupted refresh does not proceed to publishing. Unavailable races
are skipped and reported, so published history may omit races with no results yet.
To review locally first, run `run_browser.py`, inspect the dashboards, then use
`publish.py --existing`. Existing historical cache files
remain tracked for compatibility, but new cache data, `.venv/`, results, and
secret configuration are ignored and should never be force-added.

API workflow: [Netlify deployment documentation](https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/#deploy-with-the-api).
  
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
