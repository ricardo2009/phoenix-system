#!/bin/bash

# 🚀 Phoenix System Workflow Health Check
# This script validates workflow syntax and checks for common issues

set -e

echo "🔍 Phoenix System Workflow Health Check"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

WORKFLOW_DIR=".github/workflows"
ERRORS=0

echo -e "\n📁 Checking workflow directory..."
if [ ! -d "$WORKFLOW_DIR" ]; then
    echo -e "${RED}❌ Workflow directory not found: $WORKFLOW_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Workflow directory found${NC}"

echo -e "\n📝 Validating YAML syntax..."
for workflow in "$WORKFLOW_DIR"/*.yml; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow")
        echo -n "  Testing $filename... "
        
        if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
            echo -e "${GREEN}✅ Valid${NC}"
        else
            echo -e "${RED}❌ Invalid YAML${NC}"
            ((ERRORS++))
        fi
    fi
done

echo -e "\n🔍 Checking for common issues..."

echo -n "  Checking for unsupported filters... "
if grep -r "| title\|| capitalize\|| upcase\|| downcase" "$WORKFLOW_DIR"/ >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Found unsupported filters${NC}"
    grep -rn "| title\|| capitalize\|| upcase\|| downcase" "$WORKFLOW_DIR"/ | head -3
    ((ERRORS++))
else
    echo -e "${GREEN}✅ No unsupported filters${NC}"
fi

echo -n "  Checking for division operations in templates... "
if grep -r '\${{ .*/ [0-9]' "$WORKFLOW_DIR"/ >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Found division operations in templates${NC}"
    grep -rn '\${{ .*/ [0-9]' "$WORKFLOW_DIR"/ | head -3
    ((ERRORS++))
else
    echo -e "${GREEN}✅ No template division operations${NC}"
fi

echo -n "  Checking for problematic JSON parsing... "
# Only flag complex chained JSON access like fromJson().field.subfield
if grep -r "fromJson.*)\\..*\\." "$WORKFLOW_DIR"/ >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Found complex JSON parsing${NC}"
    grep -rn "fromJson.*)\\..*\\." "$WORKFLOW_DIR"/ | head -3
    ((ERRORS++))
else
    echo -e "${GREEN}✅ No problematic JSON parsing${NC}"
fi

echo -n "  Checking for overly long lines... "
LONG_LINES=$(find "$WORKFLOW_DIR" -name "*.yml" -exec wc -L {} + | awk '$1 > 200 {print $2 ": " $1}' | grep -v total || true)
if [ -n "$LONG_LINES" ]; then
    echo -e "${YELLOW}⚠️  Found long lines (>200 chars)${NC}"
    echo "$LONG_LINES"
else
    echo -e "${GREEN}✅ No overly long lines${NC}"
fi

echo -e "\n📊 Summary"
echo "=========="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Workflows are healthy.${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS potential issues. Please review and fix before committing.${NC}"
    exit 1
fi