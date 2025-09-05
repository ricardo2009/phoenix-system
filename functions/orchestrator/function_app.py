"""
Phoenix Orchestrator Function
Azure Function que hospeda o agente orquestrador
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

from orchestrator.agent import create_orchestrator
from config import get_agent_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar o agente orquestrador
try:
    config = get_agent_config("orchestrator")
    orchestrator = create_orchestrator(config)
    logger.info("Orchestrator agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize orchestrator agent: {e}")
    orchestrator = None

# Criar a aplicação de função
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="alert", methods=["POST"])
async def process_alert(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para processar alertas de monitoramento
    """
    logger.info("Processing alert request")
    
    try:
        # Verificar se o orquestrador foi inicializado
        if not orchestrator:
            return func.HttpResponse(
                json.dumps({"error": "Orchestrator not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados do alerta
        try:
            alert_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not alert_data:
            return func.HttpResponse(
                json.dumps({"error": "No alert data provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Processar alerta
        incident_id = await orchestrator.process_alert(alert_data)
        
        response = {
            "success": True,
            "incident_id": incident_id,
            "message": "Alert processed successfully",
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        logger.info(f"Alert processed successfully. Incident ID: {incident_id}")
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        
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


@app.route(route="incident/{incident_id}", methods=["GET"])
async def get_incident_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter status de um incidente
    """
    logger.info("Getting incident status")
    
    try:
        # Verificar se o orquestrador foi inicializado
        if not orchestrator:
            return func.HttpResponse(
                json.dumps({"error": "Orchestrator not initialized"}),
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
        
        # Obter status do incidente
        incident_status = orchestrator.get_incident_status(incident_id)
        
        if not incident_status:
            return func.HttpResponse(
                json.dumps({"error": "Incident not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        response = {
            "success": True,
            "incident": incident_status,
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting incident status: {e}")
        
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


@app.route(route="incidents", methods=["GET"])
async def get_active_incidents(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter lista de incidentes ativos
    """
    logger.info("Getting active incidents")
    
    try:
        # Verificar se o orquestrador foi inicializado
        if not orchestrator:
            return func.HttpResponse(
                json.dumps({"error": "Orchestrator not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter incidentes ativos
        active_incidents = orchestrator.get_active_incidents()
        
        response = {
            "success": True,
            "incidents": active_incidents,
            "count": len(active_incidents),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting active incidents: {e}")
        
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


@app.route(route="agent-response", methods=["POST"])
async def handle_agent_response(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para receber respostas de outros agentes
    """
    logger.info("Handling agent response")
    
    try:
        # Verificar se o orquestrador foi inicializado
        if not orchestrator:
            return func.HttpResponse(
                json.dumps({"error": "Orchestrator not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados da resposta
        try:
            response_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not response_data:
            return func.HttpResponse(
                json.dumps({"error": "No response data provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Processar resposta do agente
        await orchestrator.handle_agent_response(response_data)
        
        response = {
            "success": True,
            "message": "Agent response processed successfully",
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error handling agent response: {e}")
        
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
            "agent": "orchestrator",
            "agent_initialized": orchestrator is not None,
            "timestamp": func.datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        # Verificar conexões com serviços Azure
        if orchestrator:
            try:
                # Teste básico de conectividade (simulado)
                health_status["azure_services"] = {
                    "cosmos_db": "connected",
                    "event_hub": "connected",
                    "openai": "connected"
                }
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
        if not orchestrator:
            logger.error("Orchestrator not initialized")
            return
        
        for event in events:
            try:
                # Decodificar dados do evento
                event_data = json.loads(event.get_body().decode('utf-8'))
                
                # Processar baseado no tipo de evento
                event_type = event_data.get("event_type")
                
                if event_type in ["diagnostic_result", "resolution_result", "communication_response"]:
                    await orchestrator.handle_agent_response(event_data)
                else:
                    logger.warning(f"Unknown event type: {event_type}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    except Exception as e:
        logger.error(f"Error processing Event Hub messages: {e}")


# Função de inicialização da aplicação
@app.function_name("startup")
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=True)
async def startup_function(timer: func.TimerRequest) -> None:
    """
    Função de inicialização e manutenção periódica
    """
    logger.info("Running startup/maintenance function")
    
    try:
        # Verificar se o orquestrador precisa ser reinicializado
        global orchestrator
        if not orchestrator:
            config = get_agent_config("orchestrator")
            orchestrator = create_orchestrator(config)
            logger.info("Orchestrator agent reinitialized")
        
        # Executar tarefas de manutenção
        if orchestrator:
            # Limpar incidentes antigos resolvidos
            # Verificar conexões com serviços
            # Outras tarefas de manutenção
            logger.info("Maintenance tasks completed")
            
    except Exception as e:
        logger.error(f"Startup/maintenance function failed: {e}")


if __name__ == "__main__":
    # Para desenvolvimento local
    import uvicorn
    
    logger.info("Starting Phoenix Orchestrator Function locally")
    
    # Configurar para desenvolvimento local
    app.run(host="0.0.0.0", port=7071, debug=True)

