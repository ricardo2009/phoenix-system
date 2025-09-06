#!/bin/bash

# 🔍 Phoenix System - Secrets Validation Script
# This script validates if all required GitHub secrets are configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🔍 Phoenix System - Secrets Validation"
echo "======================================"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    error "GitHub CLI (gh) não está instalado. Instale: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    error "Não está autenticado no GitHub. Execute: gh auth login"
    exit 1
fi

# Get repository information
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO_NAME=$(gh repo view --json name --jq '.name')

log "Validando secrets para: $REPO_OWNER/$REPO_NAME"

# Required secrets for Phoenix System
REQUIRED_SECRETS=(
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET" 
    "AZURE_SUBSCRIPTION_ID"
    "AZURE_TENANT_ID"
    "REGISTRY_USERNAME"
    "REGISTRY_PASSWORD"
    "OPENAI_API_KEY"
    "COSMOS_DB_CONNECTION_STRING"
    "STORAGE_CONNECTION_STRING"
    "APPLICATION_INSIGHTS_KEY"
    "TEAMS_WEBHOOK_URL"
    "FUNCTION_KEY"
    "DEPLOYMENT_APPROVERS"
)

# Optional secrets (warnings if missing)
OPTIONAL_SECRETS=(
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_API_KEY"
    "EVENT_HUB_CONNECTION_STRING"
    "LOG_ANALYTICS_WORKSPACE_ID"
    "LOG_ANALYTICS_WORKSPACE_KEY"
    "SLACK_WEBHOOK_URL"
    "PAGERDUTY_INTEGRATION_KEY"
    "SECURITY_SCAN_TOKEN"
    "SONARCLOUD_TOKEN"
    "SNYK_TOKEN"
    "KUBECONFIG_DEV"
    "KUBECONFIG_STAGING"
    "KUBECONFIG_PROD"
)

# Function app publish profiles
FUNCTION_SECRETS=(
    "FUNCTION_APP_PUBLISH_PROFILE_ORCHESTRATOR"
    "FUNCTION_APP_PUBLISH_PROFILE_DIAGNOSTIC"
    "FUNCTION_APP_PUBLISH_PROFILE_RESOLUTION"
    "FUNCTION_APP_PUBLISH_PROFILE_COMMUNICATION"
)

# Get list of configured secrets
log "Obtendo lista de secrets configurados..."
CONFIGURED_SECRETS=$(gh secret list --json name --jq '.[].name')

# Validation counters
MISSING_REQUIRED=0
MISSING_OPTIONAL=0
TOTAL_CONFIGURED=0

echo ""
log "🔑 Validando secrets obrigatórios..."

for secret in "${REQUIRED_SECRETS[@]}"; do
    if echo "$CONFIGURED_SECRETS" | grep -q "^$secret$"; then
        success "✅ $secret"
        ((TOTAL_CONFIGURED++))
    else
        error "❌ $secret - OBRIGATÓRIO - AUSENTE"
        ((MISSING_REQUIRED++))
    fi
done

echo ""
log "🔑 Validando secrets opcionais..."

for secret in "${OPTIONAL_SECRETS[@]}"; do
    if echo "$CONFIGURED_SECRETS" | grep -q "^$secret$"; then
        success "✅ $secret"
        ((TOTAL_CONFIGURED++))
    else
        warning "⚠️  $secret - OPCIONAL - AUSENTE"
        ((MISSING_OPTIONAL++))
    fi
done

echo ""
log "🔑 Validando function app publish profiles..."

for secret in "${FUNCTION_SECRETS[@]}"; do
    if echo "$CONFIGURED_SECRETS" | grep -q "^$secret$"; then
        success "✅ $secret"
        ((TOTAL_CONFIGURED++))
    else
        warning "⚠️  $secret - FUNCTION APP - AUSENTE"
        ((MISSING_OPTIONAL++))
    fi
done

# Check for legacy AZURE_CREDENTIALS secret
echo ""
log "🔍 Verificando configurações legadas..."

if echo "$CONFIGURED_SECRETS" | grep -q "^AZURE_CREDENTIALS$"; then
    warning "⚠️  AZURE_CREDENTIALS - LEGADO DETECTADO"
    warning "    Este secret não é mais usado. Use AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, etc."
fi

# Summary
echo ""
echo "📊 RESUMO DA VALIDAÇÃO"
echo "======================"
echo "✅ Secrets configurados: $TOTAL_CONFIGURED"
echo "❌ Secrets obrigatórios ausentes: $MISSING_REQUIRED"
echo "⚠️  Secrets opcionais ausentes: $MISSING_OPTIONAL"

# Validation result
echo ""
if [[ $MISSING_REQUIRED -eq 0 ]]; then
    success "🎉 Todos os secrets obrigatórios estão configurados!"
    
    if [[ $MISSING_OPTIONAL -eq 0 ]]; then
        success "🌟 Configuração perfeita! Todos os secrets estão configurados."
        echo ""
        echo "🚀 PRÓXIMOS PASSOS:"
        echo "1. Execute os workflows para testar a configuração"
        echo "2. Monitore os logs para verificar autenticação"
        echo "3. Configure environment-specific secrets se necessário"
    else
        warning "⚠️  Alguns secrets opcionais estão ausentes. Funcionalidades podem estar limitadas."
        echo ""
        echo "🚀 PRÓXIMOS PASSOS:"
        echo "1. Configure os secrets opcionais conforme necessário"
        echo "2. Execute os workflows para testar a configuração"
        echo "3. Monitore os logs para verificar autenticação"
    fi
    
    exit 0
else
    error "❌ Configuração incompleta! Secrets obrigatórios estão ausentes."
    echo ""
    echo "🔧 AÇÕES NECESSÁRIAS:"
    echo "1. Configure todos os secrets obrigatórios ausentes"
    echo "2. Use o script setup-workflows.sh para configuração automática"
    echo "3. Consulte .github/SECRETS.md para instruções detalhadas"
    echo ""
    echo "📖 COMANDOS ÚTEIS:"
    echo "   ./scripts/setup-workflows.sh  # Configuração automática"
    echo "   gh secret set SECRET_NAME     # Configuração manual"
    echo "   gh secret list               # Listar secrets existentes"
    
    exit 1
fi