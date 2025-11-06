# Deep Research Channel Setup Guide

This guide explains how to set up and use the Deep Research channel feature for comprehensive topic analysis with automatic message chunking and threading.

## Overview

The Deep Research plugin enables comprehensive research on any topic, with intelligent message splitting and threaded posting to overcome Discord's 2000 character limit.

### Key Features

- 🔬 **Comprehensive Research**: Structured analysis with multiple sections
- 📝 **Automatic Chunking**: Splits messages longer than 1900 characters
- 🧵 **Thread Support**: Posts all chunks in the same Discord thread
- 🎯 **Flexible Depth**: Choose research depth (overview, comprehensive, detailed)
- 🔍 **Smart Splitting**: Chunks at paragraph/sentence boundaries

## Quick Setup

### 1. Get Your Discord Channel ID

1. Enable Discord Developer Mode:
   - User Settings → Advanced → Developer Mode (toggle ON)

2. Right-click your research channel → Copy ID

### 2. Configure Environment

Add to your `.env` file:

```bash
# Replace with your actual Discord channel ID
PLUGIN_DEEP_RESEARCH_CHANNEL_ID=1234567890123456789
```

### 3. Restart the Bot

```bash
# Stop current processes
pm2 stop all

# Or use docker
docker-compose restart

# Start services
pm2 start pm2.json

# Or with direct commands
pdm run python start_sender.py &
pdm run python start_receiver.py &
```

## Usage Examples

### Basic Research

Simply ask for research on a topic in the configured channel:

```
Research the impact of artificial intelligence on healthcare
```

### Focused Research

Specify aspects to focus on:

```
Analyze quantum computing with focus on cryptography and security applications
```

### Different Depths

**Overview:**
```
Provide an overview of blockchain technology
```

**Comprehensive (default):**
```
Research climate change effects on marine ecosystems
```

**Detailed:**
```
Detailed analysis of CRISPR gene editing technology
```

## Response Structure

The bot structures research into these sections:

1. **📋 Executive Summary** - High-level overview
2. **🔍 Key Findings** - Main discoveries and points
3. **📊 Detailed Analysis** - In-depth examination
4. **💡 Insights & Implications** - Practical implications
5. **🔗 Related Topics** - Connected subjects
6. **✅ Conclusions** - Summary and takeaways

## Message Chunking

### How It Works

When a research response exceeds 1900 characters:

1. **Smart Splitting**: Chunks at paragraph boundaries
2. **Fallback**: If paragraphs are too long, splits at sentences
3. **Numbering**: Each chunk labeled "Part 1/3", "Part 2/3", etc.
4. **Threading**: All chunks posted in the same thread
5. **Sequential**: Messages appear one after another

### Example Output

For a 5000 character research response:

```
Message 1: 🔬 Deep Research Results (Part 1/3)
[First 1900 characters]

Message 2: 📄 Continued (Part 2/3)
[Next 1900 characters]

Message 3: 📄 Continued (Part 3/3)
[Remaining content]
```

## Channel Configuration

The deep research channel is automatically configured with these settings:

```python
{
  "channel_type": "deep_research",
  "behavior": {
    "response_style": "technical",
    "prefix": "🔬",
    "functions_enabled": true,
    "web_search_enabled": true,
    "auto_respond": true,
    "require_mention": false,
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

### Customization

You can customize the channel behavior by editing `/app/config_dir/channel_config.json` or using the channel configuration tool:

```
Configure channel [CHANNEL_ID] with:
- type: deep_research
- response_style: technical
- functions_enabled: true
```

## Trigger Keywords

These keywords automatically trigger deep research:

- "research"
- "deep research"
- "analyze"
- "comprehensive"
- "detailed analysis"
- "investigate"
- "study"
- "explore"

Plus any message ending with "?"

## Technical Details

### Architecture Flow

```
User Message (Discord)
    ↓
Sender Process → RabbitMQ Queue
    ↓
Receiver Process → LLM Processing
    ↓
Deep Research Tool Execution
    ↓
Comprehensive Response Generated
    ↓
DeepResearchChannelHook (SENDER)
    ↓
Message Chunking (if > 1900 chars)
    ↓
Thread Creation & Sequential Posting
    ↓
Discord Thread Messages
```

### Hook Priority

- **Priority**: 2 (runs before message sending)
- **Trigger**: SENDER (processes outgoing messages)
- **Platform**: Discord only (`discord_hikari`)

### Message Splitting Algorithm

```python
def chunk_message(text: str, max_length: int = 1900) -> List[str]:
    # 1. Try splitting by paragraphs (\n\n)
    # 2. If paragraph > max_length, split by sentences
    # 3. Ensure no chunk exceeds max_length
    # 4. Return list of chunks
```

## Troubleshooting

### Bot Not Responding

**Check channel ID:**
```bash
# Verify in .env
grep PLUGIN_DEEP_RESEARCH_CHANNEL_ID .env

# Check logs
pm2 logs | grep "deep_research"
```

**Verify bot is running:**
```bash
pm2 status
# Both sender and receiver should be "online"
```

### Messages Not Chunking

**Check hook registration:**
```bash
# Look for hook registration in logs
pm2 logs | grep "DeepResearchChannelHook"
```

**Verify message length:**
- Only messages > 1900 characters are chunked
- Check the actual character count of the response

### Thread Issues

**Verify Discord permissions:**
- Bot needs "Send Messages in Threads" permission
- Bot needs "Create Public Threads" permission
- Check channel-specific permissions

**Check thread_id:**
- Threads require a parent message
- Ensure `thread_id` is properly set in Location

## Advanced Configuration

### Multiple Research Channels

You can configure multiple research channels by manually editing the config:

```json
{
  "1234567890123456789": {
    "channel_id": "1234567890123456789",
    "channel_type": "deep_research",
    "channel_name": "AI Research",
    "behavior": {
      "system_prompt": "Focus on AI and ML topics..."
    }
  },
  "9876543210987654321": {
    "channel_id": "9876543210987654321",
    "channel_type": "deep_research",
    "channel_name": "Science Research",
    "behavior": {
      "system_prompt": "Focus on scientific research..."
    }
  }
}
```

### Custom System Prompt

Modify the system prompt in the config file for specialized research:

```python
"system_prompt": (
    "You are a medical research assistant. "
    "Provide evidence-based analysis with citations. "
    "Focus on peer-reviewed research and clinical studies."
)
```

### Adjust Chunk Size

Edit the plugin code to change chunk size:

```python
# In llmkira/extra/plugins/deep_research/__init__.py
chunks = chunk_message(original_text, max_length=1500)  # Smaller chunks
```

## Integration with Other Plugins

### With Search Plugin

Deep research automatically uses web search when enabled:

```bash
# Enable in channel config
"web_search_enabled": true
```

The bot will search for additional information during research.

### With Code Interpreter

For technical research involving code:

```bash
# Enable in channel config
"code_interpreter_enabled": true
```

The bot can execute code examples during analysis.

## Best Practices

1. **Use Specific Topics**: More specific topics yield better research
   - ❌ "Tell me about AI"
   - ✅ "Research the application of transformer models in medical image analysis"

2. **Specify Aspects**: Guide the research direction
   - "Research solar energy with focus on efficiency and cost"

3. **Choose Appropriate Depth**:
   - Overview: Quick understanding (500-1000 words)
   - Comprehensive: Balanced detail (1500-2500 words)
   - Detailed: In-depth analysis (3000+ words)

4. **Thread Management**:
   - Start research in a clean channel or thread
   - Allow messages to post completely before asking follow-ups

5. **Rate Limiting**:
   - Wait for research to complete before new requests
   - Avoid rapid-fire questions that overwhelm the queue

## Performance Considerations

### Token Usage

- Deep research uses more tokens (1500-3000 per request)
- Configure `max_tokens` based on your LLM limits:
  ```python
  "max_tokens": 2000  # Adjust based on your model
  ```

### Message Queue

- Each chunk is a separate message in the queue
- Long research (10+ chunks) may take time to post
- Monitor RabbitMQ queue depth:
  ```bash
  # Check queue status
  docker exec -it llmbot_rabbitmq rabbitmqctl list_queues
  ```

### Discord Rate Limits

- Discord limits: 5 messages per 5 seconds per channel
- The sender automatically handles rate limiting
- Very long research may take 30+ seconds to post completely

## Migration from Other Bots

If migrating from another bot setup:

1. **Export existing research**: Save to files
2. **Configure channel**: Use same channel ID
3. **Test with short request**: Verify chunking works
4. **Adjust settings**: Tune `max_tokens`, `temperature` as needed

## API Reference

### DeepResearch Tool Schema

```python
class DeepResearch(BaseModel):
    topic: str                    # Required: Research topic
    aspects: Optional[str]        # Optional: Specific aspects
    depth: Optional[str]          # Optional: 'overview', 'comprehensive', 'detailed'
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLUGIN_DEEP_RESEARCH_CHANNEL_ID` | Yes | None | Discord channel ID for research |

### Hook Configuration

```python
@resign_hook()
class DeepResearchChannelHook(Hook):
    trigger: Trigger = Trigger.SENDER
    priority = 2
```

## Further Reading

- [Plugin Development Guide](../CONTRIBUTING.md)
- [Discord Bot Setup](../README.md)
- [Channel Handler Plugin](../llmkira/extra/plugins/channel_handler/README.md)
- [Message Queue Architecture](../docs/architecture.md)

## Support

For issues or questions:

1. Check logs: `pm2 logs | grep deep_research`
2. Verify config: `/app/config_dir/channel_config.json`
3. Open issue: https://github.com/LlmKira/Openaibot/issues
4. Include: Channel ID, error logs, bot version
