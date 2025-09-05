"""
Phoenix Agents - Configuration Management
Configuração centralizada para todos os agentes do sistema Phoenix
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class AgentConfig:
    """Configuração base para agentes Phoenix"""
    
    # Azure Services
    cosmos_endpoint: str
    cosmos_key: str
    eventhub_connection_string: str
    subscription_id: str
    resource_group: str
    
    # AI Services
    openai_api_key: str
    openai_endpoint: str
    
    # Monitoring
    log_analytics_workspace_id: str
    
    # Communication
    teams_webhook_url: Optional[str] = None
    communication_services_connection_string: Optional[str] = None
    webhook_url: Optional[str] = None
    
    # Agent-specific settings
    agent_settings: Dict[str, Any] = None


class ConfigManager:
    """Gerenciador de configuração para agentes Phoenix"""
    
    def __init__(self):
        self._config_cache: Dict[str, Any] = {}
        self._load_environment_config()
    
    def _load_environment_config(self):
        """Carregar configuração das variáveis de ambiente"""
        
        # Configurações obrigatórias
        required_vars = [
            "COSMOS_DB_ENDPOINT",
            "COSMOS_DB_KEY", 
            "EVENTHUB_CONNECTION_STRING",
            "AZURE_SUBSCRIPTION_ID",
            "RESOURCE_GROUP_NAME",
            "OPENAI_API_KEY",
            "OPENAI_ENDPOINT",
            "LOG_ANALYTICS_WORKSPACE_ID"
        ]
        
        # Verificar se todas as variáveis obrigatórias estão definidas
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Carregar configurações
        self._config_cache = {
            "cosmos_endpoint": os.getenv("COSMOS_DB_ENDPOINT"),
            "cosmos_key": os.getenv("COSMOS_DB_KEY"),
            "eventhub_connection_string": os.getenv("EVENTHUB_CONNECTION_STRING"),
            "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
            "resource_group": os.getenv("RESOURCE_GROUP_NAME"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "openai_endpoint": os.getenv("OPENAI_ENDPOINT"),
            "log_analytics_workspace_id": os.getenv("LOG_ANALYTICS_WORKSPACE_ID"),
            
            # Configurações opcionais
            "teams_webhook_url": os.getenv("TEAMS_WEBHOOK_URL"),
            "communication_services_connection_string": os.getenv("COMMUNICATION_SERVICES_CONNECTION_STRING"),
            "webhook_url": os.getenv("WEBHOOK_URL"),
            
            # Configurações específicas de recursos
            "app_service_name": os.getenv("APP_SERVICE_NAME"),
            "app_service_plan": os.getenv("APP_SERVICE_PLAN"),
            "database_name": os.getenv("DATABASE_NAME", "phoenix-db"),
            
            # Configurações de agentes
            "orchestrator": {
                "response_timeout": int(os.getenv("ORCHESTRATOR_RESPONSE_TIMEOUT", "30")),
                "max_retries": int(os.getenv("ORCHESTRATOR_MAX_RETRIES", "3"))
            },
            "diagnostic": {
                "analysis_timeout": int(os.getenv("DIAGNOSTIC_ANALYSIS_TIMEOUT", "60")),
                "confidence_threshold": float(os.getenv("DIAGNOSTIC_CONFIDENCE_THRESHOLD", "0.85"))
            },
            "resolution": {
                "execution_timeout": int(os.getenv("RESOLUTION_EXECUTION_TIMEOUT", "120")),
                "rollback_enabled": os.getenv("RESOLUTION_ROLLBACK_ENABLED", "true").lower() == "true"
            },
            "communication": {
                "escalation_timeout": int(os.getenv("COMMUNICATION_ESCALATION_TIMEOUT", "300")),
                "notification_channels": os.getenv("NOTIFICATION_CHANNELS", "teams,email").split(",")
            }
        }
    
    def get_agent_config(self, agent_type: str) -> AgentConfig:
        """Obter configuração para um tipo específico de agente"""
        
        base_config = {
            "cosmos_endpoint": self._config_cache["cosmos_endpoint"],
            "cosmos_key": self._config_cache["cosmos_key"],
            "eventhub_connection_string": self._config_cache["eventhub_connection_string"],
            "subscription_id": self._config_cache["subscription_id"],
            "resource_group": self._config_cache["resource_group"],
            "openai_api_key": self._config_cache["openai_api_key"],
            "openai_endpoint": self._config_cache["openai_endpoint"],
            "log_analytics_workspace_id": self._config_cache["log_analytics_workspace_id"],
            "teams_webhook_url": self._config_cache.get("teams_webhook_url"),
            "communication_services_connection_string": self._config_cache.get("communication_services_connection_string"),
            "webhook_url": self._config_cache.get("webhook_url")
        }
        
        # Adicionar configurações específicas do agente
        agent_settings = self._config_cache.get(agent_type, {})
        base_config["agent_settings"] = agent_settings
        
        # Adicionar configurações específicas de recursos
        base_config.update({
            "app_service_name": self._config_cache.get("app_service_name"),
            "app_service_plan": self._config_cache.get("app_service_plan"),
            "database_name": self._config_cache.get("database_name")
        })
        
        return AgentConfig(**base_config)
    
    def get_config_dict(self, agent_type: str) -> Dict[str, Any]:
        """Obter configuração como dicionário"""
        config = self.get_agent_config(agent_type)
        
        # Converter para dicionário, incluindo configurações específicas
        config_dict = {
            "cosmos_endpoint": config.cosmos_endpoint,
            "cosmos_key": config.cosmos_key,
            "eventhub_connection_string": config.eventhub_connection_string,
            "subscription_id": config.subscription_id,
            "resource_group": config.resource_group,
            "openai_api_key": config.openai_api_key,
            "openai_endpoint": config.openai_endpoint,
            "log_analytics_workspace_id": config.log_analytics_workspace_id,
            "teams_webhook_url": config.teams_webhook_url,
            "communication_services_connection_string": config.communication_services_connection_string,
            "webhook_url": config.webhook_url,
            "app_service_name": getattr(config, 'app_service_name', None),
            "app_service_plan": getattr(config, 'app_service_plan', None),
            "database_name": getattr(config, 'database_name', 'phoenix-db')
        }
        
        # Adicionar configurações específicas do agente
        if config.agent_settings:
            config_dict.update(config.agent_settings)
        
        return config_dict
    
    def validate_config(self, agent_type: str) -> bool:
        """Validar configuração para um tipo de agente"""
        
        try:
            config = self.get_agent_config(agent_type)
            
            # Verificar configurações obrigatórias
            required_fields = [
                "cosmos_endpoint", "cosmos_key", "eventhub_connection_string",
                "subscription_id", "resource_group", "openai_api_key", 
                "openai_endpoint", "log_analytics_workspace_id"
            ]
            
            for field in required_fields:
                value = getattr(config, field)
                if not value:
                    print(f"Missing required configuration: {field}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def get_environment_template(self) -> str:
        """Obter template de variáveis de ambiente"""
        
        template = """
# Phoenix System - Environment Variables Template
# Copy this file to .env and fill in the values

# Azure Cosmos DB
COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-primary-key

# Azure Event Hub
EVENTHUB_CONNECTION_STRING=Endpoint=sb://your-eventhub.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=your-key

# Azure Subscription
AZURE_SUBSCRIPTION_ID=your-subscription-id
RESOURCE_GROUP_NAME=rg-phoenix-dev-xxxxxx

# Azure OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/

# Azure Monitor
LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id

# Communication Services (Optional)
TEAMS_WEBHOOK_URL=https://your-teams-webhook-url
COMMUNICATION_SERVICES_CONNECTION_STRING=endpoint=https://your-communication-service.communication.azure.com/;accesskey=your-key
WEBHOOK_URL=https://your-webhook-endpoint

# Resource Names
APP_SERVICE_NAME=app-phoenix-dev-xxxxxx
APP_SERVICE_PLAN=asp-phoenix-dev-xxxxxx
DATABASE_NAME=phoenix-db

# Agent Configuration (Optional - defaults will be used if not specified)
ORCHESTRATOR_RESPONSE_TIMEOUT=30
ORCHESTRATOR_MAX_RETRIES=3
DIAGNOSTIC_ANALYSIS_TIMEOUT=60
DIAGNOSTIC_CONFIDENCE_THRESHOLD=0.85
RESOLUTION_EXECUTION_TIMEOUT=120
RESOLUTION_ROLLBACK_ENABLED=true
COMMUNICATION_ESCALATION_TIMEOUT=300
NOTIFICATION_CHANNELS=teams,email
        """
        
        return template.strip()


# Instância global do gerenciador de configuração
config_manager = ConfigManager()


def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """Função de conveniência para obter configuração de agente"""
    return config_manager.get_config_dict(agent_type)


def validate_agent_config(agent_type: str) -> bool:
    """Função de conveniência para validar configuração de agente"""
    return config_manager.validate_config(agent_type)


# Configurações específicas para cada tipo de agente
AGENT_DEFAULTS = {
    "orchestrator": {
        "response_timeout": 30,
        "max_retries": 3,
        "escalation_timeout": 300
    },
    "diagnostic": {
        "analysis_timeout": 60,
        "confidence_threshold": 0.85,
        "max_log_entries": 1000,
        "anomaly_detection_threshold": 2.0
    },
    "resolution": {
        "execution_timeout": 120,
        "rollback_enabled": True,
        "max_scale_instances": 20,
        "cooldown_period": 300
    },
    "communication": {
        "escalation_timeout": 300,
        "notification_channels": ["teams", "email"],
        "max_retries": 3,
        "retry_delay": 30
    }
}

