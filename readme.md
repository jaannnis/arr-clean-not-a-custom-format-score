# Arr Custom Format Cleanup

![Docker Build Status](https://github.com/jaannnis/arr-cleanup/actions/workflows/docker-build.yml/badge.svg)

This Docker container automatically cleans up Sonarr and Radarr downloads that have been rejected due to custom format scoring issues. It checks the download queue periodically and removes downloads that contain the message "Not a Custom Format upgrade".

## The Problem

When using custom format scoring in Sonarr and Radarr, sometimes downloads are rejected because they would be a downgrade according to your scoring rules. While Sonarr and Radarr don't import these files, they remain in your download folder until manually deleted.

This container solves that problem by automatically detecting and removing these rejected downloads.

## Docker Image

The image is available on GitHub Container Registry:

```bash
docker pull ghcr.io/jaannnis/arr-cleanup:latest
```

## Setup Instructions

### Quick Start with Docker Compose

1. **Create a docker-compose.yml file:**

```yaml

services:
  arr-cleanup:
    image: ghcr.io/jaannnis/arr-cleanup:latest
    container_name: arr-cleanup
    environment:
      # Sonarr configuration
      - SONARR_URL=http://sonarr:8989
      - SONARR_API_KEY=your_sonarr_api_key
      - SONARR_ENABLED=true
      
      # Radarr configuration
      - RADARR_URL=http://radarr:7878
      - RADARR_API_KEY=your_radarr_api_key
      - RADARR_ENABLED=true
      
      # General settings
      - CHECK_INTERVAL_SECONDS=3600
      - DEBUG=false
    volumes:
      - ./logs:/logs
    restart: unless-stopped
    # If Sonarr and Radarr are in the same Docker network
    networks:
      - arr-network

networks:
  arr-network:
    external: true
```

2. **Start the container:**

```bash
docker-compose up -d
```

### Quick Start with Docker Run

```bash
docker run -d \
  --name arr-cleanup \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_sonarr_api_key \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=your_radarr_api_key \
  -v $(pwd)/logs:/logs \
  --restart unless-stopped \
  --network arr-network \
  ghcr.io/jaannnis/arr-cleanup:latest
```

## Configuration

All configuration is done via environment variables:

### Required Variables
- `SONARR_URL`: URL to your Sonarr instance (e.g., http://sonarr:8989)
- `SONARR_API_KEY`: Your Sonarr API key
- `RADARR_URL`: URL to your Radarr instance (e.g., http://radarr:7878)
- `RADARR_API_KEY`: Your Radarr API key

### Optional Variables
- `SONARR_ENABLED`: Set to "false" to disable Sonarr cleanup (default: true)
- `RADARR_ENABLED`: Set to "false" to disable Radarr cleanup (default: true)
- `CHECK_INTERVAL_SECONDS`: How often to check for rejected downloads (default: 3600 seconds/1 hour)
- `DEBUG`: Set to "true" for more verbose logging (default: false)
- `LOG_FILE`: Path to the log file inside the container (default: /logs/cleanup_script.log)

## Build from Source

If you want to build the image yourself:

```bash
git clone https://github.com/jaannnis/arr-clean-not-a-custom-format-score.git
cd arr-cleanup
docker build -t arr-cleanup .
```

## How It Works

The script:
1. Connects to the Sonarr and Radarr APIs
2. Retrieves all items in the download queue
3. Identifies downloads that are not being imported due to custom format issues
4. Deletes these downloads from the queue and the download client

This helps keep your download folder clean by automatically removing downloads that would otherwise sit there until manually deleted.
