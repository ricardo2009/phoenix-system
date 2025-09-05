/**
 * Phoenix E-commerce Demo Application
 * Aplicação de demonstração que gera cenários para o sistema Phoenix
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const swaggerUi = require('swagger-ui-express');
const swaggerJsdoc = require('swagger-jsdoc');
const { createServer } = require('http');
const { Server } = require('socket.io');
const winston = require('winston');
const promClient = require('prom-client');
require('dotenv').config();

// Importar rotas e middlewares
const productRoutes = require('./routes/products');
const orderRoutes = require('./routes/orders');
const userRoutes = require('./routes/users');
const cartRoutes = require('./routes/cart');
const healthRoutes = require('./routes/health');
const metricsRoutes = require('./routes/metrics');
const chaosRoutes = require('./routes/chaos');

// Importar serviços
const DatabaseService = require('./services/database');
const CacheService = require('./services/cache');
const MetricsService = require('./services/metrics');
const PhoenixIntegration = require('./services/phoenix-integration');

// Configuração do logger
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.colorize(),
                winston.format.simple()
            )
        }),
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' })
    ]
});

// Configuração do Swagger
const swaggerOptions = {
    definition: {
        openapi: '3.0.0',
        info: {
            title: 'Phoenix E-commerce API',
            version: '1.0.0',
            description: 'API de demonstração para o sistema Phoenix',
        },
        servers: [
            {
                url: process.env.API_BASE_URL || 'http://localhost:3000',
                description: 'Servidor de desenvolvimento'
            }
        ],
    },
    apis: ['./routes/*.js', './server.js'],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);

// Configuração da aplicação
const app = express();
const server = createServer(app);
const io = new Server(server, {
    cors: {
        origin: process.env.FRONTEND_URL || "http://localhost:3000",
        methods: ["GET", "POST"]
    }
});

// Configuração de rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: process.env.RATE_LIMIT || 100, // máximo 100 requests por IP
    message: {
        error: 'Muitas requisições deste IP, tente novamente em 15 minutos.'
    }
});

// Middlewares globais
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(limiter);

// Servir arquivos estáticos
app.use(express.static('public'));

// Documentação da API
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Inicializar serviços
let databaseService;
let cacheService;
let metricsService;
let phoenixIntegration;

async function initializeServices() {
    try {
        logger.info('Inicializando serviços...');
        
        // Database
        databaseService = new DatabaseService();
        await databaseService.connect();
        
        // Cache
        cacheService = new CacheService();
        await cacheService.connect();
        
        // Métricas
        metricsService = new MetricsService();
        metricsService.initialize();
        
        // Integração Phoenix
        phoenixIntegration = new PhoenixIntegration();
        await phoenixIntegration.initialize();
        
        logger.info('Todos os serviços inicializados com sucesso');
    } catch (error) {
        logger.error('Erro ao inicializar serviços:', error);
        throw error;
    }
}

// Middleware para injetar serviços nas rotas
app.use((req, res, next) => {
    req.services = {
        database: databaseService,
        cache: cacheService,
        metrics: metricsService,
        phoenix: phoenixIntegration,
        logger: logger,
        io: io
    };
    next();
});

// Middleware para métricas
app.use((req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
        const duration = Date.now() - start;
        metricsService?.recordHttpRequest(req.method, req.route?.path || req.path, res.statusCode, duration);
    });
    
    next();
});

// Rotas da API
app.use('/api/health', healthRoutes);
app.use('/api/metrics', metricsRoutes);
app.use('/api/products', productRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/users', userRoutes);
app.use('/api/cart', cartRoutes);
app.use('/api/chaos', chaosRoutes); // Para simular problemas

/**
 * @swagger
 * /:
 *   get:
 *     summary: Página inicial da aplicação
 *     responses:
 *       200:
 *         description: Página inicial carregada com sucesso
 */
app.get('/', (req, res) => {
    res.json({
        message: 'Phoenix E-commerce Demo API',
        version: '1.0.0',
        status: 'running',
        timestamp: new Date().toISOString(),
        documentation: '/api-docs',
        endpoints: {
            health: '/api/health',
            metrics: '/api/metrics',
            products: '/api/products',
            orders: '/api/orders',
            users: '/api/users',
            cart: '/api/cart',
            chaos: '/api/chaos'
        }
    });
});

// WebSocket para atualizações em tempo real
io.on('connection', (socket) => {
    logger.info(`Cliente conectado: ${socket.id}`);
    
    socket.on('join_room', (room) => {
        socket.join(room);
        logger.info(`Cliente ${socket.id} entrou na sala: ${room}`);
    });
    
    socket.on('disconnect', () => {
        logger.info(`Cliente desconectado: ${socket.id}`);
    });
});

// Middleware de tratamento de erros
app.use((error, req, res, next) => {
    logger.error('Erro não tratado:', error);
    
    // Reportar erro para o Phoenix
    if (phoenixIntegration) {
        phoenixIntegration.reportError(error, req);
    }
    
    // Incrementar métrica de erro
    if (metricsService) {
        metricsService.incrementErrorCount(error.name || 'UnknownError');
    }
    
    const statusCode = error.statusCode || 500;
    const message = process.env.NODE_ENV === 'production' 
        ? 'Erro interno do servidor' 
        : error.message;
    
    res.status(statusCode).json({
        error: true,
        message: message,
        timestamp: new Date().toISOString(),
        requestId: req.id
    });
});

// Middleware para rotas não encontradas
app.use('*', (req, res) => {
    logger.warn(`Rota não encontrada: ${req.method} ${req.originalUrl}`);
    
    res.status(404).json({
        error: true,
        message: 'Rota não encontrada',
        path: req.originalUrl,
        method: req.method,
        timestamp: new Date().toISOString()
    });
});

// Função para simular carga de trabalho
function simulateWorkload() {
    setInterval(() => {
        // Simular diferentes tipos de carga
        const workloadType = Math.random();
        
        if (workloadType < 0.1) {
            // 10% chance de simular alta CPU
            const start = Date.now();
            while (Date.now() - start < 100) {
                Math.random() * Math.random();
            }
        } else if (workloadType < 0.2) {
            // 10% chance de simular uso de memória
            const largeArray = new Array(100000).fill('data');
            setTimeout(() => {
                largeArray.length = 0;
            }, 1000);
        }
    }, 5000);
}

// Função para simular problemas ocasionais
function simulateProblems() {
    setInterval(() => {
        const problemChance = Math.random();
        
        if (problemChance < 0.05) { // 5% chance
            // Simular erro de banco de dados
            logger.error('Simulação: Erro de conexão com banco de dados');
            if (phoenixIntegration) {
                phoenixIntegration.reportAlert({
                    title: 'Database Connection Error',
                    description: 'Simulated database connection timeout',
                    severity: 'high',
                    source: 'ecommerce-app',
                    metrics: {
                        error_rate: 15,
                        response_time: 5000
                    }
                });
            }
        } else if (problemChance < 0.08) { // 3% chance
            // Simular alta latência
            logger.warn('Simulação: Alta latência detectada');
            if (phoenixIntegration) {
                phoenixIntegration.reportAlert({
                    title: 'High Response Time',
                    description: 'Application response time above threshold',
                    severity: 'medium',
                    source: 'ecommerce-app',
                    metrics: {
                        avg_response_time: 3000,
                        cpu_percentage: 85
                    }
                });
            }
        }
    }, 30000); // A cada 30 segundos
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    logger.info('Recebido SIGTERM, iniciando shutdown graceful...');
    
    server.close(async () => {
        logger.info('Servidor HTTP fechado');
        
        try {
            if (databaseService) {
                await databaseService.disconnect();
            }
            if (cacheService) {
                await cacheService.disconnect();
            }
            logger.info('Serviços desconectados com sucesso');
        } catch (error) {
            logger.error('Erro durante shutdown:', error);
        }
        
        process.exit(0);
    });
});

process.on('SIGINT', async () => {
    logger.info('Recebido SIGINT, iniciando shutdown...');
    process.emit('SIGTERM');
});

// Inicializar aplicação
async function startServer() {
    try {
        await initializeServices();
        
        const PORT = process.env.PORT || 3000;
        const HOST = process.env.HOST || '0.0.0.0';
        
        server.listen(PORT, HOST, () => {
            logger.info(`🚀 Servidor Phoenix E-commerce rodando em http://${HOST}:${PORT}`);
            logger.info(`📚 Documentação da API: http://${HOST}:${PORT}/api-docs`);
            logger.info(`🔍 Métricas: http://${HOST}:${PORT}/api/metrics`);
            logger.info(`❤️ Health Check: http://${HOST}:${PORT}/api/health`);
            
            // Iniciar simulações em ambiente de desenvolvimento
            if (process.env.NODE_ENV !== 'production') {
                logger.info('🎭 Iniciando simulações de carga e problemas...');
                simulateWorkload();
                simulateProblems();
            }
        });
        
    } catch (error) {
        logger.error('Erro ao iniciar servidor:', error);
        process.exit(1);
    }
}

// Iniciar servidor se este arquivo for executado diretamente
if (require.main === module) {
    startServer();
}

module.exports = { app, server, io };

