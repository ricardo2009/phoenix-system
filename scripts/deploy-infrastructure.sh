#!/bin/bash

# Phoenix System - Infrastructure Deployment Script
# Provisiona toda a infraestrutura Azure usando Terraform

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Função para imprimir cabeçalho
print_header() {
    echo
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                Phoenix Infrastructure Deploy                 ║${NC}"
    echo -e "${PURPLE}║              Provisionamento da Infraestrutura              ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Função para imprimir seções
print_section() {
    echo
    echo -e "${BLUE}📋 $1${NC}"
    echo "================================================================"
}

# Função para imprimir sucesso
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Função para imprimir aviso
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Função para confirmar ação
confirm_action() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    read -p "Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Operação cancelada pelo usuário"
        exit 0
    fi
}

# Verificar se está no diretório correto
if [[ ! -f "README.md" ]] || [[ ! -d "infrastructure" ]]; then
    print_error "Execute este script a partir do diretório raiz do projeto Phoenix"
    exit 1
fi

print_header

# Carregar variáveis de ambiente
if [[ -f ".env" ]]; then
    source .env
    print_success "Variáveis de ambiente carregadas"
else
    print_warning "Arquivo .env não encontrado. Execute ./scripts/setup.sh primeiro"
fi

# Verificar autenticação Azure
print_section "Verificando Autenticação"
if ! az account show &> /dev/null; then
    print_error "Não autenticado no Azure. Execute: az login"
    exit 1
fi

ACCOUNT_INFO=$(az account show --query '{name:name, id:id}' -o tsv)
print_success "Autenticado como: $ACCOUNT_INFO"

# Navegar para o diretório Terraform
cd infrastructure/terraform

# Verificar se Terraform está inicializado
if [[ ! -d ".terraform" ]]; then
    print_warning "Terraform não inicializado. Inicializando..."
    terraform init
fi

# Selecionar workspace
WORKSPACE="${PHOENIX_ENVIRONMENT:-dev}"
terraform workspace select "$WORKSPACE" 2>/dev/null || terraform workspace new "$WORKSPACE"
print_success "Workspace '$WORKSPACE' selecionado"

# Validar configuração
print_section "Validando Configuração"
if terraform validate; then
    print_success "Configuração Terraform válida"
else
    print_error "Configuração Terraform inválida"
    exit 1
fi

# Executar terraform plan
print_section "Planejando Deployment"
print_warning "Executando terraform plan..."

if terraform plan -out=tfplan -var-file=terraform.tfvars; then
    print_success "Plano de deployment criado com sucesso"
else
    print_error "Falha ao criar plano de deployment"
    exit 1
fi

# Mostrar resumo do plano
echo
echo -e "${BLUE}📊 Resumo do Plano:${NC}"
terraform show -json tfplan | jq -r '
  .resource_changes[] | 
  select(.change.actions[] | . != "no-op") |
  "\(.change.actions | join(",")): \(.address)"
' | sort | uniq -c

# Confirmar deployment
echo
confirm_action "🚀 Pronto para provisionar a infraestrutura Phoenix no Azure."

# Executar terraform apply
print_section "Provisionando Infraestrutura"
print_warning "Iniciando provisionamento... Isso pode levar 15-30 minutos."

START_TIME=$(date +%s)

if terraform apply tfplan; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))
    
    print_success "Infraestrutura provisionada com sucesso em ${MINUTES}m ${SECONDS}s"
else
    print_error "Falha no provisionamento da infraestrutura"
    exit 1
fi

# Capturar outputs importantes
print_section "Coletando Informações da Infraestrutura"

# Salvar outputs em arquivo
terraform output -json > ../../outputs.json
print_success "Outputs salvos em outputs.json"

# Mostrar informações importantes
echo
echo -e "${PURPLE}🏗️  Recursos Provisionados:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Resource Group
RG_NAME=$(terraform output -raw resource_group_name 2>/dev/null || echo "N/A")
echo -e "${GREEN}Resource Group:${NC} $RG_NAME"

# Virtual Network
VNET_NAME=$(terraform output -raw virtual_network_name 2>/dev/null || echo "N/A")
echo -e "${GREEN}Virtual Network:${NC} $VNET_NAME"

# Application Gateway
AGW_IP=$(terraform output -raw application_gateway_public_ip 2>/dev/null || echo "N/A")
echo -e "${GREEN}Application Gateway IP:${NC} $AGW_IP"

# App Service
APP_HOSTNAME=$(terraform output -raw app_service_hostname 2>/dev/null || echo "N/A")
echo -e "${GREEN}App Service:${NC} https://$APP_HOSTNAME"

# AKS Cluster
AKS_NAME=$(terraform output -raw aks_cluster_name 2>/dev/null || echo "N/A")
echo -e "${GREEN}AKS Cluster:${NC} $AKS_NAME"

# Key Vault
KV_URI=$(terraform output -raw key_vault_uri 2>/dev/null || echo "N/A")
echo -e "${GREEN}Key Vault:${NC} $KV_URI"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Configurar kubectl para AKS
if [[ "$AKS_NAME" != "N/A" ]] && command -v kubectl &> /dev/null; then
    print_section "Configurando kubectl para AKS"
    if az aks get-credentials --resource-group "$RG_NAME" --name "$AKS_NAME" --overwrite-existing; then
        print_success "kubectl configurado para o cluster AKS"
        
        # Verificar conectividade
        if kubectl get nodes &> /dev/null; then
            print_success "Conectividade com AKS verificada"
            kubectl get nodes
        else
            print_warning "Não foi possível conectar ao cluster AKS"
        fi
    else
        print_warning "Falha ao configurar kubectl"
    fi
fi

# Salvar informações importantes em arquivo
print_section "Salvando Informações de Deployment"
cat > ../../deployment-info.txt << EOF
Phoenix System - Deployment Information
Generated: $(date)
Workspace: $WORKSPACE
Duration: ${MINUTES}m ${SECONDS}s

Resource Group: $RG_NAME
Virtual Network: $VNET_NAME
Application Gateway IP: $AGW_IP
App Service: https://$APP_HOSTNAME
AKS Cluster: $AKS_NAME
Key Vault: $KV_URI

Next Steps:
1. Deploy agents: ./scripts/deploy-agents.sh
2. Configure Copilot Studio: ./scripts/setup-copilot.sh
3. Deploy e-commerce app: ./scripts/deploy-ecommerce.sh
4. Run tests: ./scripts/run-tests.sh
EOF

print_success "Informações salvas em deployment-info.txt"

# Voltar ao diretório raiz
cd ../..

# Resumo final
print_section "Deployment Concluído"
echo -e "${GREEN}✅ Infraestrutura provisionada com sucesso${NC}"
echo -e "${GREEN}✅ Recursos Azure criados${NC}"
echo -e "${GREEN}✅ Configurações salvas${NC}"
echo -e "${GREEN}✅ kubectl configurado (se disponível)${NC}"

echo
echo -e "${PURPLE}🚀 Próximos Passos:${NC}"
echo "1. Verificar recursos no Azure Portal"
echo "2. Executar: ./scripts/deploy-agents.sh"
echo "3. Configurar Copilot Studio: ./scripts/setup-copilot.sh"
echo "4. Testar a solução: ./scripts/run-tests.sh"

echo
print_success "Infrastructure deployment concluído! 🎉"

