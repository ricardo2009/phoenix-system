"""
Phoenix Communication Agent
Mantém stakeholders informados via Teams, email e outros canais
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
import aiohttp

from azure.cosmos import CosmosClient
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from azure.identity import DefaultAzureCredential
from azure.communication.email import EmailClient
import requests


class MessageType(Enum):
    INCIDENT_DETECTED = "incident_detected"
    DIAGNOSIS_COMPLETE = "diagnosis_complete"
    RESOLUTION_IN_PROGRESS = "resolution_in_progress"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_ESCALATED = "incident_escalated"
    APPROVAL_REQUEST = "approval_request"
    STATUS_UPDATE = "status_update"


class NotificationChannel(Enum):
    TEAMS = "teams"
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Stakeholder:
    id: str
    name: str
    email: str
    role: str
    teams_id: Optional[str] = None
    phone: Optional[str] = None
    notification_preferences: List[NotificationChannel] = None
    escalation_level: int = 1


@dataclass
class NotificationTemplate:
    message_type: MessageType
    channel: NotificationChannel
    subject_template: str
    body_template: str
    priority: Priority


class PhoenixCommunicationAgent:
    """
    Agente de Comunicação do Sistema Phoenix
    
    Responsabilidades:
    - Notificar stakeholders sobre incidentes
    - Enviar atualizações de status em tempo real
    - Solicitar aprovações para ações críticas
    - Escalar comunicações quando necessário
    - Manter histórico de comunicações
    - Traduzir informações técnicas para linguagem de negócio
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = f"communication-{uuid.uuid4().hex[:8]}"
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar clientes Azure
        self._init_azure_clients()
        
        # Configurações de comunicação
        self.escalation_timeout = config.get("escalation_timeout", 300)  # 5 minutos
        self.notification_channels = config.get("notification_channels", ["teams", "email"])
        
        # Carregar stakeholders e templates
        self.stakeholders = self._load_stakeholders()
        self.templates = self._load_notification_templates()
        
        # Histórico de notificações
        self.notification_history: Dict[str, List[Dict[str, Any]]] = {}
        
    def _init_azure_clients(self):
        """Inicializar clientes dos serviços Azure"""
        try:
            # Cosmos DB para persistência
            self.cosmos_client = CosmosClient(
                self.config["cosmos_endpoint"],
                self.config["cosmos_key"]
            )
            self.database = self.cosmos_client.get_database_client("phoenix-db")
            self.incidents_container = self.database.get_container_client("incidents")
            
            # Event Hub para comunicação
            self.event_producer = EventHubProducerClient.from_connection_string(
                self.config["eventhub_connection_string"],
                eventhub_name="incidents"
            )
            
            # Azure Communication Services para email
            if "communication_services_connection_string" in self.config:
                self.email_client = EmailClient.from_connection_string(
                    self.config["communication_services_connection_string"]
                )
            
            self.logger.info("Azure clients initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure clients: {e}")
            raise
    
    def _load_stakeholders(self) -> Dict[str, Stakeholder]:
        """Carregar lista de stakeholders"""
        
        # Em produção, carregar do banco de dados ou configuração
        stakeholders = {
            "ops_team": Stakeholder(
                id="ops_team",
                name="Operations Team",
                email="ops@company.com",
                role="operations",
                teams_id="ops-team-channel",
                notification_preferences=[NotificationChannel.TEAMS, NotificationChannel.EMAIL],
                escalation_level=1
            ),
            "dev_team": Stakeholder(
                id="dev_team",
                name="Development Team",
                email="dev@company.com",
                role="development",
                teams_id="dev-team-channel",
                notification_preferences=[NotificationChannel.TEAMS],
                escalation_level=2
            ),
            "management": Stakeholder(
                id="management",
                name="Management",
                email="management@company.com",
                role="management",
                teams_id="management-channel",
                notification_preferences=[NotificationChannel.EMAIL, NotificationChannel.SMS],
                escalation_level=3
            ),
            "on_call": Stakeholder(
                id="on_call",
                name="On-Call Engineer",
                email="oncall@company.com",
                role="on_call",
                phone="+1234567890",
                notification_preferences=[NotificationChannel.SMS, NotificationChannel.TEAMS],
                escalation_level=1
            )
        }
        
        return stakeholders
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Carregar templates de notificação"""
        
        templates = {
            "incident_detected_teams": NotificationTemplate(
                message_type=MessageType.INCIDENT_DETECTED,
                channel=NotificationChannel.TEAMS,
                subject_template="🚨 Incident Detected: {incident_title}",
                body_template="""
**Phoenix System Alert**

🚨 **Incident Detected**
- **ID**: {incident_id}
- **Title**: {incident_title}
- **Severity**: {severity}
- **Time**: {created_at}
- **Source**: {source}

**Initial Metrics**:
{metrics_summary}

**Status**: Analysis in progress...

Phoenix agents are automatically investigating this incident.
                """,
                priority=Priority.HIGH
            ),
            
            "incident_detected_email": NotificationTemplate(
                message_type=MessageType.INCIDENT_DETECTED,
                channel=NotificationChannel.EMAIL,
                subject_template="Phoenix Alert: Incident Detected - {incident_title}",
                body_template="""
<h2>Phoenix System - Incident Alert</h2>

<p><strong>An incident has been automatically detected and is being analyzed by Phoenix agents.</strong></p>

<table border="1" cellpadding="5">
<tr><td><strong>Incident ID</strong></td><td>{incident_id}</td></tr>
<tr><td><strong>Title</strong></td><td>{incident_title}</td></tr>
<tr><td><strong>Severity</strong></td><td>{severity}</td></tr>
<tr><td><strong>Detected At</strong></td><td>{created_at}</td></tr>
<tr><td><strong>Source</strong></td><td>{source}</td></tr>
</table>

<h3>Initial Metrics</h3>
<pre>{metrics_summary}</pre>

<p><strong>Next Steps</strong>:</p>
<ul>
<li>Phoenix diagnostic agent is analyzing the root cause</li>
<li>You will receive updates as the investigation progresses</li>
<li>No manual intervention required at this time</li>
</ul>

<p><em>This is an automated message from Phoenix System.</em></p>
                """,
                priority=Priority.HIGH
            ),
            
            "diagnosis_complete_teams": NotificationTemplate(
                message_type=MessageType.DIAGNOSIS_COMPLETE,
                channel=NotificationChannel.TEAMS,
                subject_template="🔍 Diagnosis Complete: {incident_title}",
                body_template="""
**Phoenix System Update**

🔍 **Diagnosis Complete**
- **Incident ID**: {incident_id}
- **Root Cause**: {root_cause}
- **Confidence**: {confidence}%
- **Analysis Duration**: {analysis_duration}s

**Evidence Found**:
{evidence_summary}

**Recommended Actions**:
{recommendations}

**Status**: {next_action}
                """,
                priority=Priority.MEDIUM
            ),
            
            "resolution_in_progress_teams": NotificationTemplate(
                message_type=MessageType.RESOLUTION_IN_PROGRESS,
                channel=NotificationChannel.TEAMS,
                subject_template="⚙️ Resolution In Progress: {incident_title}",
                body_template="""
**Phoenix System Update**

⚙️ **Automatic Resolution In Progress**
- **Incident ID**: {incident_id}
- **Actions Being Taken**: {actions_summary}
- **Estimated Duration**: {estimated_duration}s
- **Progress**: {progress}

**Current Status**: Phoenix resolution agent is executing corrective actions.

You will be notified when resolution is complete.
                """,
                priority=Priority.MEDIUM
            ),
            
            "incident_resolved_teams": NotificationTemplate(
                message_type=MessageType.INCIDENT_RESOLVED,
                channel=NotificationChannel.TEAMS,
                subject_template="✅ Incident Resolved: {incident_title}",
                body_template="""
**Phoenix System - Resolution Complete**

✅ **Incident Successfully Resolved**
- **Incident ID**: {incident_id}
- **Total Duration**: {total_duration}
- **Actions Taken**: {actions_taken}
- **Resolution Time**: {resolution_time}

**Summary**:
- **Root Cause**: {root_cause}
- **Resolution**: {resolution_summary}

**System Status**: All services are operating normally.

Great job, Phoenix! 🎉
                """,
                priority=Priority.LOW
            ),
            
            "incident_escalated_teams": NotificationTemplate(
                message_type=MessageType.INCIDENT_ESCALATED,
                channel=NotificationChannel.TEAMS,
                subject_template="🚨 ESCALATION: Manual Intervention Required",
                body_template="""
**Phoenix System - ESCALATION REQUIRED**

🚨 **Manual Intervention Needed**
- **Incident ID**: {incident_id}
- **Escalation Reason**: {escalation_reason}
- **Time Since Detection**: {time_elapsed}

**Current Status**:
{current_status}

**Recommended Actions**:
{manual_actions}

**@channel** - Immediate attention required!
                """,
                priority=Priority.CRITICAL
            ),
            
            "approval_request_teams": NotificationTemplate(
                message_type=MessageType.APPROVAL_REQUEST,
                channel=NotificationChannel.TEAMS,
                subject_template="⚠️ Approval Required: High-Risk Resolution",
                body_template="""
**Phoenix System - Approval Required**

⚠️ **High-Risk Resolution Actions Need Approval**
- **Incident ID**: {incident_id}
- **Risk Level**: {risk_level}
- **Proposed Actions**: {proposed_actions}

**Impact Assessment**:
{impact_assessment}

**Please respond with**:
- ✅ APPROVE to proceed
- ❌ DENY to escalate to manual resolution
- 🔄 MODIFY to suggest alternatives

**Timeout**: Auto-escalation in {timeout_minutes} minutes
                """,
                priority=Priority.HIGH
            )
        }
        
        return templates
    
    async def handle_notification_request(self, event_data: Dict[str, Any]):
        """Processar solicitação de notificação"""
        
        try:
            event_type = event_data.get("event_type")
            incident_id = event_data.get("incident_id")
            
            self.logger.info(f"Processing notification request: {event_type} for incident {incident_id}")
            
            # Mapear tipo de evento para tipo de mensagem
            message_type = self._map_event_to_message_type(event_type)
            
            if message_type:
                await self._send_notifications(message_type, event_data)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle notification request: {e}")
    
    def _map_event_to_message_type(self, event_type: str) -> Optional[MessageType]:
        """Mapear tipo de evento para tipo de mensagem"""
        
        mapping = {
            "incident_analysis_request": MessageType.INCIDENT_DETECTED,
            "diagnostic_result": MessageType.DIAGNOSIS_COMPLETE,
            "resolution_request": MessageType.RESOLUTION_IN_PROGRESS,
            "resolution_result": MessageType.INCIDENT_RESOLVED,
            "incident_escalation": MessageType.INCIDENT_ESCALATED,
            "approval_request": MessageType.APPROVAL_REQUEST
        }
        
        return mapping.get(event_type)
    
    async def _send_notifications(self, message_type: MessageType, event_data: Dict[str, Any]):
        """Enviar notificações para stakeholders apropriados"""
        
        incident_data = event_data.get("incident_data", {})
        severity = incident_data.get("severity", "medium")
        
        # Determinar stakeholders baseado na severidade
        target_stakeholders = self._determine_target_stakeholders(severity, message_type)
        
        # Enviar notificações para cada stakeholder
        for stakeholder_id in target_stakeholders:
            stakeholder = self.stakeholders.get(stakeholder_id)
            if not stakeholder:
                continue
            
            # Enviar para cada canal preferido do stakeholder
            for channel in stakeholder.notification_preferences:
                if channel.value in self.notification_channels:
                    await self._send_notification(
                        stakeholder, channel, message_type, event_data
                    )
        
        # Registrar no histórico
        incident_id = event_data.get("incident_id")
        if incident_id not in self.notification_history:
            self.notification_history[incident_id] = []
        
        self.notification_history[incident_id].append({
            "message_type": message_type.value,
            "stakeholders": target_stakeholders,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _determine_target_stakeholders(self, severity: str, message_type: MessageType) -> List[str]:
        """Determinar stakeholders alvo baseado na severidade e tipo de mensagem"""
        
        stakeholders = []
        
        # Sempre notificar ops team
        stakeholders.append("ops_team")
        
        # Baseado na severidade
        if severity in ["high", "critical"]:
            stakeholders.extend(["dev_team", "on_call"])
            
            if severity == "critical":
                stakeholders.append("management")
        
        # Baseado no tipo de mensagem
        if message_type in [MessageType.INCIDENT_ESCALATED, MessageType.APPROVAL_REQUEST]:
            stakeholders.append("management")
        
        return list(set(stakeholders))  # Remove duplicatas
    
    async def _send_notification(self, stakeholder: Stakeholder, 
                                channel: NotificationChannel,
                                message_type: MessageType, 
                                event_data: Dict[str, Any]):
        """Enviar notificação individual"""
        
        try:
            # Obter template apropriado
            template_key = f"{message_type.value}_{channel.value}"
            template = self.templates.get(template_key)
            
            if not template:
                self.logger.warning(f"No template found for {template_key}")
                return
            
            # Preparar dados para o template
            template_data = self._prepare_template_data(event_data)
            
            # Renderizar mensagem
            subject = template.subject_template.format(**template_data)
            body = template.body_template.format(**template_data)
            
            # Enviar baseado no canal
            if channel == NotificationChannel.TEAMS:
                await self._send_teams_message(stakeholder, subject, body)
            elif channel == NotificationChannel.EMAIL:
                await self._send_email(stakeholder, subject, body)
            elif channel == NotificationChannel.SMS:
                await self._send_sms(stakeholder, subject)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook(stakeholder, subject, body, event_data)
            
            self.logger.info(f"Notification sent to {stakeholder.name} via {channel.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification to {stakeholder.name}: {e}")
    
    def _prepare_template_data(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """Preparar dados para renderização do template"""
        
        incident_data = event_data.get("incident_data", {})
        
        # Dados básicos do incidente
        template_data = {
            "incident_id": incident_data.get("id", "N/A"),
            "incident_title": incident_data.get("title", "Unknown Incident"),
            "severity": incident_data.get("severity", "medium").upper(),
            "created_at": incident_data.get("created_at", datetime.utcnow().isoformat()),
            "source": incident_data.get("source", "monitoring"),
            "metrics_summary": self._format_metrics(incident_data.get("metrics", {}))
        }
        
        # Dados específicos do diagnóstico
        if "diagnosis" in event_data:
            diagnosis = event_data["diagnosis"]
            template_data.update({
                "root_cause": diagnosis.get("root_cause", "Unknown"),
                "confidence": int(diagnosis.get("confidence", 0) * 100),
                "analysis_duration": event_data.get("analysis_duration", 0),
                "evidence_summary": self._format_evidence(diagnosis.get("evidence", [])),
                "recommendations": self._format_recommendations(event_data.get("recommendations", []))
            })
        
        # Dados específicos da resolução
        if "actions_taken" in event_data:
            actions = event_data["actions_taken"]
            template_data.update({
                "actions_summary": self._format_actions(actions),
                "estimated_duration": event_data.get("estimated_duration", 0),
                "progress": "In Progress",
                "actions_taken": len(actions),
                "resolution_summary": self._format_resolution_summary(actions)
            })
        
        # Dados de escalação
        if event_type := event_data.get("event_type"):
            if event_type == "incident_escalation":
                template_data.update({
                    "escalation_reason": event_data.get("reason", "Unknown"),
                    "time_elapsed": self._calculate_time_elapsed(incident_data),
                    "current_status": incident_data.get("status", "unknown"),
                    "manual_actions": "Please review the incident and take manual action"
                })
        
        # Dados de aprovação
        if "plan" in event_data:
            plan = event_data["plan"]
            template_data.update({
                "risk_level": plan.get("risk_level", "unknown").upper(),
                "proposed_actions": self._format_proposed_actions(plan.get("actions", [])),
                "impact_assessment": "High-risk actions require approval",
                "timeout_minutes": 15
            })
        
        # Calcular duração total se incidente resolvido
        if incident_data.get("status") == "resolved":
            template_data["total_duration"] = self._calculate_total_duration(incident_data)
            template_data["resolution_time"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Determinar próxima ação
        template_data["next_action"] = self._determine_next_action(event_data)
        
        return template_data
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Formatar métricas para exibição"""
        if not metrics:
            return "No metrics available"
        
        formatted = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                formatted.append(f"- {key}: {value}")
            else:
                formatted.append(f"- {key}: {str(value)}")
        
        return "\n".join(formatted)
    
    def _format_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """Formatar evidências para exibição"""
        if not evidence:
            return "No evidence collected"
        
        formatted = []
        for item in evidence[:3]:  # Limitar a 3 itens
            formatted.append(f"- {item.get('description', 'Unknown evidence')}")
        
        if len(evidence) > 3:
            formatted.append(f"- ... and {len(evidence) - 3} more items")
        
        return "\n".join(formatted)
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        """Formatar recomendações para exibição"""
        if not recommendations:
            return "No recommendations available"
        
        return "\n".join(f"- {rec}" for rec in recommendations[:5])
    
    def _format_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Formatar ações para exibição"""
        if not actions:
            return "No actions taken"
        
        formatted = []
        for action in actions[:3]:
            status = "✅" if action.get("success") else "❌"
            formatted.append(f"{status} {action.get('description', 'Unknown action')}")
        
        if len(actions) > 3:
            formatted.append(f"... and {len(actions) - 3} more actions")
        
        return "\n".join(formatted)
    
    def _format_resolution_summary(self, actions: List[Dict[str, Any]]) -> str:
        """Formatar resumo da resolução"""
        successful = sum(1 for action in actions if action.get("success"))
        total = len(actions)
        
        return f"{successful}/{total} actions completed successfully"
    
    def _format_proposed_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Formatar ações propostas para aprovação"""
        if not actions:
            return "No actions proposed"
        
        formatted = []
        for action in actions:
            formatted.append(f"- {action.get('description', 'Unknown action')}")
        
        return "\n".join(formatted)
    
    def _calculate_time_elapsed(self, incident_data: Dict[str, Any]) -> str:
        """Calcular tempo decorrido desde a detecção"""
        created_at = incident_data.get("created_at")
        if not created_at:
            return "Unknown"
        
        try:
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elapsed = datetime.utcnow() - created_time.replace(tzinfo=None)
            
            minutes = int(elapsed.total_seconds() / 60)
            if minutes < 60:
                return f"{minutes} minutes"
            else:
                hours = minutes // 60
                remaining_minutes = minutes % 60
                return f"{hours}h {remaining_minutes}m"
                
        except Exception:
            return "Unknown"
    
    def _calculate_total_duration(self, incident_data: Dict[str, Any]) -> str:
        """Calcular duração total do incidente"""
        return self._calculate_time_elapsed(incident_data)
    
    def _determine_next_action(self, event_data: Dict[str, Any]) -> str:
        """Determinar próxima ação baseada no evento"""
        event_type = event_data.get("event_type", "")
        
        if event_type == "incident_analysis_request":
            return "Diagnostic analysis in progress"
        elif event_type == "diagnostic_result":
            return "Resolution planning initiated"
        elif event_type == "resolution_request":
            return "Executing corrective actions"
        elif event_type == "resolution_result":
            success = event_data.get("success", False)
            return "Incident resolved" if success else "Resolution failed - escalating"
        elif event_type == "incident_escalation":
            return "Manual intervention required"
        elif event_type == "approval_request":
            return "Awaiting approval for high-risk actions"
        else:
            return "Status update"
    
    async def _send_teams_message(self, stakeholder: Stakeholder, subject: str, body: str):
        """Enviar mensagem para Microsoft Teams"""
        
        try:
            # Simular envio para Teams (em produção, usar Microsoft Graph API)
            teams_webhook_url = self.config.get("teams_webhook_url")
            
            if not teams_webhook_url:
                self.logger.warning("Teams webhook URL not configured")
                return
            
            # Preparar payload para Teams
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_theme_color(subject),
                "summary": subject,
                "sections": [{
                    "activityTitle": subject,
                    "activitySubtitle": f"Notification for {stakeholder.name}",
                    "text": body,
                    "markdown": True
                }]
            }
            
            # Simular envio (em produção, fazer POST real)
            self.logger.info(f"Teams message would be sent to {stakeholder.teams_id}")
            self.logger.debug(f"Teams payload: {json.dumps(payload, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Failed to send Teams message: {e}")
    
    def _get_theme_color(self, subject: str) -> str:
        """Obter cor do tema baseada no assunto"""
        if "🚨" in subject or "ESCALATION" in subject:
            return "FF0000"  # Vermelho
        elif "✅" in subject or "Resolved" in subject:
            return "00FF00"  # Verde
        elif "⚠️" in subject or "Approval" in subject:
            return "FFA500"  # Laranja
        else:
            return "0078D4"  # Azul (padrão)
    
    async def _send_email(self, stakeholder: Stakeholder, subject: str, body: str):
        """Enviar email"""
        
        try:
            # Simular envio de email (em produção, usar Azure Communication Services)
            self.logger.info(f"Email would be sent to {stakeholder.email}")
            self.logger.debug(f"Subject: {subject}")
            self.logger.debug(f"Body: {body[:200]}...")
            
            # Em produção:
            # message = {
            #     "senderAddress": "phoenix@company.com",
            #     "recipients": {
            #         "to": [{"address": stakeholder.email}]
            #     },
            #     "content": {
            #         "subject": subject,
            #         "html": body
            #     }
            # }
            # 
            # poller = self.email_client.begin_send(message)
            # result = poller.result()
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    async def _send_sms(self, stakeholder: Stakeholder, message: str):
        """Enviar SMS"""
        
        try:
            if not stakeholder.phone:
                self.logger.warning(f"No phone number for {stakeholder.name}")
                return
            
            # Simular envio de SMS (em produção, usar Azure Communication Services)
            # Limitar tamanho da mensagem SMS
            sms_message = message[:160] + "..." if len(message) > 160 else message
            
            self.logger.info(f"SMS would be sent to {stakeholder.phone}")
            self.logger.debug(f"SMS: {sms_message}")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS: {e}")
    
    async def _send_webhook(self, stakeholder: Stakeholder, subject: str, 
                           body: str, event_data: Dict[str, Any]):
        """Enviar webhook"""
        
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                return
            
            payload = {
                "stakeholder": stakeholder.name,
                "subject": subject,
                "body": body,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Simular envio de webhook
            self.logger.info(f"Webhook would be sent to {webhook_url}")
            self.logger.debug(f"Webhook payload: {json.dumps(payload, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook: {e}")
    
    async def handle_approval_response(self, incident_id: str, response: str, 
                                     responder: str) -> Dict[str, Any]:
        """Processar resposta de aprovação"""
        
        try:
            self.logger.info(f"Processing approval response for incident {incident_id}: {response}")
            
            # Validar resposta
            valid_responses = ["APPROVE", "DENY", "MODIFY"]
            if response.upper() not in valid_responses:
                return {
                    "success": False,
                    "message": f"Invalid response. Use: {', '.join(valid_responses)}"
                }
            
            # Enviar resposta para o orquestrador
            event_data = {
                "event_type": "approval_response",
                "incident_id": incident_id,
                "response": response.upper(),
                "responder": responder,
                "timestamp": datetime.utcnow().isoformat(),
                "source_agent": self.agent_id
            }
            
            async with self.event_producer:
                event = EventData(json.dumps(event_data, default=str))
                await self.event_producer.send_batch([event])
            
            # Notificar stakeholders sobre a decisão
            await self._notify_approval_decision(incident_id, response, responder)
            
            return {
                "success": True,
                "message": f"Approval response '{response}' recorded"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to handle approval response: {e}")
            return {
                "success": False,
                "message": f"Failed to process approval: {str(e)}"
            }
    
    async def _notify_approval_decision(self, incident_id: str, response: str, responder: str):
        """Notificar sobre decisão de aprovação"""
        
        # Criar evento de notificação
        event_data = {
            "event_type": "status_update",
            "incident_id": incident_id,
            "incident_data": {"id": incident_id},
            "message": f"Approval {response.lower()} by {responder}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Enviar notificação
        await self._send_notifications(MessageType.STATUS_UPDATE, event_data)
    
    def get_notification_history(self, incident_id: str) -> List[Dict[str, Any]]:
        """Obter histórico de notificações para um incidente"""
        return self.notification_history.get(incident_id, [])
    
    def get_stakeholder_preferences(self, stakeholder_id: str) -> Optional[Dict[str, Any]]:
        """Obter preferências de um stakeholder"""
        stakeholder = self.stakeholders.get(stakeholder_id)
        if stakeholder:
            return {
                "name": stakeholder.name,
                "email": stakeholder.email,
                "role": stakeholder.role,
                "notification_preferences": [ch.value for ch in stakeholder.notification_preferences],
                "escalation_level": stakeholder.escalation_level
            }
        return None


# Função para criar instância do agente de comunicação
def create_communication_agent(config: Dict[str, Any]) -> PhoenixCommunicationAgent:
    """Factory function para criar instância do agente de comunicação"""
    return PhoenixCommunicationAgent(config)

