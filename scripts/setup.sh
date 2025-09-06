#!/bin/bash

# Phoenix System - Setup Script
# Configura o ambiente para provisionamento da infraestrutura

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
    echo -e "${PURPLE}║                    Phoenix System Setup                     ║${NC}"
    echo -e "${PURPLE}║              Sistema Autônomo de Resolução                  ║${NC}"
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

# Verificar se está executando no diretório correto
if [[ ! -f "README.md" ]] || [[ ! -d "infrastructure" ]]; then
    print_error "Execute este script a partir do diretório raiz do projeto Phoenix"
    exit 1
fi

print_header

# Verificar pré-requisitos
print_section "Verificando Pré-requisitos"

# Verificar Azure CLI
if command -v az &> /dev/null; then
    print_success "Azure CLI encontrado: $(az --version | head -n1)"
else
    print_error "Azure CLI não encontrado. Instale: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Verificar Terraform
if command -v terraform &> /dev/null; then
    print_success "Terraform encontrado: $(terraform --version | head -n1)"
else
    print_error "Terraform não encontrado. Instale: https://www.terraform.io/downloads.html"
    exit 1
fi

# Verificar kubectl
if command -v kubectl &> /dev/null; then
    print_success "kubectl encontrado: $(kubectl version --client --short 2>/dev/null || echo 'kubectl client')"
else
    print_warning "kubectl não encontrado. Será necessário para gerenciar o AKS"
fi

# Verificar Docker
if command -v docker &> /dev/null; then
    print_success "Docker encontrado: $(docker --version)"
else
    print_warning "Docker não encontrado. Será necessário para build das aplicações"
fi

# Verificar login no Azure
print_section "Verificando Autenticação Azure"
if az account show &> /dev/null; then
    ACCOUNT_INFO=$(az account show --query '{name:name, id:id, tenantId:tenantId}' -o table)
    print_success "Autenticado no Azure:"
    echo "$ACCOUNT_INFO"
else
    print_error "Não autenticado no Azure. Execute: az login"
    exit 1
fi

# Configurar subscription (se necessário)
print_section "Configuração da Subscription"
CURRENT_SUB=$(az account show --query id -o tsv)
echo "Subscription atual: $CURRENT_SUB"

read -p "Deseja usar uma subscription diferente? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Subscriptions disponíveis:"
    az account list --query '[].{Name:name, Id:id, State:state}' -o table
    read -r -p "Digite o ID da subscription: " SUB_ID
    az account set --subscription "$SUB_ID"
    print_success "Subscription alterada para: $SUB_ID"
fi

# Verificar providers necessários
print_section "Verificando Azure Resource Providers"
REQUIRED_PROVIDERS=(
    "Microsoft.ContainerService"
    "Microsoft.ContainerRegistry"
    "Microsoft.Web"
    "Microsoft.DocumentDB"
    "Microsoft.CognitiveServices"
    "Microsoft.Search"
    "Microsoft.EventHub"
    "Microsoft.OperationalInsights"
    "Microsoft.Insights"
    "Microsoft.KeyVault"
    "Microsoft.Storage"
    "Microsoft.Network"
    "Microsoft.Compute"
)

for provider in "${REQUIRED_PROVIDERS[@]}"; do
    STATUS=$(az provider show --namespace "$provider" --query registrationState -o tsv 2>/dev/null || echo "NotRegistered")
    if [[ "$STATUS" == "Registered" ]]; then
        print_success "$provider: Registrado"
    else
        print_warning "$provider: Não registrado. Registrando..."
        az provider register --namespace "$provider" --wait
        print_success "$provider: Registrado com sucesso"
    fi
done

# Configurar Terraform
print_section "Configurando Terraform"
cd infrastructure/terraform

# Inicializar Terraform
if [[ ! -d ".terraform" ]]; then
    print_warning "Inicializando Terraform..."
    terraform init
    print_success "Terraform inicializado"
else
    print_success "Terraform já inicializado"
fi

# Validar configuração
print_warning "Validando configuração Terraform..."
if terraform validate; then
    print_success "Configuração Terraform válida"
else
    print_error "Configuração Terraform inválida"
    exit 1
fi

# Criar workspace se necessário
WORKSPACE="dev"
if terraform workspace list | grep -q "$WORKSPACE"; then
    terraform workspace select "$WORKSPACE"
    print_success "Workspace '$WORKSPACE' selecionado"
else
    terraform workspace new "$WORKSPACE"
    print_success "Workspace '$WORKSPACE' criado e selecionado"
fi

cd ../..

# Configurar variáveis de ambiente
print_section "Configurando Variáveis de Ambiente"
if [[ ! -f ".env" ]]; then
    cat > .env << EOF
# Phoenix System Environment Variables
AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
PHOENIX_ENVIRONMENT=dev
PHOENIX_LOCATION="East US"
EOF
    print_success "Arquivo .env criado"
else
    print_success "Arquivo .env já existe"
fi

# Configurar Git hooks (se for um repositório Git)
if [[ -d ".git" ]]; then
    print_section "Configurando Git Hooks"
    mkdir -p .git/hooks
    
    # Pre-commit hook para validar Terraform
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Validate Terraform before commit
if [[ -d "infrastructure/terraform" ]]; then
    cd infrastructure/terraform
    terraform fmt -check=true -diff=true
    terraform validate
    cd ../..
fi
EOF
    chmod +x .git/hooks/pre-commit
    print_success "Git hooks configurados"
fi

# Resumo final
print_section "Resumo da Configuração"
echo -e "${GREEN}✅ Pré-requisitos verificados${NC}"
echo -e "${GREEN}✅ Azure autenticado${NC}"
echo -e "${GREEN}✅ Resource Providers registrados${NC}"
echo -e "${GREEN}✅ Terraform configurado${NC}"
echo -e "${GREEN}✅ Variáveis de ambiente configuradas${NC}"

echo
echo -e "${PURPLE}🚀 Próximos Passos:${NC}"
echo "1. Revisar as variáveis em infrastructure/terraform/terraform.tfvars"
echo "2. Executar: ./scripts/deploy-infrastructure.sh"
echo "3. Aguardar o provisionamento da infraestrutura"
echo "4. Executar: ./scripts/deploy-agents.sh"
echo

print_success "Setup concluído com sucesso!"

