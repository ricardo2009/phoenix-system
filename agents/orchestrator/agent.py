"""
Phoenix Orchestrator Agent
Coordena a resposta entre agentes especializados para resolução autônoma de incidentes
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from azure.cosmos import CosmosClient
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from openai import AzureOpenAI


class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class Incident:
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    assigned_agents: List[str]
    resolution_actions: List[Dict[str, Any]]
    estimated_resolution_time: Optional[int] = None
    actual_resolution_time: Optional[int] = None


@dataclass
class AgentResponse:
    agent_id: str
    agent_type: str
    success: bool
    data: Dict[str, Any]
    execution_time: float
    confidence: float
    recommendations: List[str]


class PhoenixOrchestrator:
    """
    Agente Orquestrador do Sistema Phoenix
    
    Responsabilidades:
    - Receber alertas de monitoramento
    - Classificar incidentes por severidade
    - Coordenar agentes especializados
    - Monitorar progresso da resolução
    - Escalar quando necessário
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = f"orchestrator-{uuid.uuid4().hex[:8]}"
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar clientes Azure
        self._init_azure_clients()
        
        # Estado do orquestrador
        self.active_incidents: Dict[str, Incident] = {}
        self.agent_registry = {
            "diagnostic": "func-diag-phoenix-dev",
            "resolution": "func-res-phoenix-dev", 
            "communication": "func-comm-phoenix-dev"
        }
        
        # Configurações de timeout e retry
        self.response_timeout = config.get("response_timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        
    def _init_azure_clients(self):
        """Inicializar clientes dos serviços Azure"""
        try:
            # Cosmos DB para persistência de estado
            self.cosmos_client = CosmosClient(
                self.config["cosmos_endpoint"],
                self.config["cosmos_key"]
            )
            self.database = self.cosmos_client.get_database_client("phoenix-db")
            self.incidents_container = self.database.get_container_client("incidents")
            self.agents_container = self.database.get_container_client("agents-state")
            
            # Event Hub para comunicação entre agentes
            self.event_producer = EventHubProducerClient.from_connection_string(
                self.config["eventhub_connection_string"],
                eventhub_name="incidents"
            )
            
            # Azure OpenAI para análise inteligente
            self.openai_client = AzureOpenAI(
                api_key=self.config["openai_api_key"],
                api_version="2024-02-01",
                azure_endpoint=self.config["openai_endpoint"]
            )
            
            self.logger.info("Azure clients initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure clients: {e}")
            raise
    
    async def process_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Processar alerta de monitoramento e iniciar resposta coordenada
        
        Args:
            alert_data: Dados do alerta recebido
            
        Returns:
            ID do incidente criado
        """
        try:
            # Criar incidente a partir do alerta
            incident = await self._create_incident_from_alert(alert_data)
            
            # Registrar incidente ativo
            self.active_incidents[incident.id] = incident
            
            # Persistir no Cosmos DB
            await self._persist_incident(incident)
            
            # Iniciar coordenação de agentes
            await self._coordinate_response(incident)
            
            self.logger.info(f"Alert processed successfully. Incident ID: {incident.id}")
            return incident.id
            
        except Exception as e:
            self.logger.error(f"Failed to process alert: {e}")
            raise
    
    async def _create_incident_from_alert(self, alert_data: Dict[str, Any]) -> Incident:
        """Criar incidente estruturado a partir dos dados do alerta"""
        
        # Usar IA para classificar severidade e extrair informações
        severity = await self._classify_severity(alert_data)
        
        incident = Incident(
            id=str(uuid.uuid4()),
            title=alert_data.get("title", "Unknown Incident"),
            description=alert_data.get("description", ""),
            severity=severity,
            status=IncidentStatus.DETECTED,
            source=alert_data.get("source", "monitoring"),
            metrics=alert_data.get("metrics", {}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            assigned_agents=[],
            resolution_actions=[]
        )
        
        return incident
    
    async def _classify_severity(self, alert_data: Dict[str, Any]) -> IncidentSeverity:
        """Usar IA para classificar a severidade do incidente"""
        
        try:
            prompt = f"""
            Analise o seguinte alerta e classifique sua severidade:
            
            Título: {alert_data.get('title', 'N/A')}
            Descrição: {alert_data.get('description', 'N/A')}
            Métricas: {json.dumps(alert_data.get('metrics', {}), indent=2)}
            
            Critérios de severidade:
            - CRITICAL: Impacto total no serviço, perda de receita significativa
            - HIGH: Degradação severa, impacto em múltiplos usuários
            - MEDIUM: Degradação moderada, impacto limitado
            - LOW: Problemas menores, sem impacto significativo
            
            Responda apenas com: CRITICAL, HIGH, MEDIUM ou LOW
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            severity_text = response.choices[0].message.content.strip().upper()
            return IncidentSeverity(severity_text.lower())
            
        except Exception as e:
            self.logger.warning(f"Failed to classify severity with AI: {e}")
            # Fallback para classificação baseada em métricas
            return self._fallback_severity_classification(alert_data)
    
    def _fallback_severity_classification(self, alert_data: Dict[str, Any]) -> IncidentSeverity:
        """Classificação de severidade baseada em regras quando IA falha"""
        
        metrics = alert_data.get("metrics", {})
        
        # Regras baseadas em métricas comuns
        cpu_usage = metrics.get("cpu_percentage", 0)
        memory_usage = metrics.get("memory_percentage", 0)
        error_rate = metrics.get("error_rate", 0)
        response_time = metrics.get("avg_response_time", 0)
        
        if cpu_usage > 90 or memory_usage > 95 or error_rate > 50:
            return IncidentSeverity.CRITICAL
        elif cpu_usage > 80 or memory_usage > 85 or error_rate > 20:
            return IncidentSeverity.HIGH
        elif cpu_usage > 70 or memory_usage > 75 or error_rate > 10:
            return IncidentSeverity.MEDIUM
        else:
            return IncidentSeverity.LOW
    
    async def _coordinate_response(self, incident: Incident):
        """Coordenar resposta entre agentes especializados"""
        
        try:
            # Atualizar status
            incident.status = IncidentStatus.ANALYZING
            incident.updated_at = datetime.utcnow()
            
            # Determinar agentes necessários baseado na severidade
            required_agents = self._determine_required_agents(incident)
            incident.assigned_agents = required_agents
            
            # Enviar evento para iniciar análise diagnóstica
            await self._dispatch_to_diagnostic_agent(incident)
            
            # Iniciar monitoramento do progresso
            asyncio.create_task(self._monitor_incident_progress(incident))
            
            self.logger.info(f"Response coordination initiated for incident {incident.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to coordinate response: {e}")
            await self._escalate_incident(incident, f"Coordination failed: {e}")
    
    def _determine_required_agents(self, incident: Incident) -> List[str]:
        """Determinar quais agentes são necessários baseado no incidente"""
        
        agents = ["diagnostic"]  # Sempre iniciar com diagnóstico
        
        if incident.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            agents.extend(["resolution", "communication"])
        elif incident.severity == IncidentSeverity.MEDIUM:
            agents.append("communication")
        
        return agents
    
    async def _dispatch_to_diagnostic_agent(self, incident: Incident):
        """Enviar incidente para o agente de diagnóstico"""
        
        event_data = {
            "event_type": "incident_analysis_request",
            "incident_id": incident.id,
            "incident_data": asdict(incident),
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
        
        self.logger.info(f"Incident {incident.id} dispatched to diagnostic agent")
    
    async def _monitor_incident_progress(self, incident: Incident):
        """Monitorar progresso da resolução do incidente"""
        
        start_time = datetime.utcnow()
        timeout = timedelta(seconds=self.response_timeout)
        
        while incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.ESCALATED]:
            if datetime.utcnow() - start_time > timeout:
                await self._escalate_incident(incident, "Response timeout exceeded")
                break
            
            # Verificar atualizações no Cosmos DB
            try:
                updated_incident = await self._get_incident_from_db(incident.id)
                if updated_incident:
                    self.active_incidents[incident.id] = updated_incident
                    incident = updated_incident
            except Exception as e:
                self.logger.error(f"Failed to check incident status: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def _escalate_incident(self, incident: Incident, reason: str):
        """Escalar incidente para intervenção humana"""
        
        incident.status = IncidentStatus.ESCALATED
        incident.updated_at = datetime.utcnow()
        
        # Notificar agente de comunicação sobre escalação
        if "communication" in incident.assigned_agents:
            await self._notify_escalation(incident, reason)
        
        await self._persist_incident(incident)
        
        self.logger.warning(f"Incident {incident.id} escalated: {reason}")
    
    async def _notify_escalation(self, incident: Incident, reason: str):
        """Notificar sobre escalação via agente de comunicação"""
        
        event_data = {
            "event_type": "incident_escalation",
            "incident_id": incident.id,
            "reason": reason,
            "incident_data": asdict(incident),
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
    
    async def _persist_incident(self, incident: Incident):
        """Persistir incidente no Cosmos DB"""
        
        try:
            incident_dict = asdict(incident)
            incident_dict["id"] = incident.id
            incident_dict["incidentId"] = incident.id  # Partition key
            
            # Converter datetime para string
            incident_dict["created_at"] = incident.created_at.isoformat()
            incident_dict["updated_at"] = incident.updated_at.isoformat()
            incident_dict["severity"] = incident.severity.value
            incident_dict["status"] = incident.status.value
            
            self.incidents_container.upsert_item(incident_dict)
            
        except Exception as e:
            self.logger.error(f"Failed to persist incident: {e}")
            raise
    
    async def _get_incident_from_db(self, incident_id: str) -> Optional[Incident]:
        """Recuperar incidente do Cosmos DB"""
        
        try:
            item = self.incidents_container.read_item(
                item=incident_id,
                partition_key=incident_id
            )
            
            # Converter de volta para objeto Incident
            incident = Incident(
                id=item["id"],
                title=item["title"],
                description=item["description"],
                severity=IncidentSeverity(item["severity"]),
                status=IncidentStatus(item["status"]),
                source=item["source"],
                metrics=item["metrics"],
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                assigned_agents=item["assigned_agents"],
                resolution_actions=item["resolution_actions"],
                estimated_resolution_time=item.get("estimated_resolution_time"),
                actual_resolution_time=item.get("actual_resolution_time")
            )
            
            return incident
            
        except Exception as e:
            self.logger.error(f"Failed to get incident from DB: {e}")
            return None
    
    async def handle_agent_response(self, response_data: Dict[str, Any]):
        """Processar resposta de agente especializado"""
        
        try:
            incident_id = response_data.get("incident_id")
            agent_type = response_data.get("agent_type")
            
            if incident_id not in self.active_incidents:
                self.logger.warning(f"Received response for unknown incident: {incident_id}")
                return
            
            incident = self.active_incidents[incident_id]
            
            # Processar resposta baseado no tipo de agente
            if agent_type == "diagnostic":
                await self._handle_diagnostic_response(incident, response_data)
            elif agent_type == "resolution":
                await self._handle_resolution_response(incident, response_data)
            elif agent_type == "communication":
                await self._handle_communication_response(incident, response_data)
            
        except Exception as e:
            self.logger.error(f"Failed to handle agent response: {e}")
    
    async def _handle_diagnostic_response(self, incident: Incident, response_data: Dict[str, Any]):
        """Processar resposta do agente de diagnóstico"""
        
        diagnosis = response_data.get("diagnosis", {})
        confidence = response_data.get("confidence", 0.0)
        
        if confidence >= 0.8:  # Alta confiança no diagnóstico
            # Iniciar resolução automática
            if "resolution" in incident.assigned_agents:
                await self._dispatch_to_resolution_agent(incident, diagnosis)
            else:
                # Apenas notificar se resolução não foi atribuída
                if "communication" in incident.assigned_agents:
                    await self._dispatch_to_communication_agent(incident, "diagnosis_complete")
        else:
            # Baixa confiança - escalar
            await self._escalate_incident(incident, f"Low diagnostic confidence: {confidence}")
    
    async def _dispatch_to_resolution_agent(self, incident: Incident, diagnosis: Dict[str, Any]):
        """Enviar para agente de resolução"""
        
        event_data = {
            "event_type": "resolution_request",
            "incident_id": incident.id,
            "diagnosis": diagnosis,
            "incident_data": asdict(incident),
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
    
    async def _dispatch_to_communication_agent(self, incident: Incident, event_type: str):
        """Enviar para agente de comunicação"""
        
        event_data = {
            "event_type": event_type,
            "incident_id": incident.id,
            "incident_data": asdict(incident),
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
    
    async def _handle_resolution_response(self, incident: Incident, response_data: Dict[str, Any]):
        """Processar resposta do agente de resolução"""
        
        success = response_data.get("success", False)
        actions_taken = response_data.get("actions_taken", [])
        
        incident.resolution_actions.extend(actions_taken)
        
        if success:
            incident.status = IncidentStatus.RESOLVED
            incident.actual_resolution_time = int(
                (datetime.utcnow() - incident.created_at).total_seconds()
            )
            
            # Notificar resolução
            if "communication" in incident.assigned_agents:
                await self._dispatch_to_communication_agent(incident, "incident_resolved")
        else:
            # Resolução falhou - escalar
            await self._escalate_incident(incident, "Automatic resolution failed")
        
        await self._persist_incident(incident)
    
    async def _handle_communication_response(self, incident: Incident, response_data: Dict[str, Any]):
        """Processar resposta do agente de comunicação"""
        
        # Agente de comunicação geralmente não requer ação do orquestrador
        # Apenas log para auditoria
        self.logger.info(f"Communication agent processed incident {incident.id}")
    
    def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Obter status atual de um incidente"""
        
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            return {
                "id": incident.id,
                "status": incident.status.value,
                "severity": incident.severity.value,
                "created_at": incident.created_at.isoformat(),
                "updated_at": incident.updated_at.isoformat(),
                "assigned_agents": incident.assigned_agents,
                "resolution_actions": incident.resolution_actions
            }
        
        return None
    
    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """Obter lista de incidentes ativos"""
        
        return [
            self.get_incident_status(incident_id)
            for incident_id in self.active_incidents.keys()
        ]


# Função para criar instância do orquestrador
def create_orchestrator(config: Dict[str, Any]) -> PhoenixOrchestrator:
    """Factory function para criar instância do orquestrador"""
    return PhoenixOrchestrator(config)

