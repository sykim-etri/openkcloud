#!/bin/bash

# AI Software IDE Deployment Script
# Copyright (c) 2024 AI Software IDE Team. All rights reserved.

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Loading animation function
show_loading() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    printf " "
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Progress bar function
progress_bar() {
    local duration=$1
    local steps=20
    local step_duration=0.15
    
    printf "["
    for i in $(seq 1 $steps); do
        printf "█"
        sleep $step_duration
    done
    printf "] 100%%\n"
}

# Header function
print_header() {
    printf "%b\n" "${CYAN}"
    printf "╔══════════════════════════════════════════════════════════════╗\n"
    printf "║                                                              ║\n"
    printf "║                    AI Software IDE v1.0.0                    ║\n"
    printf "║                  Kubernetes Deployment Tool                  ║\n"
    printf "║                                                              ║\n"
    printf "╚══════════════════════════════════════════════════════════════╝\n"
    printf "%b\n" "${NC}"
}

# Status function
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info")
            printf "%b[INFO]%b %s\n" "${BLUE}" "${NC}" "$message"
            ;;
        "success")
            printf "%b[SUCCESS]%b %s\n" "${GREEN}" "${NC}" "$message"
            ;;
        "warning")
            printf "%b[WARNING]%b %s\n" "${YELLOW}" "${NC}" "$message"
            ;;
        "error")
            printf "%b[ERROR]%b %s\n" "${RED}" "${NC}" "$message"
            ;;
        "processing")
            printf "%b[PROCESSING]%b %s\n" "${PURPLE}" "${NC}" "$message"
            ;;
    esac
}

# Read namespace from values.yaml
NAMESPACE=$(grep "namespace:" values.yaml | awk '{print $2}' | head -1)
RELEASE_NAME="gpu-dashboard"
VERSION="1.0.0"

# Print header
clear
print_header

print_status "info" "Initializing AI Software IDE deployment..."
print_status "info" "Target namespace: ${NAMESPACE}"
print_status "info" "Release name: ${RELEASE_NAME}"
print_status "info" "Version: ${VERSION}"
printf "\n"

# Validate environment
print_status "processing" "Validating deployment environment..."
sleep 1

if [ ! -f "Chart.yaml" ]; then
    print_status "error" "Chart.yaml not found. Please run this script from the helm-chart directory."
    exit 1
fi

if ! command -v kubectl > /dev/null 2>&1; then
    print_status "error" "kubectl not found. Please install kubectl and configure cluster access."
    print_status "info" "Current PATH: $PATH"
    print_status "info" "Try: sudo apt-get install -y kubectl"
    exit 1
fi

if ! command -v helm > /dev/null 2>&1; then
    print_status "error" "Helm not found. Please install Helm 3.x or later."
    print_status "info" "Current PATH: $PATH"
    print_status "info" "Try: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
    exit 1
fi

# Additional cluster connectivity check
if ! kubectl cluster-info > /dev/null 2>&1; then
    print_status "warning" "kubectl found but cluster access may be limited"
    print_status "info" "Please ensure your kubeconfig is properly configured"
fi

print_status "success" "Environment validation completed"
printf "\n"

# Namespace management
print_status "processing" "Checking namespace configuration..."
if kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
    print_status "info" "Namespace '${NAMESPACE}' already exists"
else
    print_status "processing" "Creating namespace '${NAMESPACE}'..."
    kubectl create namespace "$NAMESPACE" > /dev/null 2>&1
    print_status "success" "Namespace '${NAMESPACE}' created successfully"
fi
printf "\n"

# Helm repository setup
print_status "processing" "Configuring Helm repositories..."
{
    helm repo add bitnami https://charts.bitnami.com/bitnami > /dev/null 2>&1
    helm repo update > /dev/null 2>&1
} &
show_loading $!
print_status "success" "Helm repositories configured"
printf "\n"

# Dependency management
print_status "processing" "Resolving chart dependencies..."
{
    helm dependency update > /dev/null 2>&1
    # Clean up generated .tgz files to keep workspace clean
    rm -f charts/*.tgz
} &
show_loading $!
print_status "success" "Dependencies resolved"
printf "\n"

# Deployment
print_status "processing" "Deploying AI Software IDE to Kubernetes cluster..."
printf "%bDeployment Progress:%b\n" "${YELLOW}" "${NC}"
progress_bar 3

{
    helm upgrade --install $RELEASE_NAME . \
        --namespace $NAMESPACE \
        --wait \
        --timeout 10m > /dev/null 2>&1
} &
show_loading $!

print_status "success" "AI Software IDE deployed successfully!"
printf "\n"

# Post-deployment status
print_status "info" "Verifying deployment status..."
sleep 2

kubectl get pods -n $NAMESPACE --no-headers | while read line; do
    pod_name=$(echo $line | awk '{print $1}')
    pod_status=$(echo $line | awk '{print $3}')
    if [ "$pod_status" = "Running" ]; then
        print_status "success" "Pod ${pod_name} is running"
    else
        print_status "warning" "Pod ${pod_name} status: ${pod_status}"
    fi
done

printf "\n"
printf "%b╔══════════════════════════════════════════════════════════════╗%b\n" "${GREEN}" "${NC}"
printf "%b║                    DEPLOYMENT COMPLETED                      ║%b\n" "${GREEN}" "${NC}"
printf "%b╚══════════════════════════════════════════════════════════════╝%b\n" "${GREEN}" "${NC}"
printf "\n"

# Access information
NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}" 2>/dev/null)

printf "%bAccess Information:%b\n" "${WHITE}" "${NC}"
printf "%b┌─────────────────────────────────────────────────────────────┐%b\n" "${CYAN}" "${NC}"
printf "%b│%b Service                │ Access Method                    %b│%b\n" "${CYAN}" "${NC}" "${CYAN}" "${NC}"
printf "%b├─────────────────────────────────────────────────────────────┤%b\n" "${CYAN}" "${NC}"
printf "%b│%b Frontend (Web UI)      │ http://%s:30080        %b│%b\n" "${CYAN}" "${NC}" "${NODE_IP}" "${CYAN}" "${NC}"
printf "%b│%b Backend API            │ http://%s:30800/docs   %b│%b\n" "${CYAN}" "${NC}" "${NODE_IP}" "${CYAN}" "${NC}"
printf "%b│%b Data Observer API      │ Port-forward required            %b│%b\n" "${CYAN}" "${NC}" "${CYAN}" "${NC}"
printf "%b└─────────────────────────────────────────────────────────────┘%b\n" "${CYAN}" "${NC}"
printf "\n"

printf "%bPort Forwarding Commands (Optional):%b\n" "${WHITE}" "${NC}"
printf "%b# Frontend%b\n" "${GRAY}" "${NC}"
printf "  kubectl port-forward -n %s svc/%s-frontend 8080:80\n" "${NAMESPACE}" "${RELEASE_NAME}"
printf "%b# Backend%b\n" "${GRAY}" "${NC}"
printf "  kubectl port-forward -n %s svc/%s-backend 8000:8000\n" "${NAMESPACE}" "${RELEASE_NAME}"
printf "%b# Data Observer%b\n" "${GRAY}" "${NC}"
printf "  kubectl port-forward -n %s svc/%s-data-observer 8001:8000\n" "${NAMESPACE}" "${RELEASE_NAME}"
printf "\n"

printf "%bManagement Commands:%b\n" "${WHITE}" "${NC}"
printf "%b# Check status%b\n" "${GRAY}" "${NC}"
printf "  kubectl get pods -n %s\n" "${NAMESPACE}"
printf "%b# View logs%b\n" "${GRAY}" "${NC}"
printf "  kubectl logs -n %s -l app.kubernetes.io/name=frontend\n" "${NAMESPACE}"
printf "%b# Uninstall%b\n" "${GRAY}" "${NC}"
printf "  helm uninstall %s -n %s\n" "${RELEASE_NAME}" "${NAMESPACE}"
printf "\n"

print_status "info" "For detailed documentation, see README.md and install-guide.md"
printf "%bHappy monitoring! 🚀%b\n" "${GREEN}" "${NC}"
