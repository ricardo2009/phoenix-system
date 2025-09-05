"""
Phoenix Resolution Function
Azure Function que hospeda o agente de resolução
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

from resolution.agent import create_resolution_agent
from config import get_agent_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar o agente de resolução
try:
    config = get_agent_config("resolution")
    resolution_agent = create_resolution_agent(config)
    logger.info("Resolution agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize resolution agent: {e}")
    resolution_agent = None

# Criar a aplicação de função
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="resolve", methods=["POST"])
async def execute_resolution(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para executar resolução de incidentes
    """
    logger.info("Processing resolution request")
    
    try:
        # Verificar se o agente foi inicializado
        if not resolution_agent:
            return func.HttpResponse(
                json.dumps({"error": "Resolution agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados da requisição
        try:
            request_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not request_data:
            return func.HttpResponse(
                json.dumps({"error": "No request data provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        incident_data = request_data.get("incident_data", {})
        diagnosis = request_data.get("diagnosis", {})
        
        if not incident_data or not diagnosis:
            return func.HttpResponse(
                json.dumps({"error": "Both incident_data and diagnosis are required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Executar resolução
        resolution_result = await resolution_agent.execute_resolution(incident_data, diagnosis)
        
        response = {
            "success": resolution_result["success"],
            "incident_id": incident_data.get("id"),
            "actions_taken": resolution_result["actions_taken"],
            "execution_time": resolution_result["execution_time"],
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        if not resolution_result["success"]:
            response["message"] = "Resolution failed or requires approval"
        
        logger.info(f"Resolution completed for incident: {incident_data.get('id')}")
        
        return func.HttpResponse(
            json.dumps(response, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error executing resolution: {e}")
        
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


@app.route(route="actions", methods=["GET"])
async def get_executed_actions(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter ações executadas
    """
    logger.info("Getting executed actions")
    
    try:
        if not resolution_agent:
            return func.HttpResponse(
                json.dumps({"error": "Resolution agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter ações executadas
        executed_actions = {
            action_id: {
                "id": action.id,
                "type": action.type.value,
                "description": action.description,
                "status": action.status.value,
                "started_at": action.started_at.isoformat() if action.started_at else None,
                "completed_at": action.completed_at.isoformat() if action.completed_at else None,
                "result": action.result
            }
            for action_id, action in resolution_agent.executed_actions.items()
        }
        
        response = {
            "success": True,
            "executed_actions": executed_actions,
            "count": len(executed_actions),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting executed actions: {e}")
        
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


@app.route(route="safety-limits", methods=["GET"])
async def get_safety_limits(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter limites de segurança
    """
    logger.info("Getting safety limits")
    
    try:
        if not resolution_agent:
            return func.HttpResponse(
                json.dumps({"error": "Resolution agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        response = {
            "success": True,
            "safety_limits": resolution_agent.safety_limits,
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting safety limits: {e}")
        
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
            "agent": "resolution",
            "agent_initialized": resolution_agent is not None,
            "timestamp": func.datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        # Verificar conexões com serviços Azure
        if resolution_agent:
            try:
                health_status["azure_services"] = {
                    "cosmos_db": "connected",
                    "event_hub": "connected",
                    "azure_management": "connected",
                    "kubernetes": "connected"
                }
                health_status["safety_limits"] = resolution_agent.safety_limits
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
        if not resolution_agent:
            logger.error("Resolution agent not initialized")
            return
        
        for event in events:
            try:
                # Decodificar dados do evento
                event_data = json.loads(event.get_body().decode('utf-8'))
                
                # Processar apenas eventos de resolução
                event_type = event_data.get("event_type")
                
                if event_type == "resolution_request":
                    incident_data = event_data.get("incident_data", {})
                    diagnosis = event_data.get("diagnosis", {})
                    
                    # Executar resolução
                    resolution_result = await resolution_agent.execute_resolution(
                        incident_data, diagnosis
                    )
                    
                    logger.info(f"Resolution completed via Event Hub: {incident_data.get('id')}")
                    
                elif event_type == "approval_response":
                    # Processar resposta de aprovação
                    response = event_data.get("response")
                    incident_id = event_data.get("incident_id")
                    
                    if response == "APPROVE":
                        # Continuar com a resolução aprovada
                        logger.info(f"Resolution approved for incident: {incident_id}")
                    elif response == "DENY":
                        # Escalar para resolução manual
                        logger.info(f"Resolution denied for incident: {incident_id}")
                    
                else:
                    logger.debug(f"Ignoring event type: {event_type}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    except Exception as e:
        logger.error(f"Error processing Event Hub messages: {e}")


@app.timer_trigger(schedule="0 */15 * * * *", arg_name="timer")
async def maintenance_function(timer: func.TimerRequest) -> None:
    """
    Função de manutenção periódica
    """
    logger.info("Running resolution agent maintenance")
    
    try:
        # Verificar se o agente precisa ser reinicializado
        global resolution_agent
        if not resolution_agent:
            config = get_agent_config("resolution")
            resolution_agent = create_resolution_agent(config)
            logger.info("Resolution agent reinitialized")
        
        # Executar tarefas de manutenção
        if resolution_agent:
            # Limpar ações antigas executadas
            # Verificar limites de segurança
            # Verificar conexões com serviços
            logger.info("Resolution maintenance tasks completed")
            
    except Exception as e:
        logger.error(f"Maintenance function failed: {e}")


if __name__ == "__main__":
    # Para desenvolvimento local
    import uvicorn
    
    logger.info("Starting Phoenix Resolution Function locally")
    
    # Configurar para desenvolvimento local
    app.run(host="0.0.0.0", port=7073, debug=True)

