"""
Phoenix Resolution Agent
Executa ações corretivas automatizadas baseadas no diagnóstico
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from azure.cosmos import CosmosClient
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from kubernetes import client, config
import requests


class ActionType(Enum):
    SCALE_OUT = "scale_out"
    SCALE_UP = "scale_up"
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    OPTIMIZE_DATABASE = "optimize_database"
    UPDATE_CONFIG = "update_config"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    CIRCUIT_BREAKER = "circuit_breaker"


class ActionStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ResolutionAction:
    id: str
    type: ActionType
    description: str
    parameters: Dict[str, Any]
    status: ActionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    rollback_action: Optional['ResolutionAction'] = None


@dataclass
class ResolutionPlan:
    incident_id: str
    actions: List[ResolutionAction]
    estimated_duration: int
    risk_level: str
    requires_approval: bool
    created_at: datetime


class PhoenixResolutionAgent:
    """
    Agente de Resolução do Sistema Phoenix
    
    Responsabilidades:
    - Executar ações corretivas automatizadas
    - Escalar recursos dinamicamente
    - Reiniciar serviços quando necessário
    - Otimizar configurações
    - Implementar circuit breakers
    - Fazer rollback de deployments problemáticos
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = f"resolution-{uuid.uuid4().hex[:8]}"
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar clientes Azure
        self._init_azure_clients()
        
        # Configurações de execução
        self.execution_timeout = config.get("execution_timeout", 120)
        self.rollback_enabled = config.get("rollback_enabled", True)
        
        # Registro de ações executadas
        self.executed_actions: Dict[str, ResolutionAction] = {}
        
        # Limites de segurança
        self.safety_limits = {
            "max_scale_instances": 20,
            "max_cpu_cores": 32,
            "max_memory_gb": 128,
            "cooldown_period": 300  # 5 minutos
        }
        
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
            
            # Azure Management clients
            credential = DefaultAzureCredential()
            self.web_client = WebSiteManagementClient(
                credential, self.config["subscription_id"]
            )
            self.monitor_client = MonitorManagementClient(
                credential, self.config["subscription_id"]
            )
            
            # Kubernetes client (para AKS)
            try:
                config.load_incluster_config()  # Para pods no cluster
            except:
                config.load_kube_config()  # Para desenvolvimento local
            
            self.k8s_apps_v1 = client.AppsV1Api()
            self.k8s_core_v1 = client.CoreV1Api()
            
            self.logger.info("Azure clients initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure clients: {e}")
            raise
    
    async def execute_resolution(self, incident_data: Dict[str, Any], 
                                diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executar resolução baseada no diagnóstico
        
        Args:
            incident_data: Dados do incidente
            diagnosis: Resultado do diagnóstico
            
        Returns:
            Resultado da execução das ações
        """
        incident_id = incident_data.get("id")
        
        try:
            self.logger.info(f"Starting resolution for incident {incident_id}")
            
            # Criar plano de resolução
            resolution_plan = await self._create_resolution_plan(incident_data, diagnosis)
            
            # Verificar se requer aprovação
            if resolution_plan.requires_approval:
                await self._request_approval(resolution_plan)
                return {
                    "success": False,
                    "message": "Resolution requires human approval",
                    "plan": resolution_plan
                }
            
            # Executar ações do plano
            execution_results = await self._execute_plan(resolution_plan)
            
            # Verificar sucesso geral
            success = all(result.get("success", False) for result in execution_results)
            
            # Enviar resultado para o orquestrador
            await self._send_resolution_result(incident_id, success, execution_results)
            
            self.logger.info(f"Resolution completed for incident {incident_id}")
            
            return {
                "success": success,
                "actions_taken": execution_results,
                "execution_time": sum(r.get("duration", 0) for r in execution_results)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute resolution for incident {incident_id}: {e}")
            await self._send_resolution_result(incident_id, False, [])
            raise
    
    async def _create_resolution_plan(self, incident_data: Dict[str, Any], 
                                     diagnosis: Dict[str, Any]) -> ResolutionPlan:
        """Criar plano de resolução baseado no diagnóstico"""
        
        incident_id = incident_data.get("id")
        root_cause = diagnosis.get("root_cause", "")
        confidence = diagnosis.get("confidence", 0.0)
        
        actions = []
        risk_level = "low"
        requires_approval = False
        
        # Determinar ações baseadas na causa raiz
        if "high_cpu" in root_cause.lower() or "cpu" in root_cause.lower():
            actions.extend(await self._plan_cpu_resolution(incident_data, diagnosis))
            
        elif "memory" in root_cause.lower():
            actions.extend(await self._plan_memory_resolution(incident_data, diagnosis))
            
        elif "database" in root_cause.lower():
            actions.extend(await self._plan_database_resolution(incident_data, diagnosis))
            
        elif "timeout" in root_cause.lower() or "response" in root_cause.lower():
            actions.extend(await self._plan_performance_resolution(incident_data, diagnosis))
            
        elif "error" in root_cause.lower() or "exception" in root_cause.lower():
            actions.extend(await self._plan_error_resolution(incident_data, diagnosis))
        
        # Ações padrão se nenhuma específica foi identificada
        if not actions:
            actions.extend(await self._plan_generic_resolution(incident_data, diagnosis))
        
        # Determinar nível de risco e necessidade de aprovação
        if confidence < 0.7:
            risk_level = "high"
            requires_approval = True
        elif any(action.type in [ActionType.ROLLBACK_DEPLOYMENT, ActionType.RESTART_SERVICE] 
                for action in actions):
            risk_level = "medium"
            requires_approval = incident_data.get("severity") == "critical"
        
        # Estimar duração
        estimated_duration = sum(self._estimate_action_duration(action.type) for action in actions)
        
        return ResolutionPlan(
            incident_id=incident_id,
            actions=actions,
            estimated_duration=estimated_duration,
            risk_level=risk_level,
            requires_approval=requires_approval,
            created_at=datetime.utcnow()
        )
    
    async def _plan_cpu_resolution(self, incident_data: Dict[str, Any], 
                                  diagnosis: Dict[str, Any]) -> List[ResolutionAction]:
        """Planejar resolução para problemas de CPU"""
        
        actions = []
        
        # Escalar horizontalmente
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.SCALE_OUT,
            description="Scale out application instances to distribute CPU load",
            parameters={
                "target_instances": 5,
                "resource_group": self.config.get("resource_group"),
                "app_service_name": self.config.get("app_service_name")
            },
            status=ActionStatus.PENDING
        ))
        
        # Otimizar configuração se CPU muito alto
        cpu_usage = incident_data.get("metrics", {}).get("cpu_percentage", 0)
        if cpu_usage > 90:
            actions.append(ResolutionAction(
                id=str(uuid.uuid4()),
                type=ActionType.UPDATE_CONFIG,
                description="Optimize application configuration for CPU usage",
                parameters={
                    "config_changes": {
                        "thread_pool_size": 50,
                        "connection_timeout": 30,
                        "enable_caching": True
                    }
                },
                status=ActionStatus.PENDING
            ))
        
        return actions
    
    async def _plan_memory_resolution(self, incident_data: Dict[str, Any], 
                                     diagnosis: Dict[str, Any]) -> List[ResolutionAction]:
        """Planejar resolução para problemas de memória"""
        
        actions = []
        
        # Reiniciar serviço para limpar memória
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.RESTART_SERVICE,
            description="Restart service to clear memory leaks",
            parameters={
                "service_name": self.config.get("app_service_name"),
                "resource_group": self.config.get("resource_group"),
                "graceful_shutdown": True
            },
            status=ActionStatus.PENDING
        ))
        
        # Escalar verticalmente se necessário
        memory_usage = incident_data.get("metrics", {}).get("memory_percentage", 0)
        if memory_usage > 85:
            actions.append(ResolutionAction(
                id=str(uuid.uuid4()),
                type=ActionType.SCALE_UP,
                description="Scale up instance size for more memory",
                parameters={
                    "new_sku": "P2v3",  # Upgrade to higher tier
                    "resource_group": self.config.get("resource_group"),
                    "app_service_plan": self.config.get("app_service_plan")
                },
                status=ActionStatus.PENDING
            ))
        
        return actions
    
    async def _plan_database_resolution(self, incident_data: Dict[str, Any], 
                                       diagnosis: Dict[str, Any]) -> List[ResolutionAction]:
        """Planejar resolução para problemas de banco de dados"""
        
        actions = []
        
        # Otimizar configurações do banco
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.OPTIMIZE_DATABASE,
            description="Optimize database connection settings",
            parameters={
                "connection_pool_size": 20,
                "connection_timeout": 30,
                "query_timeout": 60,
                "enable_connection_pooling": True
            },
            status=ActionStatus.PENDING
        ))
        
        # Limpar cache se houver problemas de timeout
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.CLEAR_CACHE,
            description="Clear database query cache",
            parameters={
                "cache_type": "query_cache",
                "database_name": self.config.get("database_name", "phoenix-db")
            },
            status=ActionStatus.PENDING
        ))
        
        return actions
    
    async def _plan_performance_resolution(self, incident_data: Dict[str, Any], 
                                          diagnosis: Dict[str, Any]) -> List[ResolutionAction]:
        """Planejar resolução para problemas de performance"""
        
        actions = []
        
        # Implementar circuit breaker
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.CIRCUIT_BREAKER,
            description="Enable circuit breaker for failing services",
            parameters={
                "failure_threshold": 5,
                "timeout": 60,
                "fallback_enabled": True
            },
            status=ActionStatus.PENDING
        ))
        
        # Escalar para melhorar performance
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.SCALE_OUT,
            description="Scale out to improve response times",
            parameters={
                "target_instances": 3,
                "resource_group": self.config.get("resource_group"),
                "app_service_name": self.config.get("app_service_name")
            },
            status=ActionStatus.PENDING
        ))
        
        return actions
    
    async def _plan_error_resolution(self, incident_data: Dict[str, Any], 
                                    diagnosis: Dict[str, Any]) -> List[ResolutionAction]:
        """Planejar resolução para problemas de erro"""
        
        actions = []
        
        # Verificar se é problema de deployment recente
        recent_deployment = await self._check_recent_deployment()
        if recent_deployment:
            actions.append(ResolutionAction(
                id=str(uuid.uuid4()),
                type=ActionType.ROLLBACK_DEPLOYMENT,
                description="Rollback to previous stable deployment",
                parameters={
                    "deployment_id": recent_deployment.get("id"),
                    "target_version": recent_deployment.get("previous_version")
                },
                status=ActionStatus.PENDING
            ))
        else:
            # Reiniciar serviço para resolver erros temporários
            actions.append(ResolutionAction(
                id=str(uuid.uuid4()),
                type=ActionType.RESTART_SERVICE,
                description="Restart service to resolve temporary errors",
                parameters={
                    "service_name": self.config.get("app_service_name"),
                    "resource_group": self.config.get("resource_group"),
                    "graceful_shutdown": True
                },
                status=ActionStatus.PENDING
            ))
        
        return actions
    
    async def _plan_generic_resolution(self, incident_data: Dict[str, Any], 
                                      diagnosis: Dict[str, Any]) -> List[ResolutionAction]:
        """Planejar resolução genérica quando causa específica não é identificada"""
        
        actions = []
        
        # Ações conservadoras para problemas não identificados
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.CLEAR_CACHE,
            description="Clear application cache",
            parameters={
                "cache_type": "application_cache"
            },
            status=ActionStatus.PENDING
        ))
        
        # Escalar moderadamente
        actions.append(ResolutionAction(
            id=str(uuid.uuid4()),
            type=ActionType.SCALE_OUT,
            description="Scale out instances as precautionary measure",
            parameters={
                "target_instances": 2,
                "resource_group": self.config.get("resource_group"),
                "app_service_name": self.config.get("app_service_name")
            },
            status=ActionStatus.PENDING
        ))
        
        return actions
    
    def _estimate_action_duration(self, action_type: ActionType) -> int:
        """Estimar duração da ação em segundos"""
        
        durations = {
            ActionType.SCALE_OUT: 120,
            ActionType.SCALE_UP: 180,
            ActionType.RESTART_SERVICE: 60,
            ActionType.CLEAR_CACHE: 30,
            ActionType.OPTIMIZE_DATABASE: 45,
            ActionType.UPDATE_CONFIG: 30,
            ActionType.ROLLBACK_DEPLOYMENT: 300,
            ActionType.CIRCUIT_BREAKER: 15
        }
        
        return durations.get(action_type, 60)
    
    async def _check_recent_deployment(self) -> Optional[Dict[str, Any]]:
        """Verificar se houve deployment recente"""
        
        try:
            # Simular verificação de deployment recente
            # Em produção, consultar histórico de deployments
            recent_time = datetime.utcnow() - timedelta(hours=2)
            
            # Placeholder para lógica real de verificação
            return {
                "id": "deploy-123",
                "timestamp": recent_time.isoformat(),
                "previous_version": "v1.2.3"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check recent deployment: {e}")
            return None
    
    async def _request_approval(self, resolution_plan: ResolutionPlan):
        """Solicitar aprovação humana para ações de alto risco"""
        
        event_data = {
            "event_type": "approval_request",
            "incident_id": resolution_plan.incident_id,
            "plan": {
                "actions": [
                    {
                        "type": action.type.value,
                        "description": action.description,
                        "parameters": action.parameters
                    }
                    for action in resolution_plan.actions
                ],
                "risk_level": resolution_plan.risk_level,
                "estimated_duration": resolution_plan.estimated_duration
            },
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
        
        self.logger.info(f"Approval requested for incident {resolution_plan.incident_id}")
    
    async def _execute_plan(self, resolution_plan: ResolutionPlan) -> List[Dict[str, Any]]:
        """Executar plano de resolução"""
        
        results = []
        
        for action in resolution_plan.actions:
            try:
                action.status = ActionStatus.EXECUTING
                action.started_at = datetime.utcnow()
                
                # Executar ação baseada no tipo
                result = await self._execute_action(action)
                
                action.status = ActionStatus.COMPLETED if result.get("success") else ActionStatus.FAILED
                action.completed_at = datetime.utcnow()
                action.result = result
                
                results.append({
                    "action_id": action.id,
                    "type": action.type.value,
                    "description": action.description,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "duration": (action.completed_at - action.started_at).total_seconds()
                })
                
                # Registrar ação executada
                self.executed_actions[action.id] = action
                
                # Se ação falhou e rollback está habilitado
                if not result.get("success") and self.rollback_enabled and action.rollback_action:
                    await self._execute_rollback(action)
                
            except Exception as e:
                action.status = ActionStatus.FAILED
                action.completed_at = datetime.utcnow()
                
                results.append({
                    "action_id": action.id,
                    "type": action.type.value,
                    "description": action.description,
                    "success": False,
                    "message": f"Execution failed: {str(e)}",
                    "duration": (action.completed_at - action.started_at).total_seconds()
                })
                
                self.logger.error(f"Failed to execute action {action.id}: {e}")
        
        return results
    
    async def _execute_action(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar ação específica"""
        
        try:
            if action.type == ActionType.SCALE_OUT:
                return await self._execute_scale_out(action)
            elif action.type == ActionType.SCALE_UP:
                return await self._execute_scale_up(action)
            elif action.type == ActionType.RESTART_SERVICE:
                return await self._execute_restart_service(action)
            elif action.type == ActionType.CLEAR_CACHE:
                return await self._execute_clear_cache(action)
            elif action.type == ActionType.OPTIMIZE_DATABASE:
                return await self._execute_optimize_database(action)
            elif action.type == ActionType.UPDATE_CONFIG:
                return await self._execute_update_config(action)
            elif action.type == ActionType.ROLLBACK_DEPLOYMENT:
                return await self._execute_rollback_deployment(action)
            elif action.type == ActionType.CIRCUIT_BREAKER:
                return await self._execute_circuit_breaker(action)
            else:
                return {"success": False, "message": f"Unknown action type: {action.type}"}
                
        except Exception as e:
            return {"success": False, "message": f"Action execution failed: {str(e)}"}
    
    async def _execute_scale_out(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar escalonamento horizontal"""
        
        try:
            params = action.parameters
            target_instances = params.get("target_instances", 3)
            
            # Verificar limites de segurança
            if target_instances > self.safety_limits["max_scale_instances"]:
                return {
                    "success": False,
                    "message": f"Target instances ({target_instances}) exceeds safety limit"
                }
            
            # Simular escalonamento (em produção, usar Azure Management API)
            self.logger.info(f"Scaling out to {target_instances} instances")
            
            # Simular tempo de execução
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "message": f"Successfully scaled out to {target_instances} instances",
                "details": {
                    "previous_instances": 1,
                    "new_instances": target_instances
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Scale out failed: {str(e)}"}
    
    async def _execute_scale_up(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar escalonamento vertical"""
        
        try:
            params = action.parameters
            new_sku = params.get("new_sku", "P2v3")
            
            self.logger.info(f"Scaling up to SKU: {new_sku}")
            
            # Simular tempo de execução
            await asyncio.sleep(3)
            
            return {
                "success": True,
                "message": f"Successfully scaled up to {new_sku}",
                "details": {
                    "previous_sku": "P1v3",
                    "new_sku": new_sku
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Scale up failed: {str(e)}"}
    
    async def _execute_restart_service(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar reinicialização de serviço"""
        
        try:
            params = action.parameters
            service_name = params.get("service_name")
            graceful = params.get("graceful_shutdown", True)
            
            self.logger.info(f"Restarting service: {service_name}")
            
            if graceful:
                # Simular graceful shutdown
                await asyncio.sleep(1)
            
            # Simular restart
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "message": f"Successfully restarted service {service_name}",
                "details": {
                    "graceful_shutdown": graceful,
                    "restart_time": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Service restart failed: {str(e)}"}
    
    async def _execute_clear_cache(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar limpeza de cache"""
        
        try:
            params = action.parameters
            cache_type = params.get("cache_type", "application_cache")
            
            self.logger.info(f"Clearing cache: {cache_type}")
            
            # Simular limpeza de cache
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "message": f"Successfully cleared {cache_type}",
                "details": {
                    "cache_type": cache_type,
                    "cleared_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Cache clear failed: {str(e)}"}
    
    async def _execute_optimize_database(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar otimização de banco de dados"""
        
        try:
            params = action.parameters
            
            self.logger.info("Optimizing database configuration")
            
            # Simular otimização
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "message": "Database configuration optimized",
                "details": {
                    "optimizations_applied": list(params.keys()),
                    "optimized_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Database optimization failed: {str(e)}"}
    
    async def _execute_update_config(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar atualização de configuração"""
        
        try:
            params = action.parameters
            config_changes = params.get("config_changes", {})
            
            self.logger.info("Updating application configuration")
            
            # Simular atualização de configuração
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "details": {
                    "changes_applied": config_changes,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Configuration update failed: {str(e)}"}
    
    async def _execute_rollback_deployment(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar rollback de deployment"""
        
        try:
            params = action.parameters
            target_version = params.get("target_version")
            
            self.logger.info(f"Rolling back to version: {target_version}")
            
            # Simular rollback (operação mais demorada)
            await asyncio.sleep(5)
            
            return {
                "success": True,
                "message": f"Successfully rolled back to version {target_version}",
                "details": {
                    "target_version": target_version,
                    "rolled_back_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Rollback failed: {str(e)}"}
    
    async def _execute_circuit_breaker(self, action: ResolutionAction) -> Dict[str, Any]:
        """Executar implementação de circuit breaker"""
        
        try:
            params = action.parameters
            failure_threshold = params.get("failure_threshold", 5)
            
            self.logger.info("Enabling circuit breaker")
            
            # Simular configuração de circuit breaker
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "message": "Circuit breaker enabled successfully",
                "details": {
                    "failure_threshold": failure_threshold,
                    "enabled_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Circuit breaker setup failed: {str(e)}"}
    
    async def _execute_rollback(self, action: ResolutionAction):
        """Executar rollback de uma ação que falhou"""
        
        if not action.rollback_action:
            return
        
        try:
            self.logger.info(f"Executing rollback for action {action.id}")
            rollback_result = await self._execute_action(action.rollback_action)
            
            if rollback_result.get("success"):
                action.status = ActionStatus.ROLLED_BACK
                self.logger.info(f"Successfully rolled back action {action.id}")
            else:
                self.logger.error(f"Rollback failed for action {action.id}")
                
        except Exception as e:
            self.logger.error(f"Rollback execution failed for action {action.id}: {e}")
    
    async def _send_resolution_result(self, incident_id: str, success: bool, 
                                     actions_taken: List[Dict[str, Any]]):
        """Enviar resultado da resolução para o orquestrador"""
        
        event_data = {
            "event_type": "resolution_result",
            "incident_id": incident_id,
            "agent_type": "resolution",
            "success": success,
            "actions_taken": actions_taken,
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
        
        self.logger.info(f"Resolution result sent for incident {incident_id}")


# Função para criar instância do agente de resolução
def create_resolution_agent(config: Dict[str, Any]) -> PhoenixResolutionAgent:
    """Factory function para criar instância do agente de resolução"""
    return PhoenixResolutionAgent(config)

