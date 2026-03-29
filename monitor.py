import psutil
import os
import time
import subprocess
import requests

# Configuration
THRESHOLD = 75.0  # Trigger at 75% CPU
CHECK_INTERVAL = 5 # Seconds between checks
LOCAL_NGINX_CONF = "/etc/nginx/sites-available/default"

def wait_for_cloud_ready(ip):
    """Wait until the Cloud Grafana is accessible."""
    print(f"Waiting for Cloud Grafana to start at http://{ip}:3000...")
    url = f"http://{ip}:3000"
    for i in range(20): # Try for ~3 minutes
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("Cloud Grafana is ONLINE.")
                return True
        except:
            print(f"Attempt {i+1}: Cloud still booting...")
        time.sleep(10)
    return False

def reroute_nginx(cloud_ip):
    """Update local Nginx to point to the Cloud VM."""
    print(f"Rerouting local traffic to GCP IP: {cloud_ip}")
    
    new_config = f"""
server {{
    listen 80;
    location / {{
        proxy_pass http://{cloud_ip}:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""
    # Write to a temp file then move to bypass permission issues in Python
    with open("/tmp/nginx_new", "w") as f:
        f.write(new_config)
    
    os.system("sudo mv /tmp/nginx_new " + LOCAL_NGINX_CONF)
    os.system("sudo systemctl restart nginx")
    print("SUCCESS: Traffic migrated. Access via http://192.168.1.8/")

def trigger_cloud_burst():
    print("\n[ALERT] CPU Threshold Exceeded! Initiating Cloud Burst...")
    
    # 1. Run Terraform
    print("Step 1: Provisioning GCP Resources via Terraform...")
    os.system("terraform apply -auto-approve")
    
    # 2. Get the new IP
    try:
        cloud_ip = subprocess.check_output(["terraform", "output", "-raw", "gcp_public_ip"]).decode("utf-8").strip()
        print(f"Step 2: GCP VM Created at {cloud_ip}")
        
        # 3. Wait for app readiness and reroute
        if wait_for_cloud_ready(cloud_ip):
            reroute_nginx(cloud_ip)
            print("Step 3: Migration Complete.")
    except Exception as e:
        print(f"Error during migration: {e}")

# Main Loop
print(f"Senior Architect Monitor Active (Threshold: {THRESHOLD}%)")
try:
    while True:
        cpu = psutil.cpu_percent(interval=1)
        print(f"Current Local CPU: {cpu}%")
        
        if cpu >= THRESHOLD:
            trigger_cloud_burst()
            break # Exit after successful burst
        time.sleep(CHECK_INTERVAL)
except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")
