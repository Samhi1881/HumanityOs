# Production Deployment Guide

This document describes how to deploy HumanityOS to Google Cloud Run (Backend) and Firebase Hosting (Frontend) and automate deliveries with GitHub Actions.

---

## 🐋 1. Local Production Simulation (Docker Compose)

To verify the production configurations locally, run the production docker compose coordinator:
```bash
docker-compose -f docker-compose.prod.yml up --build
```
This builds and executes the backend running under a secure non-root user context and launches the frontend served by an Nginx web proxy.

---

## ☁️ 2. Google Cloud Run Deployment (Backend)

The backend runs as a stateless container on Google Cloud Run.

### Step 1: Create Artifact Registry
Ensure a Docker repository is initialized in your GCP project:
```bash
gcloud artifacts repositories create humanityos \
    --repository-format=docker \
    --location=us-central1 \
    --description="HumanityOS Docker images"
```

### Step 2: Trigger Manual Cloud Build
Submit the build sequence directly to Google Cloud:
```bash
chmod +x scripts/deploy-cloudrun.sh
./scripts/deploy-cloudrun.sh
```
This runs the steps defined in [cloudbuild.yaml](../cloudbuild.yaml), compiling and pushing the image:
`us-central1-docker.pkg.dev/<PROJECT_ID>/humanityos/backend:latest`

### Step 3: Secret Manager Setup
In the Google Cloud Console, add these secrets to **Secret Manager**:
* `DATABASE_URL` (production PostgreSQL connection string)
* `REDIS_URL` (production Redis instance string)
* `GEMINI_API_KEY` (AI Studio authorization key)
* `SECRET_KEY` (JWT sign secret)

Mount these secrets as environment variables inside your Cloud Run service settings.

---

## 🌐 3. Firebase Hosting Deployment (Frontend)

The React SPA is deployed as static assets on Firebase Hosting.

### Step 1: Map Project ID
Ensure the project ID is mapped inside [.firebaserc](../.firebaserc):
```json
{
  "projects": {
    "default": "humanityos-prod"
  }
}
```

### Step 2: Build & Deploy manually
Install Firebase CLI:
```bash
npm install -g firebase-tools
```
Compile the assets and deploy:
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

## 🤖 4. Automated CI/CD (GitHub Actions)

Deployments are automated on pushes to the `main` branch.

### Repository Secrets Required
Add the following secrets under **Settings > Secrets and variables > Actions** in your GitHub repository:

| Secret Name | Value Example | Description |
| :--- | :--- | :--- |
| `GCP_PROJECT_ID` | `humanityos-prod-1234` | Your Google Cloud project ID. |
| `GCP_SA_KEY` | `{"type": "service_account", ...}` | GCP Service Account JSON key (must have Cloud Run Admin and Artifact Registry Writer roles). |
| `FIREBASE_SERVICE_ACCOUNT_HUMANITYOS_PROD` | `{"type": "service_account", ...}` | Firebase Service Account key (to authenticate hosting uploads). |
| `VITE_API_URL` | `https://humanityos-backend-x.run.app/api/v1` | The live URL of the deployed Cloud Run service. |

The workflow defined in [deploy.yml](../.github/workflows/deploy.yml) will trigger, run backend tests, verify frontend typecheck rules, build the Docker image, push it to Artifact Registry, update Cloud Run, and deploy the React bundle to Firebase.
