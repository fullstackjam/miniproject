# Demo Application

This is the source code repository for the Demo Application.

## Overview

A simple Python Flask application used to demonstrate GitOps workflows with ArgoCD, Argo Rollouts, and Istio.

- **Language**: Python 3.9+
- **Framework**: Flask
- **Container**: Docker

## Development

### Prerequisites

- Python 3.9+
- Docker

### Local Setup

1. Install dependencies:
   ```bash
   cd app
   pip install -r requirements.txt
   ```

2. Run locally:
   ```bash
   python app.py
   ```

### Building Docker Image

```bash
docker build -t demo:local app/
```

## CI/CD

This repository uses GitHub Actions for Continuous Integration:

1. **Build**: Creates a Docker image on every push to `main`.
2. **Push**: Pushes the image to GitHub Container Registry (ghcr.io).
3. **Deploy**: Automatically updates the [miniproject-config](https://github.com/fullstackjam/miniproject-config) repository to trigger a GitOps deployment.

## Deployment

Deployment configuration is managed in the **[miniproject-config](https://github.com/fullstackjam/miniproject-config)** repository.
