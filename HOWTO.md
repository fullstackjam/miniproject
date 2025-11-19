# How to Use GitOps Auto-Deployment

## ✅ System is Ready!

Your complete GitOps pipeline is now configured with:
- **App Repo**: github.com/fullstackjam/miniproject (code only)
- **Config Repo**: github.com/fullstackjam/miniproject-config (manifests only)
- **ArgoCD**: Watching config repo for changes
- **Argo Rollouts**: Progressive canary deployment (10% → 30% → 50% → 100%)
- **Istio**: Traffic management with header-based routing

## 🚀 How to Deploy

### Automatic Deployment (Just Push Code!)

```bash
# 1. Make any code change
cd /Users/fullstackjam/workspace/miniproject/app
echo "# My awesome feature" >> app.py

# 2. Commit and push
git add .
git commit -m "Add awesome feature"
git push origin main

# That's it! The rest is automatic:
# ✅ GitHub Actions builds Docker image (tagged with commit SHA)
# ✅ GitHub Actions pushes to ghcr.io/fullstackjam/demo:<SHA>
# ✅ GitHub Actions updates miniproject-config/base/rollout-v2.yaml
# ✅ GitHub Actions commits to config repo
# ✅ ArgoCD detects config change (polls every 3 min)
# ✅ ArgoCD syncs new manifest
# ✅ Argo Rollouts performs progressive canary deployment
# ✅ Istio manages traffic splitting
```

## 📊 Monitor the Deployment

### Watch GitHub Actions (CI)
```bash
# Open in browser:
open https://github.com/fullstackjam/miniproject/actions
```

### Watch Config Repo Update
```bash
# Open in browser:
open https://github.com/fullstackjam/miniproject-config/commits/main
```

### Watch ArgoCD Sync
```bash
# Terminal
kubectl get application demo-app -n argocd --watch

# Or ArgoCD UI (already running at https://localhost:8081)
# Username: admin
# Password: xOfJKNihU0FBZ241
```

### Watch Canary Rollout Progress
```bash
# Terminal (requires argo-rollouts plugin)
kubectl argo rollouts get rollout demo -n demo --watch

# Or watch pods
watch kubectl get pods -n demo

# Watch traffic weights
watch 'kubectl get virtualservice demo-vs -n demo -o jsonpath="{.spec.http[1].route}" | jq .'
```

### Test Traffic Distribution
```bash
# Start port-forward (if not running)
kubectl port-forward -n demo svc/demo 8080:80 &

# Test during rollout
while true; do
  echo -n "$(date +%H:%M:%S) - "
  curl -s http://localhost:8080/ | jq -r .version
  sleep 1
done

# Test header-based routing (always gets canary)
curl -H "x-beta-user: 1" http://localhost:8080/
```

## 🎯 Beta User Testing

Beta users can test new versions immediately (before full rollout):

```bash
curl -H "x-beta-user: 1" http://demo-service/
# Always returns latest canary version
```

## 🔄 Manual Deployment

If you need to deploy manually (without code change):

```bash
cd /Users/fullstackjam/workspace/miniproject-config

# Update to specific image
sed -i '' 's|image: ghcr.io/fullstackjam/demo:.*|image: ghcr.io/fullstackjam/demo:NEW_SHA|g' base/rollout-v2.yaml

# Commit and push
git add base/rollout-v2.yaml
git commit -m "Deploy NEW_SHA"
git push

# ArgoCD will sync within 3 minutes
```

## ⏪ Rollback

### Quick Rollback (Revert Config)
```bash
cd /Users/fullstackjam/workspace/miniproject-config

# Find previous working commit
git log --oneline base/rollout-v2.yaml

# Revert to previous version
git revert <commit-sha>
git push

# ArgoCD syncs the rollback automatically
```

### Emergency Rollback (Manual)
```bash
# Abort current rollout
kubectl argo rollouts abort demo -n demo

# Rollback to previous revision
kubectl argo rollouts undo demo -n demo
```

## 🔍 Troubleshooting

### CI Not Running?
```bash
# Check workflow file
cat .github/workflows/ci.yaml

# Check GitHub Actions tab
open https://github.com/fullstackjam/miniproject/actions
```

### Config Repo Not Updated?
```bash
# Check if GH_PAT secret is set
# Go to: https://github.com/fullstackjam/miniproject/settings/secrets/actions

# Check CI logs for errors
open https://github.com/fullstackjam/miniproject/actions
```

### ArgoCD Not Syncing?
```bash
# Check application status
kubectl describe application demo-app -n argocd

# Manual sync
kubectl patch application demo-app -n argocd --type merge -p '{"operation":{"sync":{}}}'

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server --tail=50
```

### Rollout Stuck?
```bash
# Check rollout status
kubectl describe rollout demo -n demo

# Check events
kubectl get events -n demo --sort-by='.lastTimestamp' | tail -20

# Promote manually
kubectl argo rollouts promote demo -n demo
```

## 📝 One More Thing: Add GH_PAT Secret

**IMPORTANT**: For CI to update the config repo, you need to add a GitHub Personal Access Token:

### Create Token:
1. Go to: https://github.com/settings/tokens/new
2. Note: `GitHub Actions - miniproject CI`
3. Scope: Check **`repo`**
4. Generate token and copy it

### Add Secret:
1. Go to: https://github.com/fullstackjam/miniproject/settings/secrets/actions
2. Click "New repository secret"
3. Name: `GH_PAT`
4. Value: Paste your token
5. Click "Add secret"

## 🎉 Ready to Test!

Try it now:
```bash
cd /Users/fullstackjam/workspace/miniproject
echo "# Test GitOps" >> README.md
git add README.md
git commit -m "Test automated deployment"
git push

# Then watch the magic happen! 🚀
```

## 📚 More Info

- **Config Repo**: /Users/fullstackjam/workspace/miniproject-config/README.md
- **Setup Docs**: /Users/fullstackjam/workspace/miniproject-config/SETUP.md
- **Demo Guide**: /Users/fullstackjam/workspace/miniproject/DEMO.md
