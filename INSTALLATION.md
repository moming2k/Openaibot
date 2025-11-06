# OpenAiBot Personal Assistant - Complete Installation Guide

A comprehensive guide to set up your personal AI assistant that monitors RSS feeds, summarizes content, and provides intelligent Discord channel management.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [RSS Feed Configuration](#rss-feed-configuration)
- [Discord Channel Management](#discord-channel-management)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Overview

This personal assistant provides:
- 📰 **RSS Feed Monitoring**: Automatically fetches and summarizes RSS feeds
- 🤖 **AI-Powered Summaries**: Uses OpenAI to create intelligent summaries
- 💬 **Discord Integration**: Posts updates and responds to messages
- 🎯 **Channel-Specific Behavior**: Different responses based on Discord channel
- ⚙️ **Fully Containerized**: Easy deployment with Docker Compose
- 🔧 **Extensible**: Plugin-based architecture for custom features

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   RSS Feeds     │────▶│   LLMKira Bot   │────▶│    Discord      │
│                 │     │                 │     │                 │
│ • News Sites    │     │ • Fetch & Parse │     │ • News Channel  │
│ • Blogs         │     │ • Summarize     │     │ • Tech Channel  │
│ • Podcasts      │     │ • Schedule      │     │ • General Chat  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │     │
                              ▼     ▼
                        ┌──────┐ ┌──────┐
                        │OpenAI│ │RabbitMQ│
                        └──────┘ └──────┘
```

## Prerequisites

### Required
- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Discord Bot Token** ([Create one here](https://discord.com/developers/applications))
- **OpenAI API Key** ([Get it here](https://platform.openai.com/api-keys))
- **4GB RAM** minimum, 8GB recommended
- **10GB disk space** for Docker images and data

### Optional
- **Domain name** for webhook endpoints
- **SSL certificate** for secure connections
- **Sentry account** for error tracking

## Quick Start

### 1. One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/LlmKira/Openaibot/main/setup-personal-assistant.sh | bash
```

Or manually:

### 2. Manual Quick Setup

```bash
# Clone repository
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot

# Copy configuration templates
cp .env.personal-assistant .env
cp docker-compose.personal-assistant.yml docker-compose.yml

# Edit configuration (add your API keys)
nano .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f llmbot
```

## Detailed Setup

### Step 1: Discord Bot Creation

1. **Create Discord Application**
   ```
   1. Visit: https://discord.com/developers/applications
   2. Click "New Application"
   3. Name it (e.g., "Personal Assistant")
   4. Go to "Bot" section
   5. Click "Add Bot"
   ```

2. **Configure Bot Permissions**

   Enable these Privileged Gateway Intents:
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
   - ✅ PRESENCE INTENT (optional)

3. **Generate Invite Link**

   Use this permission calculator:
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=3072&scope=bot
   ```

   Required permissions (3072):
   - Read Messages/View Channels (1024)
   - Send Messages (2048)

   Recommended permissions (274877975552):
   - All text permissions
   - Embed Links
   - Attach Files
   - Add Reactions
   - Use Slash Commands

### Step 2: OpenAI Configuration

1. **Get API Key**
   ```
   1. Visit: https://platform.openai.com/api-keys
   2. Click "Create new secret key"
   3. Copy and save securely
   ```

2. **Choose Model**

   Recommended for personal use:
   - `gpt-4o-mini`: Fast, affordable, good for summaries
   - `gpt-4o`: Best quality, higher cost
   - `gpt-3.5-turbo`: Legacy, fastest

### Step 3: Environment Configuration

Create `.env` file:

```bash
# ============================================
# CORE CONFIGURATION
# ============================================

# OpenAI Settings
GLOBAL_OAI_KEY=sk-your-openai-api-key-here
GLOBAL_OAI_MODEL=gpt-4o-mini
GLOBAL_OAI_TOOL_MODEL=gpt-4o-mini
# GLOBAL_OAI_ENDPOINT=https://api.openai.com/v1/

# Discord Bot
DISCORD_BOT_TOKEN=your-discord-bot-token-here
DISCORD_BOT_PREFIX=/
# DISCORD_BOT_PROXY_ADDRESS=socks5://127.0.0.1:7890

# Message Queue (Required - Don't change for Docker)
AMQP_DSN=amqp://admin:StrongPassword123!@rabbitmq:5672/

# ============================================
# RSS FEED CONFIGURATION
# ============================================

# RSS Plugin Settings
PLUGIN_RSS_ENABLED=true
PLUGIN_RSS_CHECK_INTERVAL=30  # minutes
PLUGIN_RSS_MAX_ITEMS=5        # items per feed
PLUGIN_RSS_SUMMARY_LENGTH=200 # words

# Feed Subscriptions (comma-separated)
PLUGIN_RSS_FEEDS=https://news.ycombinator.com/rss,https://feeds.arstechnica.com/arstechnica/index

# ============================================
# DISCORD CHANNEL CONFIGURATION
# ============================================

# Channel IDs (get from Discord developer mode)
PLUGIN_NEWS_CHANNEL_ID=123456789012345678
PLUGIN_TECH_CHANNEL_ID=234567890123456789
PLUGIN_GENERAL_CHANNEL_ID=345678901234567890

# Channel-specific behavior
PLUGIN_CHANNEL_NEWS_SUMMARY=true
PLUGIN_CHANNEL_NEWS_PREFIX=[📰 News]
PLUGIN_CHANNEL_TECH_PREFIX=[💻 Tech]
PLUGIN_CHANNEL_GENERAL_PREFIX=[💬]

# ============================================
# OPTIONAL SERVICES
# ============================================

# Redis Cache (improves performance)
# REDIS_DSN=redis://redis:6379/0

# MongoDB (for document storage)
# MONGODB_DSN=mongodb://admin:StrongPassword123!@mongodb:27017/?authSource=admin

# Error Tracking
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# ============================================
# ADVANCED SETTINGS
# ============================================

# Debug Mode
# DEBUG=true

# Voice Response (requires additional setup)
# VOICE_REPLY_ME=true
# REECHO_VOICE_KEY=your-reecho-key

# Rate Limiting
PLUGIN_RATE_LIMIT_MESSAGES=20
PLUGIN_RATE_LIMIT_WINDOW=60  # seconds
```

### Step 4: Deploy with Docker Compose

1. **Start Services**
   ```bash
   # Start all containers
   docker-compose up -d

   # Verify all services are running
   docker-compose ps

   # Should show:
   # llmbot     running
   # rabbitmq   running
   # redis      running (optional)
   # mongodb    running (optional)
   ```

2. **Monitor Logs**
   ```bash
   # View all logs
   docker-compose logs -f

   # View specific service
   docker-compose logs -f llmbot

   # Check for errors
   docker-compose logs llmbot | grep ERROR
   ```

3. **Verify Bot Connection**

   The bot should appear online in Discord. Test with:
   ```
   /help
   /chat Hello, are you working?
   ```

## RSS Feed Configuration

### Basic RSS Setup

The RSS plugin is automatically installed. Configure feeds via Discord:

```
/task Subscribe to RSS feed https://example.com/rss and post to channel 123456789
```

### Advanced RSS Configuration

Create custom RSS handler at `llmkira/extra/plugins/rss_advanced/__init__.py`:

```python
"""Advanced RSS Handler with categorization and filtering"""

__package__name__ = "llmkira.extra.plugins.rss_advanced"
__plugin_name__ = "rss_advanced"
__openapi_version__ = "20240416"

import feedparser
import html2text
from typing import List, Dict
from datetime import datetime, timedelta
from llmkira.sdk.tools import PluginMetadata
from llmkira.openai import OpenAI
import hashlib
import json

class AdvancedRSSReader:
    def __init__(self, openai_client: OpenAI):
        self.openai = openai_client
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.seen_articles = self.load_seen_articles()

    def load_seen_articles(self) -> set:
        """Load previously seen article IDs"""
        try:
            with open('/app/config_dir/seen_articles.json', 'r') as f:
                return set(json.load(f))
        except:
            return set()

    def save_seen_articles(self):
        """Save seen article IDs"""
        with open('/app/config_dir/seen_articles.json', 'w') as f:
            json.dump(list(self.seen_articles), f)

    async def fetch_and_summarize(self, feed_url: str, category: str = None) -> List[Dict]:
        """Fetch RSS feed and create AI summaries"""

        feed = feedparser.parse(feed_url)
        summaries = []

        for entry in feed.entries[:5]:  # Process latest 5 entries
            # Skip if already processed
            article_id = hashlib.md5(entry.link.encode()).hexdigest()
            if article_id in self.seen_articles:
                continue

            # Extract content
            title = entry.get('title', 'No title')
            link = entry.get('link', '')
            content = self.h2t.handle(entry.get('summary', ''))
            published = entry.get('published_parsed', None)

            # Skip old articles (>24 hours)
            if published:
                pub_date = datetime.fromtimestamp(published)
                if datetime.now() - pub_date > timedelta(hours=24):
                    continue

            # Generate AI summary
            summary_prompt = f"""
            Summarize this article in 2-3 sentences:
            Title: {title}
            Content: {content[:1000]}

            Focus on: key points, implications, and why it matters.
            """

            response = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=150
            )

            summary = response.choices[0].message.content

            # Categorize article
            if not category:
                category = await self.categorize_article(title, content)

            summaries.append({
                'title': title,
                'link': link,
                'summary': summary,
                'category': category,
                'published': published
            })

            self.seen_articles.add(article_id)

        self.save_seen_articles()
        return summaries

    async def categorize_article(self, title: str, content: str) -> str:
        """AI-powered article categorization"""

        prompt = f"""
        Categorize this article into ONE of these categories:
        - Tech
        - Science
        - Business
        - Politics
        - Entertainment
        - Health
        - Other

        Title: {title}
        Content preview: {content[:500]}

        Respond with just the category name.
        """

        response = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )

        return response.choices[0].message.content.strip()

    def format_discord_message(self, summaries: List[Dict], channel_type: str) -> str:
        """Format summaries for Discord based on channel type"""

        if not summaries:
            return "No new articles found."

        # Different formats for different channels
        if channel_type == "news":
            # Detailed format for news channel
            messages = []
            for item in summaries:
                msg = f"""
**{item['title']}**
*Category: {item['category']}*
{item['summary']}
[Read more]({item['link']})
"""
                messages.append(msg)
            return "\n---\n".join(messages)

        elif channel_type == "brief":
            # Brief format for general channels
            messages = []
            for item in summaries:
                msg = f"• **{item['title']}** - {item['summary'][:100]}... [Link]({item['link']})"
                messages.append(msg)
            return "\n".join(messages)

        else:
            # Default format
            return "\n".join([f"• [{item['title']}]({item['link']})" for item in summaries])

# ... rest of plugin implementation
```

### RSS Feed Sources

Recommended RSS feeds for personal assistant:

**News & Current Events:**
- BBC News: `http://feeds.bbci.co.uk/news/rss.xml`
- Reuters: `https://www.reutersagency.com/feed/?best-topics=tech`
- AP News: `https://feeds.apnews.com/rss/apf-topnews`

**Technology:**
- Hacker News: `https://news.ycombinator.com/rss`
- Ars Technica: `https://feeds.arstechnica.com/arstechnica/index`
- The Verge: `https://www.theverge.com/rss/index.xml`
- TechCrunch: `https://techcrunch.com/feed/`

**AI & Machine Learning:**
- OpenAI Blog: `https://openai.com/blog/rss.xml`
- Google AI Blog: `https://ai.googleblog.com/feeds/posts/default`
- Papers With Code: `https://paperswithcode.com/rss`

**Development:**
- GitHub Trending: `https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml`
- Dev.to: `https://dev.to/feed`
- Reddit Programming: `https://www.reddit.com/r/programming/.rss`

## Discord Channel Management

### Channel Types and Behaviors

Configure different behaviors per channel by creating channel handlers:

#### 1. News Channel Handler

```python
# llmkira/extra/plugins/channel_handlers/news_channel.py

from llmkira.openapi.trigger import Trigger, resign_trigger

@resign_trigger(
    Trigger(
        on_platform="discord_hikari",
        action="allow",
        priority=10,
        function_enable=True,
        name="news_channel_handler"
    )
)
async def news_channel_trigger(
    message: str,
    chat_id: str,
    env_map: dict,
    **kwargs
) -> bool:
    """Special handling for news channels"""

    news_channel_id = env_map.get("PLUGIN_NEWS_CHANNEL_ID")

    if chat_id == news_channel_id:
        # Auto-enable functions for news queries
        news_keywords = ["summary", "update", "latest", "news", "what's new"]
        return any(keyword in message.lower() for keyword in news_keywords)

    return False
```

#### 2. Tech Support Channel

```python
# llmkira/extra/plugins/channel_handlers/tech_channel.py

from llmkira.openapi.hook import Hook, Trigger, resign_hook
from llmkira.task.schema import EventMessage

@resign_hook()
class TechChannelHook(Hook):
    trigger = Trigger.RECEIVER
    priority = 5

    async def trigger_hook(self, *args, **kwargs) -> bool:
        chat_id = kwargs.get("locate", {}).get("chat_id", "")
        tech_channel_id = self.get_os_env("TECH_CHANNEL_ID")
        return chat_id == tech_channel_id

    async def hook_run(self, messages: list[EventMessage], **kwargs):
        """Add technical context to messages in tech channel"""

        for message in messages:
            # Prepend technical context
            message.text = f"[Technical Context] {message.text}"

            # Auto-enable code interpreter for code blocks
            if "```" in message.text:
                kwargs["enable_code_interpreter"] = True

        return (messages,), kwargs
```

#### 3. General Chat Channel

```python
# llmkira/extra/plugins/channel_handlers/general_channel.py

@resign_trigger(
    Trigger(
        on_platform="discord_hikari",
        action="allow",
        priority=5,
        function_enable=False,  # Disable functions by default
        name="general_chat_handler"
    )
)
async def general_chat_trigger(message: str, chat_id: str, env_map: dict, **kwargs) -> bool:
    """Casual conversation in general channels"""

    general_channel_id = env_map.get("PLUGIN_GENERAL_CHANNEL_ID")

    if chat_id == general_channel_id:
        # Only respond to direct mentions or questions
        return "@" in message or "?" in message

    return False
```

### Channel Configuration Examples

#### News Channel
```env
PLUGIN_NEWS_CHANNEL_ID=123456789
PLUGIN_NEWS_AUTO_SUMMARIZE=true
PLUGIN_NEWS_UPDATE_FREQUENCY=30  # minutes
PLUGIN_NEWS_MAX_LENGTH=500      # characters
```

Behavior:
- Auto-posts RSS summaries every 30 minutes
- Responds with detailed summaries
- Includes source links and timestamps

#### Tech Support Channel
```env
PLUGIN_TECH_CHANNEL_ID=234567890
PLUGIN_TECH_CODE_INTERPRETER=true
PLUGIN_TECH_SEARCH_ENABLED=true
PLUGIN_TECH_RESPONSE_STYLE=technical
```

Behavior:
- Code interpretation enabled
- Web search for documentation
- Technical language in responses

#### General Chat
```env
PLUGIN_GENERAL_CHANNEL_ID=345678901
PLUGIN_GENERAL_CASUAL_MODE=true
PLUGIN_GENERAL_FUNCTIONS_DISABLED=true
PLUGIN_GENERAL_RESPONSE_STYLE=friendly
```

Behavior:
- Casual conversation only
- No function calling
- Friendly, conversational tone

### Setting Up Channels

1. **Get Channel IDs**
   ```
   1. Enable Developer Mode in Discord (User Settings > Advanced)
   2. Right-click channel > Copy ID
   3. Add to .env file
   ```

2. **Configure Permissions**
   ```
   Per channel, set bot permissions:
   - Read Messages: ✅
   - Send Messages: ✅
   - Embed Links: ✅ (for rich content)
   - Attach Files: ✅ (for images/documents)
   - Add Reactions: ✅ (for feedback)
   ```

3. **Test Configuration**
   ```
   In each channel, test:
   /test_channel

   Bot should respond with:
   "Channel ID: [ID]
    Configuration: [Active settings]"
   ```

## Advanced Configuration

### Performance Tuning

#### Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  llmbot:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # 2 CPU cores
          memory: 4G       # 4GB RAM
        reservations:
          cpus: '0.5'      # Minimum 0.5 cores
          memory: 1G       # Minimum 1GB RAM
```

#### Message Queue Optimization

```yaml
  rabbitmq:
    environment:
      RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.8
      RABBITMQ_DISK_FREE_LIMIT: 2GB
```

### Security Hardening

#### 1. Change Default Passwords

```bash
# Generate strong passwords
openssl rand -base64 32  # For RabbitMQ
openssl rand -base64 32  # For MongoDB
openssl rand -base64 32  # For Redis
```

Update in `docker-compose.yml` and `.env`

#### 2. Network Isolation

```yaml
networks:
  bot_network:
    driver: bridge
    internal: true  # No external access

  external_network:
    driver: bridge
```

#### 3. Secrets Management

Use Docker secrets:

```yaml
secrets:
  discord_token:
    file: ./secrets/discord_token.txt
  openai_key:
    file: ./secrets/openai_key.txt

services:
  llmbot:
    secrets:
      - discord_token
      - openai_key
```

### Custom Plugins

#### Plugin Template

Create `llmkira/extra/plugins/my_plugin/__init__.py`:

```python
"""Custom Plugin Template"""

__package__name__ = "llmkira.extra.plugins.my_plugin"
__plugin_name__ = "my_custom_plugin"
__openapi_version__ = "20240416"

from typing import Union, Type
from pydantic import BaseModel, Field
from llmkira.sdk.tools import PluginMetadata, verify_openapi_version
from llmkira.sdk.tools.schema import FuncPair, BaseTool
from llmkira.openai.cell import class_tool
from llmkira.task import Task, TaskHeader
from loguru import logger

verify_openapi_version(__package__name__, __openapi_version__)

class MyPluginArgs(BaseModel):
    """Arguments for your plugin"""
    action: str = Field(description="Action to perform")
    target: str = Field(description="Target of the action")

class MyPluginTool(BaseTool):
    """Your plugin implementation"""

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = MyPluginArgs
    keywords: list = ["trigger", "keywords", "here"]
    env_required: list = []  # Required environment variables
    env_prefix: str = "MY_PLUGIN_"

    def require_auth(self, env_map: dict) -> bool:
        """Check if authentication is required"""
        return False

    def func_message(self, message_text: str, **kwargs):
        """Determine if plugin should trigger"""
        for keyword in self.keywords:
            if keyword in message_text.lower():
                return self.function
        return None

    async def failed(self, task, receiver, exception, **kwargs):
        """Handle plugin failure"""
        logger.error(f"Plugin failed: {exception}")
        # Send error message to user

    async def callback(self, task, receiver, **kwargs):
        """Post-execution callback"""
        return True

    async def run(self, task, receiver, arg, env, pending_task, **kwargs):
        """Main plugin logic"""
        args = MyPluginArgs.model_validate(arg)

        # Your plugin logic here
        result = f"Performed {args.action} on {args.target}"

        # Send response
        await self.send_response(task, receiver, result)

        return result

    async def send_response(self, task, receiver, message):
        """Helper to send response"""
        # Implementation...

__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Description of what your plugin does",
    usage="How to use your plugin",
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(MyPluginArgs), tool=MyPluginTool)},
)
```

#### Plugin Installation

1. **Local Development**
   ```bash
   # Copy plugin to container
   docker cp my_plugin/ llmbot:/app/llmkira/extra/plugins/

   # Restart to load
   docker-compose restart llmbot
   ```

2. **Package Distribution**
   ```python
   # setup.py for your plugin
   setup(
       name="llmkira-my-plugin",
       entry_points={
           "llmkira.extra.plugin": [
               "my_plugin = my_plugin:__plugin_meta__"
           ]
       }
   )
   ```

### Monitoring & Logging

#### Sentry Integration

```env
SENTRY_DSN=https://your-key@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

#### Custom Logging

```python
# In your plugins
from loguru import logger

logger.add(
    "/app/logs/custom_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

logger.info("Custom log message")
logger.error("Error with context", extra={"user_id": user_id})
```

#### Metrics Collection

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, start_http_server

message_counter = Counter('messages_processed', 'Total messages processed')
response_time = Histogram('response_duration_seconds', 'Response time')

@response_time.time()
async def process_message(message):
    message_counter.inc()
    # Process message
```

## Troubleshooting

### Common Issues and Solutions

#### Bot Not Responding

1. **Check Discord Token**
   ```bash
   docker-compose logs llmbot | grep "Discord"
   # Should see: "Discord bot connected"
   ```

2. **Verify Intents**
   - Go to Discord Developer Portal
   - Bot section > Privileged Gateway Intents
   - Enable: MESSAGE CONTENT INTENT

3. **Check RabbitMQ**
   ```bash
   docker-compose exec rabbitmq rabbitmqctl status
   # Should show: "running"
   ```

#### OpenAI Errors

1. **Invalid API Key**
   ```bash
   docker-compose logs llmbot | grep "OpenAI"
   # Error: "Incorrect API key provided"

   # Fix:
   docker-compose down
   # Update .env with correct key
   docker-compose up -d
   ```

2. **Rate Limiting**
   ```env
   # Add to .env
   PLUGIN_OPENAI_RETRY_ATTEMPTS=3
   PLUGIN_OPENAI_RETRY_DELAY=5
   ```

3. **Model Not Available**
   ```env
   # Fallback to available model
   GLOBAL_OAI_MODEL=gpt-3.5-turbo
   ```

#### RSS Feed Issues

1. **Feed Not Updating**
   ```bash
   # Check scheduler
   docker-compose exec llmbot python -c "
   from app.receiver.aps import SCHEDULER
   print(SCHEDULER.get_jobs())
   "
   ```

2. **Invalid Feed URL**
   ```bash
   # Test feed manually
   docker-compose exec llmbot python -c "
   import feedparser
   feed = feedparser.parse('YOUR_FEED_URL')
   print(f'Entries: {len(feed.entries)}')
   "
   ```

#### Memory Issues

1. **High Memory Usage**
   ```bash
   # Check container stats
   docker stats llmbot

   # Clear cache
   docker-compose exec llmbot redis-cli FLUSHALL
   ```

2. **Message Queue Full**
   ```bash
   # Purge queue
   docker-compose exec rabbitmq rabbitmqctl purge_queue receiver
   ```

### Debug Mode

Enable detailed logging:

```env
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

```bash
# View debug logs
docker-compose logs -f llmbot | grep DEBUG
```

### Health Checks

Add to `docker-compose.yml`:

```yaml
services:
  llmbot:
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Maintenance

### Backup and Restore

#### Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"

mkdir -p $BACKUP_DIR

# Backup configurations
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# Backup data volumes
docker-compose exec mongodb mongodump --out /backup
docker cp llmbot_mongodb:/backup $BACKUP_DIR/mongodb

# Backup Redis
docker-compose exec redis redis-cli SAVE
docker cp llmbot_redis:/data/dump.rdb $BACKUP_DIR/

# Backup seen articles and configs
docker cp llmbot:/app/config_dir $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

#### Restore

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./restore.sh <backup_directory>"
    exit 1
fi

# Stop services
docker-compose down

# Restore configurations
cp $BACKUP_DIR/.env ./
cp $BACKUP_DIR/docker-compose.yml ./

# Start databases
docker-compose up -d mongodb redis rabbitmq

# Restore MongoDB
docker cp $BACKUP_DIR/mongodb llmbot_mongodb:/restore
docker-compose exec mongodb mongorestore /restore

# Restore Redis
docker cp $BACKUP_DIR/dump.rdb llmbot_redis:/data/

# Restore configs
docker cp $BACKUP_DIR/config_dir llmbot:/app/

# Restart all services
docker-compose up -d

echo "Restore completed from: $BACKUP_DIR"
```

### Updates

#### Update Bot

```bash
# Pull latest changes
git pull origin main

# Update Docker images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate

# Check logs
docker-compose logs -f llmbot
```

#### Update Dependencies

```bash
# Inside container
docker-compose exec llmbot bash
pdm update

# Or update specific package
pdm add package_name@latest
```

### Monitoring

#### Service Status Dashboard

Create `monitor.sh`:

```bash
#!/bin/bash

echo "==================================="
echo "  OpenAiBot Personal Assistant    "
echo "         Service Monitor           "
echo "==================================="
echo ""

# Check Docker containers
echo "📦 Container Status:"
docker-compose ps

echo ""
echo "💾 Resource Usage:"
docker stats --no-stream llmbot rabbitmq redis mongodb

echo ""
echo "📊 Message Queue:"
docker-compose exec rabbitmq rabbitmqctl list_queues name messages consumers

echo ""
echo "🔄 Recent Logs:"
docker-compose logs --tail=10 llmbot

echo ""
echo "🤖 Bot Status:"
docker-compose exec llmbot python -c "
from app.setting.database import RabbitMQSetting
print(f'RabbitMQ: {'Connected' if RabbitMQSetting.available else 'Disconnected'}')
"

echo ""
echo "==================================="
```

Make executable and run:
```bash
chmod +x monitor.sh
./monitor.sh
```

#### Automated Monitoring

Add to crontab:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/monitor.sh >> /var/log/bot_monitor.log 2>&1

# Daily backup at 3 AM
0 3 * * * /path/to/backup.sh >> /var/log/bot_backup.log 2>&1
```

## Support & Resources

### Documentation
- [Official Docs](https://llmkira.github.io/Docs/)
- [API Reference](https://github.com/LlmKira/Openaibot/wiki)
- [Plugin Development](https://llmkira.github.io/Docs/dev/basic)

### Community
- Telegram: [https://t.me/Openai_LLM](https://t.me/Openai_LLM)
- Discord: [https://discord.gg/6QHNdwhdE5](https://discord.gg/6QHNdwhdE5)
- GitHub Issues: [Report bugs](https://github.com/LlmKira/Openaibot/issues)

### Troubleshooting Checklist

- [ ] Docker and Docker Compose installed and running
- [ ] API keys correctly set in `.env`
- [ ] Discord bot token valid and bot invited to server
- [ ] MESSAGE CONTENT INTENT enabled in Discord
- [ ] RabbitMQ service running
- [ ] No firewall blocking Docker networks
- [ ] Sufficient disk space (>1GB free)
- [ ] Correct channel IDs in configuration

---

*Last Updated: 2024*
*Version: 1.0.5*
*Compatible with: LLMKira/OpenAiBot main branch*