import urllib.request
import json
import os

token = os.getenv("GITHUB_TOKEN", "")
run_id = 40358291523
url = f"https://api.github.com/repos/Goldypahal/FFRE/actions/runs/{run_id}/jobs"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "FFRE-CI-Verifier",
    "Authorization": f"token {token}"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"Total jobs: {data.get('total_count', 0)}")
        for job in data.get("jobs", []):
            print(f"\nJob: {job.get('name')} | Status: {job.get('status')} | Conclusion: {job.get('conclusion')}")
            for step in job.get("steps", []):
                print(f"  Step: {step.get('name')} | Status: {step.get('status')} | Conclusion: {step.get('conclusion')}")
except Exception as e:
    print("Error querying job details:", e)
