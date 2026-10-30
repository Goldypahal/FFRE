import urllib.request
import json
import os

token = os.getenv("GITHUB_TOKEN", "")
url = "https://api.github.com/repos/Goldypahal/FFRE/actions/runs"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "FFRE-CI-Verifier",
    "Authorization": f"token {token}"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"Total workflow runs found: {data.get('total_count', 0)}")
        for run in data.get("workflow_runs", [])[:10]:
            print(
                f"Run ID: {run.get('id')} | "
                f"Name: {run.get('name')} | "
                f"Event: {run.get('event')} | "
                f"Status: {run.get('status')} | "
                f"Conclusion: {run.get('conclusion')} | "
                f"Commit: {run.get('head_sha', '')[:7]} | "
                f"Branch/Ref: {run.get('head_branch')} | "
                f"URL: {run.get('html_url')}"
            )
except Exception as e:
    print("Error querying GitHub Actions API:", e)
