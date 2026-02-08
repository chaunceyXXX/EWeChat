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
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Remote Paths
REMOTE_APP_DIR = "/opt/wecom-docker"

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

    print("Checking Docker installation...")
    code, _ = run_command(ssh, "docker --version", ignore_error=True)
    if code != 0:
        print("Installing Docker...")
        run_command(ssh, "yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine")
        run_command(ssh, "yum install -y yum-utils device-mapper-persistent-data lvm2")
        run_command(ssh, "yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo")
        run_command(ssh, "yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
        run_command(ssh, "systemctl start docker")
        run_command(ssh, "systemctl enable docker")
    else:
        print("Docker is already installed.")

    # Configure Docker Mirror (Critical for China)
    print("Configuring Docker Registry Mirrors...")
    daemon_json = """{
      "registry-mirrors": [
        "https://docker.m.daocloud.io",
        "https://mirror.ccs.tencentyun.com",
        "https://registry.docker-cn.com"
      ]
    }"""
    # Write to temp file then upload
    with open("daemon.json", "w") as f:
        f.write(daemon_json)
    
    # Upload to /etc/docker/daemon.json
    run_command(ssh, "mkdir -p /etc/docker")
    scp.put("daemon.json", "/etc/docker/daemon.json")
    os.remove("daemon.json")
    
    # Restart docker to apply mirrors
    run_command(ssh, "systemctl restart docker")

    # Determine compose command
    COMPOSE_CMD = "docker-compose"
    print("Checking Docker Compose...")
    # Check for plugin first (docker compose)
    code, _ = run_command(ssh, "docker compose version", ignore_error=True)
    if code == 0:
        print("Using 'docker compose' (plugin).")
        COMPOSE_CMD = "docker compose"
    else:
        # Check for standalone
        code, _ = run_command(ssh, "docker-compose --version", ignore_error=True)
        if code != 0:
            print("Installing Docker Compose Plugin...")
            run_command(ssh, "yum install -y docker-compose-plugin")
            # Recheck
            code, _ = run_command(ssh, "docker compose version", ignore_error=True)
            if code == 0:
                COMPOSE_CMD = "docker compose"
            else:
                print("Failed to install docker compose plugin. Trying pip...")
                run_command(ssh, "yum install -y python3-pip")
                run_command(ssh, "pip3 install docker-compose")
                COMPOSE_CMD = "docker-compose"
        else:
            COMPOSE_CMD = "docker-compose"

    print(f"Compose command: {COMPOSE_CMD}")

    print("Preparing Remote Directory...")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/docker")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/logs")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/monitor_data")

    print("Uploading Files...")
    scp.put("Dockerfile", f"{REMOTE_APP_DIR}/Dockerfile")
    scp.put("docker-compose.yml", f"{REMOTE_APP_DIR}/docker-compose.yml")
    
    import json
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    config['monitor_folder'] = "/data/monitor_reports"
    with open("config_docker.json", "w") as f:
        json.dump(config, f, indent=4)
    scp.put("config_docker.json", f"{REMOTE_APP_DIR}/config.json")
    os.remove("config_docker.json")

    upload_dir(scp, "docker", f"{REMOTE_APP_DIR}/docker")
    
    print("Compressing project context...")
    # Using python's tarfile to avoid OS differences and quoting issues
    import tarfile
    with tarfile.open("project_context.tar.gz", "w:gz") as tar:
        # Exclude filter
        def filter_func(tarinfo):
            name = tarinfo.name
            if "node_modules" in name or "venv" in name or ".git" in name or "dist" in name or "__pycache__" in name:
                return None
            return tarinfo
        
        # Add current directory
        tar.add(".", arcname=".", filter=filter_func)
    
    print("Uploading project context...")
    scp.put("project_context.tar.gz", f"{REMOTE_APP_DIR}/project_context.tar.gz")
    os.remove("project_context.tar.gz")
    
    print("Extracting on remote...")
    run_command(ssh, f"tar -xzf {REMOTE_APP_DIR}/project_context.tar.gz -C {REMOTE_APP_DIR}")
    run_command(ssh, f"rm -f {REMOTE_APP_DIR}/project_context.tar.gz")

    print("Building and Starting Docker Container...")
    print("Stopping legacy services...")
    run_command(ssh, "systemctl stop wecom-backend || true")
    run_command(ssh, "systemctl stop nginx || true")
    run_command(ssh, "systemctl disable wecom-backend || true")
    run_command(ssh, "systemctl disable nginx || true")
    
    # Run docker compose
    run_command(ssh, f"cd {REMOTE_APP_DIR} && {COMPOSE_CMD} up -d --build")

    print("Deployment Complete!")
    print(f"Visit http://{HOST} to access the system.")

    scp.close()
    ssh.close()

if __name__ == "__main__":
    main()
