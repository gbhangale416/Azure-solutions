import requests
import base64
import json
from datetime import datetime, timedelta, timezone
from dateutil import parser

# ================= CONFIGURATION =================

ORG = "your-org"
PROJECT = "your-project"
REPO = "your-repo"
BRANCH = "refs/heads/main"

PAT = "YOUR_PAT_TOKEN"

BASE_PATH = "/database/snow/Test_A"
SOURCE_PATH = "/database/snow/Test_A/object/Tables/Stage"
ARCHIVE_BASE_PATH = "/database/snow/Test_A/archive"

DAYS = 10  # last 10 days only
API_VERSION = "7.0"

# =================================================

BASE_URL = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git/repositories/{REPO}"

AUTH_HEADER = {
    "Authorization": "Basic " + base64.b64encode(f":{PAT}".encode()).decode(),
    "Content-Type": "application/json"
}

cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS)


# -------------------------------------------------
# Get all items under SOURCE_PATH
# -------------------------------------------------
def get_items():
    url = f"{BASE_URL}/items"
    params = {
        "scopePath": SOURCE_PATH,
        "recursionLevel": "Full",
        "includeContentMetadata": True,
        "versionDescriptor.version": BRANCH.replace("refs/heads/", ""),
        "api-version": API_VERSION
    }

    r = requests.get(url, headers=AUTH_HEADER, params=params)
    r.raise_for_status()

    response = r.json()

    # Save raw response for debugging
    with open("ado_items_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2)

    return response["value"]


# -------------------------------------------------
# Get last commit date for a file
# -------------------------------------------------
def get_last_commit_date(file_path):
    url = f"{BASE_URL}/commits"
    params = {
        "searchCriteria.itemPath": file_path,
        "searchCriteria.$top": 1,
        "api-version": API_VERSION
    }

    r = requests.get(url, headers=AUTH_HEADER, params=params)
    r.raise_for_status()

    commits = r.json()["value"]
    if not commits:
        return None

    dt = parser.parse(commits[0]["author"]["date"])
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# -------------------------------------------------
# Get latest commit ID of branch
# -------------------------------------------------
def get_latest_commit_id():
    url = f"{BASE_URL}/refs"
    params = {
        "filter": BRANCH,
        "api-version": API_VERSION
    }

    r = requests.get(url, headers=AUTH_HEADER, params=params)
    r.raise_for_status()

    return r.json()["value"][0]["objectId"]


# -------------------------------------------------
# Build archive path (preserve structure)
# -------------------------------------------------
def build_archive_path(file_path):
    if not file_path.startswith(BASE_PATH + "/"):
        raise ValueError(f"Path not under BASE_PATH: {file_path}")

    relative_path = file_path[len(BASE_PATH):]
    return f"{ARCHIVE_BASE_PATH}{relative_path}"


# -------------------------------------------------
# Create Git push (single commit)
# -------------------------------------------------
def create_push(changes):
    url = f"{BASE_URL}/pushes?api-version={API_VERSION}"

    payload = {
        "refUpdates": [{
            "name": BRANCH,
            "oldObjectId": get_latest_commit_id()
        }],
        "commits": [{
            "comment": f"Archive SQL files modified in last {DAYS} days",
            "changes": changes
        }]
    }

    r = requests.post(url, headers=AUTH_HEADER, json=payload)
    r.raise_for_status()


# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    items = get_items()
    changes = []

    for item in items:
        # Only files
        if item.get("gitObjectType") != "blob":
            continue

        path = item["path"]

        # Only SQL files
        if not path.lower().endswith(".sql"):
            continue

        # Only from SOURCE_PATH
        if not path.startswith(SOURCE_PATH + "/"):
            continue

        # Avoid re-archiving
        if path.startswith(ARCHIVE_BASE_PATH + "/"):
            continue

        last_commit_date = get_last_commit_date(path)

        if last_commit_date and last_commit_date >= cutoff_date:
            new_path = build_archive_path(path)

            changes.append({
                "changeType": "rename",
                "item": {"path": path},
                "sourceServerItem": path,
                "destinationServerItem": new_path
            })

            print(f"Moving: {path} → {new_path}")

    if not changes:
        print("No SQL files found in last 10 days.")
        return

    create_push(changes)
    print(f"Archived {len(changes)} SQL file(s) successfully.")


if __name__ == "__main__":
    main()
