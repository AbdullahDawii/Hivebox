# HiveBox

A DevOps end-to-end project built on top of the [HiveBox challenge](https://devopsroadmap.io/projects/hivebox/), extended with observability, GitOps, policy enforcement, and automated incident response.

The app itself is simple on purpose: a Flask API that reads temperature data from [openSenseMap](https://opensensemap.org/), caches it in Redis, and stores snapshots in MinIO. The interesting part is everything around it.

## What's in here

**Application**
- Flask API: `/version`, `/temperature`, `/metrics`, `/store`, `/readyz`
- Redis (Valkey) for caching, MinIO for object storage
- Runs locally via `docker compose`, and on Kubernetes via Helm

**CI/CD**
- Jenkins running on Kubernetes, 5 stages: Lint, Dockerfile Lint, Test, E2E, Build/Push
- Kaniko builds the image and pushes to GitHub Container Registry
- Pylint and Hadolint in the pipeline

**Infrastructure**
- KIND cluster provisioned with Terraform (tehcyx/kind provider)
- Helm chart for the app, Kustomize base plus dev overlay
- Ingress-Nginx with local domains, TLS via Cert-Manager (self-signed)

**Observability and Incident Response**
- kube-prometheus-stack (Prometheus, Grafana, Alertmanager)
- Robusta for alert enrichment and auto-remediation, self-hosted with a Telegram sink
- ai-log-analyzer: a Python service that polls Loki, extracts request/error features, runs Isolation Forest anomaly detection, and exposes the score as a Prometheus metric

**Security and Quality**
- SonarQube for code analysis, Terrascan for Kubernetes manifests
- Kyverno policies (audit mode)
- Dependabot for dependency updates
- OpenSSF Scorecard run locally

## Running it locally

    docker compose up --build
    curl http://localhost:5050/version

## Deploying to Kubernetes

    kind create cluster --name hivebox --config kind-config.yaml
    kubectl apply -f k8s/redis-deployment.yaml
    kubectl apply -f k8s/minio-deployment.yaml
    helm install hivebox-app hivebox-chart

## Configuration

SENSEBOX_IDS (comma-separated) overrides the default senseBoxes:
- 5eba5fbad46fb8001b799786
- 5c21ff8f919bf8001adf2488
- 5ade1acf223bd80019a1011c

Robusta config: copy robusta/values-local.yaml.example, fill in your Telegram bot token and chat ID, then:

    helm install robusta robusta/robusta -f robusta/values-local.yaml -n robusta

## Notes

- Kyverno runs in Audit mode, not Enforce. The existing workloads don't yet meet the policies, and enforcing would block them. Fixing that is on the list.
- Robusta's auto-remediation playbook is deliberately scoped to a single namespace and name prefix. Auto-deleting pods cluster-wide is not something you want on by default.
- The Terrascan and SonarQube findings are tracked in the project board, not all fixed yet.
