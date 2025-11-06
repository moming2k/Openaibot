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

### Docker
```bash
# Start all services (includes RabbitMQ, Redis, MongoDB)
docker-compose -f docker-compose.yml up -d

# Update images
docker-compose pull

# Access container shell
docker exec -it llmbot /bin/bash
```

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
