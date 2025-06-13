import subprocess

project_id = "cloud-hack-462606"

result = subprocess.run(
    f'gcloud services enable iam.googleapis.com --project {project_id}',
    shell=True,
    capture_output=True,
    text=True
)
print(result)
# print("STDOUT:", result.stdout)
# print("STDERR:", result.stderr)
