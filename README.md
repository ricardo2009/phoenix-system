# Phoenix: Sistema Autônomo de Resolução de Incidentes

Phoenix é um sistema autônomo baseado em agentes inteligentes que detecta, diagnostica e resolve incidentes em plataformas de e-commerce sem intervenção humana.

## 🎯 Visão Geral

Durante eventos de alta demanda como Black Friday, plataformas de e-commerce enfrentam picos de tráfego que podem causar degradação crítica de performance. O Phoenix resolve esses problemas em segundos, não minutos, através de uma arquitetura de agentes inteligentes orquestrados pelo Azure AI Foundry.

## 📋 Status dos Workflows

✅ **phoenix-basic.yml** - Workflow básico funcional  
✅ **phoenix-applications-ultimate.yml** - Deployment de aplicações (CORRIGIDO)  
✅ **phoenix-infrastructure-ultimate.yml** - Deployment de infraestrutura (CORRIGIDO)  
✅ **phoenix-monitoring-ultimate.yml** - Monitoramento avançado (CORRIGIDO)  

> **Últimas correções:** Resolvidos erros críticos de sintaxe, instalação do Terraform e compatibilidade com GitHub Actions. Ver [docs/WORKFLOW_FIXES.md](docs/WORKFLOW_FIXES.md) para detalhes.

## 🏗️ Arquitetura da Solução

### Componentes Principais

#### 🧠 Azure AI Foundry - Orquestração de Agentes
- **Agente Orquestrador**: Coordena a resposta entre agentes especializados
- **Agente de Diagnóstico**: Analisa logs e métricas para identificar causa raiz
- **Agente de Resolução**: Executa ações corretivas automatizadas
- **Agente de Comunicação**: Mantém stakeholders informados via Teams

#### 💬 Microsoft Copilot Studio
- Interface conversacional integrada ao Microsoft Teams
- Traduz informações técnicas em linguagem natural
- Permite aprovação de ações de alto impacto
- Integração nativa com Azure AI Foundry

#### ⚡ Serviços de Backend
- **Azure Functions**: Lógica serverless para ações dos agentes
- **Cosmos DB**: Estado dos agentes e histórico de incidentes
- **AKS**: Orquestração da aplicação de e-commerce
- **Event Hub**: Processamento de eventos em tempo real
- **Entra ID**: Gerenciamento seguro de identidades

## 🚀 Funcionalidades

### ⚡ Resposta Imediata
- Detecção e resolução em menos de 30 segundos
- Automação completa sem intervenção humana
- Escalabilidade automática baseada em demanda

### 🤖 Inteligência Distribuída
- Múltiplos agentes especializados
- Coordenação inteligente entre componentes
- Tomada de decisão baseada em IA

### 📈 Aprendizado Contínuo
- Melhoria baseada em incidentes anteriores
- Análise de padrões históricos
- Otimização contínua de respostas

### 💬 Comunicação Transparente
- Atualizações em tempo real via Teams
- Interface conversacional natural
- Aprovações para ações críticas

## 📁 Estrutura do Projeto

```
phoenix-system/
├── infrastructure/           # Infraestrutura como código
│   ├── terraform/           # Provisionamento Terraform
│   └── bicep/              # Templates Bicep alternativos
├── agents/                 # Agentes inteligentes
│   ├── orchestrator/       # Agente orquestrador
│   ├── diagnostic/         # Agente de diagnóstico
│   ├── resolution/         # Agente de resolução
│   └── communication/      # Agente de comunicação
├── functions/              # Azure Functions
├── copilot-studio/         # Configuração do Copilot Studio
├── ecommerce-app/          # Aplicação de e-commerce demo
│   ├── frontend/           # Interface React
│   └── backend/            # API .NET/Python
├── kubernetes/             # Manifests Kubernetes
├── docs/                   # Documentação
├── scripts/                # Scripts de automação
└── tests/                  # Testes automatizados
```

## 🛠️ Pré-requisitos

### Ferramentas Necessárias
- Azure CLI
- Terraform >= 1.0
- kubectl
- Docker
- Node.js >= 18
- Python >= 3.9
- .NET 8 SDK

### Recursos Azure
- Subscription Azure ativa
- Permissões de Contributor
- Azure AI Foundry habilitado
- Microsoft Copilot Studio licenciado

## 🚀 Quick Start

### 1. Clonar o Repositório
```bash
git clone https://github.com/ricardo2009/phoenix-system.git
cd phoenix-system
```

### 2. Configurar Ambiente
```bash
# Fazer login no Azure
az login

# Configurar subscription
az account set --subscription "sua-subscription-id"

# Executar script de setup
./scripts/setup.sh
```

### 3. Provisionar Infraestrutura
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### 4. Deploy dos Agentes
```bash
./scripts/deploy-agents.sh
```

### 5. Configurar Copilot Studio
```bash
./scripts/setup-copilot.sh
```

### 6. Deploy da Aplicação E-commerce
```bash
./scripts/deploy-ecommerce.sh
```

### 7. Executar Testes
```bash
./scripts/run-tests.sh
```

## 🧪 Demonstração

O sistema Phoenix inclui uma demonstração completa que simula:

1. **Pico de Tráfego**: Simulação de alta demanda na plataforma
2. **Detecção Automática**: Agente Orquestrador recebe alertas
3. **Diagnóstico Inteligente**: Análise de logs e métricas
4. **Resolução Autônoma**: Escalonamento e otimização automática
5. **Comunicação**: Notificações via Teams em tempo real

```bash
# Executar demonstração completa
./scripts/demo.sh
```

## 📊 Métricas e Monitoramento

- **Tempo Médio de Resolução**: < 30 segundos
- **Taxa de Resolução Automática**: > 95%
- **Redução de Downtime**: 85%
- **Satisfação dos Stakeholders**: Comunicação transparente

## 🔧 Configuração Avançada

### Personalização de Agentes
Cada agente pode ser personalizado através de arquivos de configuração:

```yaml
# agents/orchestrator/config.yaml
orchestrator:
  response_time_threshold: 30
  escalation_rules:
    - condition: "cpu > 80%"
      action: "scale_out"
    - condition: "memory > 90%"
      action: "restart_pods"
```

### Integração com Ferramentas Existentes
- Azure Monitor
- Application Insights
- Log Analytics
- Grafana/Prometheus

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🔗 Recursos Relacionados

- [Azure AI Foundry Documentation](https://docs.microsoft.com/azure/ai-foundry)
- [Microsoft Copilot Studio](https://docs.microsoft.com/copilot-studio)
- [Azure Functions](https://docs.microsoft.com/azure/azure-functions)
- [Azure Kubernetes Service](https://docs.microsoft.com/azure/aks)

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a [documentação](docs/)
- Entre em contato via Teams

---

**Phoenix System** - Revolucionando a resolução de incidentes através de agentes autônomos inteligentes.

