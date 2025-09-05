/**
 * Phoenix Integration Service
 * Serviço responsável por integrar a aplicação e-commerce com o sistema Phoenix
 */

const axios = require('axios');
const winston = require('winston');

class PhoenixIntegration {
    constructor() {
        this.phoenixBaseUrl = process.env.PHOENIX_ORCHESTRATOR_URL || 'https://func-orchestrator-phoenix-dev.azurewebsites.net/api';
        this.functionKey = process.env.PHOENIX_FUNCTION_KEY || '';
        this.appName = process.env.APP_NAME || 'ecommerce-app';
        this.environment = process.env.ENVIRONMENT || 'dev';
        
        this.logger = winston.createLogger({
            level: 'info',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.json()
            ),
            transports: [
                new winston.transports.Console()
            ]
        });
        
        this.alertQueue = [];
        this.isProcessingQueue = false;
        this.maxRetries = 3;
        this.retryDelay = 5000; // 5 segundos
    }
    
    async initialize() {
        this.logger.info('Inicializando integração com Phoenix System...');
        
        try {
            // Testar conectividade com o Phoenix
            await this.testConnection();
            
            // Iniciar processamento da fila de alertas
            this.startQueueProcessor();
            
            this.logger.info('Integração com Phoenix System inicializada com sucesso');
        } catch (error) {
            this.logger.error('Erro ao inicializar integração com Phoenix:', error.message);
            // Não falhar a inicialização se Phoenix não estiver disponível
        }
    }
    
    async testConnection() {
        try {
            const response = await axios.get(`${this.phoenixBaseUrl}/health`, {
                headers: this.getHeaders(),
                timeout: 10000
            });
            
            if (response.data.status === 'healthy') {
                this.logger.info('Conexão com Phoenix System estabelecida');
                return true;
            } else {
                throw new Error('Phoenix System não está saudável');
            }
        } catch (error) {
            this.logger.warn('Falha ao conectar com Phoenix System:', error.message);
            throw error;
        }
    }
    
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': `${this.appName}/${this.environment}`
        };
        
        if (this.functionKey) {
            headers['x-functions-key'] = this.functionKey;
        }
        
        return headers;
    }
    
    /**
     * Reportar alerta para o sistema Phoenix
     * @param {Object} alertData - Dados do alerta
     */
    async reportAlert(alertData) {
        const alert = {
            title: alertData.title,
            description: alertData.description,
            severity: alertData.severity || 'medium',
            source: alertData.source || this.appName,
            metrics: alertData.metrics || {},
            timestamp: new Date().toISOString(),
            environment: this.environment,
            application: this.appName,
            ...alertData
        };
        
        // Adicionar à fila para processamento assíncrono
        this.alertQueue.push(alert);
        
        this.logger.info('Alerta adicionado à fila para Phoenix:', {
            title: alert.title,
            severity: alert.severity
        });
    }
    
    /**
     * Reportar erro para o sistema Phoenix
     * @param {Error} error - Erro ocorrido
     * @param {Object} context - Contexto adicional (req, etc.)
     */
    async reportError(error, context = {}) {
        const alertData = {
            title: `Application Error: ${error.name || 'UnknownError'}`,
            description: error.message || 'Unknown error occurred',
            severity: this.classifyErrorSeverity(error),
            source: this.appName,
            metrics: {
                error_type: error.name || 'UnknownError',
                stack_trace: error.stack,
                url: context.originalUrl,
                method: context.method,
                user_agent: context.get ? context.get('User-Agent') : undefined,
                ip: context.ip
            },
            error_details: {
                name: error.name,
                message: error.message,
                stack: error.stack,
                code: error.code
            }
        };
        
        await this.reportAlert(alertData);
    }
    
    /**
     * Reportar métricas de performance
     * @param {Object} metrics - Métricas coletadas
     */
    async reportMetrics(metrics) {
        // Verificar se métricas indicam problemas
        const issues = this.analyzeMetrics(metrics);
        
        for (const issue of issues) {
            await this.reportAlert(issue);
        }
    }
    
    /**
     * Analisar métricas para identificar problemas
     * @param {Object} metrics - Métricas para análise
     * @returns {Array} Lista de problemas identificados
     */
    analyzeMetrics(metrics) {
        const issues = [];
        
        // CPU alto
        if (metrics.cpu_percentage && metrics.cpu_percentage > 80) {
            issues.push({
                title: 'High CPU Usage Detected',
                description: `CPU usage is at ${metrics.cpu_percentage}%`,
                severity: metrics.cpu_percentage > 90 ? 'critical' : 'high',
                metrics: { cpu_percentage: metrics.cpu_percentage }
            });
        }
        
        // Memória alta
        if (metrics.memory_percentage && metrics.memory_percentage > 85) {
            issues.push({
                title: 'High Memory Usage Detected',
                description: `Memory usage is at ${metrics.memory_percentage}%`,
                severity: metrics.memory_percentage > 95 ? 'critical' : 'high',
                metrics: { memory_percentage: metrics.memory_percentage }
            });
        }
        
        // Tempo de resposta alto
        if (metrics.avg_response_time && metrics.avg_response_time > 2000) {
            issues.push({
                title: 'High Response Time Detected',
                description: `Average response time is ${metrics.avg_response_time}ms`,
                severity: metrics.avg_response_time > 5000 ? 'critical' : 'medium',
                metrics: { avg_response_time: metrics.avg_response_time }
            });
        }
        
        // Taxa de erro alta
        if (metrics.error_rate && metrics.error_rate > 5) {
            issues.push({
                title: 'High Error Rate Detected',
                description: `Error rate is at ${metrics.error_rate}%`,
                severity: metrics.error_rate > 20 ? 'critical' : 'high',
                metrics: { error_rate: metrics.error_rate }
            });
        }
        
        // Conexões de banco de dados
        if (metrics.db_connection_errors && metrics.db_connection_errors > 0) {
            issues.push({
                title: 'Database Connection Errors',
                description: `${metrics.db_connection_errors} database connection errors detected`,
                severity: 'high',
                metrics: { db_connection_errors: metrics.db_connection_errors }
            });
        }
        
        return issues;
    }
    
    /**
     * Classificar severidade do erro
     * @param {Error} error - Erro para classificar
     * @returns {string} Nível de severidade
     */
    classifyErrorSeverity(error) {
        // Erros críticos
        if (error.name === 'MongoNetworkError' || 
            error.name === 'MongoServerError' ||
            error.code === 'ECONNREFUSED' ||
            error.code === 'ETIMEDOUT') {
            return 'critical';
        }
        
        // Erros altos
        if (error.name === 'ValidationError' ||
            error.name === 'CastError' ||
            error.statusCode >= 500) {
            return 'high';
        }
        
        // Erros médios
        if (error.statusCode >= 400) {
            return 'medium';
        }
        
        // Padrão
        return 'low';
    }
    
    /**
     * Processar fila de alertas
     */
    startQueueProcessor() {
        setInterval(async () => {
            if (this.isProcessingQueue || this.alertQueue.length === 0) {
                return;
            }
            
            this.isProcessingQueue = true;
            
            try {
                while (this.alertQueue.length > 0) {
                    const alert = this.alertQueue.shift();
                    await this.sendAlertToPhoenix(alert);
                }
            } catch (error) {
                this.logger.error('Erro ao processar fila de alertas:', error.message);
            } finally {
                this.isProcessingQueue = false;
            }
        }, 5000); // Processar a cada 5 segundos
    }
    
    /**
     * Enviar alerta para o Phoenix
     * @param {Object} alert - Alerta para enviar
     */
    async sendAlertToPhoenix(alert, retryCount = 0) {
        try {
            const response = await axios.post(`${this.phoenixBaseUrl}/alert`, alert, {
                headers: this.getHeaders(),
                timeout: 15000
            });
            
            if (response.data.success) {
                this.logger.info('Alerta enviado com sucesso para Phoenix:', {
                    incident_id: response.data.incident_id,
                    title: alert.title
                });
            } else {
                throw new Error('Phoenix retornou sucesso = false');
            }
            
        } catch (error) {
            this.logger.error('Erro ao enviar alerta para Phoenix:', {
                error: error.message,
                alert_title: alert.title,
                retry_count: retryCount
            });
            
            // Tentar novamente se não excedeu o limite
            if (retryCount < this.maxRetries) {
                setTimeout(() => {
                    this.sendAlertToPhoenix(alert, retryCount + 1);
                }, this.retryDelay * (retryCount + 1));
            } else {
                this.logger.error('Máximo de tentativas excedido para alerta:', alert.title);
            }
        }
    }
    
    /**
     * Obter status de um incidente
     * @param {string} incidentId - ID do incidente
     * @returns {Object} Status do incidente
     */
    async getIncidentStatus(incidentId) {
        try {
            const response = await axios.get(`${this.phoenixBaseUrl}/incident/${incidentId}`, {
                headers: this.getHeaders(),
                timeout: 10000
            });
            
            return response.data;
        } catch (error) {
            this.logger.error('Erro ao obter status do incidente:', error.message);
            throw error;
        }
    }
    
    /**
     * Obter lista de incidentes ativos
     * @returns {Array} Lista de incidentes
     */
    async getActiveIncidents() {
        try {
            const response = await axios.get(`${this.phoenixBaseUrl}/incidents`, {
                headers: this.getHeaders(),
                timeout: 10000
            });
            
            return response.data.incidents || [];
        } catch (error) {
            this.logger.error('Erro ao obter incidentes ativos:', error.message);
            throw error;
        }
    }
    
    /**
     * Simular diferentes tipos de problemas para demonstração
     */
    async simulateProblems() {
        const problems = [
            {
                title: 'Database Connection Timeout',
                description: 'Connection to MongoDB timed out after 30 seconds',
                severity: 'critical',
                metrics: {
                    db_connection_time: 30000,
                    active_connections: 0,
                    error_rate: 25
                }
            },
            {
                title: 'High Memory Usage',
                description: 'Application memory usage exceeded 90%',
                severity: 'high',
                metrics: {
                    memory_percentage: 92,
                    heap_used: 1800000000,
                    heap_total: 2000000000
                }
            },
            {
                title: 'Slow API Response',
                description: 'API response time increased significantly',
                severity: 'medium',
                metrics: {
                    avg_response_time: 3500,
                    p95_response_time: 8000,
                    requests_per_second: 45
                }
            },
            {
                title: 'Payment Gateway Error',
                description: 'Payment processing failures detected',
                severity: 'high',
                metrics: {
                    payment_success_rate: 75,
                    failed_payments: 15,
                    revenue_impact: 2500
                }
            }
        ];
        
        // Selecionar problema aleatório
        const problem = problems[Math.floor(Math.random() * problems.length)];
        
        this.logger.info('Simulando problema:', problem.title);
        await this.reportAlert(problem);
    }
    
    /**
     * Gerar relatório de integração
     * @returns {Object} Relatório de status
     */
    generateIntegrationReport() {
        return {
            phoenix_url: this.phoenixBaseUrl,
            app_name: this.appName,
            environment: this.environment,
            queue_size: this.alertQueue.length,
            is_processing: this.isProcessingQueue,
            last_connection_test: new Date().toISOString()
        };
    }
}

module.exports = PhoenixIntegration;

