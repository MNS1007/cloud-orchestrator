import subprocess

def debug_gcloud_command():
    metric_name = "signup_count"
    description = "Counts the number of successful user signups"
    log_name = "user_signup_count_cmd"
    match_text = "User registration successful"

    project_id = subprocess.check_output("gcloud config get-value project", shell=True).decode().strip()
    log_filter = f'logName="projects/{project_id}/logs/{log_name}" AND textPayload:"{match_text}"'

    cmd = [
        "gcloud", "logging", "metrics", "create", metric_name,
        f"--description={description}",
        f"--log-filter={log_filter}"
    ]

    print("🔧 Running Command:")
    print(" ".join(cmd))  # This is what gets executed

    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\n📤 STDOUT:\n", result.stdout)
    print("\n❌ STDERR:\n", result.stderr)

debug_gcloud_command()
