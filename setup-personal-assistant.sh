#!/bin/bash

# ============================================
# OpenAiBot Personal Assistant Setup Script
# ============================================
# This script automates the setup of OpenAiBot as a personal assistant
# with RSS feed monitoring and Discord channel management.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE=".env"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
CONFIG_DIR="./config_dir"
LOGS_DIR="./logs"
CUSTOM_PLUGINS_DIR="./custom_plugins"
SECRETS_DIR="./secrets"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║      OpenAiBot Personal Assistant Setup Script         ║"
    echo "║           Automated Installation & Configuration        ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker from: https://www.docker.com/get-started"
        exit 1
    fi
    print_info "Docker found: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed!"
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi

    # Determine docker-compose command
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_info "Docker Compose found: $(docker compose version)"
    else
        COMPOSE_CMD="docker-compose"
        print_info "Docker Compose found: $(docker-compose --version)"
    fi

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running!"
        echo "Please start Docker and try again."
        exit 1
    fi

    # Check disk space (require at least 5GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        print_warning "Low disk space: ${available_space}GB available (5GB recommended)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    print_success "All prerequisites met!"
}

# Create directory structure
create_directories() {
    print_step "Creating directory structure..."

    directories=("$CONFIG_DIR" "$LOGS_DIR" "$BACKUP_DIR" "$CUSTOM_PLUGINS_DIR" "$SECRETS_DIR")

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_info "Created directory: $dir"
        else
            print_info "Directory exists: $dir"
        fi
    done

    # Set permissions
    chmod 755 "$CONFIG_DIR" "$LOGS_DIR" "$BACKUP_DIR" "$CUSTOM_PLUGINS_DIR"
    chmod 700 "$SECRETS_DIR"

    print_success "Directory structure created!"
}

# Setup configuration files
setup_configuration() {
    print_step "Setting up configuration files..."

    # Check if .env exists
    if [ -f "$CONFIG_FILE" ]; then
        print_warning "Configuration file already exists: $CONFIG_FILE"
        read -p "Do you want to backup and create a new one? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            backup_file="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            mv "$CONFIG_FILE" "$backup_file"
            print_info "Backed up existing config to: $backup_file"
        else
            print_info "Keeping existing configuration"
            return
        fi
    fi

    # Use personal assistant template if it exists
    if [ -f ".env.personal-assistant" ]; then
        cp ".env.personal-assistant" "$CONFIG_FILE"
        print_info "Using personal assistant template"
    elif [ -f ".env.exp" ]; then
        cp ".env.exp" "$CONFIG_FILE"
        print_info "Using example template"
    else
        print_error "No configuration template found!"
        exit 1
    fi

    # Setup Docker Compose file
    if [ -f "docker-compose.personal-assistant.yml" ]; then
        if [ -f "$DOCKER_COMPOSE_FILE" ]; then
            backup_file="${DOCKER_COMPOSE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            mv "$DOCKER_COMPOSE_FILE" "$backup_file"
            print_info "Backed up existing docker-compose.yml to: $backup_file"
        fi
        cp "docker-compose.personal-assistant.yml" "$DOCKER_COMPOSE_FILE"
        print_info "Using optimized Docker Compose configuration"
    fi

    print_success "Configuration files ready!"
}

# Collect API keys and tokens
collect_credentials() {
    print_step "Collecting API credentials..."

    echo -e "\n${YELLOW}Please have the following ready:${NC}"
    echo "1. OpenAI API Key (from https://platform.openai.com/api-keys)"
    echo "2. Discord Bot Token (from https://discord.com/developers/applications)"
    echo "3. Discord Channel IDs (right-click channels with Developer Mode enabled)"
    echo ""

    # OpenAI API Key
    read -p "Enter your OpenAI API Key (sk-...): " openai_key
    if [ -z "$openai_key" ]; then
        print_warning "No OpenAI key provided. You'll need to add it manually later."
    else
        # Validate key format
        if [[ ! $openai_key =~ ^sk- ]]; then
            print_warning "API key doesn't start with 'sk-'. Make sure it's correct."
        fi
        sed -i.bak "s|GLOBAL_OAI_KEY=.*|GLOBAL_OAI_KEY=$openai_key|" "$CONFIG_FILE"
        # Save to secrets
        echo "$openai_key" > "$SECRETS_DIR/openai_key.txt"
        chmod 600 "$SECRETS_DIR/openai_key.txt"
    fi

    # Discord Bot Token
    read -p "Enter your Discord Bot Token: " discord_token
    if [ -z "$discord_token" ]; then
        print_warning "No Discord token provided. You'll need to add it manually later."
    else
        sed -i.bak "s|DISCORD_BOT_TOKEN=.*|DISCORD_BOT_TOKEN=$discord_token|" "$CONFIG_FILE"
        # Save to secrets
        echo "$discord_token" > "$SECRETS_DIR/discord_token.txt"
        chmod 600 "$SECRETS_DIR/discord_token.txt"
    fi

    # Discord Channel IDs
    echo -e "\n${BLUE}Discord Channel Configuration:${NC}"
    echo "Leave blank to skip channel configuration"

    read -p "News Channel ID (for RSS updates): " news_channel
    if [ ! -z "$news_channel" ]; then
        sed -i.bak "s|PLUGIN_NEWS_CHANNEL_ID=.*|PLUGIN_NEWS_CHANNEL_ID=$news_channel|" "$CONFIG_FILE"
    fi

    read -p "Tech Channel ID (for tech discussions): " tech_channel
    if [ ! -z "$tech_channel" ]; then
        sed -i.bak "s|PLUGIN_TECH_CHANNEL_ID=.*|PLUGIN_TECH_CHANNEL_ID=$tech_channel|" "$CONFIG_FILE"
    fi

    read -p "General Channel ID (for casual chat): " general_channel
    if [ ! -z "$general_channel" ]; then
        sed -i.bak "s|PLUGIN_GENERAL_CHANNEL_ID=.*|PLUGIN_GENERAL_CHANNEL_ID=$general_channel|" "$CONFIG_FILE"
    fi

    # Clean up backup files
    rm -f "${CONFIG_FILE}.bak"

    print_success "Credentials configured!"
}

# Configure RSS feeds
configure_rss_feeds() {
    print_step "Configuring RSS feeds..."

    echo -e "\n${BLUE}RSS Feed Configuration:${NC}"
    echo "Default feeds are already configured. You can add more later."

    read -p "Do you want to add custom RSS feeds now? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Enter RSS feed URLs (one per line, empty line to finish):"
        custom_feeds=""
        while true; do
            read -p "Feed URL: " feed_url
            if [ -z "$feed_url" ]; then
                break
            fi
            if [ -z "$custom_feeds" ]; then
                custom_feeds="$feed_url"
            else
                custom_feeds="$custom_feeds,$feed_url"
            fi
        done

        if [ ! -z "$custom_feeds" ]; then
            echo "PLUGIN_RSS_CUSTOM_FEEDS=$custom_feeds" >> "$CONFIG_FILE"
            print_info "Added custom RSS feeds"
        fi
    fi

    print_success "RSS feeds configured!"
}

# Generate secure passwords
generate_passwords() {
    print_step "Generating secure passwords..."

    # Generate random passwords
    RABBITMQ_PASS=$(openssl rand -base64 24 | tr -d "=/+")
    REDIS_PASS=$(openssl rand -base64 24 | tr -d "=/+")
    MONGO_PASS=$(openssl rand -base64 24 | tr -d "=/+")

    # Update configuration
    sed -i.bak "s|RABBITMQ_PASS=.*|RABBITMQ_PASS=$RABBITMQ_PASS|" "$CONFIG_FILE"
    sed -i.bak "s|StrongPassword123!|$RABBITMQ_PASS|g" "$CONFIG_FILE"

    sed -i.bak "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASS|" "$CONFIG_FILE"
    sed -i.bak "s|StrongRedisPass123!|$REDIS_PASS|g" "$CONFIG_FILE"

    sed -i.bak "s|MONGO_PASS=.*|MONGO_PASS=$MONGO_PASS|" "$CONFIG_FILE"
    sed -i.bak "s|StrongMongoPass123!|$MONGO_PASS|g" "$CONFIG_FILE"

    # Save passwords to secrets
    echo "RabbitMQ: $RABBITMQ_PASS" > "$SECRETS_DIR/passwords.txt"
    echo "Redis: $REDIS_PASS" >> "$SECRETS_DIR/passwords.txt"
    echo "MongoDB: $MONGO_PASS" >> "$SECRETS_DIR/passwords.txt"
    chmod 600 "$SECRETS_DIR/passwords.txt"

    # Clean up backup files
    rm -f "${CONFIG_FILE}.bak"

    print_info "Secure passwords generated and saved to: $SECRETS_DIR/passwords.txt"
    print_success "Passwords configured!"
}

# Pull Docker images
pull_docker_images() {
    print_step "Pulling Docker images..."

    $COMPOSE_CMD pull

    print_success "Docker images pulled!"
}

# Start services
start_services() {
    print_step "Starting services..."

    # Start in detached mode
    $COMPOSE_CMD up -d

    # Wait for services to be ready
    print_info "Waiting for services to start..."
    sleep 10

    # Check service health
    if $COMPOSE_CMD ps | grep -q "Up"; then
        print_success "Services started successfully!"
    else
        print_error "Some services failed to start. Check logs with: $COMPOSE_CMD logs"
        exit 1
    fi
}

# Create helper scripts
create_helper_scripts() {
    print_step "Creating helper scripts..."

    # Start script
    cat > "start.sh" << 'EOF'
#!/bin/bash
docker compose up -d
echo "Services started. Check logs with: docker compose logs -f"
EOF
    chmod +x start.sh

    # Stop script
    cat > "stop.sh" << 'EOF'
#!/bin/bash
docker compose down
echo "Services stopped."
EOF
    chmod +x stop.sh

    # Restart script
    cat > "restart.sh" << 'EOF'
#!/bin/bash
docker compose restart
echo "Services restarted. Check logs with: docker compose logs -f"
EOF
    chmod +x restart.sh

    # Logs script
    cat > "logs.sh" << 'EOF'
#!/bin/bash
docker compose logs -f llmbot
EOF
    chmod +x logs.sh

    # Backup script
    cat > "backup.sh" << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"
mkdir -p $BACKUP_DIR

# Backup configurations
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# Backup data
docker compose exec -T redis redis-cli SAVE
docker cp llmbot_redis:/data/dump.rdb $BACKUP_DIR/ 2>/dev/null || true
cp -r ./config_dir $BACKUP_DIR/ 2>/dev/null || true

echo "Backup completed: $BACKUP_DIR"
EOF
    chmod +x backup.sh

    # Status script
    cat > "status.sh" << 'EOF'
#!/bin/bash
echo "==================================="
echo "  OpenAiBot Personal Assistant    "
echo "         Service Status            "
echo "==================================="
echo ""
docker compose ps
echo ""
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""
echo "Recent Logs:"
docker compose logs --tail=5 llmbot
EOF
    chmod +x status.sh

    print_success "Helper scripts created!"
}

# Display final information
display_final_info() {
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗"
    echo -e "║            Installation Complete!                       ║"
    echo -e "╚════════════════════════════════════════════════════════╝${NC}\n"

    echo -e "${BLUE}Service Status:${NC}"
    $COMPOSE_CMD ps

    echo -e "\n${BLUE}Quick Commands:${NC}"
    echo "  ./start.sh    - Start services"
    echo "  ./stop.sh     - Stop services"
    echo "  ./restart.sh  - Restart services"
    echo "  ./logs.sh     - View logs"
    echo "  ./backup.sh   - Create backup"
    echo "  ./status.sh   - Check status"

    echo -e "\n${BLUE}Management URLs:${NC}"
    echo "  RabbitMQ: http://localhost:15672"
    echo "  Username: admin"
    echo "  Password: Check $SECRETS_DIR/passwords.txt"

    echo -e "\n${BLUE}Configuration:${NC}"
    echo "  Config file: $CONFIG_FILE"
    echo "  Secrets: $SECRETS_DIR/"
    echo "  Logs: $LOGS_DIR/"
    echo "  Backups: $BACKUP_DIR/"

    echo -e "\n${BLUE}Discord Commands:${NC}"
    echo "  /help - Show help message"
    echo "  /login - Configure OpenAI settings"
    echo "  /chat - Chat with AI"
    echo "  /task - Execute tasks with functions"

    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Invite your bot to Discord server"
    echo "2. Configure channel permissions"
    echo "3. Test with /help command"
    echo "4. Subscribe to RSS feeds with /task command"

    echo -e "\n${YELLOW}Important:${NC}"
    echo "- Keep your $SECRETS_DIR/ folder secure"
    echo "- Regular backups: ./backup.sh"
    echo "- Monitor logs: ./logs.sh"
    echo "- Update regularly: git pull && docker compose pull"

    echo -e "\n${GREEN}Your personal assistant is ready!${NC}"
}

# Main installation flow
main() {
    print_header

    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root is not recommended. Continue anyway? (y/N)"
        read -p "" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Change to script directory
    cd "$SCRIPT_DIR"

    # Run installation steps
    check_prerequisites
    create_directories
    setup_configuration
    collect_credentials
    configure_rss_feeds

    # Ask about security
    read -p "Generate secure passwords for services? (recommended) (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        generate_passwords
    fi

    # Pull and start
    pull_docker_images
    start_services
    create_helper_scripts

    # Display final information
    display_final_info
}

# Handle errors
trap 'print_error "Installation failed! Check the error above."; exit 1' ERR

# Run main installation
main "$@"