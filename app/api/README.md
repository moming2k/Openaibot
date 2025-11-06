# Newsletter API Server

HTTP API server for submitting long-form content to the newsletter channel. Useful when content exceeds Discord's message length limits.

## Features

- Submit long-form content via HTTP POST
- Automatic summarization in Traditional Chinese (繁體中文)
- Extract actionable items
- API key authentication
- Swagger UI documentation

## Quick Start

### 1. Enable the API Server

Add to your `.env` file:

```bash
# Newsletter API Configuration
NEWSLETTER_API_ENABLED=true
NEWSLETTER_API_PORT=8765
NEWSLETTER_API_HOST=0.0.0.0
NEWSLETTER_API_KEY=your-secure-api-key-here  # Change this!
```

### 2. Start the API Server

**Using Docker Compose:**

```bash
# Start with API profile enabled
docker-compose --profile api up -d newsletter_api

# Or start all services including API
docker-compose --profile api up -d
```

**Using PDM (Development):**

```bash
# Install API dependencies
pdm install -G api

# Run the API server
pdm run python start_api.py
```

### 3. Access the Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc
- **Health Check**: http://localhost:8765/health

## API Endpoints

### POST /newsletter/submit

Submit content for newsletter processing.

**Headers:**
- `X-API-Key`: Your API key (from `NEWSLETTER_API_KEY` environment variable)
- `Content-Type`: application/json

**Request Body:**
```json
{
  "content": "Your long article or newsletter content here...",
  "channel_id": "1435035369975447662"  // Optional: override default channel
}
```

**Response:**
```json
{
  "success": true,
  "message": "Content submitted for processing. Response will be sent to Discord channel.",
  "task_id": "abc123..."
}
```

## Usage Examples

### cURL

```bash
curl -X POST "http://localhost:8765/newsletter/submit" \
     -H "X-API-Key: your-secure-api-key-here" \
     -H "Content-Type: application/json" \
     -d '{
       "content": "Your long article content here..."
     }'
```

### Python

```python
import requests

url = "http://localhost:8765/newsletter/submit"
headers = {
    "X-API-Key": "your-secure-api-key-here",
    "Content-Type": "application/json"
}
data = {
    "content": "Your long article content here..."
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const url = 'http://localhost:8765/newsletter/submit';
const headers = {
  'X-API-Key': 'your-secure-api-key-here',
  'Content-Type': 'application/json'
};
const data = {
  content: 'Your long article content here...'
};

axios.post(url, data, { headers })
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

## Security

- **API Key**: Always use a strong, random API key
- **Network**: The API server is exposed on the configured port (default: 8765)
- **Production**: Consider using:
  - HTTPS/TLS with a reverse proxy (nginx, Caddy)
  - Rate limiting
  - IP whitelisting if possible

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEWSLETTER_API_ENABLED` | `false` | Enable the API server |
| `NEWSLETTER_API_PORT` | `8765` | Port to listen on |
| `NEWSLETTER_API_HOST` | `0.0.0.0` | Host to bind to |
| `NEWSLETTER_API_KEY` | - | API key for authentication (required) |
| `PLUGIN_NEWS_CHANNEL_ID` | - | Discord channel ID for newsletter |

## Troubleshooting

### API returns 401 Unauthorized
- Check that `X-API-Key` header matches `NEWSLETTER_API_KEY` in `.env`
- Ensure the API key doesn't have trailing spaces

### API returns 500 Internal Server Error
- Check that `PLUGIN_NEWS_CHANNEL_ID` is configured
- Verify RabbitMQ is running and accessible
- Check logs: `docker logs llmbot_newsletter_api`

### Response not appearing in Discord
- Verify the Discord bot is running
- Check the receiver process is consuming messages
- Ensure the channel ID is correct

## Health Check

```bash
curl http://localhost:8765/health
# Returns: {"status": "healthy"}
```

## Logging

View API server logs:

```bash
# Docker
docker logs -f llmbot_newsletter_api

# Local development
# Logs will appear in console output
```

## Development

### Install Dependencies

```bash
pdm install -G api -G bot
```

### Run in Development Mode

```bash
pdm run python start_api.py
```

### Auto-reload on Changes

```bash
pdm run uvicorn app.api.server:app --reload --host 0.0.0.0 --port 8765
```

## Production Deployment

### With Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### With Docker Compose

```yaml
services:
  newsletter_api:
    image: sudoskys/llmbot:latest
    restart: always
    env_file: .env
    command: ["python", "start_api.py"]
    ports:
      - "8765:8765"
    # ... rest of configuration
```

## License

Same as the main LLMKira project (Apache-2.0).
