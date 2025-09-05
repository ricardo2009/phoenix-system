#!/bin/bash

# Phoenix System - Workflow Setup Script
# Este script configura todos os workflows e secrets necessários para o sistema Phoenix

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Banner
echo -e "${PURPLE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                    🚀 PHOENIX SYSTEM                          ║
║                  Workflow Setup Script                        ║
║                                                               ║
║  Configuração automatizada de workflows GitHub Actions       ║
║  com matriz complexa e automação avançada                     ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar pré-requisitos
log "Verificando pré-requisitos..."

# Verificar se está no diretório correto
if [[ ! -f "README.md" ]] || [[ ! -d ".github/workflows" ]]; then
    error "Execute este script no diretório raiz do projeto Phoenix"
    exit 1
fi

# Verificar GitHub CLI
if ! command -v gh &> /dev/null; then
    error "GitHub CLI (gh) não está instalado. Instale: https://cli.github.com/"
    exit 1
fi

# Verificar Azure CLI
if ! command -v az &> /dev/null; then
    error "Azure CLI não está instalado. Instale: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Verificar se está logado no GitHub
if ! gh auth status &> /dev/null; then
    error "Não está autenticado no GitHub. Execute: gh auth login"
    exit 1
fi

# Verificar se está logado no Azure
if ! az account show &> /dev/null; then
    error "Não está autenticado no Azure. Execute: az login"
    exit 1
fi

success "Todos os pré-requisitos atendidos"

# Obter informações do repositório
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO_NAME=$(gh repo view --json name --jq '.name')
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"

log "Repositório: ${REPO_URL}"

# Menu de opções
echo ""
echo -e "${CYAN}Selecione uma opção:${NC}"
echo "1. 🔧 Setup completo (recomendado)"
echo "2. 🔐 Configurar apenas secrets"
echo "3. 📊 Validar workflows existentes"
echo "4. 🧪 Testar workflows localmente"
echo "5. 📋 Gerar documentação"
echo "6. 🚀 Deploy inicial"
echo ""

read -r -p "Digite sua escolha (1-6): " choice

case $choice in
    1)
        log "Iniciando setup completo..."
        SETUP_TYPE="full"
        ;;
    2)
        log "Configurando apenas secrets..."
        SETUP_TYPE="secrets"
        ;;
    3)
        log "Validando workflows..."
        SETUP_TYPE="validate"
        ;;
    4)
        log "Testando workflows localmente..."
        SETUP_TYPE="test"
        ;;
    5)
        log "Gerando documentação..."
        SETUP_TYPE="docs"
        ;;
    6)
        log "Executando deploy inicial..."
        SETUP_TYPE="deploy"
        ;;
    *)
        error "Opção inválida"
        exit 1
        ;;
esac

# Função para configurar secrets
setup_secrets() {
    log "Configurando secrets do GitHub..."
    
    # Verificar se o arquivo de secrets existe
    if [[ ! -f ".github/SECRETS.md" ]]; then
        error "Arquivo .github/SECRETS.md não encontrado"
        return 1
    fi
    
    # Obter informações do Azure
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    TENANT_ID=$(az account show --query tenantId -o tsv)
    
    log "Subscription ID: $SUBSCRIPTION_ID"
    log "Tenant ID: $TENANT_ID"
    
    # Criar Service Principal se não existir
    SP_NAME="phoenix-system-github-${REPO_NAME}"
    
    if az ad sp list --display-name "$SP_NAME" --query '[0].appId' -o tsv | grep -q .; then
        warning "Service Principal já existe: $SP_NAME"
        CLIENT_ID=$(az ad sp list --display-name "$SP_NAME" --query '[0].appId' -o tsv)
        
        # Tentar extrair secrets existentes se AZURE_CREDENTIALS estiver configurado
        if gh secret list | grep -q "AZURE_CREDENTIALS"; then
            log "Verificando se secrets individuais estão configurados..."
            
            # Verificar se os secrets individuais existem
            if ! gh secret list | grep -q "AZURE_CLIENT_ID"; then
                warning "AZURE_CLIENT_ID não configurado, mas AZURE_CREDENTIALS existe"
                warning "Para usar a nova autenticação, configure os secrets individuais"
            fi
        fi
    else
        log "Criando Service Principal: $SP_NAME"
        
        SP_OUTPUT=$(az ad sp create-for-rbac \
            --name "$SP_NAME" \
            --role contributor \
            --scopes "/subscriptions/$SUBSCRIPTION_ID" \
            --sdk-auth)
            
        CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.clientId')
        CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.clientSecret')
        
        success "Service Principal criado com sucesso"
        
        # Configurar secrets principais
        log "Configurando secrets principais..."
        
        # AZURE_CLIENT_ID
        echo "$CLIENT_ID" | gh secret set AZURE_CLIENT_ID
        success "AZURE_CLIENT_ID configurado"
        
        # AZURE_CLIENT_SECRET
        echo "$CLIENT_SECRET" | gh secret set AZURE_CLIENT_SECRET
        success "AZURE_CLIENT_SECRET configurado"
        
        # AZURE_SUBSCRIPTION_ID
        echo "$SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID
        success "AZURE_SUBSCRIPTION_ID configurado"
        
        # AZURE_TENANT_ID
        echo "$TENANT_ID" | gh secret set AZURE_TENANT_ID
        success "AZURE_TENANT_ID configurado"
        
        # AZURE_CREDENTIALS (for backward compatibility, if needed)
        echo "$SP_OUTPUT" | gh secret set AZURE_CREDENTIALS
        success "AZURE_CREDENTIALS configurado (backward compatibility)"
        echo "$CLIENT_ID" | gh secret set AZURE_CLIENT_ID
        echo "$CLIENT_SECRET" | gh secret set AZURE_CLIENT_SECRET
        
        success "Secrets do Azure configurados"
    fi
    
    # Configurar outros secrets interativamente
    setup_interactive_secrets
}

# Função para configurar secrets interativamente
setup_interactive_secrets() {
    log "Configuração interativa de secrets..."
    
    # OpenAI API Key
    if ! gh secret list | grep -q "OPENAI_API_KEY"; then
        echo ""
        read -r -p "Digite sua OpenAI API Key (ou pressione Enter para pular): " openai_key
        if [[ -n "$openai_key" ]]; then
            echo "$openai_key" | gh secret set OPENAI_API_KEY
            success "OPENAI_API_KEY configurado"
        fi
    fi
    
    # Teams Webhook URL
    if ! gh secret list | grep -q "TEAMS_WEBHOOK_URL"; then
        echo ""
        read -r -p "Digite a URL do webhook do Teams (ou pressione Enter para pular): " teams_webhook
        if [[ -n "$teams_webhook" ]]; then
            echo "$teams_webhook" | gh secret set TEAMS_WEBHOOK_URL
            success "TEAMS_WEBHOOK_URL configurado"
        fi
    fi
    
    # Slack Webhook URL
    if ! gh secret list | grep -q "SLACK_WEBHOOK_URL"; then
        echo ""
        read -r -p "Digite a URL do webhook do Slack (ou pressione Enter para pular): " slack_webhook
        if [[ -n "$slack_webhook" ]]; then
            echo "$slack_webhook" | gh secret set SLACK_WEBHOOK_URL
            success "SLACK_WEBHOOK_URL configurado"
        fi
    fi
    
    # Deployment Approvers
    if ! gh secret list | grep -q "DEPLOYMENT_APPROVERS"; then
        echo ""
        read -r -p "Digite os usuários aprovadores (separados por vírgula): " approvers
        if [[ -n "$approvers" ]]; then
            echo "$approvers" | gh secret set DEPLOYMENT_APPROVERS
            success "DEPLOYMENT_APPROVERS configurado"
        fi
    fi
}

# Função para validar workflows
validate_workflows() {
    log "Validando workflows..."
    
    local workflows=(
        ".github/workflows/phoenix-basic.yml"
        ".github/workflows/phoenix-infrastructure-ultimate.yml"
        ".github/workflows/phoenix-applications-ultimate.yml"
        ".github/workflows/phoenix-monitoring-ultimate.yml"
    )
    
    for workflow in "${workflows[@]}"; do
        if [[ -f "$workflow" ]]; then
            success "$(basename "$workflow") existe"
            
            # Validar sintaxe YAML
            if command -v yamllint &> /dev/null; then
                if yamllint "$workflow" &> /dev/null; then
                    success "$(basename "$workflow") - sintaxe válida"
                else
                    warning "$(basename "$workflow") - problemas de sintaxe"
                fi
            fi
        else
            error "$(basename "$workflow") não encontrado"
        fi
    done
}

# Função para testar workflows localmente
test_workflows() {
    log "Testando workflows localmente..."
    
    # Instalar act se não estiver disponível
    if ! command -v act &> /dev/null; then
        warning "act não está instalado. Instalando..."
        
        if command -v brew &> /dev/null; then
            brew install act
        elif command -v curl &> /dev/null; then
            curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
        else
            error "Não foi possível instalar act automaticamente"
            info "Instale manualmente: https://github.com/nektos/act"
            return 1
        fi
    fi
    
    # Testar workflow de CI/CD
    log "Testando workflow de CI/CD..."
    act -W .github/workflows/phoenix-cicd.yml --dry-run
    
    success "Teste de workflows concluído"
}

# Função para gerar documentação
generate_docs() {
    log "Gerando documentação..."
    
    # Criar README dos workflows
    cat > .github/workflows/README.md << 'EOF'
# 🚀 Phoenix System - GitHub Actions Workflows

Este diretório contém os workflows GitHub Actions para o sistema Phoenix, implementando CI/CD avançado com matriz complexa e automação inteligente.

## 📋 Workflows Disponíveis

### 🏗️ phoenix-infrastructure.yml
**Propósito:** Provisionamento e gerenciamento da infraestrutura Azure com Terraform

**Triggers:**
- Push em `main`, `develop`
- Pull requests para `main`
- Execução manual

**Características:**
- Matriz dinâmica por ambiente e prioridade
- Deploy paralelo de módulos Terraform
- Validação pós-deploy
- Rollback automático em falhas

### 🚀 phoenix-applications.yml
**Propósito:** Build e deploy das aplicações (Azure Functions, AKS, Copilot Studio)

**Triggers:**
- Push em branches principais
- Pull requests
- Execução manual

**Características:**
- Análise de mudanças inteligente
- Matriz complexa de testes e builds
- Estratégias de deploy avançadas (rolling, blue-green, canary)
- Testes pós-deploy automatizados

### 📊 phoenix-monitoring.yml
**Propósito:** Monitoramento contínuo e observabilidade do sistema

**Triggers:**
- Agendamento (a cada 15 minutos)
- Push em arquivos de monitoramento
- Execução manual

**Características:**
- Health checks distribuídos
- Monitoramento de performance
- Análise de segurança
- Análise de custos
- Sistema de alertas inteligente

### 🔄 phoenix-cicd.yml
**Propósito:** Pipeline CI/CD principal com orquestração avançada

**Triggers:**
- Push em qualquer branch
- Pull requests
- Releases
- Execução manual

**Características:**
- Orquestração dinâmica de pipeline
- Matriz de testes paralelos com dependências
- Build multi-plataforma
- Deploy com aprovações
- Relatórios detalhados

## 🎯 Matriz Complexa

Os workflows utilizam matrizes dinâmicas que se adaptam baseado em:

- **Escopo de mudanças:** Detecta automaticamente quais componentes foram alterados
- **Ambiente alvo:** Diferentes configurações por ambiente (dev/staging/prod)
- **Tipo de deploy:** Estratégias adaptativas baseadas no ambiente
- **Dependências:** Execução sequencial ou paralela baseada em dependências

## 🔐 Secrets Necessários

Consulte `.github/SECRETS.md` para a lista completa de secrets necessários.

## 🚀 Como Usar

### Deploy Manual
```bash
# Deploy para desenvolvimento
gh workflow run phoenix-applications.yml -f environment=dev

# Deploy para produção com aprovação
gh workflow run phoenix-applications.yml -f environment=prod -f deployment_type=blue-green
```

### Monitoramento
```bash
# Executar monitoramento completo
gh workflow run phoenix-monitoring.yml -f monitoring_type=all

# Análise de custos específica
gh workflow run phoenix-monitoring.yml -f monitoring_type=cost-analysis
```

### Infraestrutura
```bash
# Provisionar infraestrutura
gh workflow run phoenix-infrastructure.yml -f environment=dev

# Destruir infraestrutura (cuidado!)
gh workflow run phoenix-infrastructure.yml -f destroy_infrastructure=true
```

## 📊 Dashboards

- **GitHub Actions:** Visualização nativa do GitHub
- **Azure Monitor:** Métricas de infraestrutura e aplicação
- **Application Insights:** Telemetria detalhada das aplicações

## 🔧 Troubleshooting

### Falhas Comuns

1. **Secrets não configurados**
   - Verifique `.github/SECRETS.md`
   - Execute `scripts/setup-workflows.sh`

2. **Falhas de autenticação Azure**
   - Verifique Service Principal
   - Renove credenciais se necessário

3. **Timeouts em deploy**
   - Verifique recursos Azure
   - Ajuste timeouts nos workflows

### Logs e Debugging

- Use `gh run list` para listar execuções
- Use `gh run view <run-id>` para detalhes
- Ative debug com `ACTIONS_STEP_DEBUG=true`

## 📞 Suporte

- 📧 Email: devops@phoenix-system.com
- 💬 Teams: Phoenix DevOps Channel
- 🐛 Issues: GitHub Issues deste repositório
EOF

    success "Documentação gerada em .github/workflows/README.md"
}

# Função para deploy inicial
initial_deploy() {
    log "Executando deploy inicial..."
    
    # Verificar se os secrets estão configurados
    local required_secrets=("AZURE_CREDENTIALS" "AZURE_SUBSCRIPTION_ID" "OPENAI_API_KEY")
    
    for secret in "${required_secrets[@]}"; do
        if ! gh secret list | grep -q "$secret"; then
            error "Secret obrigatório não configurado: $secret"
            info "Execute primeiro: $0 com opção 2 (configurar secrets)"
            return 1
        fi
    done
    
    # Executar workflow de infraestrutura
    log "Iniciando provisionamento da infraestrutura..."
    gh workflow run phoenix-infrastructure.yml -f environment=dev
    
    # Aguardar conclusão
    log "Aguardando conclusão do workflow..."
    sleep 30
    
    # Verificar status
    LATEST_RUN=$(gh run list --workflow=phoenix-infrastructure.yml --limit=1 --json databaseId --jq '.[0].databaseId')
    
    if [[ -n "$LATEST_RUN" ]]; then
        info "Workflow iniciado. ID: $LATEST_RUN"
        info "Acompanhe o progresso: gh run view $LATEST_RUN"
        info "Ou acesse: ${REPO_URL}/actions/runs/${LATEST_RUN}"
    fi
    
    success "Deploy inicial iniciado com sucesso"
}

# Executar ação baseada na escolha
case $SETUP_TYPE in
    "full")
        setup_secrets
        validate_workflows
        generate_docs
        
        echo ""
        read -r -p "Deseja executar o deploy inicial? (y/N): " deploy_choice
        if [[ "$deploy_choice" =~ ^[Yy]$ ]]; then
            initial_deploy
        fi
        ;;
    "secrets")
        setup_secrets
        ;;
    "validate")
        validate_workflows
        ;;
    "test")
        test_workflows
        ;;
    "docs")
        generate_docs
        ;;
    "deploy")
        initial_deploy
        ;;
esac

# Resumo final
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ SETUP CONCLUÍDO                         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

info "Próximos passos:"
echo "1. 📋 Revise os workflows em .github/workflows/"
echo "2. 🔐 Configure secrets adicionais se necessário"
echo "3. 🚀 Execute um deploy de teste"
echo "4. 📊 Configure monitoramento e alertas"
echo "5. 📖 Leia a documentação em .github/workflows/README.md"

echo ""
info "Comandos úteis:"
echo "• gh workflow list                    # Listar workflows"
echo "• gh run list                         # Listar execuções"
echo "• gh secret list                      # Listar secrets"
echo "• gh workflow run <workflow> -f key=value  # Executar workflow"

echo ""
success "Sistema Phoenix configurado com sucesso! 🎉"

