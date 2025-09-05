# 🔐 Phoenix System - Secrets and Variables Configuration

Este documento lista todos os secrets e variáveis necessários para o funcionamento completo dos workflows do sistema Phoenix.

## 📋 Repository Secrets

Configure os seguintes secrets no GitHub Repository Settings > Secrets and variables > Actions:

### 🔑 Azure Authentication

⚠️ **ATUALIZAÇÃO IMPORTANTE**: A partir de 2024, os workflows usam autenticação individual ao invés do formato JSON consolidado.

**Método Atual (Recomendado):**
```
AZURE_CLIENT_ID
```
**Descrição:** Client ID do Service Principal  
**Exemplo:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

```
AZURE_CLIENT_SECRET
```
**Descrição:** Client Secret do Service Principal  
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

```
AZURE_SUBSCRIPTION_ID
```
**Descrição:** ID da subscription do Azure  
**Exemplo:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

```
AZURE_TENANT_ID
```
**Descrição:** ID do tenant do Azure AD  
**Exemplo:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Método Legado (Deprecated):**
```
AZURE_CREDENTIALS
```
**Descrição:** Credenciais do Service Principal para autenticação no Azure  
**Status:** 🚨 DEPRECATED - Use os secrets individuais acima  
**Formato:** JSON
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### 🔑 Azure Individual Secrets (Duplicação removida)

### 🐳 Container Registry
```
REGISTRY_USERNAME
```
**Descrição:** Username para o Azure Container Registry
**Exemplo:** `phoenixsystem`

```
REGISTRY_PASSWORD
```
**Descrição:** Password para o Azure Container Registry
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 🤖 AI Services
```
OPENAI_API_KEY
```
**Descrição:** Chave da API do OpenAI para os agentes inteligentes
**Exemplo:** `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

```
AZURE_OPENAI_ENDPOINT
```
**Descrição:** Endpoint do Azure OpenAI Service
**Exemplo:** `https://phoenix-openai-dev.openai.azure.com/`

```
AZURE_OPENAI_API_KEY
```
**Descrição:** Chave da API do Azure OpenAI Service
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 🗄️ Database and Storage
```
COSMOS_DB_CONNECTION_STRING
```
**Descrição:** String de conexão do Azure Cosmos DB
**Exemplo:** `AccountEndpoint=https://phoenix-cosmos-dev.documents.azure.com:443/;AccountKey=xxxxxxxxxx==;`

```
STORAGE_CONNECTION_STRING
```
**Descrição:** String de conexão do Azure Storage Account
**Exemplo:** `DefaultEndpointsProtocol=https;AccountName=phoenixstoragedev;AccountKey=xxxxxxxxxx==;EndpointSuffix=core.windows.net`

```
EVENT_HUB_CONNECTION_STRING
```
**Descrição:** String de conexão do Azure Event Hub
**Exemplo:** `Endpoint=sb://phoenix-eventhub-dev.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=xxxxxxxxxx=`

### 📊 Monitoring and Observability
```
APPLICATION_INSIGHTS_KEY
```
**Descrição:** Instrumentation Key do Application Insights
**Exemplo:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

```
LOG_ANALYTICS_WORKSPACE_ID
```
**Descrição:** ID do workspace do Log Analytics
**Exemplo:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

```
LOG_ANALYTICS_WORKSPACE_KEY
```
**Descrição:** Chave primária do workspace do Log Analytics
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx==`

### 🔔 Notifications
```
TEAMS_WEBHOOK_URL
```
**Descrição:** URL do webhook do Microsoft Teams para notificações
**Exemplo:** `https://outlook.office.com/webhook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/IncomingWebhook/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

```
SLACK_WEBHOOK_URL
```
**Descrição:** URL do webhook do Slack para notificações
**Exemplo:** `https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX/xxxxxxxxxxxxxxxxxxxxxxxx`

```
PAGERDUTY_INTEGRATION_KEY
```
**Descrição:** Chave de integração do PagerDuty
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 🔧 Azure Functions
```
FUNCTION_KEY
```
**Descrição:** Chave de acesso para as Azure Functions
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx==`

```
FUNCTION_APP_PUBLISH_PROFILE_ORCHESTRATOR
```
**Descrição:** Perfil de publicação da Function App do Orchestrator
**Formato:** XML do publish profile

```
FUNCTION_APP_PUBLISH_PROFILE_DIAGNOSTIC
```
**Descrição:** Perfil de publicação da Function App do Diagnostic
**Formato:** XML do publish profile

```
FUNCTION_APP_PUBLISH_PROFILE_RESOLUTION
```
**Descrição:** Perfil de publicação da Function App do Resolution
**Formato:** XML do publish profile

```
FUNCTION_APP_PUBLISH_PROFILE_COMMUNICATION
```
**Descrição:** Perfil de publicação da Function App do Communication
**Formato:** XML do publish profile

### 🚀 Deployment
```
DEPLOYMENT_APPROVERS
```
**Descrição:** Lista de usuários autorizados a aprovar deployments
**Exemplo:** `user1,user2,user3`

```
KUBECONFIG_DEV
```
**Descrição:** Configuração do kubectl para o ambiente de desenvolvimento
**Formato:** Base64 encoded kubeconfig

```
KUBECONFIG_STAGING
```
**Descrição:** Configuração do kubectl para o ambiente de staging
**Formato:** Base64 encoded kubeconfig

```
KUBECONFIG_PROD
```
**Descrição:** Configuração do kubectl para o ambiente de produção
**Formato:** Base64 encoded kubeconfig

### 🔒 Security
```
SECURITY_SCAN_TOKEN
```
**Descrição:** Token para ferramentas de security scanning
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

```
SONARCLOUD_TOKEN
```
**Descrição:** Token do SonarCloud para análise de código
**Exemplo:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

```
SNYK_TOKEN
```
**Descrição:** Token do Snyk para análise de vulnerabilidades
**Exemplo:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## 🌍 Environment Variables

Configure as seguintes variáveis no GitHub Repository Settings > Secrets and variables > Actions > Variables:

### 🏗️ Infrastructure
```
TERRAFORM_BACKEND_RESOURCE_GROUP=rg-phoenix-tfstate
TERRAFORM_BACKEND_STORAGE_ACCOUNT=phoenixterraformstate
TERRAFORM_BACKEND_CONTAINER_NAME=tfstate
```

### 🐳 Container Registry
```
REGISTRY_NAME=phoenixsystem
REGISTRY_URL=phoenixsystem.azurecr.io
```

### 🌐 Networking
```
VNET_ADDRESS_SPACE=10.0.0.0/16
SUBNET_APP_GATEWAY=10.0.1.0/24
SUBNET_APP_SERVICE=10.0.2.0/24
SUBNET_AKS=10.0.3.0/24
SUBNET_PRIVATE_ENDPOINTS=10.0.4.0/24
```

### 📊 Monitoring
```
ALERT_EMAIL_RECIPIENTS=ops@phoenix-system.com,admin@phoenix-system.com
MONITORING_RETENTION_DAYS=90
LOG_LEVEL=INFO
```

### 🔧 Application Configuration
```
NODE_ENV=production
PYTHON_ENV=production
API_VERSION=v1
MAX_RETRY_ATTEMPTS=3
TIMEOUT_SECONDS=30
```

## 🎯 Environment-Specific Secrets

### Development Environment
Prefixe todos os secrets acima com `DEV_` para o ambiente de desenvolvimento.

### Staging Environment
Prefixe todos os secrets acima com `STAGING_` para o ambiente de staging.

### Production Environment
Prefixe todos os secrets acima com `PROD_` para o ambiente de produção.

## 🔧 Setup Instructions

### 1. Azure Service Principal Creation
```bash
# Criar Service Principal
az ad sp create-for-rbac --name "phoenix-system-github" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Output será usado no secret AZURE_CREDENTIALS
```

### 2. Azure Container Registry Setup
```bash
# Criar Container Registry
az acr create --resource-group rg-phoenix-shared \
  --name phoenixsystem \
  --sku Premium \
  --admin-enabled true

# Obter credenciais
az acr credential show --name phoenixsystem
```

### 3. Azure OpenAI Service Setup
```bash
# Criar Azure OpenAI Service
az cognitiveservices account create \
  --name phoenix-openai-dev \
  --resource-group rg-phoenix-dev \
  --kind OpenAI \
  --sku S0 \
  --location eastus2

# Obter chaves
az cognitiveservices account keys list \
  --name phoenix-openai-dev \
  --resource-group rg-phoenix-dev
```

### 4. Notification Webhooks Setup

#### Microsoft Teams
1. Acesse o canal do Teams
2. Clique em "..." > "Connectors"
3. Configure "Incoming Webhook"
4. Copie a URL gerada

#### Slack
1. Acesse https://api.slack.com/apps
2. Crie uma nova app
3. Configure "Incoming Webhooks"
4. Copie a URL gerada

### 5. PagerDuty Integration
1. Acesse PagerDuty > Services
2. Crie um novo serviço
3. Configure integração "Events API v2"
4. Copie a Integration Key

## 🔍 Validation Script

Use o script de validação para verificar se todos os secrets estão configurados:

```bash
# Executar validação completa
./scripts/validate-secrets.sh

# Ou usar o script integrado no setup
./scripts/setup-workflows.sh
```

### Script Manual de Validação

Se preferir validar manualmente:

```bash
#!/bin/bash
# validate-secrets.sh

REQUIRED_SECRETS=(
  "AZURE_CREDENTIALS"
  "AZURE_SUBSCRIPTION_ID"
  "AZURE_TENANT_ID"
  "AZURE_CLIENT_ID"
  "AZURE_CLIENT_SECRET"
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

echo "🔍 Validating GitHub Secrets..."

for secret in "${REQUIRED_SECRETS[@]}"; do
  if gh secret list | grep -q "$secret"; then
    echo "✅ $secret"
  else
    echo "❌ $secret - MISSING"
  fi
done

echo "🔍 Validation complete!"
```

## 🚨 Security Best Practices

1. **Rotação Regular:** Rotacione secrets a cada 90 dias
2. **Princípio do Menor Privilégio:** Use permissões mínimas necessárias
3. **Monitoramento:** Configure alertas para uso de secrets
4. **Backup:** Mantenha backup seguro dos secrets críticos
5. **Auditoria:** Revise regularmente o acesso aos secrets

## 📞 Support

Para dúvidas sobre configuração de secrets:
- 📧 Email: devops@phoenix-system.com
- 💬 Teams: Phoenix DevOps Channel
- 📖 Wiki: [Internal Documentation](https://wiki.phoenix-system.com/secrets)

---

**⚠️ IMPORTANTE:** Nunca commite secrets no código fonte. Use sempre o GitHub Secrets ou Azure Key Vault.

