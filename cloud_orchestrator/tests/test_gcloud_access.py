import subprocess, json, os

def test_gcloud_access():
    
    token = subprocess.check_output(
        ["gcloud","auth","print-access-token"], text=True).strip()
    assert token and len(token) > 100

    out = subprocess.check_output(
        ["gcloud","projects","list","--format=json"], text=True)
    projects = json.loads(out)
    print(projects)
    assert isinstance(projects, list)