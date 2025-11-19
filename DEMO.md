# ArgoCD + Argo Rollouts Demo - Complete Setup Guide

## Current Setup Status

### ✅ Infrastructure Deployed:
- **Kubernetes**: OrbStack (v1.32.6+orb1)
- **Istio**: 1.28.0 (demo profile with ingress/egress gateways)
- **ArgoCD**: Latest stable version
- **Argo Rollouts**: Latest stable version
- **Argo CD Image Updater**: v0.12.0

### ✅ Application Deployed:
- **Repository**: https://github.com/fullstackjam/miniproject
- **Images**: ghcr.io/fullstackjam/demo:v1, v2, v3
- **Current Version**: v3 (deployed via GitOps)

## How It Works

### Complete Automation Flow:

```
1. Developer commits code change
   └─> git commit -m "Add new feature"
   └─> git push origin main

2. GitHub Actions CI workflow triggers
   └─> Builds Docker image tagged with commit SHA
   └─> Pushes image to ghcr.io/fullstackjam/demo:<SHA>
   └─> Updates k8s/rollout-v2.yaml with new image tag
   └─> Commits and pushes manifest change back to git

3. ArgoCD detects git change
   └─> Polls repository every 3 minutes (or instant with webhook)
   └─> Sees new commit with updated manifest
   └─> Auto-syncs the change

4. Argo Rollouts performs canary deployment
   └─> Step 1: 10% traffic to new version (pause 30s)
   └─> Step 2: 30% traffic to new version (pause 30s)
   └─> Step 3: 50% traffic to new version (pause 30s)
   └─> Step 4: 100% traffic to new version (promoted!)

5. Istio manages traffic splitting
   └─> VirtualService updated by Argo Rollouts
   └─> Header-based routing: x-beta-user:1 → always canary
   └─> Default routing: weighted split during rollout
```

## Access Points

### ArgoCD UI
```bash
# Port-forward (already running in background)
kubectl port-forward svc/argocd-server -n argocd 8081:443

# Access at: https://localhost:8081
# Username: admin
# Password: xOfJKNihU0FBZ241
```

### Demo Application
```bash
# Port-forward (already running in background)
kubectl port-forward -n demo svc/demo 8080:80

# Test default routing
curl http://localhost:8080/

# Test header-based routing (always gets canary)
curl -H "x-beta-user: 1" http://localhost:8080/
```

## Testing the Complete Workflow

### Test Auto-Deployment:

```bash
# 1. Build new version
docker build -t ghcr.io/fullstackjam/demo:v4 ./app

# 2. Push to GHCR
docker push ghcr.io/fullstackjam/demo:v4

# 3. Wait 2-3 minutes for Image Updater to detect

# 4. Watch the rollout progress
kubectl argo rollouts get rollout demo -n demo --watch

# 5. Monitor traffic split
watch -n 2 'kubectl get virtualservice demo-vs -n demo -o jsonpath="{.spec.http[1].route}" | jq .'

# 6. Test traffic distribution
for i in {1..20}; do curl -s http://localhost:8080/ | jq -r .version; done | sort | uniq -c
```

### Watch Canary Progression:

```bash
# Terminal 1: Watch rollout
kubectl argo rollouts get rollout demo -n demo --watch

# Terminal 2: Watch pods
watch kubectl get pods -n demo

# Terminal 3: Test traffic
while true; do
  echo -n "$(date +%H:%M:%S) - "
  curl -s http://localhost:8080/ | jq -r .version
  sleep 1
done
```

## Key Features Demonstrated

### 1. Header-Based Routing (Beta Users)
Beta users always get the latest version:
```bash
curl -H "x-beta-user: 1" http://localhost:8080/
# Returns: latest canary version
```

### 2. Progressive Canary Deployment
Automatic traffic shift with health checks:
- **10% canary** → Wait 30s
- **30% canary** → Wait 30s
- **50% canary** → Wait 30s
- **100% canary** → Promotion complete!

### 3. GitOps Workflow
All infrastructure as code:
- Manifests in Git
- ArgoCD auto-sync
- Image Updater automation
- Full audit trail

### 4. Zero-Downtime Deployments
- Rolling update of pods
- Traffic gradually shifted
- Old version remains until new version is healthy
- Automatic rollback on failure

## Monitoring Commands

```bash
# Check ArgoCD Application status
kubectl get application demo-app -n argocd

# Check Rollout status
kubectl get rollout demo -n demo

# Check current traffic weights
kubectl get virtualservice demo-vs -n demo -o jsonpath='{.spec.http[1].route}' | jq .

# Check Image Updater logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-image-updater --tail=50 -f

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server --tail=50 -f

# Check Argo Rollouts controller logs
kubectl logs -n argo-rollouts -l app.kubernetes.io/name=argo-rollouts --tail=50 -f
```

## Manual Rollout Control

If you need to manually control the rollout:

```bash
# Promote to next step
kubectl argo rollouts promote demo -n demo

# Abort rollout
kubectl argo rollouts abort demo -n demo

# Restart rollout
kubectl argo rollouts restart demo -n demo

# Set image manually (bypasses Image Updater)
kubectl argo rollouts set image demo demo=ghcr.io/fullstackjam/demo:v5 -n demo
```

## Troubleshooting

### Image Updater Not Working?

```bash
# Check Image Updater is running
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-image-updater

# Check logs for errors
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-image-updater --tail=100

# Verify application annotations
kubectl get application demo-app -n argocd -o yaml | grep -A 10 annotations

# Force image check
kubectl annotate application demo-app \
  -n argocd \
  argocd-image-updater.argoproj.io/image-list=demo=ghcr.io/fullstackjam/demo \
  --overwrite
```

### Rollout Stuck?

```bash
# Check rollout status
kubectl describe rollout demo -n demo

# Check pods
kubectl get pods -n demo

# Check events
kubectl get events -n demo --sort-by='.lastTimestamp'
```

### Traffic Not Switching?

```bash
# Check VirtualService
kubectl get virtualservice demo-vs -n demo -o yaml

# Check DestinationRule
kubectl get destinationrule demo -n demo -o yaml

# Check service endpoints
kubectl get endpoints demo -n demo
kubectl get endpoints demo-canary -n demo
```

## Next Steps

1. **Enable GitHub Packages**: Ensure your repository settings allow Actions to write to packages
2. **Test CI/CD**: Push a change to trigger the workflow
3. **Monitor Rollout**: Watch the automated deployment happen
4. **Try Rollback**: Push an older version to test downgrade

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Workflow                       │
│                                                              │
│  1. docker build + push ────────────────┐                   │
│                                          ▼                   │
│                              ghcr.io/fullstackjam/demo:vX   │
└───────────────────────────────────────────┬─────────────────┘
                                            │
                                            │ (2-3 min polling)
                                            ▼
┌────────────────────────────────────────────────────────────┐
│              Argo CD Image Updater                          │
│  - Detects new image tag                                    │
│  - Updates ArgoCD Application spec                          │
└───────────────────────────────┬────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────┐
│                     ArgoCD                                  │
│  - Syncs from Git                                           │
│  - Applies Rollout manifest                                 │
└───────────────────────────────┬────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────┐
│                  Argo Rollouts                              │
│  - Creates canary pods                                      │
│  - Updates Istio VirtualService weights                     │
│  - Progressive traffic shift: 10% → 30% → 50% → 100%       │
└───────────────────────────────┬────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────┐
│                     Istio                                   │
│  - Routes traffic based on weights                          │
│  - Header-based routing for beta users                      │
│  - Service mesh observability                               │
└────────────────────────────────────────────────────────────┘
```

## Summary

You now have a fully automated GitOps pipeline where:

✅ Developers only push Docker images
✅ No manual YAML edits required
✅ Automatic canary deployments with progressive traffic shift
✅ Header-based routing for beta testing
✅ Zero-downtime deployments
✅ Full observability via ArgoCD UI
✅ Automatic rollback on failures

**Just push an image and watch the magic happen!** 🚀
