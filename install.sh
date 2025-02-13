#!/bin/bash

# Function to log messages with timestamps
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a install.log
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_message "ERROR: $1 is not installed"
        echo "Please install $1 before continuing."
        echo "Visit https://docs.docker.com/engine/install/ for Docker installation instructions."
        exit 1
    fi
}

# Function to detect system architecture
detect_architecture() {
    local arch=$(uname -m)
    case $arch in
        x86_64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        armv7l)
            echo "armv7"
            ;;
        *)
            log_message "ERROR: Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

# Function to clean Docker environment
clean_docker() {
    local clean_all=$1

    log_message "Starting Docker cleanup..."

    # Stop and remove containers
    if [ "$(docker ps -q)" ]; then
        log_message "Stopping all running containers..."
        docker stop $(docker ps -q)
        log_message "Removing all containers..."
        docker rm $(docker ps -aq)
    else
        log_message "No containers to remove"
    fi

    # Remove images
    if [ "$clean_all" = "true" ] && [ "$(docker images -q)" ]; then
        log_message "Removing all Docker images..."
        docker rmi $(docker images -q) || true
    else
        log_message "Removing project-specific images..."
        docker rmi ${BIND9_IMAGE} ${TRAEFIK_IMAGE} ${NGINX_IMAGE} ${POSTGRES_IMAGE} ${CLOUDFLARE_DDNS_IMAGE} 2>/dev/null || true
    fi

    # Remove networks
    log_message "Removing project network if exists..."
    docker network rm terrerov_net 2>/dev/null || true
    if [ "$clean_all" = "true" ]; then
        log_message "Pruning unused networks..."
        docker network prune -f
    fi

    # Clean volumes
    log_message "Pruning unused volumes..."
    docker volume prune -f

    log_message "Docker cleanup completed"
}

# Clear or create log file
> install.log

log_message "Starting installation process..."

# Check prerequisites
log_message "Checking prerequisites..."
check_command docker
check_command docker-compose

# Detect system architecture
ARCH=$(detect_architecture)
log_message "Detected architecture: $ARCH"

# Set Docker image variables based on architecture
case $ARCH in
    amd64)
        export BIND9_IMAGE="ubuntu/bind9:latest"
        export TRAEFIK_IMAGE="traefik:v2.10"
        export NGINX_IMAGE="nginx:alpine"
        export POSTGRES_IMAGE="postgres:15-alpine"
        export CLOUDFLARE_DDNS_IMAGE="oznu/cloudflare-ddns:latest"
        ;;
    arm64|armv7)
        export BIND9_IMAGE="ubuntu/bind9:latest"
        export TRAEFIK_IMAGE="traefik:v2.10"
        export NGINX_IMAGE="arm64v8/nginx:alpine"
        export POSTGRES_IMAGE="arm64v8/postgres:15-alpine"
        export CLOUDFLARE_DDNS_IMAGE="oznu/cloudflare-ddns:latest"
        ;;
    *)
        log_message "ERROR: Unsupported architecture"
        exit 1
        ;;
esac

# Ask user about cleanup options
read -p "Do you want to perform a complete Docker cleanup? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    clean_docker true
else
    clean_docker false
fi

# Check Docker version
DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
if [ $? -ne 0 ]; then
    log_message "ERROR: Docker daemon is not running"
    echo "Please start the Docker daemon before continuing."
    exit 1
fi
log_message "Docker version: $DOCKER_VERSION"

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_message "ERROR: .env file not found"
    echo "Please create .env file from .env.example and configure it before continuing."
    exit 1
fi

# Create Docker network if it doesn't exist
log_message "Setting up Docker network..."
if ! docker network inspect terrerov_net >/dev/null 2>&1; then
    docker network create --driver bridge \
        --subnet=172.18.0.0/16 \
        terrerov_net
    log_message "Created terrerov_net network"
else
    log_message "Network terrerov_net already exists"
fi

# Pull Docker images
log_message "Pulling Docker images..."
echo "Pulling required Docker images..."
docker-compose pull

# Start services
log_message "Starting services..."
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check if containers are running
log_message "Checking container status..."
for service in bind9 traefik nginx postgres; do
    if [ "$(docker ps -q -f name=$service)" ]; then
        log_message "$service is running"
    else
        log_message "ERROR: $service failed to start"
        echo "Check logs with: docker-compose logs $service"
        exit 1
    fi
done

# Test DNS resolution
log_message "Testing DNS resolution..."
echo "Testing DNS resolution..."
if docker exec bind9 nslookup www.terrerov.com localhost > /dev/null 2>&1; then
    log_message "DNS resolution test passed"
else
    log_message "WARNING: DNS resolution test failed"
fi

# Test web access
log_message "Testing web access..."
echo "Testing web access..."
if curl -s -H "Host: www.terrerov.com" http://localhost > /dev/null; then
    log_message "Web access test passed"
else
    log_message "WARNING: Web access test failed"
fi

# Test database connection
log_message "Testing database connection..."
echo "Testing database connection..."
if docker exec postgres pg_isready -U ${POSTGRES_USER} > /dev/null 2>&1; then
    log_message "Database connection test passed"
else
    log_message "WARNING: Database connection test failed"
fi

# Final status
log_message "Installation completed"
echo "
Installation completed! Check install.log for detailed information.

Access your services at:
- Traefik Dashboard: https://traefik.terrerov.com
- Web Server: https://www.terrerov.com
- Database: db.terrerov.com:5432
"