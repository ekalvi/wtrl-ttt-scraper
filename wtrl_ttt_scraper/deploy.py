import os
import requests
import json

# Configurations
NETLIFY_AUTH_TOKEN = "your_netlify_auth_token"  # Replace with your token
SITE_IDS = {
    "wcc": "your_wcc_site_id",  # Replace with actual site ID
    "sisu": "your_sisu_site_id",  # Replace with actual site ID
}

# Directory containing static files
OUTPUT_DIR = "output"


def deploy_to_netlify(site_name, site_id):
    """Deploys files from OUTPUT_DIR to the given Netlify site."""
    headers = {
        "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    # Step 1: Create a new deploy request
    deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    deploy_response = requests.post(deploy_url, headers=headers)

    if deploy_response.status_code != 201:
        print(
            f"❌ Failed to create deploy for {site_name}. Error: {deploy_response.text}"
        )
        return

    deploy_id = deploy_response.json()["id"]
    print(f"✅ Deploy ID created for {site_name}: {deploy_id}")

    # Step 2: Upload files
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.relpath(file_path, OUTPUT_DIR)

            with open(file_path, "rb") as f:
                file_data = f.read()

            upload_url = (
                f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/{file_name}"
            )
            upload_headers = {
                "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
                "Content-Type": "application/octet-stream",
            }
            response = requests.put(upload_url, headers=upload_headers, data=file_data)

            if response.status_code == 200:
                print(f"✅ Uploaded {file_name} to {site_name}")
            else:
                print(
                    f"❌ Failed to upload {file_name} to {site_name}. Error: {response.text}"
                )

    # Step 3: Publish deploy
    publish_url = (
        f"https://api.netlify.com/api/v1/sites/{site_id}/deploys/{deploy_id}/restore"
    )
    publish_response = requests.post(publish_url, headers=headers)

    if publish_response.status_code == 200:
        print(f"🚀 Successfully deployed to {site_name} ({SITE_IDS[site_name]})")
    else:
        print(
            f"❌ Failed to publish deploy for {site_name}. Error: {publish_response.text}"
        )


# Deploy to both Netlify sites
for site in SITE_IDS.keys():
    deploy_to_netlify(site, SITE_IDS[site])
