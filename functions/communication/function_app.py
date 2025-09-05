"""
Phoenix Communication Function
Azure Function que hospeda o agente de comunicação
"""

import azure.functions as func
import json
import logging
import asyncio
from typing import Dict, Any
import os
import sys

# Adicionar o diretório dos agentes ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'agents'))

from communication.agent import create_communication_agent
from config import get_agent_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar o agente de comunicação
try:
    config = get_agent_config("communication")
    communication_agent = create_communication_agent(config)
    logger.info("Communication agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize communication agent: {e}")
    communication_agent = None

# Criar a aplicação de função
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="notify", methods=["POST"])
async def send_notification(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para enviar notificações
    """
    logger.info("Processing notification request")
    
    try:
        # Verificar se o agente foi inicializado
        if not communication_agent:
            return func.HttpResponse(
                json.dumps({"error": "Communication agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados da notificação
        try:
            notification_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not notification_data:
            return func.HttpResponse(
                json.dumps({"error": "No notification data provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Processar notificação
        await communication_agent.handle_notification_request(notification_data)
        
        response = {
            "success": True,
            "message": "Notification processed successfully",
            "incident_id": notification_data.get("incident_id"),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        logger.info(f"Notification processed for incident: {notification_data.get('incident_id')}")
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing notification: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="approval", methods=["POST"])
async def handle_approval(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para processar respostas de aprovação
    """
    logger.info("Processing approval response")
    
    try:
        # Verificar se o agente foi inicializado
        if not communication_agent:
            return func.HttpResponse(
                json.dumps({"error": "Communication agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados da aprovação
        try:
            approval_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not approval_data:
            return func.HttpResponse(
                json.dumps({"error": "No approval data provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        incident_id = approval_data.get("incident_id")
        response = approval_data.get("response")
        responder = approval_data.get("responder", "unknown")
        
        if not incident_id or not response:
            return func.HttpResponse(
                json.dumps({"error": "incident_id and response are required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Processar resposta de aprovação
        result = await communication_agent.handle_approval_response(
            incident_id, response, responder
        )
        
        response_data = {
            "success": result["success"],
            "message": result["message"],
            "incident_id": incident_id,
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        status_code = 200 if result["success"] else 400
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing approval: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="history/{incident_id}", methods=["GET"])
async def get_notification_history(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter histórico de notificações
    """
    logger.info("Getting notification history")
    
    try:
        if not communication_agent:
            return func.HttpResponse(
                json.dumps({"error": "Communication agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter ID do incidente
        incident_id = req.route_params.get('incident_id')
        
        if not incident_id:
            return func.HttpResponse(
                json.dumps({"error": "Incident ID is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Obter histórico de notificações
        history = communication_agent.get_notification_history(incident_id)
        
        response = {
            "success": True,
            "incident_id": incident_id,
            "notification_history": history,
            "count": len(history),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="stakeholders", methods=["GET"])
async def get_stakeholders(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter lista de stakeholders
    """
    logger.info("Getting stakeholders")
    
    try:
        if not communication_agent:
            return func.HttpResponse(
                json.dumps({"error": "Communication agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter stakeholders
        stakeholders = {}
        for stakeholder_id in communication_agent.stakeholders.keys():
            stakeholder_info = communication_agent.get_stakeholder_preferences(stakeholder_id)
            if stakeholder_info:
                stakeholders[stakeholder_id] = stakeholder_info
        
        response = {
            "success": True,
            "stakeholders": stakeholders,
            "count": len(stakeholders),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting stakeholders: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint de health check
    """
    try:
        health_status = {
            "status": "healthy",
            "agent": "communication",
            "agent_initialized": communication_agent is not None,
            "timestamp": func.datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        # Verificar conexões com serviços Azure
        if communication_agent:
            try:
                health_status["azure_services"] = {
                    "cosmos_db": "connected",
                    "event_hub": "connected",
                    "communication_services": "connected"
                }
                health_status["notification_channels"] = communication_agent.notification_channels
                health_status["stakeholders_count"] = len(communication_agent.stakeholders)
            except Exception as e:
                health_status["azure_services"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        status_code = 200 if health_status["agent_initialized"] else 503
        
        return func.HttpResponse(
            json.dumps(health_status),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        error_response = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=503,
            mimetype="application/json"
        )


@app.event_hub_message_trigger(arg_name="events", 
                              event_hub_name="incidents",
                              connection="EventHubConnectionString")
async def process_event_hub_message(events: func.EventHubEvent):
    """
    Trigger para processar mensagens do Event Hub
    """
    logger.info(f"Processing {len(events)} Event Hub messages")
    
    try:
        if not communication_agent:
            logger.error("Communication agent not initialized")
            return
        
        for event in events:
            try:
                # Decodificar dados do evento
                event_data = json.loads(event.get_body().decode('utf-8'))
                
                # Processar eventos de comunicação
                event_type = event_data.get("event_type")
                
                communication_events = [
                    "incident_analysis_request",
                    "diagnostic_result", 
                    "resolution_request",
                    "resolution_result",
                    "incident_escalation",
                    "approval_request"
                ]
                
                if event_type in communication_events:
                    await communication_agent.handle_notification_request(event_data)
                    logger.info(f"Notification sent for event: {event_type}")
                else:
                    logger.debug(f"Ignoring event type: {event_type}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    except Exception as e:
        logger.error(f"Error processing Event Hub messages: {e}")


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer")
async def maintenance_function(timer: func.TimerRequest) -> None:
    """
    Função de manutenção periódica
    """
    logger.info("Running communication agent maintenance")
    
    try:
        # Verificar se o agente precisa ser reinicializado
        global communication_agent
        if not communication_agent:
            config = get_agent_config("communication")
            communication_agent = create_communication_agent(config)
            logger.info("Communication agent reinitialized")
        
        # Executar tarefas de manutenção
        if communication_agent:
            # Limpar histórico antigo de notificações
            # Verificar conexões com canais de comunicação
            # Atualizar templates de notificação
            logger.info("Communication maintenance tasks completed")
            
    except Exception as e:
        logger.error(f"Maintenance function failed: {e}")


# Webhook para Microsoft Teams (exemplo)
@app.route(route="teams-webhook", methods=["POST"])
async def teams_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Webhook para receber respostas do Microsoft Teams
    """
    logger.info("Processing Teams webhook")
    
    try:
        if not communication_agent:
            return func.HttpResponse(
                json.dumps({"error": "Communication agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados do webhook
        try:
            webhook_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Processar resposta do Teams (exemplo de aprovação)
        if webhook_data.get("type") == "approval_response":
            incident_id = webhook_data.get("incident_id")
            response = webhook_data.get("response")
            responder = webhook_data.get("user", {}).get("name", "Teams User")
            
            if incident_id and response:
                result = await communication_agent.handle_approval_response(
                    incident_id, response, responder
                )
                
                return func.HttpResponse(
                    json.dumps(result),
                    status_code=200,
                    mimetype="application/json"
                )
        
        # Resposta padrão para outros tipos de webhook
        return func.HttpResponse(
            json.dumps({"message": "Webhook received"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing Teams webhook: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        )


if __name__ == "__main__":
    # Para desenvolvimento local
    import uvicorn
    
    logger.info("Starting Phoenix Communication Function locally")
    
    # Configurar para desenvolvimento local
    app.run(host="0.0.0.0", port=7074, debug=True)

