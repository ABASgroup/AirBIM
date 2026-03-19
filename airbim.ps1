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

function Cmd-Clean {
    Check-Docker

    Write-Host ""
    warn "WARNING: This will permanently delete all AirBIM containers, volumes and networks."
    warn "All data stored in the database will be LOST and cannot be recovered."
    Write-Host ""
    $confirm = Read-Host "Are you sure you want to proceed? (Y/n)"
    if ($confirm -eq "n" -or $confirm -eq "N"-or $confirm -eq "no" -or $confirm -eq "NO"-or $confirm -eq "No") {
        info "Clean cancelled."
        return
    }
    Write-Host ""

    $containers = @("airbim-frontend-dev", "airbim-frontend", "airbim-backend", "airbim-database", "airbim-cache", "airbim-broker", "airbim-storage")
    $volumes    = @("airbim_database_data", "airbim_frontend_node_modules", "airbim_cache_data", "airbim_storage_data", "airbim_broker_data")
    $networks   = @("airbim_default")

    info "Removing containers..."
    foreach ($c in $containers) {
        $ErrorActionPreference = "SilentlyContinue"
        $null = docker container inspect $c 2>&1
        $ok = $LASTEXITCODE -eq 0
        $ErrorActionPreference = "Stop"
        if ($ok) {
            docker rm -f $c | Out-Null
            success "Container removed: $c"
        } else {
            warn "Container not found, skipping: $c"
        }
    }

    info "Removing volumes..."
    foreach ($v in $volumes) {
        $ErrorActionPreference = "SilentlyContinue"
        $null = docker volume inspect $v 2>&1
        $ok = $LASTEXITCODE -eq 0
        $ErrorActionPreference = "Stop"
        if ($ok) {
            docker volume rm $v | Out-Null
            success "Volume removed: $v"
        } else {
            warn "Volume not found, skipping: $v"
        }
    }

    info "Removing networks..."
    foreach ($n in $networks) {
        $ErrorActionPreference = "SilentlyContinue"
        $null = docker network inspect $n 2>&1
        $ok = $LASTEXITCODE -eq 0
        $ErrorActionPreference = "Stop"
        if ($ok) {
            docker network rm $n | Out-Null
            success "Network removed: $n"
        } else {
            warn "Network not found, skipping: $n"
        }
    }

    success "Clean complete."
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
    Write-Host "  clean            Remove all AirBIM containers, volumes and networks (be careful, you'll lose all data from the database)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\airbim.ps1 start            # Production foreground"
    Write-Host "  .\airbim.ps1 start --dev      # Dev foreground"
    Write-Host "  .\airbim.ps1 start --dev -d   # Dev detached"
    Write-Host "  .\airbim.ps1 start -d         # Production detached"
    Write-Host "  .\airbim.ps1 rebuild          # Rebuild images"
    Write-Host "  .\airbim.ps1 logs backend     # Tail backend logs"
    Write-Host "  .\airbim.ps1 clean            # WARNING: This will delete ALL containers, volumes and networks related to AirBIM, including database data!"
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
    "clean"   { Cmd-Clean }
    "help|--help"    { Show-Usage; exit 1 }
    default   { Show-Usage; exit 1 }
}