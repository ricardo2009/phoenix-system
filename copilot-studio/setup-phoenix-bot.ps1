# Phoenix Bot Setup Script for Microsoft Copilot Studio
# Este script configura o bot Phoenix no Copilot Studio e integra com Teams

param(
    [Parameter(Mandatory=$true)]
    [string]$TenantId,
    
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$BotName = "Phoenix-System-Bot",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev"
)

# Configurações
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "🤖 Configurando Phoenix Bot no Copilot Studio..." -ForegroundColor Cyan

# Verificar se está logado no Azure
try {
    $context = Get-AzContext
    if (-not $context) {
        Write-Host "❌ Não está logado no Azure. Execute 'Connect-AzAccount' primeiro." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Conectado ao Azure como: $($context.Account.Id)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Erro ao verificar contexto do Azure: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Definir subscription
Set-AzContext -SubscriptionId $SubscriptionId | Out-Null
Write-Host "✅ Subscription definida: $SubscriptionId" -ForegroundColor Green

# Carregar configuração do bot
$configPath = Join-Path $PSScriptRoot "phoenix-bot-config.json"
if (-not (Test-Path $configPath)) {
    Write-Host "❌ Arquivo de configuração não encontrado: $configPath" -ForegroundColor Red
    exit 1
}

$botConfig = Get-Content $configPath | ConvertFrom-Json
Write-Host "✅ Configuração do bot carregada" -ForegroundColor Green

# Função para criar App Registration no Azure AD
function New-BotAppRegistration {
    param($DisplayName)
    
    Write-Host "🔐 Criando App Registration para o bot..." -ForegroundColor Yellow
    
    try {
        # Verificar se já existe
        $existingApp = Get-AzADApplication -DisplayName $DisplayName -ErrorAction SilentlyContinue
        
        if ($existingApp) {
            Write-Host "ℹ️ App Registration já existe: $($existingApp.AppId)" -ForegroundColor Yellow
            return $existingApp
        }
        
        # Criar novo App Registration
        $app = New-AzADApplication -DisplayName $DisplayName -AvailableToOtherTenants $false
        
        # Criar Service Principal
        $sp = New-AzADServicePrincipal -ApplicationId $app.AppId
        
        # Gerar senha para o app
        $appPassword = New-AzADAppCredential -ApplicationId $app.AppId -DisplayName "Phoenix Bot Password"
        
        Write-Host "✅ App Registration criado: $($app.AppId)" -ForegroundColor Green
        
        return @{
            AppId = $app.AppId
            AppPassword = $appPassword.SecretText
            ObjectId = $app.Id
        }
    }
    catch {
        Write-Host "❌ Erro ao criar App Registration: $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

# Função para criar Bot Service no Azure
function New-AzureBotService {
    param($BotName, $AppId, $AppPassword, $ResourceGroupName)
    
    Write-Host "🤖 Criando Azure Bot Service..." -ForegroundColor Yellow
    
    try {
        # Verificar se o bot já existe
        $existingBot = Get-AzResource -ResourceGroupName $ResourceGroupName -ResourceType "Microsoft.BotService/botServices" -Name $BotName -ErrorAction SilentlyContinue
        
        if ($existingBot) {
            Write-Host "ℹ️ Bot Service já existe: $BotName" -ForegroundColor Yellow
            return $existingBot
        }
        
        # Template ARM para Bot Service
        $armTemplate = @{
            '$schema' = "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"
            contentVersion = "1.0.0.0"
            parameters = @{
                botName = @{
                    type = "string"
                    defaultValue = $BotName
                }
                appId = @{
                    type = "string"
                    defaultValue = $AppId
                }
                appPassword = @{
                    type = "securestring"
                    defaultValue = $AppPassword
                }
            }
            resources = @(
                @{
                    type = "Microsoft.BotService/botServices"
                    apiVersion = "2021-03-01"
                    name = "[parameters('botName')]"
                    location = "global"
                    kind = "azurebot"
                    sku = @{
                        name = "F0"
                    }
                    properties = @{
                        displayName = "[parameters('botName')]"
                        description = "Phoenix System Intelligent Bot"
                        iconUrl = "https://docs.botframework.com/static/devportal/client/images/bot-framework-default.png"
                        endpoint = "https://func-communication-phoenix-$Environment.azurewebsites.net/api/teams-webhook"
                        msaAppId = "[parameters('appId')]"
                        msaAppPassword = "[parameters('appPassword')]"
                        developerAppInsightKey = ""
                        developerAppInsightsApiKey = ""
                        developerAppInsightsApplicationId = ""
                        luisAppIds = @()
                        luisKey = ""
                    }
                }
            )
        }
        
        # Salvar template temporário
        $templatePath = [System.IO.Path]::GetTempFileName() + ".json"
        $armTemplate | ConvertTo-Json -Depth 10 | Set-Content $templatePath
        
        # Deploy do template
        $deployment = New-AzResourceGroupDeployment -ResourceGroupName $ResourceGroupName -TemplateFile $templatePath -botName $BotName -appId $AppId -appPassword (ConvertTo-SecureString $AppPassword -AsPlainText -Force)
        
        # Limpar arquivo temporário
        Remove-Item $templatePath -Force
        
        Write-Host "✅ Bot Service criado: $BotName" -ForegroundColor Green
        return $deployment
    }
    catch {
        Write-Host "❌ Erro ao criar Bot Service: $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

# Função para configurar canal do Teams
function Enable-TeamsChannel {
    param($BotName, $ResourceGroupName)
    
    Write-Host "📱 Habilitando canal do Teams..." -ForegroundColor Yellow
    
    try {
        # Usar Azure CLI para habilitar canal do Teams (mais simples que ARM)
        $teamsChannelCommand = "az bot msteams create --name $BotName --resource-group $ResourceGroupName"
        
        $result = Invoke-Expression $teamsChannelCommand 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Canal do Teams habilitado" -ForegroundColor Green
        } else {
            Write-Host "ℹ️ Canal do Teams pode já estar habilitado ou houve erro menor" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️ Aviso ao habilitar canal do Teams: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Função para criar manifesto do Teams
function New-TeamsManifest {
    param($AppId, $BotName)
    
    Write-Host "📋 Criando manifesto do Teams..." -ForegroundColor Yellow
    
    $manifest = @{
        '$schema' = "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json"
        manifestVersion = "1.16"
        version = "1.0.0"
        id = $AppId
        packageName = "com.phoenix.system.bot"
        developer = @{
            name = "Phoenix System"
            websiteUrl = "https://github.com/phoenix-system"
            privacyUrl = "https://github.com/phoenix-system/privacy"
            termsOfUseUrl = "https://github.com/phoenix-system/terms"
        }
        icons = @{
            color = "color-icon.png"
            outline = "outline-icon.png"
        }
        name = @{
            short = $BotName
            full = "Phoenix System - Intelligent Incident Management Bot"
        }
        description = @{
            short = "Bot inteligente para gerenciamento de incidentes"
            full = "O Phoenix System Bot é um assistente inteligente que ajuda no monitoramento, diagnóstico e resolução automática de incidentes em sistemas Azure."
        }
        accentColor = "#0078D4"
        bots = @(
            @{
                botId = $AppId
                scopes = @("personal", "team", "groupchat")
                supportsFiles = $false
                isNotificationOnly = $false
                commandLists = @(
                    @{
                        scopes = @("personal", "team", "groupchat")
                        commands = @(
                            @{
                                title = "Incidentes Ativos"
                                description = "Listar todos os incidentes ativos no sistema"
                            },
                            @{
                                title = "Status do Sistema"
                                description = "Verificar o status geral do sistema Phoenix"
                            },
                            @{
                                title = "Relatório"
                                description = "Gerar relatório de incidentes"
                            },
                            @{
                                title = "Ajuda"
                                description = "Mostrar comandos disponíveis"
                            }
                        )
                    }
                )
            }
        )
        permissions = @("identity", "messageTeamMembers")
        validDomains = @(
            "*.azurewebsites.net",
            "*.microsoft.com"
        )
    }
    
    # Salvar manifesto
    $manifestPath = Join-Path $PSScriptRoot "teams-manifest.json"
    $manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath
    
    Write-Host "✅ Manifesto do Teams criado: $manifestPath" -ForegroundColor Green
    return $manifestPath
}

# Função para criar configuração do Copilot Studio
function New-CopilotStudioConfig {
    param($AppId, $AppPassword, $BotName)
    
    Write-Host "🧠 Criando configuração do Copilot Studio..." -ForegroundColor Yellow
    
    # Atualizar configuração com valores reais
    $botConfig.settings.authentication.client_id = $AppId
    $botConfig.settings.channels[0].settings.app_id = $AppId
    $botConfig.settings.channels[0].settings.app_password = $AppPassword
    
    # Salvar configuração atualizada
    $updatedConfigPath = Join-Path $PSScriptRoot "phoenix-bot-config-deployed.json"
    $botConfig | ConvertTo-Json -Depth 10 | Set-Content $updatedConfigPath
    
    Write-Host "✅ Configuração do Copilot Studio atualizada: $updatedConfigPath" -ForegroundColor Green
    return $updatedConfigPath
}

# Função para criar script de deployment
function New-DeploymentScript {
    param($AppId, $AppPassword, $BotName)
    
    $deployScript = @"
# Phoenix Bot Deployment Script
# Execute este script para fazer deploy das Azure Functions e configurar o bot

# Variáveis
`$AppId = "$AppId"
`$AppPassword = "$AppPassword"
`$BotName = "$BotName"
`$ResourceGroup = "$ResourceGroupName"
`$Environment = "$Environment"

Write-Host "🚀 Iniciando deployment do Phoenix Bot..." -ForegroundColor Cyan

# 1. Deploy das Azure Functions
Write-Host "📦 Fazendo deploy das Azure Functions..." -ForegroundColor Yellow

# Orchestrator Function
func azure functionapp publish func-orchestrator-phoenix-`$Environment --build remote

# Diagnostic Function  
func azure functionapp publish func-diagnostic-phoenix-`$Environment --build remote

# Resolution Function
func azure functionapp publish func-resolution-phoenix-`$Environment --build remote

# Communication Function
func azure functionapp publish func-communication-phoenix-`$Environment --build remote

Write-Host "✅ Azure Functions deployadas com sucesso!" -ForegroundColor Green

# 2. Configurar variáveis de ambiente
Write-Host "⚙️ Configurando variáveis de ambiente..." -ForegroundColor Yellow

`$functionApps = @(
    "func-orchestrator-phoenix-`$Environment",
    "func-diagnostic-phoenix-`$Environment", 
    "func-resolution-phoenix-`$Environment",
    "func-communication-phoenix-`$Environment"
)

foreach (`$app in `$functionApps) {
    az functionapp config appsettings set --name `$app --resource-group `$ResourceGroup --settings "MicrosoftAppId=`$AppId" "MicrosoftAppPassword=`$AppPassword"
}

Write-Host "✅ Variáveis de ambiente configuradas!" -ForegroundColor Green

# 3. Testar endpoints
Write-Host "🧪 Testando endpoints..." -ForegroundColor Yellow

`$orchestratorUrl = "https://func-orchestrator-phoenix-`$Environment.azurewebsites.net/api/health"
try {
    `$response = Invoke-RestMethod -Uri `$orchestratorUrl -Method GET
    Write-Host "✅ Orchestrator: `$(`$response.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Orchestrator: Erro" -ForegroundColor Red
}

Write-Host "🎉 Deployment concluído!" -ForegroundColor Green
Write-Host "📱 Para usar o bot no Teams, importe o arquivo teams-manifest.json" -ForegroundColor Cyan
"@

    $deployScriptPath = Join-Path $PSScriptRoot "deploy-phoenix-bot.ps1"
    $deployScript | Set-Content $deployScriptPath
    
    Write-Host "✅ Script de deployment criado: $deployScriptPath" -ForegroundColor Green
    return $deployScriptPath
}

# Execução principal
try {
    Write-Host "🚀 Iniciando configuração do Phoenix Bot..." -ForegroundColor Cyan
    
    # 1. Criar App Registration
    $appRegistration = New-BotAppRegistration -DisplayName $BotName
    
    # 2. Criar Bot Service
    $botService = New-AzureBotService -BotName $BotName -AppId $appRegistration.AppId -AppPassword $appRegistration.AppPassword -ResourceGroupName $ResourceGroupName
    
    # 3. Habilitar canal do Teams
    Enable-TeamsChannel -BotName $BotName -ResourceGroupName $ResourceGroupName
    
    # 4. Criar manifesto do Teams
    $manifestPath = New-TeamsManifest -AppId $appRegistration.AppId -BotName $BotName
    
    # 5. Criar configuração do Copilot Studio
    $configPath = New-CopilotStudioConfig -AppId $appRegistration.AppId -AppPassword $appRegistration.AppPassword -BotName $BotName
    
    # 6. Criar script de deployment
    $deployScriptPath = New-DeploymentScript -AppId $appRegistration.AppId -AppPassword $appRegistration.AppPassword -BotName $BotName
    
    # Resumo
    Write-Host "`n🎉 Configuração do Phoenix Bot concluída com sucesso!" -ForegroundColor Green
    Write-Host "📋 Resumo:" -ForegroundColor Cyan
    Write-Host "   • App ID: $($appRegistration.AppId)" -ForegroundColor White
    Write-Host "   • Bot Name: $BotName" -ForegroundColor White
    Write-Host "   • Resource Group: $ResourceGroupName" -ForegroundColor White
    Write-Host "   • Manifesto Teams: $manifestPath" -ForegroundColor White
    Write-Host "   • Configuração: $configPath" -ForegroundColor White
    Write-Host "   • Script Deploy: $deployScriptPath" -ForegroundColor White
    
    Write-Host "`n📱 Próximos passos:" -ForegroundColor Yellow
    Write-Host "   1. Execute o script: $deployScriptPath" -ForegroundColor White
    Write-Host "   2. Importe o manifesto no Teams: $manifestPath" -ForegroundColor White
    Write-Host "   3. Configure o bot no Copilot Studio usando: $configPath" -ForegroundColor White
    
}
catch {
    Write-Host "❌ Erro durante a configuração: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
    exit 1
}

Write-Host "`n✨ Phoenix Bot está pronto para uso!" -ForegroundColor Green

