#!/bin/bash

# AI Trading Bot - Docker Quick Start Script

set -e

echo "🐳 AI Crypto Trading Bot - Docker Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if .env file exists
check_config() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        
        if [ -f "config.env.example" ]; then
            print_status "Copying config.env.example to .env"
            cp config.env.example .env
            print_warning "Please edit .env file with your API keys and settings"
            print_status "You can edit it with: nano .env"
            read -p "Press Enter after configuring .env file..."
        else
            print_error "config.env.example not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success ".env file found"
    fi
}

# Create required directories
create_directories() {
    print_status "Creating required directories..."
    mkdir -p logs data
    print_success "Directories created"
}

# Check Google credentials
check_google_credentials() {
    if [ ! -f "google-credentials.json" ]; then
        print_warning "google-credentials.json not found"
        print_status "Google Sheets integration will be disabled"
        print_status "To enable: Place your Google service account credentials in google-credentials.json"
    else
        print_success "Google credentials found"
    fi
}

# Show menu
show_menu() {
    echo ""
    echo "Choose deployment option:"
    echo "1) Main Trading Bot (with Redis)"
    echo "2) Dashboard Only"
    echo "3) Complete Suite (Bot + Dashboard + Redis) [Recommended]"
    echo "4) Alternative Bot (without Redis)"
    echo "5) Redis Only"
    echo "6) Build Images Only"
    echo "7) Stop All Services"
    echo "8) View Logs"
    echo "9) System Status"
    echo "10) Clean Up (Remove containers and images)"
    echo "11) Exit"
    echo ""
}

# Deploy main trading bot with Redis
deploy_main_bot() {
    print_status "Deploying main trading bot with Redis..."
    docker-compose up -d redis trading-bot
    print_success "Trading bot and Redis deployed"
    print_status "View logs with: docker-compose logs -f trading-bot"
    print_status "Redis available at: localhost:6379"
}

# Deploy dashboard only
deploy_dashboard() {
    print_status "Deploying dashboard with Redis..."
    docker-compose up -d redis dashboard
    print_success "Dashboard and Redis deployed"
    print_status "Access dashboard at: http://localhost:8050"
    print_status "View logs with: docker-compose logs -f dashboard"
}

# Deploy complete suite
deploy_suite() {
    print_status "Deploying complete trading suite..."
    docker-compose up -d redis trading-suite
    print_success "Complete trading suite deployed"
    print_status "Access dashboard at: http://localhost:8050"
    print_status "Bot API available at: http://localhost:5001"
    print_status "Redis available at: localhost:6379"
    print_status "View logs with: docker-compose logs -f trading-suite"
}

# Deploy alternative bot (without Redis)
deploy_alternative_bot() {
    print_status "Deploying alternative trading bot..."
    docker-compose --profile alternative up -d ai-trading-bot
    print_success "Alternative trading bot deployed"
    print_status "View logs with: docker-compose logs -f ai-trading-bot"
}

# Deploy Redis only
deploy_redis() {
    print_status "Deploying Redis cache..."
    docker-compose up -d redis
    print_success "Redis deployed"
    print_status "Redis available at: localhost:6379"
    print_status "View logs with: docker-compose logs -f redis"
}

# Build images only
build_images() {
    print_status "Building Docker images..."
    docker-compose build
    print_success "Images built successfully"
}

# Stop all services
stop_services() {
    print_status "Stopping all services..."
    docker-compose down
    print_success "All services stopped"
}

# View logs
view_logs() {
    echo ""
    echo "Choose service to view logs:"
    echo "1) Main Trading Bot"
    echo "2) Dashboard"
    echo "3) Trading Suite"
    echo "4) Alternative Bot"
    echo "5) Redis"
    echo "6) All Services"
    echo ""
    read -p "Enter choice (1-6): " log_choice
    
    case $log_choice in
        1)
            docker-compose logs -f trading-bot
            ;;
        2)
            docker-compose logs -f dashboard
            ;;
        3)
            docker-compose logs -f trading-suite
            ;;
        4)
            docker-compose logs -f ai-trading-bot
            ;;
        5)
            docker-compose logs -f redis
            ;;
        6)
            docker-compose logs -f
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# Show system status
show_status() {
    print_status "System Status"
    echo ""
    
    # Check running containers
    echo "📦 Running Containers:"
    docker-compose ps
    echo ""
    
    # Check Redis connection
    echo "🔴 Redis Status:"
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is running and responding"
    else
        print_warning "Redis is not responding"
    fi
    echo ""
    
    # Check disk usage
    echo "💾 Docker Disk Usage:"
    docker system df
    echo ""
    
    # Check logs for errors
    echo "📋 Recent Errors (last 10):"
    docker-compose logs --tail=50 | grep -i error | tail -10 || echo "No recent errors found"
}

# Clean up
cleanup() {
    print_warning "This will remove all containers, images, and volumes!"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        print_status "Stopping services..."
        docker-compose down -v
        
        print_status "Removing images..."
        docker-compose down --rmi all
        
        print_status "Cleaning up Docker system..."
        docker system prune -f
        
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main execution
main() {
    print_status "Starting Docker deployment script..."
    
    # Pre-flight checks
    check_docker
    check_config
    create_directories
    check_google_credentials
    
    # Main loop
    while true; do
        show_menu
        read -p "Enter your choice (1-11): " choice
        
        case $choice in
            1)
                deploy_main_bot
                ;;
            2)
                deploy_dashboard
                ;;
            3)
                deploy_suite
                ;;
            4)
                deploy_alternative_bot
                ;;
            5)
                deploy_redis
                ;;
            6)
                build_images
                ;;
            7)
                stop_services
                ;;
            8)
                view_logs
                ;;
            9)
                show_status
                ;;
            10)
                cleanup
                ;;
            11)
                print_status "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-11."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main 