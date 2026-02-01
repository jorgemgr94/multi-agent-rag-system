#!/bin/bash
# ==============================================================================
# Multi-Agent RAG System - VPS Deployment Script
# ==============================================================================
# This script sets up and deploys the complete stack using Docker Compose.
# Designed for local demos or simple VPS deployments.
#
# Usage:
#   ./deploy.sh          # Start all services
#   ./deploy.sh stop     # Stop all services
#   ./deploy.sh restart  # Restart all services
#   ./deploy.sh logs     # View logs
#   ./deploy.sh clean    # Stop and remove all containers/volumes
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed.${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed.${NC}"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Determine which docker compose command to use
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Setup environment
setup_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}No .env file found. Creating from .env.example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}.env file created. Please edit it with your API keys.${NC}"
        else
            echo -e "${RED}Error: .env.example not found.${NC}"
            exit 1
        fi
    fi
}

# Start services
start() {
    echo -e "${GREEN}🚀 Starting Multi-Agent RAG System...${NC}"
    setup_env
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD up -d --build
    
    echo ""
    echo -e "${GREEN}✅ All services started!${NC}"
    echo ""
    echo "📊 Access the services:"
    echo "   - Backend API:    http://localhost:8000"
    echo "   - API Docs:       http://localhost:8000/docs"
    echo "   - Dashboard:      http://localhost:8501"
    echo "   - Neo4j Browser:  http://localhost:7474"
    echo ""
    echo "Run './deploy.sh logs' to view logs"
}

# Stop services
stop() {
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD down
    echo -e "${GREEN}✅ Services stopped.${NC}"
}

# Restart services
restart() {
    stop
    start
}

# View logs
logs() {
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD logs -f
}

# Clean up everything
clean() {
    echo -e "${RED}⚠️  This will remove all containers and volumes (including Neo4j data).${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        COMPOSE_CMD=$(get_compose_cmd)
        $COMPOSE_CMD down -v --remove-orphans
        echo -e "${GREEN}✅ Cleanup complete.${NC}"
    else
        echo "Cancelled."
    fi
}

# Main
check_docker

case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    clean)
        clean
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|clean}"
        exit 1
        ;;
esac
