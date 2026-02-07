# Docker Deployment Guide

This project supports Docker deployment, encapsulating both the Frontend (React) and Backend (Python) into a single container.

## Prerequisites

*   Docker Installed
*   Docker Compose Installed

## Directory Structure

*   `Dockerfile`: Builds the image.
*   `docker-compose.yml`: Defines the service and volumes.
*   `docker/`: Contains Nginx and Supervisor configurations.

## Quick Start

1.  **Prepare Configuration**:
    Make sure you have a `config.json` file in the root directory. If not, copy the example:
    ```bash
    cp config.example.json config.json
    ```
    *Edit `config.json` to fill in your WeCom API credentials.*
    *Note: The `monitor_folder` in `config.json` should match the container path `/data/monitor_reports` (or whatever you mount).*

2.  **Prepare Monitor Directory**:
    Create a folder to store the reports/files you want to send.
    ```bash
    mkdir -p monitor_data
    ```

3.  **Build and Run**:
    ```bash
    docker-compose up -d --build
    ```

4.  **Access**:
    Open http://localhost in your browser.

## Configuration Details

### config.json
Since the application runs inside Docker, the `monitor_folder` path in `config.json` MUST be the path **inside the container**.
The default `docker-compose.yml` mounts `./monitor_data` to `/data/monitor_reports`.
So, please update your `config.json`:
```json
{
    "monitor_folder": "/data/monitor_reports",
    ...
}
```

### Volumes
*   `./config.json`: Maps to `/app/config.json`.
*   `./monitor_data`: Maps to `/data/monitor_reports`. Place files here to trigger sending.
*   `./logs`: Maps to `/app/logs`. Check `app.log` here.

## Troubleshooting

*   **Logs**:
    ```bash
    docker-compose logs -f
    ```
*   **Rebuild**:
    If you modified code, rebuild the image:
    ```bash
    docker-compose up -d --build
    ```
