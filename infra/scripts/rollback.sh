#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
NAMESPACE="monitoring"
DEPLOYMENT_NAME="medai-flow-backend"
REVISION=0  # 0 means roll back to previous version

function usage() {
    echo "Usage: $0 [-n NAMESPACE] [-d DEPLOYMENT_NAME] [-r REVISION]"
    echo "  -n: Kubernetes namespace (default: monitoring)"
    echo "  -d: Deployment name (default: medai-flow-backend)"
    echo "  -r: Revision to rollback to (default: previous version)"
    exit 1
}

# Parse command line arguments
while getopts "n:d:r:h" opt; do
    case $opt in
        n) NAMESPACE="$OPTARG" ;;
        d) DEPLOYMENT_NAME="$OPTARG" ;;
        r) REVISION="$OPTARG" ;;
        h) usage ;;
        \?) usage ;;
    esac
done

echo -e "${YELLOW}Starting rollback procedure...${NC}"

# 1. Save current state
echo -e "${YELLOW}Saving current state...${NC}"
kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o yaml > deployment_backup.yaml
kubectl get configmap -n $NAMESPACE -o yaml > configmap_backup.yaml

# 2. Scale down monitoring components
echo -e "${YELLOW}Scaling down monitoring components...${NC}"
kubectl scale deployment prometheus-server -n $NAMESPACE --replicas=0
kubectl scale deployment grafana -n $NAMESPACE --replicas=0
kubectl scale deployment alertmanager -n $NAMESPACE --replicas=0

# 3. Perform rollback
echo -e "${YELLOW}Rolling back deployment...${NC}"
if [ $REVISION -eq 0 ]; then
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
else
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE --to-revision=$REVISION
fi

# 4. Wait for rollback to complete
echo -e "${YELLOW}Waiting for rollback to complete...${NC}"
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# 5. Scale up monitoring components
echo -e "${YELLOW}Scaling up monitoring components...${NC}"
kubectl scale deployment prometheus-server -n $NAMESPACE --replicas=1
kubectl scale deployment grafana -n $NAMESPACE --replicas=1
kubectl scale deployment alertmanager -n $NAMESPACE --replicas=1

# 6. Verify monitoring components
echo -e "${YELLOW}Verifying monitoring components...${NC}"
./verify_monitoring.sh

# 7. Verify application health
echo -e "${YELLOW}Verifying application health...${NC}"
HEALTH_ENDPOINT=$(kubectl get ing -n $NAMESPACE $DEPLOYMENT_NAME -o jsonpath='{.spec.rules[0].host}')/health
if curl -s "http://$HEALTH_ENDPOINT" | grep -q "ok"; then
    echo -e "${GREEN}✓ Application is healthy${NC}"
else
    echo -e "${RED}✗ Application health check failed${NC}"
    echo -e "${YELLOW}Consider restoring from backup:${NC}"
    echo "kubectl apply -f deployment_backup.yaml"
    echo "kubectl apply -f configmap_backup.yaml"
    exit 1
fi

echo -e "${GREEN}Rollback completed successfully!${NC}"