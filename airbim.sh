#!/usr/bin/env bash

set -euo pipefail

# ─── Configuration ───────────────────────────────────────────────────────────

PROJECT_NAME="airbim"
COMPOSE_BASE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"
COMPOSE_DEV="docker-compose.dev.yml"
MODE_FILE=".airbim_deploy_mode"

# ─── Colors ──────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Helpers ─────────────────────────────────────────────────────────────────

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Environment check ──────────────────────────────────────────────────────

check_env() {
    if [ ! -f .env ]; then
        warn ".env file not found."
        if [ -f example.env ]; then
            info "Creating .env from example.env ..."
            cp example.env .env
            warn "Please edit the .env file with your actual settings, then run the command again."
            exit 1
        else
            error "example.env not found either. Cannot proceed without a .env file."
            exit 1
        fi
    fi
}

# ─── Env file reader ────────────────────────────────────────────────────────

get_env_value() {
    local key="$1"
    local default="$2"
    if [ -f .env ]; then
        local val
        val=$(grep -E "^\s*${key}\s*=" .env | head -1 | sed 's/[^=]*=//' | sed 's/#.*//' | tr -d '[:space:]')
        [ -n "$val" ] && echo "$val" || echo "$default"
    else
        echo "$default"
    fi
}


# ─── Docker checks ──────────────────────────────────────────────────────────

check_docker() {
    if ! command -v docker &>/dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    if ! docker info &>/dev/null; then
        error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
}

# ─── Compose command builder ────────────────────────────────────────────────

compose_cmd() {
    local mode="$1"
    if [ "$mode" = "dev" ]; then
        echo "docker compose -p ${PROJECT_NAME} -f ${COMPOSE_BASE} -f ${COMPOSE_DEV}"
    else
        echo "docker compose -p ${PROJECT_NAME} -f ${COMPOSE_BASE} -f ${COMPOSE_PROD}"
    fi
}

# ─── Mode persistence ───────────────────────────────────────────────────────

save_mode() { echo "$1" > "${MODE_FILE}"; }

load_mode() {
    if [ -f "${MODE_FILE}" ]; then
        cat "${MODE_FILE}"
    else
        echo "prod"
    fi
}

# ─── Commands ────────────────────────────────────────────────────────────────

cmd_start() {
    local mode="prod"
    local detached=false

    # Parse flags in any order
    while [ $# -gt 0 ]; do
        case "$1" in
            --dev) mode="dev" ;;
            -d)    detached=true ;;
            "")    ;; # skip empty args
            *)     error "Unknown option: $1"; usage; exit 1 ;;
        esac
        shift
    done

    check_docker
    check_env
    save_mode "$mode"

    local cmd
    cmd=$(compose_cmd "$mode")

    local vite_port api_port nginx_port frontend_url
    vite_port=$(get_env_value "VITE_PORT" "5173")
    api_port=$(get_env_value "API_PORT" "8000")
    nginx_port=$(get_env_value "NGINX_PORT" "80")
    if [ "$nginx_port" = "80" ]; then
        frontend_url="http://localhost"
    else
        frontend_url="http://localhost:${nginx_port}"
    fi


    if [ "$mode" = "dev" ]; then
        info "Starting AirBIM in ${BOLD}DEVELOPMENT${NC} mode..."
    else
        info "Starting AirBIM in ${BOLD}PRODUCTION${NC} mode..."
    fi

    # docker compose up (without --build) only builds images when they
    # don't exist yet; existing images are reused as-is.
    # Use 'rebuild' command to force a rebuild.

    if [ "$detached" = true ]; then
        info "Starting containers (detached)..."
        $cmd up -d

        echo ""
        if [ "$mode" = "dev" ]; then
            success "AirBIM is running in development mode!"
            info "Frontend (Vite):  http://localhost:${vite_port}"
            info "Backend  (API):   http://localhost:${api_port} or http://localhost:${vite_port}/api"
        else
            success "AirBIM is running in production mode!"
            info "Application:      ${frontend_url}"
            info "Backend  (API):   http://localhost:${api_port} or ${frontend_url}/api"
        fi
    else
        echo ""
        if [ "$mode" = "dev" ]; then
            info "Frontend (Vite):  http://localhost:${vite_port}"
            info "Backend  (API):   http://localhost:${api_port} or http://localhost:${vite_port}/api"
        else
            info "Application:      ${frontend_url}"
            info "Backend  (API):   http://localhost:${api_port} or ${frontend_url}/api"
        fi
        info "Streaming logs... Press ${BOLD}Ctrl+C${NC} to stop all containers."
        echo ""

        # Run in foreground: shows logs, Ctrl+C stops containers
        trap 'echo ""; info "Stopping containers..."; $cmd stop; success "All containers stopped."; exit 0' INT TERM
        $cmd up || true
    fi
}

cmd_up() {
    check_docker
    check_env

    local mode
    mode=$(load_mode)

    local cmd
    cmd=$(compose_cmd "$mode")

    info "Starting containers without rebuilding (mode: ${mode})..."
    $cmd up -d

    success "Containers started."
}

cmd_stop() {
    check_docker

    local mode
    mode=$(load_mode)

    local cmd
    cmd=$(compose_cmd "$mode")

    info "Stopping containers..."
    $cmd stop

    success "All containers stopped."
}

cmd_down() {
    check_docker

    local mode
    mode=$(load_mode)

    local cmd
    cmd=$(compose_cmd "$mode")

    info "Stopping and removing containers..."
    $cmd down

    success "All containers removed."
}

cmd_rebuild() {
    check_docker
    check_env

    local mode
    mode=$(load_mode)

    local cmd
    cmd=$(compose_cmd "$mode")

    local no_cache=""
    for arg in "$@"; do
        if [[ "$arg" == "--no-cache" ]]; then
            no_cache="--no-cache"
        fi
    done

    info "Rebuilding containers (mode: ${mode})..."
    $cmd build $no_cache

    success "Containers rebuilt"
}

cmd_logs() {
    check_docker

    local mode
    mode=$(load_mode)

    local cmd
    cmd=$(compose_cmd "$mode")

    $cmd logs -f "$@"
}

cmd_clean() {
    check_docker

    echo ""
    warn "WARNING: This will permanently delete all AirBIM containers, volumes and networks."
    warn "All data stored in the database will be LOST and cannot be recovered."
    echo ""
    read -rp "Are you sure you want to proceed? (Y/n): " confirm
    if [[ "$confirm" == "n" || "$confirm" == "N" || "$confirm" == "no" || "$confirm" == "NO" || "$confirm" == "No" ]]; then
        info "Clean cancelled."
        return
    fi
    echo ""

    local containers=("airbim-frontend-dev" "airbim-frontend" "airbim-backend" "airbim-database" "airbim-cache" "airbim-broker")
    local volumes=("airbim_database_data" "airbim_frontend_node_modules")
    local networks=("airbim_default")

    info "Removing containers..."
    for c in "${containers[@]}"; do
        if docker container inspect "$c" &>/dev/null; then
            docker rm -f "$c" && success "Container removed: $c" || true
        else
            warn "Container not found, skipping: $c"
        fi
    done

    info "Removing volumes..."
    for v in "${volumes[@]}"; do
        if docker volume inspect "$v" &>/dev/null; then
            docker volume rm "$v" && success "Volume removed: $v" || true
        else
            warn "Volume not found, skipping: $v"
        fi
    done

    info "Removing networks..."
    for n in "${networks[@]}"; do
        if docker network inspect "$n" &>/dev/null; then
            docker network rm "$n" && success "Network removed: $n" || true
        else
            warn "Network not found, skipping: $n"
        fi
    done

    success "Clean complete."
}

cmd_status() {
    check_docker

    local mode
    mode=$(load_mode)

    local cmd
    cmd=$(compose_cmd "$mode")

    info "Current mode: ${BOLD}${mode}${NC}"
    echo ""
    $cmd ps
}

# ─── Usage ───────────────────────────────────────────────────────────────────

usage() {
    echo ""
    echo -e "${BOLD}AirBIM — Docker deployment helper${NC}"
    echo ""
    echo "Usage: ./airbim.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start [flags]    Start all containers (builds images only if missing)"
    echo "      --dev        Start in development mode (Vite HMR + hot reload)"
    echo "      -d           Run in detached mode (background, no log output)"
    echo "  up               Start existing containers without rebuilding (start analog, but uses last saved deployment mode - dev or prod)"
    echo "  stop             Stop all running containers"
    echo "  down             Stop and remove all containers"
    echo "  rebuild [flags]  Force-rebuild images"
    echo "      --no-cache   Do not use cache when building images"
    echo "  logs [service]   Follow container logs (optionally for a specific service)"
    echo "  status           Show status of all containers"
    echo "  clean            Remove all AirBIM containers, volumes and networks (be careful, you'll lose all data from the database)"
    echo ""
    echo "Examples:"
    echo "  ./airbim.sh start            # Production foreground (logs + Ctrl+C stops)"
    echo "  ./airbim.sh start --dev      # Dev foreground (Vite + hot reload)"
    echo "  ./airbim.sh start --dev -d   # Dev detached (background)"
    echo "  ./airbim.sh start -d         # Production detached (background)"
    echo "  ./airbim.sh rebuild          # Rebuild images after code changes"
    echo "  ./airbim.sh logs backend     # Tail backend logs"
    echo "  ./airbim.sh clean            # WARNING: This will delete ALL containers, volumes and networks related to AirBIM, including database data!"
    echo ""
}

# ─── Entrypoint ──────────────────────────────────────────────────────────────

case "${1:-}" in
    start)   shift; cmd_start "$@" ;;
    up)      cmd_up ;;
    stop)    cmd_stop ;;
    down)    cmd_down ;;
    rebuild) shift; cmd_rebuild "$@" ;;
    logs)    shift; cmd_logs "$@" ;;
    status)  cmd_status ;;
    clean)   cmd_clean ;;
    help|--help) usage; exit 0 ;;
    *)       usage; exit 1 ;;
esac
