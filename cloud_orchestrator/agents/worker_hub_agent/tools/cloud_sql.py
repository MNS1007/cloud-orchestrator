from __future__ import annotations
import os, subprocess, time, shlex, socket
from typing import Dict, List, Optional
from google.adk.tools.function_tool import FunctionTool

def _sh(cmd: str | List[str]) -> str:
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)


def _ensure_proxy(instance_connection_name: str, port: int = 5432) -> int:
    """Launch Cloud SQL Auth Proxy on localhost:<port> if not already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return port  
    cmd = [
        "cloud_sql_proxy",
        f"-instances={instance_connection_name}=tcp:{port}",
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2) 
    return port


@FunctionTool
def run_psql_query(
    instance_name: str,
    db_name: str,
    password: str,
    query: str,
    user: str = "postgres",
    project_id: Optional[str] = None,
) -> Dict[str, str]:

    try:
        
        host = _sh(
            f"gcloud sql instances describe {instance_name} --format=value(ipAddresses[0].ipAddress)"
        ).strip()
        if host:
            port = 5432
            ssl_flag = "sslmode=require"
        else:
           
            icn = _sh(
                f"gcloud sql instances describe {instance_name} --format=value(connectionName)"
            ).strip()
            if not icn:
                return {"error": "❌ Could not determine instance connection name."}
            port = _ensure_proxy(icn)
            host = "127.0.0.1"
            ssl_flag = "sslmode=disable"

        # 3) prepare env + escaped query
        env = os.environ.copy(); env["PGPASSWORD"] = password
        safe_query = query.replace("\"", "\\\"")

        result = subprocess.run(
            f"psql -h {host} -p {port} -U {user} -d {db_name} -v {ssl_flag} -c \"{safe_query}\"",
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return {"status": "success", "stdout": result.stdout}
        return {
            "status": "error",
            "stderr": result.stderr,
            "stdout": result.stdout,
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "stderr": e.stderr, "stdout": e.stdout}
    except Exception as ex:
        return {"status": "error", "stderr": str(ex)}
