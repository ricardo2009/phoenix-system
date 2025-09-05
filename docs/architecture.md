# Arquitetura do Sistema Phoenix

## Visão Geral da Arquitetura

O sistema Phoenix implementa uma arquitetura de microserviços distribuída na Azure, com agentes inteligentes orquestrados pelo Azure AI Foundry para resolução autônoma de incidentes.

## Diagrama da Arquitetura

```mermaid
graph TB
    %% External
    Internet[🌐 Internet Sources]
    Users[👥 Users]
    
    %% Virtual Network
    subgraph VNet["🔷 Virtual Network"]
        %% Application Gateway Subnet
        subgraph AGWSubnet["Application Gateway Subnet"]
            AGW[🚪 Application Gateway<br/>with Azure WAF]
        end
        
        %% App Service Integration Subnet
        subgraph AppSubnet["App Service Integration Subnet"]
            AppSvc[⚡ App Service<br/>Managed Identity]
            
            %% Private Endpoints
            subgraph PrivateEndpoints["Private Endpoints"]
                PE1[🔒 Key Vault<br/>private endpoint]
                PE2[🔒 Storage<br/>private endpoint]
                PE3[🔒 Azure AI Foundry<br/>private endpoint]
                PE4[🔒 Azure AI Search<br/>private endpoint]
                PE5[🔒 Azure Cosmos DB<br/>private endpoint]
                PE6[🔒 Storage<br/>private endpoint]
                PE7[🔒 Knowledge store<br/>private endpoint]
            end
        end
        
        %% Azure AI Agent Integration Subnet
        subgraph AISubnet["Azure AI Agent Integration Subnet"]
            AIFoundry[🧠 Azure AI Foundry<br/>Foundry Agent Service]
            Firewall[🛡️ Azure Firewall<br/>Outbound traffic]
        end
        
        %% Azure Bastion Subnet
        subgraph BastionSubnet["Azure Bastion Subnet"]
            Bastion[🔐 Azure Bastion<br/>Jump box]
        end
        
        %% Build Agents Subnet
        subgraph BuildSubnet["Build Agents Subnet"]
            BuildAgents[🔨 Build agents]
        end
    end
    
    %% External Services
    subgraph ExternalServices["External Services"]
        KeyVault[🔑 Azure Key Vault]
        Storage[💾 Azure Storage]
        AISearch[🔍 Azure AI Search]
        CosmosDB[🗄️ Azure Cosmos DB]
        KnowledgeStore[📚 Knowledge Store]
    end
    
    %% Azure AI Foundry Components
    subgraph AIFoundryServices["🧠 Azure AI Foundry"]
        FoundryAccount[Azure AI Foundry Account]
        FoundryProject[Azure AI Foundry Project]
        OpenAIModel[Azure OpenAI Model]
        ManagedIdentity[Managed Identities]
    end
    
    %% Monitoring
    subgraph Monitoring["📊 Monitoring"]
        AppInsights[Application Insights]
        AzureMonitor[Azure Monitor]
    end
    
    %% DNS and Identity
    subgraph Identity["🔐 Identity & DNS"]
        PrivateDNS[Private DNS zones]
        EntraID[Microsoft Entra ID]
    end
    
    %% Connections
    Internet --> AGW
    Users --> AGW
    AGW --> AppSvc
    
    AppSvc --> PE1
    AppSvc --> PE2
    AppSvc --> PE3
    AppSvc --> PE4
    AppSvc --> PE5
    AppSvc --> PE6
    AppSvc --> PE7
    
    PE1 --> KeyVault
    PE2 --> Storage
    PE3 --> AIFoundry
    PE4 --> AISearch
    PE5 --> CosmosDB
    PE6 --> Storage
    PE7 --> KnowledgeStore
    
    AIFoundry --> FoundryAccount
    FoundryAccount --> FoundryProject
    FoundryProject --> OpenAIModel
    FoundryProject --> ManagedIdentity
    
    Firewall --> Internet
    AIFoundry --> Firewall
    
    AppSvc --> AppInsights
    AIFoundry --> AzureMonitor
    
    %% Styling
    classDef subnet fill:#e1f5fe
    classDef service fill:#f3e5f5
    classDef ai fill:#e8f5e8
    classDef security fill:#fff3e0
    classDef storage fill:#fce4ec
    
    class AGWSubnet,AppSubnet,AISubnet,BastionSubnet,BuildSubnet subnet
    class AppSvc,AGW,Bastion,BuildAgents service
    class AIFoundry,FoundryAccount,FoundryProject,OpenAIModel ai
    class Firewall,EntraID,PrivateDNS,KeyVault security
    class Storage,CosmosDB,KnowledgeStore,AISearch storage
```

## Componentes da Arquitetura

### 1. Camada de Rede (Virtual Network)

#### Application Gateway Subnet
- **Application Gateway com WAF**: Ponto de entrada para tráfego externo
- **Azure WAF**: Proteção contra ataques web comuns
- **Load Balancing**: Distribuição de tráfego

#### App Service Integration Subnet
- **App Service**: Hospedagem da aplicação principal
- **Managed Identity**: Autenticação segura sem credenciais
- **Private Endpoints**: Conectividade privada com serviços Azure

#### Azure AI Agent Integration Subnet
- **Azure AI Foundry**: Orquestração dos agentes inteligentes
- **Foundry Agent Service**: Execução dos agentes especializados
- **Azure Firewall**: Controle de tráfego de saída

### 2. Agentes Inteligentes

#### Agente Orquestrador
```python
# Exemplo de configuração
orchestrator_config = {
    "name": "Phoenix Orchestrator",
    "triggers": ["performance_alert", "error_spike", "resource_exhaustion"],
    "coordination_strategy": "priority_based",
    "escalation_timeout": 30
}
```

#### Agente de Diagnóstico
```python
diagnostic_config = {
    "name": "Phoenix Diagnostic",
    "data_sources": ["app_insights", "log_analytics", "metrics"],
    "analysis_models": ["anomaly_detection", "root_cause_analysis"],
    "confidence_threshold": 0.85
}
```

#### Agente de Resolução
```python
resolution_config = {
    "name": "Phoenix Resolution",
    "actions": ["scale_out", "restart_service", "clear_cache", "optimize_queries"],
    "approval_required": ["scale_beyond_limit", "restart_critical_service"],
    "rollback_strategy": "automatic"
}
```

#### Agente de Comunicação
```python
communication_config = {
    "name": "Phoenix Communication",
    "channels": ["teams", "email", "slack"],
    "message_templates": ["incident_detected", "resolution_in_progress", "incident_resolved"],
    "stakeholder_groups": ["ops_team", "dev_team", "management"]
}
```

### 3. Serviços de Dados

#### Azure Cosmos DB
- **Armazenamento de Estado**: Estado atual dos agentes
- **Histórico de Incidentes**: Dados para aprendizado contínuo
- **Configurações**: Parâmetros dos agentes
- **Métricas**: KPIs e performance

#### Azure AI Search
- **Indexação de Logs**: Busca inteligente em logs
- **Knowledge Base**: Base de conhecimento para diagnósticos
- **Semantic Search**: Busca semântica em documentação

#### Azure Storage
- **Artifacts**: Armazenamento de modelos e configurações
- **Backups**: Backup de configurações críticas
- **Logs**: Armazenamento de longo prazo

### 4. Segurança e Identidade

#### Microsoft Entra ID
- **Identidades Gerenciadas**: Autenticação sem credenciais
- **RBAC**: Controle de acesso baseado em funções
- **Conditional Access**: Políticas de acesso condicional

#### Azure Key Vault
- **Secrets**: Chaves de API e conexões
- **Certificates**: Certificados SSL/TLS
- **Keys**: Chaves de criptografia

#### Private Endpoints
- **Conectividade Privada**: Tráfego não passa pela internet pública
- **Isolamento de Rede**: Segmentação de rede
- **DNS Privado**: Resolução de nomes privada

### 5. Monitoramento e Observabilidade

#### Application Insights
- **Telemetria**: Métricas de aplicação
- **Distributed Tracing**: Rastreamento de requisições
- **Custom Metrics**: Métricas específicas dos agentes

#### Azure Monitor
- **Alertas**: Configuração de alertas automáticos
- **Dashboards**: Visualização de métricas
- **Log Analytics**: Análise de logs centralizados

## Fluxo de Dados

### 1. Detecção de Incidente
```mermaid
sequenceDiagram
    participant Monitor as Azure Monitor
    participant Orch as Agente Orquestrador
    participant Diag as Agente Diagnóstico
    participant Res as Agente Resolução
    participant Comm as Agente Comunicação
    
    Monitor->>Orch: Alert: High CPU Usage
    Orch->>Diag: Analyze incident
    Diag->>Diag: Query logs & metrics
    Diag->>Orch: Root cause identified
    Orch->>Res: Execute resolution
    Res->>Res: Scale out services
    Orch->>Comm: Notify stakeholders
    Comm->>Comm: Send Teams message
```

### 2. Resolução Automática
```mermaid
graph LR
    A[Incident Detected] --> B[Orchestrator Activated]
    B --> C[Diagnostic Analysis]
    C --> D{Root Cause Found?}
    D -->|Yes| E[Resolution Actions]
    D -->|No| F[Escalate to Human]
    E --> G[Monitor Results]
    G --> H{Issue Resolved?}
    H -->|Yes| I[Notify Success]
    H -->|No| J[Try Alternative]
    J --> E
    I --> K[Update Knowledge Base]
```

## Padrões de Implementação

### 1. Event-Driven Architecture
- **Event Hub**: Processamento de eventos em tempo real
- **Service Bus**: Mensageria confiável entre componentes
- **Event Grid**: Roteamento de eventos

### 2. Microservices Pattern
- **Containerização**: Docker containers no AKS
- **Service Mesh**: Istio para comunicação segura
- **API Gateway**: Centralização de APIs

### 3. CQRS e Event Sourcing
- **Command Query Separation**: Separação de leitura e escrita
- **Event Store**: Histórico completo de eventos
- **Projections**: Views otimizadas para consulta

## Considerações de Segurança

### 1. Zero Trust Network
- **Verificação Contínua**: Validação de identidade e dispositivo
- **Least Privilege**: Acesso mínimo necessário
- **Micro-segmentation**: Isolamento de componentes

### 2. Encryption
- **Data at Rest**: Criptografia de dados armazenados
- **Data in Transit**: TLS/SSL para comunicação
- **Key Management**: Azure Key Vault para chaves

### 3. Compliance
- **GDPR**: Proteção de dados pessoais
- **SOC 2**: Controles de segurança
- **ISO 27001**: Gestão de segurança da informação

## Escalabilidade e Performance

### 1. Auto Scaling
- **Horizontal Scaling**: Adição de instâncias
- **Vertical Scaling**: Aumento de recursos
- **Predictive Scaling**: Baseado em padrões históricos

### 2. Caching Strategy
- **Redis Cache**: Cache distribuído
- **CDN**: Content Delivery Network
- **Application Cache**: Cache local da aplicação

### 3. Database Optimization
- **Partitioning**: Distribuição de dados
- **Indexing**: Otimização de consultas
- **Read Replicas**: Distribuição de leitura

