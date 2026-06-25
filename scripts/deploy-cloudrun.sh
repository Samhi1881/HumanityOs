#!/bin/bash
# humanityos manual deployment script
set -e

# Configuration
GCP_PROJECT_ID=$(gcloud config get-value project)
echo "--------------------------------------------------------"
echo "Deploying HumanityOS to Google Cloud Run & Firebase"
echo "Active GCP Project ID: $GCP_PROJECT_ID"
echo "--------------------------------------------------------"

# Ensure Artifact Registry repository exists
echo "Verifying Artifact Registry repository..."
gcloud artifacts repositories create humanityos \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for HumanityOS" \
    || echo "Repository already exists or could not be created."

# Trigger Google Cloud Build
echo "Submitting build to Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

echo "--------------------------------------------------------"
echo "Deployment submitted successfully!"
echo "--------------------------------------------------------"
