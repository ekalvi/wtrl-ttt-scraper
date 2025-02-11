import os
import hashlib
import time
import requests
from config import Config, ClubConfig


# Function to calculate SHA-1 hash of a file
def calculate_sha1(file_path: str) -> str:
    """Compute SHA-1 hash of a file."""
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha1()
        while chunk := f.read(8192):
            file_hash.update(chunk)
        return file_hash.hexdigest()


def wait_for_deploy_ready(deploy_id, headers, club_name):
    """Wait for the deploy to be ready before publishing."""
    deploy_status_url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}"

    print(f"⏳ Waiting for deploy {deploy_id} to be ready...")

    for _ in range(20):  # Try for ~20 seconds
        response = requests.get(deploy_status_url, headers=headers)
        if response.status_code == 200:
            deploy_data = response.json()
            if deploy_data.get("state") == "ready":
                print(f"✅ Deploy {deploy_id} for {club_name} is ready!")
                return True
        time.sleep(2)  # Wait and retry

    print(f"❌ Deploy {deploy_id} for {club_name} was not ready in time.")
    return False


def deploy_to_netlify(club: ClubConfig, config: Config):
    """Deploys files from the club's results directory to Netlify using the correct API."""
    output_dir = club.club_results_dir
    print(f"\n🚀 Deploying {club.club_name} to Netlify...")

    # Step 1: Gather files and calculate SHA1 hashes
    files = []

    for root, _, filenames in os.walk(output_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(
                file_path, output_dir
            )  # Ensure relative paths
            files.append(relative_path)

    if not files:
        print(
            f"❌ No files found in {output_dir}. Skipping deployment for {club.club_name}."
        )
        return

    # Step 2: Create deploy request
    deploy_url = f"https://api.netlify.com/api/v1/sites/{club.site_id}/deploys"
    headers = {
        "Authorization": f"Bearer {config.netlify_auth_token}",
        "Content-Type": "application/json",
    }
    deploy_payload = {
        "files": {f"/{file}": calculate_sha1(f"{output_dir}/{file}") for file in files}
    }
    deploy_response = requests.post(deploy_url, json=deploy_payload, headers=headers)

    if deploy_response.status_code not in [200, 201]:
        print(
            f"❌ Failed to create deploy for {club.club_name}. Error: {deploy_response.text}"
        )
        return

    deploy_data = deploy_response.json()
    deploy_id = deploy_data["id"]
    print(f"✅ Deploy ID created for {club.club_name}: {deploy_id}")

    # Step 2: Upload Required Files
    for file in files:
        file_path = f"{output_dir}/{file}"
        with open(file_path, "rb") as f:
            file_buffer = f.read()

        upload_url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/{file}"
        upload_headers = {
            "Authorization": f"Bearer {config.netlify_auth_token}",
            "Content-Type": "application/octet-stream",
        }
        upload_response = requests.put(
            upload_url, data=file_buffer, headers=upload_headers
        )

        if upload_response.status_code == 200:
            print(f"✅ Uploaded {file}")
        else:
            print(f"❌ Failed to upload {file}: {upload_response.status_code}")

    print("🚀 Deployment complete!")

    # Step 5: Publish deploy
    if wait_for_deploy_ready(deploy_id, headers, club.club_name):
        publish_url = f"https://api.netlify.com/api/v1/sites/{club.site_id}/deploys/{deploy_id}/restore"
        publish_response = requests.post(publish_url, headers=headers)

        if publish_response.status_code == 200:
            print(f"🚀 Successfully deployed {club.club_name} to Netlify! 🌍")
        else:
            print(
                f"❌ Failed to publish deploy for {club.club_name}. Error: {publish_response.text}"
            )
    else:
        print(f"⚠️ Skipping publish for {club.club_name} as deploy was not ready.")


def deploy_all_sites(config: Config):
    """Deploys all configured Netlify sites using club-specific directories."""
    print("\n🌍 Deploying all sites to Netlify...")
    for club in config.clubs:
        deploy_to_netlify(club, config)
