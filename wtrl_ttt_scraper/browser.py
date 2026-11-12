"""Optional transport using a fresh, manually authenticated Chrome session.

Cookies and the integrity token stay inside Chrome. No browser profile is reused.
"""

import time

from requests import Response
from . import scrape
from .calculate import latest_race

REQUEST_SCRIPT = r"""
const path = arguments[0], method = arguments[1], body = arguments[2];
const done = arguments[arguments.length - 1];
if (location.origin !== 'https://www.wtrl.racing') {
    done({error: 'Open the WTRL results page in this Chrome window first.'});
    return;
}
const headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01' };
if (method === 'GET') {
    const token = sessionStorage.getItem('ctoken');
    if (!token) {
        done({error: 'No integrity token available. Load the results page first.'});
        return;
    }
    headers['Wtrl-Integrity'] = token;
    headers['Wtrl-Api-Version'] = '2.7';
    headers['X-Requested-With'] = 'XMLHttpRequest';
    headers['Authorization'] = 'Bearer undefined';
} else {
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
    headers['Accept'] = 'text/html';
}
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), 30000);
fetch(path, {
    method, headers, credentials: 'same-origin', cache: 'no-store',
    redirect: 'error', signal: controller.signal,
    ...(body === null ? {} : {body})
}).then(async response => {
    const text = await response.text();
    done({status: response.status, text});
}).catch(() => done({error: 'Browser request failed, redirected, or timed out.'}))
  .finally(() => clearTimeout(timer));
"""


class BrowserSource:
    def __init__(self, driver):
        self.driver = driver
        self.latest = latest_race()
        driver.set_script_timeout(40)

    def request(self, path, method="GET", body=None):
        time.sleep(0.5)
        payload = self.driver.execute_async_script(REQUEST_SCRIPT, path, method, body)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        response = Response()
        response.status_code = payload["status"]
        response.encoding = "utf-8"
        response._content = payload["text"].encode("utf-8")
        # Never print response bodies: a login/error response could contain secrets.
        if response.status_code != 200:
            raise RuntimeError(
                f"WTRL browser request returned HTTP {response.status_code}; stopped. "
                "Check that results still load in the Chrome window."
            )
        return response

    def fetch_result(self, race):
        response = self.request(
            f"/api/wtrlruby/?wtrlid=ttt&season={race}&action=results"
            f"&_={int(time.time() * 1000)}"
        )
        try:
            data = response.json()
        except ValueError:
            raise RuntimeError("WTRL returned non-JSON results; stopped.") from None
        if not isinstance(data, dict) or not data.get("loggedin"):
            raise RuntimeError("WTRL did not confirm the browser session; stopped.")
        return response

    def fetch_event(self, race):
        return self.request("/ttt/TTT-Results-beta.php", "POST", f"wtrlid={race}")

    def is_authenticated(self):
        # A transport/session failure raises rather than triggering cookie extraction.
        # Calendar-based latest race may not have results yet. fetch_result checks
        # loggedin; scrape_result handles success=false as ResultsUnavailableError.
        self.fetch_result(self.latest)
        return True

    def scrape_result(self, race, refresh_cache=False):
        return scrape.scrape_result(
            race,
            refresh_cache=refresh_cache or race == self.latest,
            fetcher=self.fetch_result,
        )

    def scrape_event(self, race, refresh_cache=False):
        return scrape.scrape_event(
            race,
            refresh_cache=refresh_cache or race == self.latest,
            fetcher=self.fetch_event,
        )
