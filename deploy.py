import paramiko
from scp import SCPClient
import os
import time

# Server Config
HOST = "39.97.181.139"
USER = "root"
PASS = "Azsxdc@098"

# Local Paths
BASE_DIR = os.getcwd()
DIST_DIR = os.path.join(BASE_DIR, "dist")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Remote Paths
REMOTE_ROOT = "/opt/wecom-sender"
REMOTE_FRONTEND = "/var/www/wecom-sender"
REMOTE_MONITOR = "/data/monitor_reports"
PYTHON_DIR = f"{REMOTE_ROOT}/python"
PYTHON_BIN = f"{PYTHON_DIR}/bin/python3"
PIP_BIN = f"{PYTHON_DIR}/bin/pip3"

# Portable Python URL
PYTHON_URL = "https://github.com/indygreg/python-build-standalone/releases/download/20240224/cpython-3.9.18+20240224-x86_64-unknown-linux-gnu-install_only.tar.gz"

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def run_command(ssh, command, ignore_error=False):
    print(f"Running: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if exit_status != 0 and not ignore_error:
        print(f"Error executing command: {command}")
        print(f"STDOUT: {out}")
        print(f"STDERR: {err}")
    
    return exit_status, out

def upload_dir(scp, local_path, remote_path):
    print(f"Uploading directory {local_path} to {remote_path}")
    scp.put(local_path, recursive=True, remote_path=remote_path)

def main():
    print(f"Connecting to {HOST}...")
    ssh = create_ssh_client(HOST, 22, USER, PASS)
    scp = SCPClient(ssh.get_transport())

    print("Preparing remote directories...")
    run_command(ssh, f"mkdir -p {REMOTE_ROOT}")
    run_command(ssh, f"mkdir -p {REMOTE_FRONTEND}")
    run_command(ssh, f"mkdir -p {REMOTE_MONITOR}")

    print("Installing Nginx and dependencies...")
    run_command(ssh, "yum install -y nginx tar gzip || apt-get install -y nginx tar gzip")

    print("Checking/Installing Portable Python 3.9...")
    # Check if python exists
    code, _ = run_command(ssh, f"ls {PYTHON_BIN}", ignore_error=True)
    if code != 0:
        print("Downloading Portable Python...")
        run_command(ssh, f"curl -L {PYTHON_URL} -o /tmp/python.tar.gz")
        print("Extracting Python...")
        run_command(ssh, f"mkdir -p {PYTHON_DIR}")
        # The tarball contains a 'python' directory usually, or installs into .
        # Let's inspect content or just extract.
        # usually it has 'python/bin/...'
        # We strip components if needed.
        # Actually, let's extract to temp and move.
        run_command(ssh, "mkdir -p /tmp/python_extract")
        run_command(ssh, "tar -xzf /tmp/python.tar.gz -C /tmp/python_extract")
        # Move contents of /tmp/python_extract/python to PYTHON_DIR
        run_command(ssh, f"cp -r /tmp/python_extract/python/* {PYTHON_DIR}/")
        run_command(ssh, "rm -rf /tmp/python_extract /tmp/python.tar.gz")
    else:
        print("Portable Python already installed.")

    print(f"Python binary: {PYTHON_BIN}")
    run_command(ssh, f"{PYTHON_BIN} --version")

    print("Uploading Backend...")
    run_command(ssh, f"rm -rf {REMOTE_ROOT}/backend")
    upload_dir(scp, BACKEND_DIR, REMOTE_ROOT)
    
    print("Installing requirements...")
    req_path = f"{REMOTE_ROOT}/backend/requirements.txt"
    run_command(ssh, f"{PIP_BIN} install --upgrade pip")
    # Install dependencies
    code, out = run_command(ssh, f"{PIP_BIN} install -r {req_path}")
    print(out[-500:])

    print("Uploading Frontend...")
    run_command(ssh, f"rm -rf {REMOTE_FRONTEND}/*")
    print("Uploading dist folder...")
    scp.put(DIST_DIR, recursive=True, remote_path="/tmp/dist_temp")
    run_command(ssh, f"cp -r /tmp/dist_temp/* {REMOTE_FRONTEND}/")
    run_command(ssh, f"rm -rf /tmp/dist_temp")

    print("Configuring Config.json...")
    import json
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    config['monitor_folder'] = REMOTE_MONITOR
    with open("config_remote.json", "w") as f:
        json.dump(config, f, indent=4)
    scp.put("config_remote.json", os.path.join(REMOTE_ROOT, "config.json"))
    os.remove("config_remote.json")

    print("Configuring Nginx...")
    nginx_conf = """
server {
    listen 80;
    server_name _;

    location / {
        root /var/www/wecom-sender;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
"""
    with open("nginx_wecom.conf", "w") as f:
        f.write(nginx_conf)
    scp.put("nginx_wecom.conf", "/etc/nginx/conf.d/wecom.conf")
    os.remove("nginx_wecom.conf")
    run_command(ssh, "rm -f /etc/nginx/conf.d/default.conf")
    run_command(ssh, "rm -f /etc/nginx/sites-enabled/default")
    run_command(ssh, "systemctl enable nginx")
    run_command(ssh, "systemctl restart nginx")

    print("Setting up Systemd for Backend...")
    systemd_conf = f"""
[Unit]
Description=WeCom Sender Backend
After=network.target

[Service]
User=root
WorkingDirectory={REMOTE_ROOT}
ExecStart={PYTHON_BIN} -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open("wecom-backend.service", "w") as f:
        f.write(systemd_conf)
    scp.put("wecom-backend.service", "/etc/systemd/system/wecom-backend.service")
    os.remove("wecom-backend.service")
    run_command(ssh, "systemctl daemon-reload")
    run_command(ssh, "systemctl enable wecom-backend")
    run_command(ssh, "systemctl restart wecom-backend")

    print("Deployment Complete!")
    print(f"Visit http://{HOST} to access the system.")

    scp.close()
    ssh.close()

if __name__ == "__main__":
    main()
