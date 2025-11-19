# ArgoCD + Argo Rollouts + Istio Demo

A complete demonstration of header-based traffic routing and weighted canary deployments using Istio, Argo Rollouts, and ArgoCD on Minikube.

## Project Overview

This project demonstrates:
- **Header-based routing**: Route traffic to canary version based on `x-beta-user: 1` header
- **Weighted canary deployments**: Gradual rollout (10% → 30% → 100%) managed by Argo Rollouts
- **Service mesh**: Istio for advanced traffic management
- **GitOps**: ArgoCD for continuous deployment
- **CI/CD**: GitHub Actions for automated image builds

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Istio Gateway                        │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  VirtualService       │
        │  (demo-vs)            │
        └───────────┬───────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│ x-beta-user:1│        │ Default      │
│ → Canary     │        │ → Weighted   │
│   (100%)     │        │   Split      │
└──────┬───────┘        └──────┬───────┘
       │                       │
       │                ┌──────┴──────┐
       │                │             │
       ▼                ▼             ▼
┌──────────────┐  ┌──────────┐  ┌──────────┐
│ demo-canary  │  │   demo   │  │demo-canary│
│ Service (v2) │  │Service(v1)│ │Service(v2)│
└──────────────┘  └──────────┘  └──────────┘
```

## Prerequisites

- Docker Desktop or Docker Engine
- kubectl CLI
- Minikube (or any Kubernetes cluster)
- GitHub account (for CI/CD)

## Installation Guide

### 1. Install Minikube

```bash
# macOS
brew install minikube

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Windows (via Chocolatey)
choco install minikube
```

Start Minikube with sufficient resources:

```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

### 2. Install Istio

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Install Istio with demo profile
istioctl install --set profile=demo -y

# Verify installation
kubectl get pods -n istio-system
```

### 3. Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Access ArgoCD UI (in a new terminal)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Access ArgoCD UI at: https://localhost:8080
- Username: `admin`
- Password: (output from command above)

### 4. Install Argo Rollouts

```bash
# Install Argo Rollouts controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install Argo Rollouts kubectl plugin (optional, for easier management)
# macOS
brew install argoproj/tap/kubectl-argo-rollouts

# Linux
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

## Deployment Instructions

### 1. Build and Push Docker Images

First, authenticate to GitHub Container Registry:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u fullstackjam --password-stdin
```

Build and push v1:

```bash
cd app
docker build -t ghcr.io/fullstackjam/demo:v1 --build-arg VERSION=v1 .
docker push ghcr.io/fullstackjam/demo:v1
```

Build and push v2:

```bash
docker build -t ghcr.io/fullstackjam/demo:v2 --build-arg VERSION=v2 .
docker push ghcr.io/fullstackjam/demo:v2
cd ..
```

### 2. Apply Kubernetes Manifests

Apply all manifests in order:

```bash
# Create namespace with Istio injection enabled
kubectl apply -f k8s/namespace.yaml

# Deploy services
kubectl apply -f k8s/service-stable.yaml
kubectl apply -f k8s/service-canary.yaml

# Deploy Istio traffic management
kubectl apply -f k8s/destinationrule.yaml
kubectl apply -f k8s/virtualservice.yaml

# Deploy stable version (v1)
kubectl apply -f k8s/deployment-stable-v1.yaml

# Wait for v1 to be ready
kubectl wait --for=condition=available --timeout=300s deployment/demo-v1 -n demo

# Deploy canary version (v2) with Argo Rollout
kubectl apply -f k8s/rollout-v2.yaml
```

### 3. Verify Deployment

```bash
# Check all resources in demo namespace
kubectl get all -n demo

# Check Istio VirtualService
kubectl get virtualservice -n demo

# Check Argo Rollout status
kubectl argo rollouts get rollout demo -n demo

# Watch rollout progress (optional)
kubectl argo rollouts get rollout demo -n demo --watch
```

## How It Works

### Header-Based Routing

The Istio VirtualService (`virtualservice.yaml`) defines two routing rules:

1. **Primary route** (header-based):
   - Matches requests with header `x-beta-user: 1`
   - Routes 100% traffic to canary (v2) subset
   - This allows beta users to always access the latest version

2. **Default route** (weighted):
   - Handles all other traffic
   - Uses weights modified by Argo Rollouts for canary deployment
   - Initially routes 100% to stable (v1)

### Weighted Canary Rollout

The Argo Rollout (`rollout-v2.yaml`) defines a progressive canary strategy:

```
Step 1: 10% traffic to canary → pause 10s
Step 2: 30% traffic to canary → pause 10s
Step 3: 100% traffic to canary (promotion complete)
```

Argo Rollouts automatically updates the VirtualService weights during the rollout process.

## Testing

### Get the Service IP/URL

If using Minikube:

```bash
# Get Minikube IP
minikube ip

# Or use port-forward
kubectl port-forward -n demo svc/demo 8080:80
```

Then access via: `http://localhost:8080`

If using Istio Gateway (recommended for production):

```bash
kubectl get svc istio-ingressgateway -n istio-system
```

### Test Header-Based Routing

Test default routing (should return v1):

```bash
curl http://localhost:8080/
# Expected: {"service": "demo", "version": "v1"}
```

Test beta user routing (should return v2):

```bash
curl -H "x-beta-user: 1" http://localhost:8080/
# Expected: {"service": "demo", "version": "v2"}
```

### Test Canary Rollout

To trigger a rollout update:

```bash
# Update the image in rollout-v2.yaml to a new version
kubectl set image rollout/demo demo=ghcr.io/fullstackjam/demo:v2-new -n demo

# Watch the rollout progress
kubectl argo rollouts get rollout demo -n demo --watch
```

You'll see traffic gradually shift from v1 to v2 (10% → 30% → 100%).

### Manual Rollout Control

Promote the rollout manually:

```bash
kubectl argo rollouts promote demo -n demo
```

Abort a rollout:

```bash
kubectl argo rollouts abort demo -n demo
```

Restart a rollout:

```bash
kubectl argo rollouts restart demo -n demo
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yaml`) automatically:

1. Builds Docker image on push to `main` branch
2. Tags with commit SHA
3. Pushes to GitHub Container Registry (ghcr.io)

To enable CI/CD:

1. Ensure GitHub Actions has write access to GHCR (enabled by default for repositories)
2. Push changes to trigger the workflow
3. Manually update the Rollout image reference to trigger a new deployment

## Monitoring

### View Rollout Dashboard

```bash
kubectl argo rollouts dashboard
```

Access at: http://localhost:3100

### Check Istio Traffic

```bash
# View VirtualService details
kubectl describe virtualservice demo-vs -n demo

# Check DestinationRule
kubectl describe destinationrule demo -n demo
```

### View Logs

```bash
# View v1 logs
kubectl logs -l version=v1 -n demo

# View v2 logs
kubectl logs -l version=v2 -n demo
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n demo
kubectl logs <pod-name> -n demo
```

### Istio sidecar not injected

Verify namespace has Istio injection enabled:

```bash
kubectl get namespace demo --show-labels
```

Should show `istio-injection=enabled`.

### Rollout stuck

```bash
# Check rollout status
kubectl argo rollouts get rollout demo -n demo

# Describe rollout for events
kubectl describe rollout demo -n demo

# Check ReplicaSets
kubectl get rs -n demo
```

### Traffic not routing correctly

```bash
# Check VirtualService status
kubectl get virtualservice demo-vs -n demo -o yaml

# Verify services have endpoints
kubectl get endpoints -n demo
```

## Cleanup

```bash
# Delete demo namespace
kubectl delete namespace demo

# Uninstall Argo Rollouts
kubectl delete namespace argo-rollouts

# Uninstall ArgoCD
kubectl delete namespace argocd

# Uninstall Istio
istioctl uninstall --purge -y

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

## Project Structure

```
.
├── CLAUDE.md                      # Project specification
├── README.md                      # This file
├── app/
│   ├── app.py                     # Flask application
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Container image definition
├── k8s/
│   ├── namespace.yaml             # Demo namespace with Istio injection
│   ├── service-stable.yaml        # Service for v1 (stable)
│   ├── service-canary.yaml        # Service for v2 (canary)
│   ├── destinationrule.yaml       # Istio subsets definition
│   ├── virtualservice.yaml        # Traffic routing rules
│   ├── deployment-stable-v1.yaml  # Stable deployment (v1)
│   └── rollout-v2.yaml            # Canary rollout (v2)
└── .github/
    └── workflows/
        └── ci.yaml                # GitHub Actions CI pipeline
```

## Additional Resources

- [Istio Documentation](https://istio.io/latest/docs/)
- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)

## License

MIT License - Feel free to use this demo for learning and development purposes.
