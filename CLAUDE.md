# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLMKira (OpenAiBot) is an event-driven LLM chatbot framework supporting multiple messaging platforms (Telegram, Discord, Kook, Slack). It uses a message queue architecture with RabbitMQ to decouple message sending and receiving, enabling flexible plugin-based functionality.

**Key Architecture Principle**: The system is split into two separate processes:
- **Sender** (`start_sender.py`): Handles platform-specific message sending and bot events
- **Receiver** (`start_receiver.py`): Processes messages, executes LLM interactions, and runs plugins

These communicate asynchronously via RabbitMQ message queues.

## Development Commands

### Package Management
This project uses **PDM** (Python Development Master) for dependency management, NOT pip or poetry.

```bash
# Install dependencies
pdm install -G bot           # Install with bot platform dependencies
pdm install -G testing       # Install with testing dependencies

# Run the bot
pdm run python start_sender.py      # Start sender (platform bots)
pdm run python start_receiver.py    # Start receiver (LLM processing)

# Skip tutorial on startup
pdm run python start_sender.py --no_tutorial
pdm run python start_receiver.py --no_tutorial
```

### Running with PM2 (Production)
```bash
npm install pm2 -g
pm2 start pm2.json           # Starts both sender and receiver
pm2 status                   # Check status
pm2 logs                     # View logs
```

### Docker Deployment

#### Quick Reference (Development Mode)

**Most common commands for day-to-day development:**

```bash
# After making code changes - restart container
docker restart llmbot_personal_assistant

# Watch logs in real-time
docker logs llmbot_personal_assistant --tail 50 --follow

# Stop all services
docker compose down

# Start in Development Mode (code mounted from host)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Verify source code volumes are mounted correctly
docker inspect llmbot_personal_assistant --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' | grep -E "/app/(app|llmkira|start_)"

# Clear Python bytecode cache if seeing old behavior
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
docker exec llmbot_personal_assistant find /app -type d -name __pycache__ -exec rm -rf {} +
docker restart llmbot_personal_assistant
```

---

**IMPORTANT: Understanding Docker Setup**

This project uses Docker with a **pre-built image** (`sudoskys/llmbot:latest`). The source code is **baked into the Docker image**, NOT mounted as a volume by default. This means:

- ✅ Production: Use pre-built image for stability
- ❌ Development: Code changes on host won't reflect in container
- ⚠️ **Problem**: Editing files with Claude Code won't update running container

**Two Deployment Modes:**

#### 1. Production Mode (Pre-built Image)
```bash
# Use pre-built image (code is in the image)
docker compose -f docker-compose.yml up -d

# Update images from Docker Hub
docker compose pull

# Restart to apply new image
docker compose restart llmbot

# Access container shell
docker exec -it llmbot_personal_assistant /bin/bash
```

**When code changes are made:**
- Changes to host files do NOT affect running container
- Must either:
  - Rebuild the Docker image, OR
  - Use Development Mode (below)

#### 2. Development Mode (Source Code Mounted) **← RECOMMENDED FOR CLAUDE CODE**
```bash
# Use both configs to mount source code as volumes
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Restart to apply code changes
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart llmbot

# Stop services
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

**Benefits of Development Mode:**
- ✅ Host code changes immediately available in container
- ✅ No need to rebuild images
- ✅ Faster development iteration
- ⚠️ Must restart container after Python code changes

**After making code changes in Development Mode:**
```bash
# Clear Python bytecode cache (optional but recommended)
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Restart container to reload Python code
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart llmbot

# Or restart specific service (faster)
docker restart llmbot_personal_assistant
```

#### Manual Code Deployment (Emergency)
If you need to deploy code changes to a running production container:

```bash
# Copy updated file to container
docker cp ./path/to/file.py llmbot_personal_assistant:/app/path/to/file.py

# Restart container
docker restart llmbot_personal_assistant
```

**Note**: This is NOT recommended for regular development. Use Development Mode instead.

#### Common Docker Issues & Solutions

**Problem: Code changes don't appear in container**
- **Cause**: Using production mode (code is in Docker image, not mounted)
- **Solution**: Switch to Development Mode OR manually copy files with `docker cp`

**Problem: Container still has old code after restart**
- **Cause**: Python bytecode cache (.pyc files)
- **Solution**:
  ```bash
  # Clear cache on host
  find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

  # Clear cache in container
  docker exec llmbot_personal_assistant find /app -type d -name __pycache__ -exec rm -rf {} +

  # Restart
  docker restart llmbot_personal_assistant
  ```

**Problem: "Module not found" after code changes**
- **Cause**: Development mode not properly configured
- **Solution**: Verify docker-compose.dev.yml is being used AND volumes are mounted correctly

**Best Practices for Development:**
1. ✅ Always use Development Mode for active development
2. ✅ Restart container after Python code changes (Python loads modules on startup)
3. ✅ Clear bytecode cache if seeing old behavior
4. ✅ Use `docker logs llmbot_personal_assistant --tail 50 --follow` to watch for errors
5. ❌ Don't edit files inside container - edit on host (volumes keep them in sync)

### Testing
```bash
# The project structure suggests tests exist but no explicit test commands are documented
# Standard pytest should work:
pdm run pytest tests/
```

## Architecture & Code Structure

### Message Flow Architecture

1. **Platform Bot (Sender)** receives user message → packages as `TaskHeader` → sends to RabbitMQ queue
2. **RabbitMQ** buffers and routes messages
3. **Receiver** consumes from queue → processes with LLM → executes plugins → sends response back to queue
4. **Platform Bot (Sender)** consumes response from queue → sends to user

### Directory Structure

```
app/                    # Application layer - platform integrations
  sender/               # Platform-specific bot implementations (Telegram, Discord, etc.)
  receiver/             # Message processing and LLM interaction
  components/           # Shared components (credentials, etc.)
  middleware/           # Request/response middleware
  setting/              # Configuration management

llmkira/               # Core framework library
  sdk/                 # Plugin SDK and tools
    tools/             # Plugin loading, registration, metadata
  task/                # Message queue task management
  openai/              # OpenAI API client and schemas
  openapi/             # Plugin execution framework
    fuse/              # Plugin executor registration
    trigger/           # Plugin trigger logic
    hook/              # Event hooks
  memory/              # Conversation memory management
  cache/               # Caching layer (Redis/file-based)
  kv_manager/          # Key-value storage abstraction
  extra/               # Built-in plugins and hooks
    plugins/           # Built-in plugins (search, alarm, code_interpreter)
    voice_hook.py      # Voice response hook

start_sender.py        # Entry point for sender process
start_receiver.py      # Entry point for receiver process
```

### Key Components

**Task System (`llmkira/task/__init__.py`)**:
- Manages RabbitMQ message queue operations
- `Task.send_task()` publishes messages to queue
- `Task.consuming_task()` consumes messages from queue
- Uses `TaskHeader` schema for message structure

**Plugin System (`llmkira/sdk/tools/`)**:
- Plugins are loaded from `llmkira/extra/plugins/` or via entrypoints
- Each plugin must define:
  - `BaseTool` subclass with `run()`, `failed()`, `callback()` methods
  - Pydantic model for function arguments
  - `PluginMetadata` with name, description, function pairs
- Plugins registered via `@resign_plugin_executor(tool=ModelClass)` decorator
- Dynamic plugin loading via `load_plugins()` and `load_from_entrypoint()`

**Environment Configuration (`.env`)**:
- `AMQP_DSN`: RabbitMQ connection (required)
- `REDIS_DSN`: Redis connection (optional, falls back to file-based storage)
- `MONGODB_DSN`: MongoDB connection (optional, falls back to file-based storage)
- `GLOBAL_OAI_KEY`, `GLOBAL_OAI_MODEL`, `GLOBAL_OAI_ENDPOINT`: Default LLM config
- Platform tokens: `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `KOOK_BOT_TOKEN`, `SLACK_*`
- Plugin-specific: `PLUGIN_*`, `SERPER_API_KEY`, etc.

**Login Mechanism**:
- Users can configure their own LLM endpoints per-user
- `/login <url>$<token>`: Posts token to URL to retrieve configuration
- `/login <endpoint>$<key>$<model>$<tool_model>`: Direct configuration

## Code Style & Conventions

From `.github/CONTRIBUTING.md`:

- **Python version**: 3.9 to 3.11 (NOT 3.12+)
- **No modern syntax**: Don't use `str | None`, `:=`, `list[dict]` (Python 3.8 compat)
- **PEP8 naming**: Follow standard Python naming conventions
- **Pydantic**: Use `pydantic>=2.0.0` for all data validation
- **Logger conventions**:
  - Place at function head/tail, not at call sites
  - Start messages with capital letter, no ending punctuation
  - Use `--` not `:` to separate parameters
  - Example: `logger.info("Task sent success --queue test_queue")`
- **Error handling**:
  - Use `assert` for parameter validation in function headers
  - Throw exceptions on failure, don't return `None`
  - Exception messages should be clear and actionable
- **Code organization**:
  - Atomic commits (one feature per commit)
  - Mark issues with `# TODO [Issue Number]` or `# FIXME [Issue Number]`
  - Create GitHub issue if one doesn't exist

## Important Notes

- The project is in **maintenance mode** - no new features planned
- Always use `pdm` not `pip` for dependency management
- Both sender and receiver must be running for the bot to function
- RabbitMQ is required; Redis and MongoDB are optional (will use local file storage as fallback)
- Plugins can be installed via pip with entrypoint `llmkira.extra.plugin`
- The framework supports OpenAI-compatible APIs via gateways like Portkey or one-api
- Voice hooks can be enabled via `VOICE_REPLY_ME=true` environment variable
