"""
Phoenix Diagnostic Agent
Analisa logs e métricas para identificar causa raiz de incidentes
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import uuid
import re
from collections import defaultdict

from azure.cosmos import CosmosClient
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from azure.monitor.query import LogsQueryClient, MetricsQueryClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


@dataclass
class DiagnosticResult:
    incident_id: str
    root_cause: str
    confidence: float
    evidence: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_duration: float
    patterns_detected: List[str]
    anomalies: List[Dict[str, Any]]


@dataclass
class LogPattern:
    pattern: str
    frequency: int
    severity: str
    first_seen: datetime
    last_seen: datetime
    examples: List[str]


class PhoenixDiagnosticAgent:
    """
    Agente de Diagnóstico do Sistema Phoenix
    
    Responsabilidades:
    - Analisar logs de aplicação e sistema
    - Identificar padrões anômalos em métricas
    - Correlacionar eventos temporalmente
    - Determinar causa raiz com alta confiança
    - Fornecer recomendações baseadas em análise
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = f"diagnostic-{uuid.uuid4().hex[:8]}"
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar clientes Azure
        self._init_azure_clients()
        
        # Configurações de análise
        self.analysis_timeout = config.get("analysis_timeout", 60)
        self.confidence_threshold = config.get("confidence_threshold", 0.85)
        
        # Padrões conhecidos de problemas
        self.known_patterns = self._load_known_patterns()
        
        # Cache de análises recentes
        self.analysis_cache = {}
        
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
            
            # Azure Monitor para logs e métricas
            credential = DefaultAzureCredential()
            self.logs_client = LogsQueryClient(credential)
            self.metrics_client = MetricsQueryClient(credential)
            
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
    
    def _load_known_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Carregar padrões conhecidos de problemas"""
        return {
            "high_cpu": {
                "pattern": r"CPU usage.*?(\d+)%",
                "threshold": 80,
                "severity": "high",
                "category": "performance"
            },
            "memory_leak": {
                "pattern": r"OutOfMemoryError|Memory usage.*?(\d+)%",
                "threshold": 90,
                "severity": "critical",
                "category": "memory"
            },
            "database_timeout": {
                "pattern": r"database.*?timeout|connection.*?timeout",
                "threshold": 1,
                "severity": "high",
                "category": "database"
            },
            "api_errors": {
                "pattern": r"HTTP.*?5\d\d|Internal Server Error",
                "threshold": 10,
                "severity": "medium",
                "category": "api"
            },
            "disk_space": {
                "pattern": r"disk.*?full|no space left",
                "threshold": 1,
                "severity": "critical",
                "category": "storage"
            }
        }
    
    async def analyze_incident(self, incident_data: Dict[str, Any]) -> DiagnosticResult:
        """
        Analisar incidente e determinar causa raiz
        
        Args:
            incident_data: Dados do incidente a ser analisado
            
        Returns:
            Resultado do diagnóstico com causa raiz e recomendações
        """
        start_time = datetime.utcnow()
        incident_id = incident_data.get("id")
        
        try:
            self.logger.info(f"Starting diagnostic analysis for incident {incident_id}")
            
            # Coletar dados de múltiplas fontes
            logs_data = await self._collect_logs(incident_data)
            metrics_data = await self._collect_metrics(incident_data)
            
            # Analisar padrões nos logs
            log_patterns = await self._analyze_log_patterns(logs_data)
            
            # Detectar anomalias nas métricas
            metric_anomalies = await self._detect_metric_anomalies(metrics_data)
            
            # Correlacionar eventos temporalmente
            correlations = await self._correlate_events(logs_data, metrics_data, incident_data)
            
            # Usar IA para análise avançada
            ai_analysis = await self._ai_root_cause_analysis(
                incident_data, logs_data, metrics_data, log_patterns, metric_anomalies
            )
            
            # Combinar todas as análises
            root_cause, confidence = await self._determine_root_cause(
                log_patterns, metric_anomalies, correlations, ai_analysis
            )
            
            # Gerar recomendações
            recommendations = await self._generate_recommendations(
                root_cause, log_patterns, metric_anomalies
            )
            
            # Criar resultado do diagnóstico
            analysis_duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = DiagnosticResult(
                incident_id=incident_id,
                root_cause=root_cause,
                confidence=confidence,
                evidence=self._compile_evidence(log_patterns, metric_anomalies, correlations),
                recommendations=recommendations,
                analysis_duration=analysis_duration,
                patterns_detected=[p.pattern for p in log_patterns],
                anomalies=metric_anomalies
            )
            
            # Enviar resultado para o orquestrador
            await self._send_diagnostic_result(result)
            
            self.logger.info(f"Diagnostic analysis completed for incident {incident_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze incident {incident_id}: {e}")
            raise
    
    async def _collect_logs(self, incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Coletar logs relevantes do Azure Monitor"""
        
        try:
            # Definir janela de tempo para análise
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)  # Última hora
            
            # Query KQL para logs de aplicação
            query = """
            AppTraces
            | union AppExceptions
            | union AppRequests
            | where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
            | where SeverityLevel >= 2
            | project TimeGenerated, SeverityLevel, Message, Properties
            | order by TimeGenerated desc
            | limit 1000
            """.format(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )
            
            # Executar query
            response = self.logs_client.query_workspace(
                workspace_id=self.config["log_analytics_workspace_id"],
                query=query,
                timespan=(start_time, end_time)
            )
            
            logs = []
            for table in response.tables:
                for row in table.rows:
                    logs.append({
                        "timestamp": row[0],
                        "severity": row[1],
                        "message": row[2],
                        "properties": row[3] if row[3] else {}
                    })
            
            self.logger.info(f"Collected {len(logs)} log entries")
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to collect logs: {e}")
            return []
    
    async def _collect_metrics(self, incident_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Coletar métricas relevantes do Azure Monitor"""
        
        try:
            # Definir janela de tempo
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics_data = {}
            
            # Métricas de performance comuns
            metric_names = [
                "Percentage CPU",
                "Memory percentage",
                "Http5xx",
                "ResponseTime",
                "Requests",
                "Exceptions"
            ]
            
            for metric_name in metric_names:
                try:
                    # Simular coleta de métricas (em produção, usar resource_uri real)
                    metrics_data[metric_name] = self._generate_sample_metrics(
                        metric_name, start_time, end_time
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to collect metric {metric_name}: {e}")
            
            return metrics_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return {}
    
    def _generate_sample_metrics(self, metric_name: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Gerar métricas de exemplo para demonstração"""
        
        metrics = []
        current_time = start_time
        
        while current_time < end_time:
            # Simular valores baseados no tipo de métrica
            if "CPU" in metric_name:
                value = np.random.normal(75, 15)  # CPU alto para simular problema
            elif "Memory" in metric_name:
                value = np.random.normal(85, 10)  # Memória alta
            elif "Http5xx" in metric_name:
                value = np.random.poisson(5)  # Alguns erros 5xx
            elif "ResponseTime" in metric_name:
                value = np.random.normal(2000, 500)  # Tempo de resposta alto
            else:
                value = np.random.normal(100, 20)
            
            metrics.append({
                "timestamp": current_time,
                "value": max(0, value),  # Não permitir valores negativos
                "unit": self._get_metric_unit(metric_name)
            })
            
            current_time += timedelta(minutes=5)
        
        return metrics
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Obter unidade da métrica"""
        if "percentage" in metric_name.lower() or "CPU" in metric_name:
            return "percent"
        elif "Time" in metric_name:
            return "milliseconds"
        elif "Requests" in metric_name or "Exceptions" in metric_name:
            return "count"
        else:
            return "unit"
    
    async def _analyze_log_patterns(self, logs_data: List[Dict[str, Any]]) -> List[LogPattern]:
        """Analisar padrões nos logs"""
        
        patterns_found = []
        pattern_counts = defaultdict(list)
        
        for log_entry in logs_data:
            message = log_entry.get("message", "")
            timestamp = log_entry.get("timestamp")
            
            # Verificar padrões conhecidos
            for pattern_name, pattern_config in self.known_patterns.items():
                pattern = pattern_config["pattern"]
                
                if re.search(pattern, message, re.IGNORECASE):
                    pattern_counts[pattern_name].append({
                        "timestamp": timestamp,
                        "message": message,
                        "severity": pattern_config["severity"]
                    })
        
        # Criar objetos LogPattern
        for pattern_name, occurrences in pattern_counts.items():
            if len(occurrences) >= self.known_patterns[pattern_name]["threshold"]:
                timestamps = [occ["timestamp"] for occ in occurrences]
                
                pattern = LogPattern(
                    pattern=pattern_name,
                    frequency=len(occurrences),
                    severity=self.known_patterns[pattern_name]["severity"],
                    first_seen=min(timestamps),
                    last_seen=max(timestamps),
                    examples=[occ["message"] for occ in occurrences[:3]]
                )
                patterns_found.append(pattern)
        
        self.logger.info(f"Found {len(patterns_found)} significant log patterns")
        return patterns_found
    
    async def _detect_metric_anomalies(self, metrics_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detectar anomalias nas métricas usando análise estatística"""
        
        anomalies = []
        
        for metric_name, data_points in metrics_data.items():
            if len(data_points) < 10:  # Dados insuficientes
                continue
            
            values = [dp["value"] for dp in data_points]
            timestamps = [dp["timestamp"] for dp in data_points]
            
            # Calcular estatísticas
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            # Detectar outliers (valores > 2 desvios padrão)
            threshold = mean_val + (2 * std_val)
            
            for i, value in enumerate(values):
                if value > threshold:
                    anomalies.append({
                        "metric": metric_name,
                        "timestamp": timestamps[i],
                        "value": value,
                        "expected_range": f"{mean_val:.2f} ± {std_val:.2f}",
                        "severity": self._classify_anomaly_severity(metric_name, value, mean_val, std_val)
                    })
        
        # Usar clustering para detectar padrões anômalos
        cluster_anomalies = await self._detect_cluster_anomalies(metrics_data)
        anomalies.extend(cluster_anomalies)
        
        self.logger.info(f"Detected {len(anomalies)} metric anomalies")
        return anomalies
    
    def _classify_anomaly_severity(self, metric_name: str, value: float, mean_val: float, std_val: float) -> str:
        """Classificar severidade da anomalia"""
        
        deviations = abs(value - mean_val) / std_val if std_val > 0 else 0
        
        if deviations > 3:
            return "critical"
        elif deviations > 2.5:
            return "high"
        elif deviations > 2:
            return "medium"
        else:
            return "low"
    
    async def _detect_cluster_anomalies(self, metrics_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detectar anomalias usando clustering"""
        
        try:
            # Preparar dados para clustering
            all_metrics = []
            timestamps = []
            
            # Assumir que todas as métricas têm os mesmos timestamps
            if not metrics_data:
                return []
            
            first_metric = list(metrics_data.keys())[0]
            timestamps = [dp["timestamp"] for dp in metrics_data[first_metric]]
            
            # Criar matriz de features
            for timestamp in timestamps:
                metric_values = []
                for metric_name, data_points in metrics_data.items():
                    # Encontrar valor para este timestamp
                    value = next((dp["value"] for dp in data_points if dp["timestamp"] == timestamp), 0)
                    metric_values.append(value)
                all_metrics.append(metric_values)
            
            if len(all_metrics) < 5:  # Dados insuficientes para clustering
                return []
            
            # Normalizar dados
            scaler = StandardScaler()
            normalized_metrics = scaler.fit_transform(all_metrics)
            
            # Aplicar DBSCAN para detectar outliers
            clustering = DBSCAN(eps=0.5, min_samples=3)
            cluster_labels = clustering.fit_predict(normalized_metrics)
            
            # Pontos com label -1 são considerados outliers
            anomalies = []
            for i, label in enumerate(cluster_labels):
                if label == -1:  # Outlier
                    anomalies.append({
                        "type": "cluster_anomaly",
                        "timestamp": timestamps[i],
                        "metrics_snapshot": dict(zip(metrics_data.keys(), all_metrics[i])),
                        "severity": "medium"
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect cluster anomalies: {e}")
            return []
    
    async def _correlate_events(self, logs_data: List[Dict[str, Any]], 
                               metrics_data: Dict[str, List[Dict[str, Any]]], 
                               incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Correlacionar eventos temporalmente"""
        
        correlations = []
        incident_time = datetime.fromisoformat(incident_data.get("created_at", datetime.utcnow().isoformat()))
        
        # Janela de correlação (±5 minutos do incidente)
        correlation_window = timedelta(minutes=5)
        
        # Correlacionar logs próximos ao tempo do incidente
        relevant_logs = [
            log for log in logs_data
            if abs(log["timestamp"] - incident_time) <= correlation_window
        ]
        
        if relevant_logs:
            correlations.append({
                "type": "temporal_log_correlation",
                "count": len(relevant_logs),
                "time_window": "±5 minutes from incident",
                "severity_distribution": self._analyze_log_severity_distribution(relevant_logs)
            })
        
        # Correlacionar picos de métricas
        for metric_name, data_points in metrics_data.items():
            relevant_metrics = [
                dp for dp in data_points
                if abs(dp["timestamp"] - incident_time) <= correlation_window
            ]
            
            if relevant_metrics:
                avg_value = np.mean([dp["value"] for dp in relevant_metrics])
                correlations.append({
                    "type": "metric_correlation",
                    "metric": metric_name,
                    "average_value": avg_value,
                    "time_window": "±5 minutes from incident"
                })
        
        return correlations
    
    def _analyze_log_severity_distribution(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analisar distribuição de severidade nos logs"""
        
        distribution = defaultdict(int)
        for log in logs:
            severity = log.get("severity", 0)
            if severity >= 4:
                distribution["critical"] += 1
            elif severity >= 3:
                distribution["error"] += 1
            elif severity >= 2:
                distribution["warning"] += 1
            else:
                distribution["info"] += 1
        
        return dict(distribution)
    
    async def _ai_root_cause_analysis(self, incident_data: Dict[str, Any], 
                                     logs_data: List[Dict[str, Any]],
                                     metrics_data: Dict[str, List[Dict[str, Any]]],
                                     log_patterns: List[LogPattern],
                                     metric_anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Usar IA para análise avançada de causa raiz"""
        
        try:
            # Preparar contexto para a IA
            context = {
                "incident": {
                    "title": incident_data.get("title", ""),
                    "description": incident_data.get("description", ""),
                    "severity": incident_data.get("severity", ""),
                    "metrics": incident_data.get("metrics", {})
                },
                "log_patterns": [
                    {
                        "pattern": p.pattern,
                        "frequency": p.frequency,
                        "severity": p.severity,
                        "examples": p.examples[:2]  # Limitar exemplos
                    }
                    for p in log_patterns
                ],
                "metric_anomalies": metric_anomalies[:5],  # Limitar anomalias
                "metrics_summary": {
                    metric_name: {
                        "avg": np.mean([dp["value"] for dp in data_points]),
                        "max": np.max([dp["value"] for dp in data_points]),
                        "count": len(data_points)
                    }
                    for metric_name, data_points in metrics_data.items()
                }
            }
            
            prompt = f"""
            Analise o seguinte incidente e determine a causa raiz mais provável:
            
            CONTEXTO DO INCIDENTE:
            {json.dumps(context, indent=2, default=str)}
            
            Com base nos dados fornecidos, identifique:
            1. A causa raiz mais provável
            2. Nível de confiança (0.0 a 1.0)
            3. Evidências que suportam sua conclusão
            4. Possíveis causas alternativas
            
            Responda em formato JSON:
            {{
                "root_cause": "descrição da causa raiz",
                "confidence": 0.85,
                "primary_evidence": ["evidência 1", "evidência 2"],
                "alternative_causes": ["causa alternativa 1"],
                "reasoning": "explicação do raciocínio"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse da resposta JSON
            ai_result = json.loads(response.choices[0].message.content)
            
            self.logger.info("AI root cause analysis completed")
            return ai_result
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            return {
                "root_cause": "AI analysis unavailable",
                "confidence": 0.0,
                "primary_evidence": [],
                "alternative_causes": [],
                "reasoning": f"AI analysis failed: {str(e)}"
            }
    
    async def _determine_root_cause(self, log_patterns: List[LogPattern],
                                   metric_anomalies: List[Dict[str, Any]],
                                   correlations: List[Dict[str, Any]],
                                   ai_analysis: Dict[str, Any]) -> Tuple[str, float]:
        """Determinar causa raiz combinando todas as análises"""
        
        # Começar com análise da IA se disponível
        if ai_analysis.get("confidence", 0) >= 0.7:
            return ai_analysis["root_cause"], ai_analysis["confidence"]
        
        # Fallback para análise baseada em regras
        confidence_scores = []
        potential_causes = []
        
        # Analisar padrões de log
        for pattern in log_patterns:
            if pattern.severity in ["critical", "high"]:
                potential_causes.append(f"Log pattern: {pattern.pattern}")
                confidence_scores.append(0.8 if pattern.severity == "critical" else 0.6)
        
        # Analisar anomalias de métricas
        critical_anomalies = [a for a in metric_anomalies if a.get("severity") == "critical"]
        if critical_anomalies:
            for anomaly in critical_anomalies:
                potential_causes.append(f"Metric anomaly: {anomaly['metric']}")
                confidence_scores.append(0.7)
        
        # Determinar causa mais provável
        if potential_causes:
            max_confidence = max(confidence_scores)
            best_cause_index = confidence_scores.index(max_confidence)
            root_cause = potential_causes[best_cause_index]
        else:
            root_cause = "Unable to determine root cause with available data"
            max_confidence = 0.3
        
        return root_cause, max_confidence
    
    async def _generate_recommendations(self, root_cause: str,
                                       log_patterns: List[LogPattern],
                                       metric_anomalies: List[Dict[str, Any]]) -> List[str]:
        """Gerar recomendações baseadas na análise"""
        
        recommendations = []
        
        # Recomendações baseadas em padrões de log
        for pattern in log_patterns:
            if pattern.pattern == "high_cpu":
                recommendations.append("Scale out application instances to distribute CPU load")
                recommendations.append("Investigate CPU-intensive processes")
            elif pattern.pattern == "memory_leak":
                recommendations.append("Restart affected services to clear memory")
                recommendations.append("Investigate memory leaks in application code")
            elif pattern.pattern == "database_timeout":
                recommendations.append("Check database connection pool settings")
                recommendations.append("Optimize slow database queries")
        
        # Recomendações baseadas em anomalias de métricas
        for anomaly in metric_anomalies:
            metric = anomaly.get("metric", "")
            if "CPU" in metric:
                recommendations.append("Monitor CPU usage and consider horizontal scaling")
            elif "Memory" in metric:
                recommendations.append("Investigate memory usage patterns")
            elif "ResponseTime" in metric:
                recommendations.append("Optimize application performance")
        
        # Recomendações gerais se nenhuma específica foi encontrada
        if not recommendations:
            recommendations.extend([
                "Monitor system metrics for patterns",
                "Review recent deployments or configuration changes",
                "Check external dependencies and services",
                "Verify network connectivity and latency"
            ])
        
        return recommendations
    
    def _compile_evidence(self, log_patterns: List[LogPattern],
                         metric_anomalies: List[Dict[str, Any]],
                         correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compilar evidências para o diagnóstico"""
        
        evidence = []
        
        # Evidências dos padrões de log
        for pattern in log_patterns:
            evidence.append({
                "type": "log_pattern",
                "description": f"Pattern '{pattern.pattern}' found {pattern.frequency} times",
                "severity": pattern.severity,
                "examples": pattern.examples[:2]
            })
        
        # Evidências das anomalias de métricas
        for anomaly in metric_anomalies:
            evidence.append({
                "type": "metric_anomaly",
                "description": f"Anomaly in {anomaly.get('metric', 'unknown metric')}",
                "value": anomaly.get("value"),
                "severity": anomaly.get("severity", "unknown")
            })
        
        # Evidências das correlações
        for correlation in correlations:
            evidence.append({
                "type": "correlation",
                "description": f"Temporal correlation: {correlation.get('type', 'unknown')}",
                "details": correlation
            })
        
        return evidence
    
    async def _send_diagnostic_result(self, result: DiagnosticResult):
        """Enviar resultado do diagnóstico para o orquestrador"""
        
        event_data = {
            "event_type": "diagnostic_result",
            "incident_id": result.incident_id,
            "agent_type": "diagnostic",
            "diagnosis": {
                "root_cause": result.root_cause,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "patterns_detected": result.patterns_detected,
                "anomalies": result.anomalies
            },
            "recommendations": result.recommendations,
            "analysis_duration": result.analysis_duration,
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": self.agent_id
        }
        
        async with self.event_producer:
            event = EventData(json.dumps(event_data, default=str))
            await self.event_producer.send_batch([event])
        
        self.logger.info(f"Diagnostic result sent for incident {result.incident_id}")


# Função para criar instância do agente diagnóstico
def create_diagnostic_agent(config: Dict[str, Any]) -> PhoenixDiagnosticAgent:
    """Factory function para criar instância do agente diagnóstico"""
    return PhoenixDiagnosticAgent(config)

