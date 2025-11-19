# Claude Project Specification
This repository defines a complete **ArgoCD + Argo Rollouts + Istio** demo project
for header-based traffic switching, built on **Minikube/OrbStack**, with:

- A simple Python demo app (Flask)
- Two versions: v1 (stable) and v2 (canary)
- Istio VirtualService with header-based routing
- Argo Rollout for weighted canary (10% → 30% → 100%)
- GitHub Actions CI to build & push images and update manifests
- Fully reproducible infra for blog/demo purposes

Claude must read this file and generate the entire project structure.

---

# 📁 TARGET PROJECT STRUCTURE

Generate all files exactly as listed:

.
├── claude.md
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│
├── k8s/
│   ├── namespace.yaml
│   ├── service-stable.yaml
│   ├── service-canary.yaml
│   ├── destinationrule.yaml
│   ├── virtualservice.yaml
│   ├── deployment-stable-v1.yaml
│   ├── rollout-v2.yaml
│
├── .github/
│   └── workflows/
│       └── ci.yaml
│
└── README.md

---

# 🐍 Python Service Specification

### File: `app/app.py`

Use EXACTLY this code:

```python
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    version = os.getenv("VERSION", "unknown")
    return jsonify({"service": "demo", "version": version})

@app.route("/healthz")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

File: app/requirements.txt

flask


⸻

🐳 Dockerfile Specification

File: app/Dockerfile

FROM python:3.11-slim
WORKDIR /app
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV VERSION=unknown
EXPOSE 8080
CMD ["python", "app.py"]


⸻

☸ Kubernetes Manifests Specification

File: k8s/namespace.yaml

apiVersion: v1
kind: Namespace
metadata:
  name: demo
  labels:
    istio-injection: enabled


⸻

File: k8s/service-stable.yaml

apiVersion: v1
kind: Service
metadata:
  name: demo
  namespace: demo
spec:
  selector:
    app: demo
    version: v1
  ports:
  - port: 80
    targetPort: 8080

File: k8s/service-canary.yaml

apiVersion: v1
kind: Service
metadata:
  name: demo-canary
  namespace: demo
spec:
  selector:
    app: demo
    version: v2
  ports:
  - port: 80
    targetPort: 8080


⸻

File: k8s/destinationrule.yaml

apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: demo
  namespace: demo
spec:
  host: demo
  subsets:
  - name: stable
    labels:
      version: v1
  - name: canary
    labels:
      version: v2


⸻

File: k8s/virtualservice.yaml

Header-based routing + Argo Rollouts integration.

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: demo-vs
  namespace: demo
spec:
  hosts:
  - demo.demo.svc.cluster.local
  http:
  # ① Header-based routing → 100% canary
  - name: primary
    match:
    - headers:
        x-beta-user:
          exact: "1"
    route:
    - destination:
        host: demo
        subset: canary
      weight: 100

  # ② Default traffic → weights modified by Argo Rollouts
  - name: default
    route:
    - destination:
        host: demo
        subset: stable
      weight: 100


⸻

File: k8s/deployment-stable-v1.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-v1
  namespace: demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo
      version: v1
  template:
    metadata:
      labels:
        app: demo
        version: v1
    spec:
      containers:
      - name: demo
        image: ghcr.io/<your_user>/demo:v1
        env:
        - name: VERSION
          value: "v1"
        ports:
        - containerPort: 8080


⸻

File: k8s/rollout-v2.yaml

apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: demo
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo
  strategy:
    canary:
      canaryService: demo-canary
      stableService: demo
      trafficRouting:
        istio:
          virtualService:
            name: demo-vs
            routes:
            - primary
      steps:
      - setWeight: 10
      - pause: { duration: 10 }
      - setWeight: 30
      - pause: { duration: 10 }
      - setWeight: 100
  template:
    metadata:
      labels:
        app: demo
        version: v2
    spec:
      containers:
      - name: demo
        image: ghcr.io/<your_user>/demo:v2
        env:
        - name: VERSION
          value: "v2"
        ports:
        - containerPort: 8080


⸻

🛠 GitHub Actions CI Spec

File: .github/workflows/ci.yaml

name: CI

on:
  push:
    branches: ["main"]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Login to GHCR
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.repository_owner }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build image
      run: |
        docker build -t ghcr.io/${{ github.repository_owner }}/demo:${{ github.sha }} ./app

    - name: Push image
      run: |
        docker push ghcr.io/${{ github.repository_owner }}/demo:${{ github.sha }}


⸻

📘 README Requirements

Claude must generate:
	•	Minikube/OrbStack installation & Istio install guide
	•	ArgoCD + Argo Rollouts install
	•	How to apply manifests
	•	How header routing works
	•	How weighted rollout works
	•	curl test examples:

curl http://<IP>
curl -H "X-Beta-User: 1" http://<IP>



⸻

FINAL INSTRUCTIONS FOR CLAUDE

Claude must:
	1.	Generate all files listed above.
	2.	Use valid YAML indentation.
	3.	Generate a full README.md with instructions.
	4.	Replace nothing except <your_user> placeholder.
	5.	Output everything as a single multi-file response.
	6.	Do NOT modify architecture.

BEGIN PROJECT GENERATION

END CLAUDE FILE
