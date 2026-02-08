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
        print(f"Error: {err}")
        return False
    if out:
        print(out)
    return True

def check_docker(ssh):
    print("Checking Docker installation...")
    if not run_command(ssh, "docker --version"):
        print("Installing Docker...")
        run_command(ssh, "curl -fsSL https://get.docker.com | bash")
        run_command(ssh, "systemctl start docker")
        run_command(ssh, "systemctl enable docker")
    print("Docker is ready.")

def configure_docker_mirror(ssh):
    print("Configuring Docker Registry Mirrors...")
    mirror_config = '''{
    "registry-mirrors": [
        "https://registry.docker-cn.com",
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com",
        "https://mirror.ccs.tencentyun.com"
    ]
}'''
    run_command(ssh, f"mkdir -p /etc/docker")
    run_command(ssh, f"echo '{mirror_config}' > /etc/docker/daemon.json")
    run_command(ssh, "systemctl restart docker")
    time.sleep(5)

def check_docker_compose(ssh):
    print("Checking Docker Compose...")
    if run_command(ssh, "docker compose version", ignore_error=True):
        return "docker compose"
    elif run_command(ssh, "docker-compose --version", ignore_error=True):
        return "docker-compose"
    else:
        print("Installing Docker Compose...")
        run_command(ssh, "curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose")
        run_command(ssh, "chmod +x /usr/local/bin/docker-compose")
        return "docker-compose"

def prepare_remote_files(ssh):
    print("Preparing Remote Directory...")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/docker")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/logs")
    run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/monitor_data")

def upload_files(ssh):
    print("Uploading Files...")
    try:
        with SCPClient(ssh.get_transport()) as scp:
            # 上传 docker-compose.yml
            if os.path.exists("docker-compose.yml"):
                scp.put("docker-compose.yml", f"{REMOTE_APP_DIR}/docker-compose.yml")
            
            # 上传 Dockerfile
            if os.path.exists("Dockerfile"):
                scp.put("Dockerfile", f"{REMOTE_APP_DIR}/Dockerfile")
            
            # 上传 nginx 配置
            if os.path.exists("nginx.conf"):
                scp.put("nginx.conf", f"{REMOTE_APP_DIR}/nginx.conf")
            
            # 上传 supervisord 配置
            if os.path.exists("supervisord.conf"):
                scp.put("supervisord.conf", f"{REMOTE_APP_DIR}/supervisord.conf")
            
            # 上传后端代码
            if os.path.exists("backend"):
                run_command(ssh, f"rm -rf {REMOTE_APP_DIR}/backend")
                run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/backend")
                scp.put("backend", f"{REMOTE_APP_DIR}/", recursive=True)
            
            # 上传前端代码
            if os.path.exists("src"):
                run_command(ssh, f"rm -rf {REMOTE_APP_DIR}/src")
                run_command(ssh, f"mkdir -p {REMOTE_APP_DIR}/src")
                scp.put("src", f"{REMOTE_APP_DIR}/", recursive=True)
            
            # 上传 package.json
            if os.path.exists("package.json"):
                scp.put("package.json", f"{REMOTE_APP_DIR}/package.json")
            
            # 上传 requirements.txt
            if os.path.exists("requirements.txt"):
                scp.put("requirements.txt", f"{REMOTE_APP_DIR}/requirements.txt")
                
    except Exception as e:
        print(f"Upload error: {e}")
        return False
    return True

def deploy_containers(ssh, compose_cmd):
    print("Deploying Containers...")
    run_command(ssh, f"cd {REMOTE_APP_DIR} && {compose_cmd} down")
    run_command(ssh, f"cd {REMOTE_APP_DIR} && {compose_cmd} build --no-cache")
    run_command(ssh, f"cd {REMOTE_APP_DIR} && {compose_cmd} up -d")

def check_deployment(ssh):
    print("Checking Deployment Status...")
    run_command(ssh, "docker ps")
    print("\nChecking Service Logs...")
    run_command(ssh, f"cd {REMOTE_APP_DIR} && docker compose logs --tail=20")

def main():
    print(f"Connecting to {HOST}...")
    ssh = create_ssh_client(HOST, 22, USER, PASS)
    
    try:
        check_docker(ssh)
        configure_docker_mirror(ssh)
        compose_cmd = check_docker_compose(ssh)
        prepare_remote_files(ssh)
        
        if upload_files(ssh):
            deploy_containers(ssh, compose_cmd)
            check_deployment(ssh)
            print("\n✅ Deployment completed successfully!")
            print(f"Your application should be accessible at: http://{HOST}:8080")
        else:
            print("\n❌ File upload failed!")
            
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()