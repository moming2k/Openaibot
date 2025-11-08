# Conversation History Tracking

## Overview

The LLMKira API now includes a comprehensive conversation history tracking system that allows you to review all request/response pairs through a Web UI. This feature helps you track topics submitted, monitor AI interactions, and analyze conversation patterns.

## Features

- **Automatic Tracking**: All LLM conversations are automatically captured and stored
- **Web UI**: Interactive dashboard for browsing history
- **REST API**: Programmatic access to conversation history
- **Filtering**: Search by platform, user, date range
- **Metadata**: Includes model used, token usage, tool calls
- **Persistence**: History stored in Redis/MongoDB or local file storage

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable/disable history tracking (default: true)
HISTORY_TRACKING_ENABLED=true

# API server configuration (required for Web UI access)
NEWSLETTER_API_ENABLED=true
NEWSLETTER_API_PORT=8765
NEWSLETTER_API_HOST=0.0.0.0
NEWSLETTER_API_KEY=your-secure-api-key-here
```

### Storage Backend

History is stored using the existing KV manager infrastructure:
- **Redis** (preferred): If `REDIS_DSN` is configured
- **MongoDB**: If `MONGODB_DSN` is configured
- **Local File Storage**: Fallback if neither is available

History entries are retained for **30 days** by default.

## Web UI Access

### Starting the API Server

```bash
# Start the API server
pdm run python start_api.py

# Or with Docker (development mode)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Accessing the UI

1. Open your browser to: `http://localhost:8765/history/ui`
2. Enter your API key (from `NEWSLETTER_API_KEY` environment variable)
3. Click "Load History" to view conversations

### UI Features

- **Platform Filter**: Filter by Telegram, Discord, Kook, or Slack
- **User Filter**: View conversations for specific users
- **Pagination**: Navigate through history with Next/Previous buttons
- **Expand/Collapse**: Click any entry to view full request/response text
- **Tool Calls**: See which plugins/tools were invoked
- **Metadata**: View timestamps, token usage, task IDs

## REST API Endpoints

### Get History List

```bash
GET /history?platform=telegram&user_id=123&limit=20&offset=0
Headers: X-API-Key: your-api-key
```

**Query Parameters:**
- `platform` (optional): Filter by platform (telegram, discord_hikari, kook, slack)
- `user_id` (optional): Filter by user ID (requires platform)
- `limit` (optional): Items per page (1-100, default: 50)
- `offset` (optional): Skip N items (default: 0)

**Response:**
```json
{
  "success": true,
  "total": 10,
  "entries": [
    {
      "task_id": "ABCD1",
      "timestamp": 1699564800,
      "platform": "telegram",
      "user_id": "123456",
      "chat_id": "789012",
      "request": "What is the weather today?",
      "response": "I don't have access to real-time weather...",
      "model": "gpt-4",
      "tool_calls": ["search_web"],
      "token_usage": 245
    }
  ],
  "offset": 0,
  "limit": 20
}
```

### Get Single Entry

```bash
GET /history/{task_id}
Headers: X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "entry": {
    "task_id": "ABCD1",
    "timestamp": 1699564800,
    "platform": "telegram",
    "user_id": "123456",
    "chat_id": "789012",
    "request": "What is the weather today?",
    "response": "I don't have access to real-time weather...",
    "model": "gpt-4",
    "tool_calls": ["search_web"],
    "token_usage": 245
  }
}
```

## Data Model

### HistoryEntry

```python
{
  "task_id": str,          # Unique task identifier
  "timestamp": int,        # Unix timestamp
  "platform": str,         # Platform name (telegram, discord, etc.)
  "user_id": str,          # User identifier
  "chat_id": str,          # Chat/channel identifier
  "request": str,          # User's request (max 10,000 chars)
  "response": str,         # LLM response (max 10,000 chars)
  "model": str,            # Model name (e.g., "gpt-4")
  "tool_calls": [str],     # List of tools invoked
  "token_usage": int       # Total tokens consumed
}
```

## Architecture

### Components

1. **History Manager** (`llmkira/kv_manager/history.py`)
   - Handles storage and retrieval of history entries
   - Maintains indexes for users and global history
   - Supports pagination and filtering

2. **Middleware Hook** (`app/middleware/llm_task.py`)
   - Captures requests/responses in `OpenaiMiddleware.request_openai()`
   - Automatically tracks all LLM interactions
   - Extracts metadata (model, tokens, tool calls)

3. **API Endpoints** (`app/api/server.py`)
   - `/history` - List history with filters
   - `/history/{task_id}` - Get specific entry
   - `/history/ui` - Web UI dashboard

4. **Web UI** (`app/api/static/history.html`)
   - Single-page application
   - Responsive design
   - Local storage for API key

### Storage Strategy

History entries are stored with multiple indexes:

- **Entry Storage**: `kv:history:entry:{task_id}` → Full entry data
- **User Index**: `kv:history:user:{platform}:{user_id}` → List of task IDs sorted by timestamp
- **Global Index**: `kv:history:global:all` → List of all task IDs sorted by timestamp

Indexes maintain the last 1,000 entries to prevent unbounded growth.

## Disabling History Tracking

To disable history tracking:

```bash
# In .env
HISTORY_TRACKING_ENABLED=false
```

Or remove the environment variable entirely (defaults to enabled).

## Privacy & Security

- **API Key Required**: All API endpoints require authentication
- **No Public Access**: Web UI requires API key to load data
- **TTL**: Entries expire after 30 days
- **Length Limits**: Request/response text limited to 10,000 characters
- **Selective Tracking**: Only tracks successful LLM completions

## Troubleshooting

### History not appearing

1. Check that history tracking is enabled:
   ```bash
   echo $HISTORY_TRACKING_ENABLED  # Should be "true" or unset
   ```

2. Verify the API server is running:
   ```bash
   curl http://localhost:8765/health
   ```

3. Check logs for tracking errors:
   ```bash
   docker logs llmbot_personal_assistant | grep "History tracked"
   ```

### Cannot access Web UI

1. Ensure API server is running on correct port
2. Check firewall rules allow access to port 8765
3. Verify static files exist:
   ```bash
   ls -la app/api/static/history.html
   ```

### Authentication errors

1. Verify API key matches `.env` configuration:
   ```bash
   echo $NEWSLETTER_API_KEY
   ```

2. Check API key header format:
   ```bash
   curl -H "X-API-Key: your-key" http://localhost:8765/history
   ```

## Example Use Cases

### Review Recent Conversations

Visit the Web UI to browse recent interactions across all platforms.

### Analyze Tool Usage

Query the API to find conversations where specific tools were called:

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8765/history?limit=100" | \
  jq '.entries[] | select(.tool_calls | length > 0)'
```

### Export User History

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8765/history?platform=telegram&user_id=123&limit=100" \
  > user_history.json
```

### Monitor Token Usage

```bash
curl -H "X-API-Key: your-key" \
  "http://localhost:8765/history?limit=100" | \
  jq '[.entries[].token_usage] | add'
```

## Future Enhancements

Potential improvements (not yet implemented):

- Full-text search across request/response content
- Export to CSV/JSON
- Advanced analytics dashboard
- User-specific retention policies
- Conversation threading support
- Response rating/feedback system
