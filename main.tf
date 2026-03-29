provider "google" {
  project = "vcc-project-488909" # Ensure this matches your GCP Project ID
  region  = "us-central1"
}

# 1. Create the Cloud VM (The "Burst" Instance)
resource "google_compute_instance" "scaled_vm" {
  name         = "gcp-burst-instance"
  machine_type = "e2-medium"
  zone         = "us-central1-a"
  tags         = ["http-server", "grafana-server"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {
      # This provides a Public IP
    }
  }

  # Startup script to install the full stack on the Cloud VM
  metadata_startup_script = <<-EOT
    #!/bin/bash
    sudo apt update
    # Install Nginx, Prometheus, and Node Exporter
    sudo apt install -y nginx prometheus prometheus-node-exporter wget
    
    # Install Grafana
    wget https://dl.grafana.com/oss/release/grafana_10.0.0_amd64.deb
    sudo apt install -y ./grafana_10.0.0_amd64.deb
    
    # Start and enable all services
    sudo systemctl enable --now grafana-server
    sudo systemctl enable --now prometheus
    sudo systemctl enable --now prometheus-node-exporter
    sudo systemctl restart nginx
  EOT
}

# 2. Firewall Rule to allow Grafana (3000) and Prometheus (9090)
resource "google_compute_firewall" "allow_monitoring" {
  name    = "allow-monitoring-ports"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "3000", "9090"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["grafana-server"]
}

# 3. Output the IP so the Python script can read it
output "gcp_public_ip" {
  value = google_compute_instance.scaled_vm.network_interface.0.access_config.0.nat_ip
}
