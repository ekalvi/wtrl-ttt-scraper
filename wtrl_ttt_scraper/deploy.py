"""Explicit, verified Netlify publishing. No raw API bodies or credentials logged."""

import hashlib
import time
from pathlib import Path
from urllib.parse import quote

import requests

API = "https://api.netlify.com/api/v1"


class DeployError(RuntimeError):
    pass


def dashboard_files(directory):
    """Snapshot generated HTML only; fail closed on unexpected output."""
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise DeployError(
            "Missing or symlinked results directory; generate results first."
        )
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise DeployError("Refusing to publish symlinks.")
        if path.is_dir():
            continue
        relative = path.relative_to(root)
        if path.suffix != ".html" or any(p.startswith(".") for p in relative.parts):
            raise DeployError(
                "Unexpected file in results directory; only dashboard HTML is allowed."
            )
        files[relative.as_posix()] = path.read_bytes()
    if not files.get("index.html"):
        raise DeployError("Missing or empty index.html; generate results first.")
    return files


class NetlifyPublisher:
    def __init__(self, token, session=None, poll_attempts=30):
        if not token or token.startswith("your_"):
            raise DeployError("Set a valid netlify_auth_token in config.secret.json.")
        self.session = session or requests.Session()
        self.headers = {"Authorization": f"Bearer {token}"}
        self.poll_attempts = poll_attempts

    def request(self, method, path, **kwargs):
        headers = {**self.headers, **kwargs.pop("headers", {})}
        try:
            response = self.session.request(
                method,
                API + path,
                headers=headers,
                timeout=30,
                allow_redirects=False,
                **kwargs,
            )
        except requests.RequestException:
            raise DeployError(
                f"Netlify {method} request failed or timed out. "
                "No write was retried; inspect Netlify before rerunning."
            ) from None
        if response.status_code not in (200, 201):
            hint = (
                " Check the Netlify token and site access."
                if response.status_code in (401, 403)
                else ""
            )
            raise DeployError(
                f"Netlify {method} returned HTTP {response.status_code}.{hint}"
            )
        # Upload responses need not contain JSON.
        if method == "PUT":
            return None
        try:
            data = response.json()
        except ValueError:
            raise DeployError(
                "Netlify returned invalid JSON; inspect deploy status before retrying."
            ) from None
        if not isinstance(data, dict):
            raise DeployError("Netlify returned an unexpected response.")
        return data

    def site(self, site_id):
        return self.request("GET", f"/sites/{quote(site_id, safe='')}")

    def prepare(self, site_id, files):
        """Upload a draft. It is externally accessible but does not replace production."""
        hashes = {
            name: hashlib.sha1(content).hexdigest() for name, content in files.items()
        }
        deploy = self.request(
            "POST",
            f"/sites/{quote(site_id, safe='')}/deploys",
            json={
                "draft": True,
                "files": {f"/{name}": sha for name, sha in hashes.items()},
            },
        )
        deploy_id = deploy.get("id")
        if not isinstance(deploy_id, str) or not deploy_id:
            raise DeployError("Deploy ID missing; inspect Netlify before retrying.")
        print(f"  Draft deploy: {deploy_id}", flush=True)
        required = deploy.get("required", [])
        if not isinstance(required, list) or any(
            sha not in hashes.values() for sha in required
        ):
            raise DeployError(f"Unexpected upload manifest for deploy {deploy_id}.")
        uploaded = set()
        for name, sha in hashes.items():
            if sha not in required or sha in uploaded:
                continue
            self.request(
                "PUT",
                f"/deploys/{quote(deploy_id, safe='')}/files/{quote(name, safe='/')}",
                data=files[name],
                headers={"Content-Type": "application/octet-stream"},
            )
            uploaded.add(sha)
        for _ in range(self.poll_attempts):
            status = self.request("GET", f"/deploys/{quote(deploy_id, safe='')}")
            if status.get("state") == "ready":
                return deploy_id
            if status.get("state") in ("error", "failed", "canceled"):
                raise DeployError(
                    f"Deploy {deploy_id} failed; production was not changed."
                )
            time.sleep(2)
        raise DeployError(
            f"Deploy {deploy_id} not ready in time; inspect it before retrying."
        )

    def publish(self, site_id, deploy_id):
        # An uncertain restore may have succeeded. Reconcile with a read, never retry it.
        failure = None
        try:
            self.request(
                "POST",
                f"/sites/{quote(site_id, safe='')}/deploys/{quote(deploy_id, safe='')}/restore",
            )
        except DeployError as error:
            failure = error
        for _ in range(self.poll_attempts):
            site = self.site(site_id)
            if (site.get("published_deploy") or {}).get("id") == deploy_id:
                return site.get("ssl_url") or site.get("url") or "(URL unavailable)"
            if failure:
                raise DeployError(
                    f"Publish outcome for deploy {deploy_id} is unconfirmed. {failure}"
                )
            time.sleep(2)
        raise DeployError(
            f"Live deploy {deploy_id} could not be verified; inspect Netlify before rerunning."
        )


def deploy_all_sites(config, publish=False, publisher=None):
    """Preflight all clubs before writes; prepare all drafts before promoting any."""
    if not config.clubs:
        raise DeployError("No clubs configured.")
    ids = [club.site_id for club in config.clubs]
    if any(not site_id or site_id.startswith("your_") for site_id in ids) or len(
        set(ids)
    ) != len(ids):
        raise DeployError("Each club needs a distinct, valid Netlify site_id.")
    snapshots = [
        (club, dashboard_files(club.club_results_dir)) for club in config.clubs
    ]
    publisher = publisher or NetlifyPublisher(config.netlify_auth_token)
    for club, files in snapshots:
        site = publisher.site(club.site_id)
        print(
            f"Preflight: {club.club_name}: {len(files)} files -> {site.get('ssl_url') or site.get('url')}"
        )
    if not publish:
        print(
            "Preflight passed. Nothing uploaded or published. Use --publish to proceed."
        )
        return []

    drafts = []
    published = []
    try:
        for club, files in snapshots:
            print(f"Preparing {club.club_name}", flush=True)
            drafts.append((club, publisher.prepare(club.site_id, files)))
        for club, deploy_id in drafts:
            url = publisher.publish(club.site_id, deploy_id)
            published.append((club.club_name, deploy_id, url))
            print(
                f"Verified live: {club.club_name}: {url} (deploy {deploy_id})",
                flush=True,
            )
    except DeployError:
        print(
            f"Stopped. Verified published sites: {len(published)}/{len(snapshots)}.",
            flush=True,
        )
        for name, deploy_id, url in published:
            print(f"  {name}: {url} (deploy {deploy_id})", flush=True)
        print(
            "Inspect any draft/unconfirmed deployment before rerunning; no automatic retries or rollback."
        )
        raise
    return published
