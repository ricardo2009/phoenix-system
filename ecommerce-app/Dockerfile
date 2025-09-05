# Phoenix E-commerce Demo Application
# Multi-stage build para otimizar o tamanho da imagem

# Estágio 1: Build
FROM node:18-alpine AS builder

# Instalar dependências do sistema
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências
RUN npm ci --only=production && npm cache clean --force

# Copiar código fonte
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs public/uploads

# Build da aplicação (se houver frontend)
RUN npm run build || echo "No build script found"

# Estágio 2: Runtime
FROM node:18-alpine AS runtime

# Instalar dependências de runtime
RUN apk add --no-cache \
    dumb-init \
    curl \
    && addgroup -g 1001 -S nodejs \
    && adduser -S nodejs -u 1001

# Definir diretório de trabalho
WORKDIR /app

# Copiar aplicação do estágio de build
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package*.json ./
COPY --from=builder --chown=nodejs:nodejs /app/server.js ./
COPY --from=builder --chown=nodejs:nodejs /app/routes ./routes
COPY --from=builder --chown=nodejs:nodejs /app/services ./services
COPY --from=builder --chown=nodejs:nodejs /app/middleware ./middleware
COPY --from=builder --chown=nodejs:nodejs /app/models ./models
COPY --from=builder --chown=nodejs:nodejs /app/public ./public
COPY --from=builder --chown=nodejs:nodejs /app/logs ./logs

# Criar diretórios com permissões corretas
RUN mkdir -p /app/logs /app/tmp \
    && chown -R nodejs:nodejs /app/logs /app/tmp \
    && chmod 755 /app/logs /app/tmp

# Configurar usuário não-root
USER nodejs

# Expor porta
EXPOSE 3000

# Variáveis de ambiente padrão
ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Labels para metadados
LABEL maintainer="Phoenix System Team" \
      version="1.0.0" \
      description="Phoenix E-commerce Demo Application" \
      org.opencontainers.image.title="Phoenix E-commerce" \
      org.opencontainers.image.description="Aplicação de demonstração para o sistema Phoenix" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Phoenix System" \
      org.opencontainers.image.licenses="MIT"

# Comando de inicialização
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]

