# Docker Image Rebuild Instructions

## Issues Fixed

1. **Discord Package Dependencies**: Added `crescent>=0.0.17` to the bot dependencies in `pyproject.toml`
2. **Missing Functions**: Ensured `util_func.py` contains all required functions including `logout`
3. **API Dependencies**: Added API dependencies to Dockerfile for Newsletter API functionality

## Changes Made

### 1. pyproject.toml
- Added `crescent>=0.0.17` to the `[project.optional-dependencies]` bot section
- This ensures the Discord bot has all required packages

### 2. Dockerfile
- Updated dependency installation to include both bot AND api groups:
  ```dockerfile
  RUN pdm sync -G bot -G api --prod --no-editable
  ```
- This ensures the image has both Discord bot dependencies and Newsletter API dependencies

### 3. util_func.py
- The file already contains all required functions:
  - `auth_reloader` (line 86)
  - `save_credential` (line 138)
  - `learn_instruction` (line 144)
  - `logout` (line 223)

## Rebuild Instructions

### Option 1: Local Build
```bash
# Stop current containers
docker-compose down

# Build the new image with updated dependencies
docker build -t sudoskys/llmbot:latest .

# Start with the new image
docker-compose up -d
```

### Option 2: Build with Docker Compose
```bash
# Stop and remove current containers
docker-compose down

# Build and start with updated image
docker-compose build
docker-compose up -d
```

### Option 3: Push to Registry (for maintainers)
```bash
# Build the image
docker build -t sudoskys/llmbot:latest .

# Tag for versioning (optional)
docker tag sudoskys/llmbot:latest sudoskys/llmbot:v1.0.6

# Push to Docker Hub (requires authentication)
docker push sudoskys/llmbot:latest
docker push sudoskys/llmbot:v1.0.6
```

## Testing the Rebuilt Image

After rebuilding, verify the Discord sender works:

```bash
# Check PM2 status
docker exec llmbot_personal_assistant pm2 status

# Check Discord sender logs
docker exec llmbot_personal_assistant pm2 logs llm_sender --lines 20

# Verify dependencies are installed
docker exec llmbot_personal_assistant pip list | grep -E "(crescent|hikari|fastapi|uvicorn)"
```

## Environment Variables for Newsletter Feature

Ensure these are set in your `.env` file:

```bash
# Newsletter Channel Configuration
PLUGIN_NEWS_CHANNEL_ID=1435035369975447662  # Your Discord channel ID

# Newsletter API Configuration (optional)
NEWSLETTER_API_ENABLED=true
NEWSLETTER_API_PORT=8765
NEWSLETTER_API_HOST=0.0.0.0
NEWSLETTER_API_KEY=your-secure-api-key-here  # Change this!
```

## Features Included

1. **Discord Bot Support**: Full Discord integration with hikari, crescent libraries
2. **Newsletter Auto-Summarization**: Automatically processes messages in configured Discord channel
3. **File Attachment Support**: Reads and processes text files in newsletter channel
4. **HTTP API Server**: Accept long-form content via REST API for newsletter processing
5. **Multi-Platform Support**: Telegram, Discord, Slack, and Kook bot support

## Notes

- The Docker image now includes all dependencies for both bot platforms and the API server
- PM2 is used for process management inside the container
- Redis and RabbitMQ are required external services (defined in docker-compose.yml)
- The Newsletter API runs on port 8765 by default when enabled

## Troubleshooting

If the Discord sender crashes after rebuild:
1. Check if all environment variables are set correctly
2. Verify RabbitMQ and Redis are running: `docker-compose ps`
3. Check PM2 logs: `docker exec llmbot_personal_assistant pm2 logs`
4. Ensure Discord bot token is valid in `.env` file