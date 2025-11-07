#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Prometheus
echo -e "${YELLOW}Checking Prometheus status...${NC}"
if kubectl get pods -n monitoring -l app=prometheus -o jsonpath='{.items[*].status.containerStatuses[0].ready}' | grep -q "true"; then
    echo -e "${GREEN}✓ Prometheus is running${NC}"
else
    echo -e "${RED}✗ Prometheus is not ready${NC}"
    exit 1
fi

# Check Grafana
echo -e "${YELLOW}Checking Grafana status...${NC}"
if kubectl get pods -n monitoring -l app=grafana -o jsonpath='{.items[*].status.containerStatuses[0].ready}' | grep -q "true"; then
    echo -e "${GREEN}✓ Grafana is running${NC}"
else
    echo -e "${RED}✗ Grafana is not ready${NC}"
    exit 1
fi

# Check AlertManager
echo -e "${YELLOW}Checking AlertManager status...${NC}"
if kubectl get pods -n monitoring -l app=alertmanager -o jsonpath='{.items[*].status.containerStatuses[0].ready}' | grep -q "true"; then
    echo -e "${GREEN}✓ AlertManager is running${NC}"
else
    echo -e "${RED}✗ AlertManager is not ready${NC}"
    exit 1
fi

# Verify Prometheus metrics endpoint
echo -e "${YELLOW}Verifying Prometheus metrics collection...${NC}"
METRICS_ENDPOINT=$(kubectl get ing -n monitoring prometheus-server -o jsonpath='{.spec.rules[0].host}')/metrics
if curl -s "http://$METRICS_ENDPOINT" | grep -q "rate_limit"; then
    echo -e "${GREEN}✓ Rate limiting metrics found${NC}"
else
    echo -e "${RED}✗ Rate limiting metrics not found${NC}"
    exit 1
fi

# Check Grafana dashboards
echo -e "${YELLOW}Verifying Grafana dashboards...${NC}"
GRAFANA_POD=$(kubectl get pods -n monitoring -l app=grafana -o jsonpath='{.items[0].metadata.name}')
if kubectl exec -n monitoring $GRAFANA_POD -- grafana-cli folders ls | grep -q "Rate Limiting"; then
    echo -e "${GREEN}✓ Rate limiting dashboard found${NC}"
else
    echo -e "${RED}✗ Rate limiting dashboard not found${NC}"
    exit 1
fi

# Verify Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if kubectl get pods -n monitoring -l app=redis-exporter -o jsonpath='{.items[*].status.containerStatuses[0].ready}' | grep -q "true"; then
    echo -e "${GREEN}✓ Redis exporter is running${NC}"
else
    echo -e "${RED}✗ Redis exporter is not ready${NC}"
    exit 1
fi

echo -e "${GREEN}All monitoring components verified successfully!${NC}"