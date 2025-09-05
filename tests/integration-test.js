/**
 * Phoenix System - Integration Tests
 * Testes de integração end-to-end para validar todo o sistema
 */

const axios = require('axios');
const { performance } = require('perf_hooks');
const winston = require('winston');

// Configuração do logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.colorize(),
        winston.format.simple()
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'tests/integration-test.log' })
    ]
});

class PhoenixIntegrationTest {
    constructor() {
        this.config = {
            orchestrator: process.env.ORCHESTRATOR_URL || 'https://func-orchestrator-phoenix-dev.azurewebsites.net/api',
            diagnostic: process.env.DIAGNOSTIC_URL || 'https://func-diagnostic-phoenix-dev.azurewebsites.net/api',
            resolution: process.env.RESOLUTION_URL || 'https://func-resolution-phoenix-dev.azurewebsites.net/api',
            communication: process.env.COMMUNICATION_URL || 'https://func-communication-phoenix-dev.azurewebsites.net/api',
            ecommerce: process.env.ECOMMERCE_URL || 'http://localhost:3000/api',
            functionKey: process.env.FUNCTION_KEY || ''
        };
        
        this.testResults = {
            passed: 0,
            failed: 0,
            total: 0,
            details: []
        };
        
        this.timeout = 30000; // 30 segundos
    }
    
    async runAllTests() {
        logger.info('🚀 Iniciando testes de integração do Sistema Phoenix...');
        
        const startTime = performance.now();
        
        try {
            // Testes de conectividade
            await this.testConnectivity();
            
            // Testes de health check
            await this.testHealthChecks();
            
            // Testes de fluxo completo
            await this.testCompleteIncidentFlow();
            
            // Testes de performance
            await this.testPerformance();
            
            // Testes de resiliência
            await this.testResilience();
            
            // Testes de integração com Teams/Copilot
            await this.testCommunicationIntegration();
            
        } catch (error) {
            logger.error('Erro durante execução dos testes:', error);
        }
        
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);
        
        this.generateReport(duration);
    }
    
    async testConnectivity() {
        logger.info('🔗 Testando conectividade com todos os serviços...');
        
        const services = [
            { name: 'Orchestrator', url: this.config.orchestrator },
            { name: 'Diagnostic', url: this.config.diagnostic },
            { name: 'Resolution', url: this.config.resolution },
            { name: 'Communication', url: this.config.communication },
            { name: 'E-commerce', url: this.config.ecommerce }
        ];
        
        for (const service of services) {
            await this.runTest(`Conectividade - ${service.name}`, async () => {
                const response = await axios.get(`${service.url}/health`, {
                    timeout: this.timeout,
                    headers: this.getHeaders()
                });
                
                if (response.status !== 200) {
                    throw new Error(`Status HTTP inválido: ${response.status}`);
                }
                
                return { status: response.status, data: response.data };
            });
        }
    }
    
    async testHealthChecks() {
        logger.info('❤️ Testando health checks detalhados...');
        
        await this.runTest('Health Check - Orchestrator', async () => {
            const response = await axios.get(`${this.config.orchestrator}/health`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            const health = response.data;
            
            if (health.status !== 'healthy') {
                throw new Error(`Orchestrator não está saudável: ${health.status}`);
            }
            
            if (!health.agent_initialized) {
                throw new Error('Agente orquestrador não foi inicializado');
            }
            
            return health;
        });
        
        await this.runTest('Health Check - Diagnostic', async () => {
            const response = await axios.get(`${this.config.diagnostic}/health`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            const health = response.data;
            
            if (health.status !== 'healthy' || !health.agent_initialized) {
                throw new Error('Agente de diagnóstico não está operacional');
            }
            
            return health;
        });
        
        await this.runTest('Health Check - Resolution', async () => {
            const response = await axios.get(`${this.config.resolution}/health`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            const health = response.data;
            
            if (health.status !== 'healthy' || !health.agent_initialized) {
                throw new Error('Agente de resolução não está operacional');
            }
            
            return health;
        });
        
        await this.runTest('Health Check - Communication', async () => {
            const response = await axios.get(`${this.config.communication}/health`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            const health = response.data;
            
            if (health.status !== 'healthy' || !health.agent_initialized) {
                throw new Error('Agente de comunicação não está operacional');
            }
            
            return health;
        });
    }
    
    async testCompleteIncidentFlow() {
        logger.info('🔄 Testando fluxo completo de incidente...');
        
        let incidentId;
        
        // 1. Criar alerta
        await this.runTest('Criar Alerta', async () => {
            const alertData = {
                title: 'Test Database Connection Error',
                description: 'Simulated database connection timeout for testing',
                severity: 'high',
                source: 'integration-test',
                metrics: {
                    error_rate: 15,
                    response_time: 5000,
                    db_connection_errors: 3
                },
                timestamp: new Date().toISOString()
            };
            
            const response = await axios.post(`${this.config.orchestrator}/alert`, alertData, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            if (!response.data.success) {
                throw new Error('Falha ao criar alerta');
            }
            
            incidentId = response.data.incident_id;
            
            if (!incidentId) {
                throw new Error('ID do incidente não foi retornado');
            }
            
            return { incident_id: incidentId };
        });
        
        // 2. Verificar status do incidente
        await this.runTest('Verificar Status do Incidente', async () => {
            // Aguardar processamento
            await this.sleep(5000);
            
            const response = await axios.get(`${this.config.orchestrator}/incident/${incidentId}`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            if (!response.data.success) {
                throw new Error('Falha ao obter status do incidente');
            }
            
            const incident = response.data.incident;
            
            if (!incident) {
                throw new Error('Dados do incidente não encontrados');
            }
            
            return incident;
        });
        
        // 3. Verificar lista de incidentes ativos
        await this.runTest('Listar Incidentes Ativos', async () => {
            const response = await axios.get(`${this.config.orchestrator}/incidents`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            if (!response.data.success) {
                throw new Error('Falha ao listar incidentes');
            }
            
            const incidents = response.data.incidents;
            
            if (!Array.isArray(incidents)) {
                throw new Error('Lista de incidentes inválida');
            }
            
            // Verificar se nosso incidente está na lista
            const ourIncident = incidents.find(inc => inc.id === incidentId);
            
            if (!ourIncident) {
                throw new Error('Incidente criado não encontrado na lista');
            }
            
            return { count: incidents.length, found: true };
        });
    }
    
    async testPerformance() {
        logger.info('⚡ Testando performance do sistema...');
        
        await this.runTest('Performance - Múltiplos Alertas', async () => {
            const alertPromises = [];
            const alertCount = 5;
            
            for (let i = 0; i < alertCount; i++) {
                const alertData = {
                    title: `Performance Test Alert ${i + 1}`,
                    description: `Performance test alert number ${i + 1}`,
                    severity: 'low',
                    source: 'performance-test',
                    metrics: {
                        test_number: i + 1,
                        timestamp: Date.now()
                    }
                };
                
                alertPromises.push(
                    axios.post(`${this.config.orchestrator}/alert`, alertData, {
                        timeout: this.timeout,
                        headers: this.getHeaders()
                    })
                );
            }
            
            const startTime = performance.now();
            const responses = await Promise.all(alertPromises);
            const endTime = performance.now();
            
            const duration = endTime - startTime;
            const avgResponseTime = duration / alertCount;
            
            // Verificar se todos foram processados com sucesso
            const successCount = responses.filter(r => r.data.success).length;
            
            if (successCount !== alertCount) {
                throw new Error(`Apenas ${successCount}/${alertCount} alertas foram processados com sucesso`);
            }
            
            return {
                total_alerts: alertCount,
                total_time: Math.round(duration),
                avg_response_time: Math.round(avgResponseTime),
                success_rate: (successCount / alertCount) * 100
            };
        });
        
        await this.runTest('Performance - Tempo de Resposta', async () => {
            const startTime = performance.now();
            
            const response = await axios.get(`${this.config.orchestrator}/health`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            const endTime = performance.now();
            const responseTime = endTime - startTime;
            
            if (responseTime > 2000) { // 2 segundos
                throw new Error(`Tempo de resposta muito alto: ${Math.round(responseTime)}ms`);
            }
            
            return { response_time: Math.round(responseTime) };
        });
    }
    
    async testResilience() {
        logger.info('🛡️ Testando resiliência do sistema...');
        
        await this.runTest('Resiliência - Requisições Inválidas', async () => {
            try {
                // Tentar enviar alerta com dados inválidos
                await axios.post(`${this.config.orchestrator}/alert`, {
                    invalid: 'data'
                }, {
                    timeout: this.timeout,
                    headers: this.getHeaders()
                });
                
                throw new Error('Sistema aceitou dados inválidos');
            } catch (error) {
                if (error.response && error.response.status >= 400 && error.response.status < 500) {
                    // Esperado - erro de validação
                    return { handled_correctly: true, status: error.response.status };
                } else {
                    throw error;
                }
            }
        });
        
        await this.runTest('Resiliência - Endpoint Inexistente', async () => {
            try {
                await axios.get(`${this.config.orchestrator}/nonexistent-endpoint`, {
                    timeout: this.timeout,
                    headers: this.getHeaders()
                });
                
                throw new Error('Sistema não retornou 404 para endpoint inexistente');
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    return { handled_correctly: true };
                } else {
                    throw error;
                }
            }
        });
    }
    
    async testCommunicationIntegration() {
        logger.info('💬 Testando integração de comunicação...');
        
        await this.runTest('Comunicação - Enviar Notificação', async () => {
            const notificationData = {
                incident_id: 'test-incident-123',
                type: 'incident_created',
                severity: 'medium',
                title: 'Test Notification',
                message: 'This is a test notification from integration tests',
                recipients: ['test@example.com']
            };
            
            const response = await axios.post(`${this.config.communication}/notify`, notificationData, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            if (!response.data.success) {
                throw new Error('Falha ao enviar notificação');
            }
            
            return response.data;
        });
        
        await this.runTest('Comunicação - Listar Stakeholders', async () => {
            const response = await axios.get(`${this.config.communication}/stakeholders`, {
                timeout: this.timeout,
                headers: this.getHeaders()
            });
            
            if (!response.data.success) {
                throw new Error('Falha ao listar stakeholders');
            }
            
            return {
                stakeholder_count: response.data.count || 0,
                stakeholders: response.data.stakeholders || {}
            };
        });
    }
    
    async runTest(testName, testFunction) {
        this.testResults.total++;
        
        try {
            logger.info(`  ▶️ ${testName}`);
            const startTime = performance.now();
            
            const result = await testFunction();
            
            const endTime = performance.now();
            const duration = Math.round(endTime - startTime);
            
            this.testResults.passed++;
            this.testResults.details.push({
                name: testName,
                status: 'PASSED',
                duration: duration,
                result: result
            });
            
            logger.info(`  ✅ ${testName} - PASSOU (${duration}ms)`);
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.details.push({
                name: testName,
                status: 'FAILED',
                error: error.message,
                stack: error.stack
            });
            
            logger.error(`  ❌ ${testName} - FALHOU: ${error.message}`);
        }
    }
    
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Phoenix-Integration-Test/1.0.0'
        };
        
        if (this.config.functionKey) {
            headers['x-functions-key'] = this.config.functionKey;
        }
        
        return headers;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    generateReport(duration) {
        logger.info('\n📊 RELATÓRIO DE TESTES DE INTEGRAÇÃO');
        logger.info('=====================================');
        logger.info(`⏱️  Duração total: ${duration}ms`);
        logger.info(`📈 Testes executados: ${this.testResults.total}`);
        logger.info(`✅ Testes aprovados: ${this.testResults.passed}`);
        logger.info(`❌ Testes falharam: ${this.testResults.failed}`);
        logger.info(`📊 Taxa de sucesso: ${Math.round((this.testResults.passed / this.testResults.total) * 100)}%`);
        
        if (this.testResults.failed > 0) {
            logger.info('\n❌ TESTES QUE FALHARAM:');
            this.testResults.details
                .filter(test => test.status === 'FAILED')
                .forEach(test => {
                    logger.error(`  • ${test.name}: ${test.error}`);
                });
        }
        
        logger.info('\n📋 DETALHES DOS TESTES:');
        this.testResults.details.forEach(test => {
            const status = test.status === 'PASSED' ? '✅' : '❌';
            const duration = test.duration ? ` (${test.duration}ms)` : '';
            logger.info(`  ${status} ${test.name}${duration}`);
        });
        
        // Salvar relatório em arquivo
        const reportData = {
            timestamp: new Date().toISOString(),
            duration: duration,
            summary: {
                total: this.testResults.total,
                passed: this.testResults.passed,
                failed: this.testResults.failed,
                success_rate: Math.round((this.testResults.passed / this.testResults.total) * 100)
            },
            tests: this.testResults.details
        };
        
        require('fs').writeFileSync('tests/integration-report.json', JSON.stringify(reportData, null, 2));
        
        logger.info('\n💾 Relatório salvo em: tests/integration-report.json');
        
        // Exit code baseado no resultado
        if (this.testResults.failed > 0) {
            process.exit(1);
        } else {
            logger.info('\n🎉 Todos os testes passaram com sucesso!');
            process.exit(0);
        }
    }
}

// Executar testes se este arquivo for chamado diretamente
if (require.main === module) {
    const tester = new PhoenixIntegrationTest();
    tester.runAllTests().catch(error => {
        logger.error('Erro fatal durante execução dos testes:', error);
        process.exit(1);
    });
}

module.exports = PhoenixIntegrationTest;

