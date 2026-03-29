# VCC_Assignment-3
# Hybrid Cloud Bursting & Automated Resource Migration

## Objective
To monitor a local VM's CPU usage and automatically "burst" to Google Cloud Platform (GCP) when utilization exceeds **75%**, rerouting traffic via Nginx for seamless service availability.

## Architecture Diagram
```mermaid
graph TD
    User((User)) -->|Port 80| Nginx[Local Nginx Proxy]
    Nginx -->|Default| LocalApp[Local Grafana]
    Monitor[Python Monitor] -->|Polls CPU| LocalVM[Local VM]
    Monitor -->|If >75%| Terraform[Terraform Apply]
    Terraform -->|Provision| GCP_VM[GCP Compute Instance]
    GCP_VM -->|Install| CloudApp[Cloud Grafana]
    GCP_VM -->|Return IP| Monitor
    Monitor -->|Update Config| Nginx
    Nginx -.->|Rerouted| CloudApp
