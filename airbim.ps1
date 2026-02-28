#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── Configuration ───────────────────────────────────────────────────────────

$PROJECT_NAME  = "airbim"
$COMPOSE_BASE  = "docker-compose.yml"
$COMPOSE_PROD  = "docker-compose.prod.yml"
$COMPOSE_DEV   = "docker-compose.dev.yml"
$MODE_FILE     = ".airbim_deploy_mode"

# ─── Colors / Helpers ────────────────────────────────────────────────────────

function info    { param($msg) Write-Host "[INFO]  $msg"  -ForegroundColor Cyan }
function success { param($msg) Write-Host "[OK]    $msg"  -ForegroundColor Green }
function warn    { param($msg) Write-Host "[WARN]  $msg"  -ForegroundColor Yellow }
function err     { param($msg) Write-Host "[ERROR] $msg"  -ForegroundColor Red }

# ─── Environment check ───────────────────────────────────────────────────────

function Check-Env {
    if (-not (Test-Path ".env")) {
        warn ".env file not found."
        if (Test-Path "example.env") {
            info "Creating .env from example.env ..."
            Copy-Item "example.env" ".env"
            warn "Please edit the .env file with your actual settings, then run the command again."
            exit 1
        } else {
            err "example.env not found either. Cannot proceed without a .env file."
            exit 1
        }
    }
}

# ─── Env file reader ────────────────────────────────────────────────────────

function Get-EnvValue {
    param([string]$key, [string]$default = "")
    if (Test-Path ".env") {
        $line = Get-Content ".env" | Where-Object { $_ -match "^\s*$key\s*=" } | Select-Object -First 1
        if ($line) {
            $val = ($line -split '=', 2)[1] -replace '#.*$', '' -replace '^\s+|\s+$', ''
            if ($val) { return $val }
        }
    }
    return $default
}

# ─── Docker checks ───────────────────────────────────────────────────────────

function Check-Docker {
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        err "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        err "Docker daemon is not running. Please start Docker Desktop first."
        exit 1
    }
}

# ─── Compose command builder ─────────────────────────────────────────────────

function Get-ComposeCmd {
    param([string]$mode)
    if ($mode -eq "dev") {
        return "docker compose -p $PROJECT_NAME -f $COMPOSE_BASE -f $COMPOSE_DEV"
    } else {
        return "docker compose -p $PROJECT_NAME -f $COMPOSE_BASE -f $COMPOSE_PROD"
    }
}

# ─── Mode persistence ────────────────────────────────────────────────────────

function Save-Mode { param($m) Set-Content -Path $MODE_FILE -Value $m }

function Load-Mode {
    if (Test-Path $MODE_FILE) {
        return (Get-Content $MODE_FILE -Raw).Trim()
    }
    return "prod"
}

# ─── Commands ────────────────────────────────────────────────────────────────

function Cmd-Start {
    param([string[]]$cmdArgs)

    $mode     = "prod"
    $detached = $false

    foreach ($arg in $cmdArgs) {
        switch ($arg) {
            "--dev" { $mode = "dev" }
            "-d"    { $detached = $true }
            ""      { }
            default { err "Unknown option: $arg"; Show-Usage; exit 1 }
        }
    }

    Check-Docker
    Check-Env
    Save-Mode $mode

    $cmd = Get-ComposeCmd $mode
    $vitePort     = Get-EnvValue "VITE_PORT"     "5173"
    $apiPort      = Get-EnvValue "API_PORT"      "8000"
    $nginxPort = Get-EnvValue "NGINX_PORT" "80"
    $frontendUrl  = if ($nginxPort -eq "80") { "http://localhost" } else { "http://localhost:$nginxPort" }


    if ($mode -eq "dev") {
        info "Starting AirBIM in DEVELOPMENT mode..."
    } else {
        info "Starting AirBIM in PRODUCTION mode..."
    }

    if ($detached) {
        info "Starting containers (detached)..."
        Invoke-Expression "$cmd up -d"

        Write-Host ""
        if ($mode -eq "dev") {
            success "AirBIM is running in development mode!"
            info "Frontend (Vite):  http://localhost:$vitePort"
            info "Backend  (API):   http://localhost:$apiPort or http://localhost:$vitePort/api"
        } else {
            success "AirBIM is running in production mode!"
            info "Application:      $frontendUrl"
            info "Backend  (API):   http://localhost:$apiPort or $frontendUrl/api"
        }
    } else {
       Write-Host ""
        if ($mode -eq "dev") {
            info "Frontend (Vite):  http://localhost:$vitePort"
            info "Backend  (API):   http://localhost:$apiPort or http://localhost:$vitePort/api"
        } else {
            info "Application:      $frontendUrl"
            info "Backend  (API):   http://localhost:$apiPort or $frontendUrl/api"
        }
        info "Streaming logs... Press Ctrl+C to stop all containers."
        Write-Host ""

        try {
            Invoke-Expression "$cmd up"
        } finally {
            Write-Host ""
            info "Stopping containers..."
            Invoke-Expression "$cmd stop"
            success "All containers stopped."
        }
    }
}

function Cmd-Up {
    Check-Docker
    Check-Env
    $mode = Load-Mode
    $cmd  = Get-ComposeCmd $mode
    info "Starting containers without rebuilding (mode: $mode)..."
    Invoke-Expression "$cmd up -d"
    success "Containers started."
}

function Cmd-Stop {
    Check-Docker
    $mode = Load-Mode
    $cmd  = Get-ComposeCmd $mode
    info "Stopping containers..."
    Invoke-Expression "$cmd stop"
    success "All containers stopped."
}

function Cmd-Down {
    Check-Docker
    $mode = Load-Mode
    $cmd  = Get-ComposeCmd $mode
    info "Stopping and removing containers..."
    Invoke-Expression "$cmd down"
    success "All containers removed."
}

function Cmd-Rebuild {
    param([string[]]$cmdArgs)
    Check-Docker
    Check-Env
    $mode = Load-Mode
    foreach ($arg in $cmdArgs) {
        switch ($arg) {
            "--dev"  { $mode = "dev" }
            "--prod" { $mode = "prod" }
        }
    }
    Save-Mode $mode
    $cmd     = Get-ComposeCmd $mode
    $noCache = ""
    if ($cmdArgs -contains "--no-cache") { $noCache = "--no-cache" }
    info "Rebuilding containers (mode: $mode)..."
    Invoke-Expression "$cmd build $noCache"
    success "Containers rebuilt."
}

function Cmd-Logs {
    param([string[]]$cmdArgs)
    Check-Docker
    $mode = Load-Mode
    $cmd  = Get-ComposeCmd $mode
    $extra = $cmdArgs -join " "
    Invoke-Expression "$cmd logs -f $extra"
}

function Cmd-Status {
    Check-Docker
    $mode = Load-Mode
    $cmd  = Get-ComposeCmd $mode
    info "Current mode: $mode"
    Write-Host ""
    Invoke-Expression "$cmd ps"
}

# ─── Usage ───────────────────────────────────────────────────────────────────

function Show-Usage {
    Write-Host ""
    Write-Host "AirBIM — Docker deployment helper" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage: .\airbim.ps1 command [options]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start [flags]    Start all containers (builds images only if missing)"
    Write-Host "      --dev        Start in development mode (Vite HMR + hot reload)"
    Write-Host "      -d           Run in detached mode (background, no log output)"
    Write-Host "  up               Start existing containers without rebuilding"
    Write-Host "  stop             Stop all running containers"
    Write-Host "  down             Stop and remove all containers"
    Write-Host "  rebuild [flags]  Force-rebuild images"
    Write-Host "      --dev        Rebuild in development mode"
    Write-Host "      --prod       Rebuild in production mode"
    Write-Host "      --no-cache   Do not use cache when building images"
    Write-Host "  logs [service]   Follow container logs"
    Write-Host "  status           Show status of all containers"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\airbim.ps1 start            # Production foreground"
    Write-Host "  .\airbim.ps1 start --dev      # Dev foreground"
    Write-Host "  .\airbim.ps1 start --dev -d   # Dev detached"
    Write-Host "  .\airbim.ps1 start -d         # Production detached"
    Write-Host "  .\airbim.ps1 rebuild          # Rebuild images"
    Write-Host "  .\airbim.ps1 logs backend     # Tail backend logs"
    Write-Host ""
}

# ─── Entrypoint ──────────────────────────────────────────────────────────────

$command = if ($args.Count -gt 0) { $args[0] } else { "" }
$rest    = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }

switch ($command) {
    "start"   { Cmd-Start   $rest }
    "up"      { Cmd-Up }
    "stop"    { Cmd-Stop }
    "down"    { Cmd-Down }
    "rebuild" { Cmd-Rebuild $rest }
    "logs"    { Cmd-Logs    $rest }
    "status"  { Cmd-Status }
    "help|--help"    { Show-Usage; exit 1 }
    default   { Show-Usage; exit 1 }
}