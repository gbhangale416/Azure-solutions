import requests
import base64
from datetime import datetime, timedelta
from dateutil import parser

# ---------------- CONFIG ----------------
ORG = "your-org"
PROJECT = "your-project"
REPO = "your-repo"
BRANCH = "refs/heads/main"

SOURCE_PATH = "/source/path"
ARCHIVE_PATH = "/archive/path"

PAT = "YOUR_PAT_TOKEN"
MONTHS_OLD = 6
# ----------------------------------------

BASE_URL = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/git/repositories/{REPO}"
AUTH_HEADER = {
    "Authorization": "Basic " + base64.b64encode(f":{PAT}".encode()).decode()
}

cutoff_date = datetime.utcnow() - timedelta(days=MONTHS_OLD * 30)


def get_items():
    url = f"{BASE_URL}/items"
    params = {
        "scopePath": SOURCE_PATH,
        "recursionLevel": "Full",
        "includeContentMetadata": True,
        "versionDescriptor.version": BRANCH.replace("refs/heads/", ""),
        "api-version": "7.0"
    }
    r = requests.get(url, headers=AUTH_HEADER, params=params)
    r.raise_for_status()
    return r.json()["value"]


def get_last_commit_date(path):
    url = f"{BASE_URL}/commits"
    params = {
        "searchCriteria.itemPath": path,
        "searchCriteria.$top": 1,
        "api-version": "7.0"
    }
    r = requests.get(url, headers=AUTH_HEADER, params=params)
    r.raise_for_status()
    commits = r.json()["value"]
    if not commits:
        return None
    return parser.parse(commits[0]["author"]["date"])


def get_latest_commit():
    url = f"{BASE_URL}/refs"
    params = {"filter": BRANCH, "api-version": "7.0"}
    r = requests.get(url, headers=AUTH_HEADER, params=params)
    r.raise_for_status()
    return r.json()["value"][0]["objectId"]


def create_push(changes):
    url = f"{BASE_URL}/pushes?api-version=7.0"
    payload = {
        "refUpdates": [{
            "name": BRANCH,
            "oldObjectId": get_latest_commit()
        }],
        "commits": [{
            "comment": "Archive files older than 6 months",
            "changes": changes
        }]
    }
    r = requests.post(url, headers={**AUTH_HEADER, "Content-Type": "application/json"}, json=payload)
    r.raise_for_status()


def main():
    items = get_items()
    changes = []

    for item in items:
        if item["isFolder"]:
            continue

        path = item["path"]
        last_commit_date = get_last_commit_date(path)

        if last_commit_date and last_commit_date < cutoff_date:
            new_path = path.replace(SOURCE_PATH, ARCHIVE_PATH, 1)

            changes.append({
                "changeType": "rename",
                "item": {"path": path},
                "newContent": None,
                "sourceServerItem": path,
                "destinationServerItem": new_path
            })

            print(f"Archiving: {path} → {new_path}")

    if changes:
        create_push(changes)
        print("Archival commit completed.")
    else:
        print("No files eligible for archival.")


if __name__ == "__main__":
    main()
