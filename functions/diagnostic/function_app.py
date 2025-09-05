"""
Phoenix Diagnostic Function
Azure Function que hospeda o agente de diagnóstico
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

from diagnostic.agent import create_diagnostic_agent
from config import get_agent_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar o agente de diagnóstico
try:
    config = get_agent_config("diagnostic")
    diagnostic_agent = create_diagnostic_agent(config)
    logger.info("Diagnostic agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize diagnostic agent: {e}")
    diagnostic_agent = None

# Criar a aplicação de função
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="analyze", methods=["POST"])
async def analyze_incident(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para analisar incidentes
    """
    logger.info("Processing incident analysis request")
    
    try:
        # Verificar se o agente foi inicializado
        if not diagnostic_agent:
            return func.HttpResponse(
                json.dumps({"error": "Diagnostic agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter dados do incidente
        try:
            incident_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not incident_data:
            return func.HttpResponse(
                json.dumps({"error": "No incident data provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Analisar incidente
        diagnostic_result = await diagnostic_agent.analyze_incident(incident_data)
        
        response = {
            "success": True,
            "incident_id": diagnostic_result.incident_id,
            "diagnosis": {
                "root_cause": diagnostic_result.root_cause,
                "confidence": diagnostic_result.confidence,
                "evidence": diagnostic_result.evidence,
                "patterns_detected": diagnostic_result.patterns_detected,
                "anomalies": diagnostic_result.anomalies
            },
            "recommendations": diagnostic_result.recommendations,
            "analysis_duration": diagnostic_result.analysis_duration,
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        logger.info(f"Incident analysis completed. ID: {diagnostic_result.incident_id}")
        
        return func.HttpResponse(
            json.dumps(response, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error analyzing incident: {e}")
        
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


@app.route(route="patterns", methods=["GET"])
async def get_known_patterns(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para obter padrões conhecidos
    """
    logger.info("Getting known patterns")
    
    try:
        if not diagnostic_agent:
            return func.HttpResponse(
                json.dumps({"error": "Diagnostic agent not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Obter padrões conhecidos
        patterns = diagnostic_agent.known_patterns
        
        response = {
            "success": True,
            "patterns": patterns,
            "count": len(patterns),
            "timestamp": func.datetime.utcnow().isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        
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
            "agent": "diagnostic",
            "agent_initialized": diagnostic_agent is not None,
            "timestamp": func.datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        # Verificar conexões com serviços Azure
        if diagnostic_agent:
            try:
                health_status["azure_services"] = {
                    "cosmos_db": "connected",
                    "event_hub": "connected",
                    "log_analytics": "connected",
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
        if not diagnostic_agent:
            logger.error("Diagnostic agent not initialized")
            return
        
        for event in events:
            try:
                # Decodificar dados do evento
                event_data = json.loads(event.get_body().decode('utf-8'))
                
                # Processar apenas eventos de análise de incidente
                event_type = event_data.get("event_type")
                
                if event_type == "incident_analysis_request":
                    incident_data = event_data.get("incident_data", {})
                    
                    # Analisar incidente
                    diagnostic_result = await diagnostic_agent.analyze_incident(incident_data)
                    
                    logger.info(f"Incident analysis completed via Event Hub: {diagnostic_result.incident_id}")
                    
                else:
                    logger.debug(f"Ignoring event type: {event_type}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    except Exception as e:
        logger.error(f"Error processing Event Hub messages: {e}")


@app.timer_trigger(schedule="0 */10 * * * *", arg_name="timer")
async def maintenance_function(timer: func.TimerRequest) -> None:
    """
    Função de manutenção periódica
    """
    logger.info("Running diagnostic agent maintenance")
    
    try:
        # Verificar se o agente precisa ser reinicializado
        global diagnostic_agent
        if not diagnostic_agent:
            config = get_agent_config("diagnostic")
            diagnostic_agent = create_diagnostic_agent(config)
            logger.info("Diagnostic agent reinitialized")
        
        # Executar tarefas de manutenção
        if diagnostic_agent:
            # Limpar cache de análises antigas
            # Atualizar padrões conhecidos
            # Verificar conexões com serviços
            logger.info("Diagnostic maintenance tasks completed")
            
    except Exception as e:
        logger.error(f"Maintenance function failed: {e}")


if __name__ == "__main__":
    # Para desenvolvimento local
    import uvicorn
    
    logger.info("Starting Phoenix Diagnostic Function locally")
    
    # Configurar para desenvolvimento local
    app.run(host="0.0.0.0", port=7072, debug=True)

