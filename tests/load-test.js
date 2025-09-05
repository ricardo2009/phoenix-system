/**
 * Phoenix System - Load Testing
 * Script para teste de carga e simulação de cenários reais
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
        new winston.transports.File({ filename: 'tests/load-test.log' })
    ]
});

class PhoenixLoadTest {
    constructor() {
        this.config = {
            orchestrator: process.env.ORCHESTRATOR_URL || 'https://func-orchestrator-phoenix-dev.azurewebsites.net/api',
            ecommerce: process.env.ECOMMERCE_URL || 'http://localhost:3000/api',
            functionKey: process.env.FUNCTION_KEY || ''
        };
        
        this.scenarios = {
            light: { users: 10, duration: 60, rampUp: 10 },
            moderate: { users: 50, duration: 300, rampUp: 30 },
            heavy: { users: 100, duration: 600, rampUp: 60 },
            stress: { users: 200, duration: 300, rampUp: 30 }
        };
        
        this.metrics = {
            requests: 0,
            responses: 0,
            errors: 0,
            responseTimes: [],
            errorTypes: {},
            incidentsCreated: 0
        };
        
        this.isRunning = false;
    }
    
    async runLoadTest(scenarioName = 'moderate') {
        const scenario = this.scenarios[scenarioName];
        
        if (!scenario) {
            throw new Error(`Cenário '${scenarioName}' não encontrado`);
        }
        
        logger.info(`🚀 Iniciando teste de carga: ${scenarioName}`);
        logger.info(`👥 Usuários: ${scenario.users}`);
        logger.info(`⏱️  Duração: ${scenario.duration}s`);
        logger.info(`📈 Ramp-up: ${scenario.rampUp}s`);
        
        this.isRunning = true;
        const startTime = performance.now();
        
        // Iniciar usuários virtuais gradualmente
        const userPromises = [];
        const userInterval = (scenario.rampUp * 1000) / scenario.users;
        
        for (let i = 0; i < scenario.users; i++) {
            setTimeout(() => {
                if (this.isRunning) {
                    userPromises.push(this.simulateUser(i, scenario.duration));
                }
            }, i * userInterval);
        }
        
        // Parar teste após duração especificada
        setTimeout(() => {
            this.isRunning = false;
            logger.info('⏹️  Parando teste de carga...');
        }, (scenario.rampUp + scenario.duration) * 1000);
        
        // Aguardar todos os usuários terminarem
        await Promise.allSettled(userPromises);
        
        const endTime = performance.now();
        const totalDuration = Math.round(endTime - startTime);
        
        this.generateLoadTestReport(scenarioName, totalDuration);
    }
    
    async simulateUser(userId, duration) {
        const endTime = Date.now() + (duration * 1000);
        
        logger.info(`👤 Usuário ${userId} iniciado`);
        
        while (this.isRunning && Date.now() < endTime) {
            try {
                // Simular diferentes tipos de atividade
                const activity = this.selectRandomActivity();
                await this.executeActivity(userId, activity);
                
                // Intervalo aleatório entre atividades (1-5 segundos)
                const delay = Math.random() * 4000 + 1000;
                await this.sleep(delay);
                
            } catch (error) {
                this.recordError(error);
            }
        }
        
        logger.info(`👤 Usuário ${userId} finalizado`);
    }
    
    selectRandomActivity() {
        const activities = [
            { type: 'browse_products', weight: 30 },
            { type: 'create_order', weight: 20 },
            { type: 'check_health', weight: 15 },
            { type: 'simulate_error', weight: 10 },
            { type: 'high_cpu_usage', weight: 8 },
            { type: 'database_timeout', weight: 7 },
            { type: 'memory_leak', weight: 5 },
            { type: 'payment_failure', weight: 5 }
        ];
        
        const totalWeight = activities.reduce((sum, activity) => sum + activity.weight, 0);
        let random = Math.random() * totalWeight;
        
        for (const activity of activities) {
            random -= activity.weight;
            if (random <= 0) {
                return activity.type;
            }
        }
        
        return 'browse_products'; // fallback
    }
    
    async executeActivity(userId, activityType) {
        const startTime = performance.now();
        
        try {
            switch (activityType) {
                case 'browse_products':
                    await this.browseProducts(userId);
                    break;
                    
                case 'create_order':
                    await this.createOrder(userId);
                    break;
                    
                case 'check_health':
                    await this.checkHealth(userId);
                    break;
                    
                case 'simulate_error':
                    await this.simulateError(userId);
                    break;
                    
                case 'high_cpu_usage':
                    await this.simulateHighCpuUsage(userId);
                    break;
                    
                case 'database_timeout':
                    await this.simulateDatabaseTimeout(userId);
                    break;
                    
                case 'memory_leak':
                    await this.simulateMemoryLeak(userId);
                    break;
                    
                case 'payment_failure':
                    await this.simulatePaymentFailure(userId);
                    break;
                    
                default:
                    await this.browseProducts(userId);
            }
            
            const endTime = performance.now();
            const responseTime = endTime - startTime;
            
            this.recordResponse(responseTime);
            
        } catch (error) {
            const endTime = performance.now();
            const responseTime = endTime - startTime;
            
            this.recordError(error, responseTime);
        }
    }
    
    async browseProducts(userId) {
        this.metrics.requests++;
        
        const response = await axios.get(`${this.config.ecommerce}/products`, {
            timeout: 10000,
            headers: {
                'User-Agent': `LoadTest-User-${userId}`,
                'X-Load-Test': 'true'
            }
        });
        
        if (response.status !== 200) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    }
    
    async createOrder(userId) {
        this.metrics.requests++;
        
        const orderData = {
            user_id: `load-test-user-${userId}`,
            items: [
                { product_id: 'test-product-1', quantity: Math.floor(Math.random() * 3) + 1 },
                { product_id: 'test-product-2', quantity: Math.floor(Math.random() * 2) + 1 }
            ],
            total: Math.random() * 500 + 50
        };
        
        const response = await axios.post(`${this.config.ecommerce}/orders`, orderData, {
            timeout: 15000,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': `LoadTest-User-${userId}`,
                'X-Load-Test': 'true'
            }
        });
        
        if (response.status !== 201) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    }
    
    async checkHealth(userId) {
        this.metrics.requests++;
        
        const response = await axios.get(`${this.config.ecommerce}/health`, {
            timeout: 5000,
            headers: {
                'User-Agent': `LoadTest-User-${userId}`,
                'X-Load-Test': 'true'
            }
        });
        
        if (response.status !== 200) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    }
    
    async simulateError(userId) {
        this.metrics.requests++;
        
        // Simular erro que deve ser capturado pelo Phoenix
        const alertData = {
            title: `Load Test Simulated Error - User ${userId}`,
            description: 'Simulated error during load testing to validate Phoenix response',
            severity: 'medium',
            source: 'load-test',
            metrics: {
                user_id: userId,
                error_type: 'simulated',
                timestamp: Date.now()
            }
        };
        
        const response = await axios.post(`${this.config.orchestrator}/alert`, alertData, {
            timeout: 10000,
            headers: this.getHeaders()
        });
        
        if (response.data.success) {
            this.metrics.incidentsCreated++;
        }
    }
    
    async simulateHighCpuUsage(userId) {
        this.metrics.requests++;
        
        const alertData = {
            title: `High CPU Usage Detected - User ${userId}`,
            description: 'CPU usage exceeded 85% threshold during load test',
            severity: 'high',
            source: 'load-test',
            metrics: {
                cpu_percentage: 87 + Math.random() * 10,
                user_id: userId,
                load_average: 4.5 + Math.random() * 2
            }
        };
        
        const response = await axios.post(`${this.config.orchestrator}/alert`, alertData, {
            timeout: 10000,
            headers: this.getHeaders()
        });
        
        if (response.data.success) {
            this.metrics.incidentsCreated++;
        }
    }
    
    async simulateDatabaseTimeout(userId) {
        this.metrics.requests++;
        
        const alertData = {
            title: `Database Connection Timeout - User ${userId}`,
            description: 'Database connection timed out during high load',
            severity: 'critical',
            source: 'load-test',
            metrics: {
                db_connection_time: 30000 + Math.random() * 10000,
                active_connections: Math.floor(Math.random() * 5),
                user_id: userId,
                error_rate: 15 + Math.random() * 10
            }
        };
        
        const response = await axios.post(`${this.config.orchestrator}/alert`, alertData, {
            timeout: 10000,
            headers: this.getHeaders()
        });
        
        if (response.data.success) {
            this.metrics.incidentsCreated++;
        }
    }
    
    async simulateMemoryLeak(userId) {
        this.metrics.requests++;
        
        const alertData = {
            title: `Memory Leak Detected - User ${userId}`,
            description: 'Memory usage continuously increasing, possible memory leak',
            severity: 'high',
            source: 'load-test',
            metrics: {
                memory_percentage: 88 + Math.random() * 10,
                heap_used: 1800000000 + Math.random() * 200000000,
                user_id: userId,
                gc_frequency: Math.floor(Math.random() * 20) + 10
            }
        };
        
        const response = await axios.post(`${this.config.orchestrator}/alert`, alertData, {
            timeout: 10000,
            headers: this.getHeaders()
        });
        
        if (response.data.success) {
            this.metrics.incidentsCreated++;
        }
    }
    
    async simulatePaymentFailure(userId) {
        this.metrics.requests++;
        
        const alertData = {
            title: `Payment Processing Failure - User ${userId}`,
            description: 'Multiple payment processing failures detected',
            severity: 'high',
            source: 'load-test',
            metrics: {
                payment_success_rate: 70 + Math.random() * 15,
                failed_payments: Math.floor(Math.random() * 10) + 5,
                user_id: userId,
                revenue_impact: Math.random() * 5000 + 1000
            }
        };
        
        const response = await axios.post(`${this.config.orchestrator}/alert`, alertData, {
            timeout: 10000,
            headers: this.getHeaders()
        });
        
        if (response.data.success) {
            this.metrics.incidentsCreated++;
        }
    }
    
    recordResponse(responseTime) {
        this.metrics.responses++;
        this.metrics.responseTimes.push(responseTime);
    }
    
    recordError(error, responseTime = 0) {
        this.metrics.errors++;
        
        if (responseTime > 0) {
            this.metrics.responseTimes.push(responseTime);
        }
        
        const errorType = error.code || error.name || 'UnknownError';
        this.metrics.errorTypes[errorType] = (this.metrics.errorTypes[errorType] || 0) + 1;
    }
    
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Phoenix-Load-Test/1.0.0',
            'X-Load-Test': 'true'
        };
        
        if (this.config.functionKey) {
            headers['x-functions-key'] = this.config.functionKey;
        }
        
        return headers;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    generateLoadTestReport(scenarioName, duration) {
        const responseTimes = this.metrics.responseTimes.sort((a, b) => a - b);
        const totalRequests = this.metrics.requests;
        const successfulRequests = this.metrics.responses;
        const errorRate = (this.metrics.errors / totalRequests) * 100;
        
        // Calcular percentis
        const p50 = this.calculatePercentile(responseTimes, 50);
        const p95 = this.calculatePercentile(responseTimes, 95);
        const p99 = this.calculatePercentile(responseTimes, 99);
        const avgResponseTime = responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
        
        // Calcular throughput
        const throughput = (successfulRequests / (duration / 1000)).toFixed(2);
        
        logger.info('\n📊 RELATÓRIO DE TESTE DE CARGA');
        logger.info('===============================');
        logger.info(`🎯 Cenário: ${scenarioName}`);
        logger.info(`⏱️  Duração: ${Math.round(duration / 1000)}s`);
        logger.info(`📈 Total de requisições: ${totalRequests}`);
        logger.info(`✅ Requisições bem-sucedidas: ${successfulRequests}`);
        logger.info(`❌ Erros: ${this.metrics.errors}`);
        logger.info(`📊 Taxa de erro: ${errorRate.toFixed(2)}%`);
        logger.info(`🚀 Throughput: ${throughput} req/s`);
        logger.info(`🎯 Incidentes criados: ${this.metrics.incidentsCreated}`);
        
        logger.info('\n⏱️  TEMPOS DE RESPOSTA:');
        logger.info(`   Média: ${Math.round(avgResponseTime)}ms`);
        logger.info(`   P50: ${Math.round(p50)}ms`);
        logger.info(`   P95: ${Math.round(p95)}ms`);
        logger.info(`   P99: ${Math.round(p99)}ms`);
        logger.info(`   Mínimo: ${Math.round(Math.min(...responseTimes))}ms`);
        logger.info(`   Máximo: ${Math.round(Math.max(...responseTimes))}ms`);
        
        if (Object.keys(this.metrics.errorTypes).length > 0) {
            logger.info('\n❌ TIPOS DE ERRO:');
            Object.entries(this.metrics.errorTypes).forEach(([type, count]) => {
                logger.info(`   ${type}: ${count}`);
            });
        }
        
        // Salvar relatório em arquivo
        const reportData = {
            scenario: scenarioName,
            timestamp: new Date().toISOString(),
            duration: Math.round(duration / 1000),
            summary: {
                total_requests: totalRequests,
                successful_requests: successfulRequests,
                errors: this.metrics.errors,
                error_rate: parseFloat(errorRate.toFixed(2)),
                throughput: parseFloat(throughput),
                incidents_created: this.metrics.incidentsCreated
            },
            response_times: {
                average: Math.round(avgResponseTime),
                p50: Math.round(p50),
                p95: Math.round(p95),
                p99: Math.round(p99),
                min: Math.round(Math.min(...responseTimes)),
                max: Math.round(Math.max(...responseTimes))
            },
            error_types: this.metrics.errorTypes
        };
        
        require('fs').writeFileSync('tests/load-test-report.json', JSON.stringify(reportData, null, 2));
        
        logger.info('\n💾 Relatório salvo em: tests/load-test-report.json');
        
        // Avaliar resultados
        if (errorRate > 10) {
            logger.warn('⚠️  Taxa de erro alta detectada!');
        }
        
        if (avgResponseTime > 2000) {
            logger.warn('⚠️  Tempo de resposta médio alto!');
        }
        
        if (parseFloat(throughput) < 10) {
            logger.warn('⚠️  Throughput baixo detectado!');
        }
        
        logger.info('\n🎉 Teste de carga concluído!');
    }
    
    calculatePercentile(sortedArray, percentile) {
        const index = Math.ceil((percentile / 100) * sortedArray.length) - 1;
        return sortedArray[index] || 0;
    }
}

// Executar teste se este arquivo for chamado diretamente
if (require.main === module) {
    const scenario = process.argv[2] || 'moderate';
    
    const loadTester = new PhoenixLoadTest();
    loadTester.runLoadTest(scenario).catch(error => {
        logger.error('Erro fatal durante teste de carga:', error);
        process.exit(1);
    });
}

module.exports = PhoenixLoadTest;

