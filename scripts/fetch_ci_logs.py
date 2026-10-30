import urllib.request
import os
import json

token = os.getenv("GITHUB_TOKEN", "")
run_id = 40358291523

url_jobs = f"https://api.github.com/repos/Goldypahal/FFRE/actions/runs/{run_id}/jobs"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "FFRE-CI-Verifier",
    "Authorization": f"token {token}"
}

class NoAuthRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req and "api.github.com" not in newurl:
            new_req.headers.pop("Authorization", None)
            new_req.headers.pop("authorization", None)
        return new_req

opener = urllib.request.build_opener(NoAuthRedirectHandler())

req = urllib.request.Request(url_jobs, headers=headers)
with opener.open(req) as resp:
    data = json.loads(resp.read().decode())

for job in data.get("jobs", []):
    job_id = job.get("id")
    job_name = job.get("name")
    print(f"\n==================== JOB: {job_name} ({job_id}) ====================")
    log_url = f"https://api.github.com/repos/Goldypahal/FFRE/actions/jobs/{job_id}/logs"
    req_log = urllib.request.Request(log_url, headers=headers)
    try:
        with opener.open(req_log) as resp_log:
            log_text = resp_log.read().decode("utf-8", errors="replace")
            lines = log_text.splitlines()
            print("Total log lines:", len(lines))
            print("--- Last 50 lines of log ---")
            for line in lines[-50:]:
                print(line)
    except Exception as e:
        print(f"Error fetching log for job {job_id}: {e}")
