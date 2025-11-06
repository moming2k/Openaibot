# Deep Research Plugin

A comprehensive research plugin for Discord that performs in-depth analysis on any topic and automatically formats responses in threaded messages.

## Features

- 🔬 **Comprehensive Research**: Performs deep analysis on any topic with structured output
- 📝 **Automatic Chunking**: Splits long responses into 2000-character chunks
- 🧵 **Thread Support**: Posts all chunks sequentially in a Discord thread
- 🎯 **Flexible Depth**: Choose between overview, comprehensive, or detailed analysis
- 🔍 **Aspect Focusing**: Optionally focus on specific aspects of a topic

## Configuration

### Environment Variables

Set the deep research channel ID in your `.env` file:

```bash
# Discord channel ID for deep research
PLUGIN_DEEP_RESEARCH_CHANNEL_ID=1234567890123456789
```

### How It Works

1. **User Request**: User asks for research on a topic in the configured channel
2. **Topic Analysis**: The bot identifies the research request
3. **Deep Research**: Performs comprehensive analysis with structured sections
4. **Chunking**: Automatically splits responses longer than 1900 characters
5. **Thread Posting**: Posts all chunks sequentially in a Discord thread

## Usage Examples

### Basic Research Request

```
Research the impact of artificial intelligence on modern healthcare
```

### Focused Research

```
Analyze quantum computing with focus on cryptography applications
```

### Detailed Research

```
Provide detailed research on climate change effects on marine ecosystems
```

## Research Structure

The bot structures research into the following sections:

1. 📋 **Executive Summary** - High-level overview
2. 🔍 **Key Findings** - Main discoveries and points
3. 📊 **Detailed Analysis** - In-depth examination
4. 💡 **Insights & Implications** - Practical implications
5. 🔗 **Related Topics** - Connected subjects
6. ✅ **Conclusions** - Summary and takeaways

## Message Chunking

- Maximum 1900 characters per chunk (leaving room for formatting)
- Chunks at paragraph boundaries when possible
- Falls back to sentence boundaries for very long paragraphs
- Each chunk is numbered: "Part 1/3", "Part 2/3", etc.

## Thread Behavior

- All chunks are posted in the same thread
- Messages appear sequentially, one after another
- First chunk includes the full header with 🔬 icon
- Subsequent chunks marked with 📄 icon
- Files (if any) attached only to the first chunk

## Integration with Channel Handler

The plugin integrates with the channel handler plugin for additional customization:

```python
# Customize research channel behavior
{
  "channel_id": "1234567890123456789",
  "channel_type": "custom",
  "behavior": {
    "response_style": "technical",
    "functions_enabled": true,
    "auto_respond": true,
    "system_prompt": "You are a research assistant specializing in detailed analysis."
  }
}
```

## Keywords That Trigger Research

The following keywords automatically trigger deep research:

- "research"
- "deep research"
- "analyze"
- "comprehensive"
- "detailed analysis"
- "investigate"
- "study"
- "explore"

## API Schema

### DeepResearch Tool

```python
class DeepResearch(BaseModel):
    topic: str  # Required: The topic to research
    aspects: Optional[str]  # Optional: Specific aspects to focus on
    depth: Optional[str]  # Optional: 'overview', 'comprehensive', or 'detailed'
```

## Technical Details

### Hook Priority

- **Priority**: 2 (runs after channel handler)
- **Trigger**: SENDER (processes outgoing messages)
- **Platform**: Discord (discord_hikari) only

### Message Processing Flow

```
User Message → Receiver → LLM Processing → Deep Research Tool
                                                ↓
                                    Research Response Generated
                                                ↓
                                    Hook Processes Response
                                                ↓
                        Split into Chunks (if > 1900 chars)
                                                ↓
                        Sequential Thread Messages → Discord
```

## Error Handling

- Failed research attempts send error messages to the channel
- Maintains thread context even on errors
- Logs detailed error information for debugging

## Development

### File Structure

```
llmkira/extra/plugins/deep_research/
├── __init__.py       # Main plugin implementation
└── README.md         # This file
```

### Testing

Test the plugin by:

1. Setting `PLUGIN_DEEP_RESEARCH_CHANNEL_ID` in `.env`
2. Sending a research request in the configured channel
3. Verifying chunking works with very long responses
4. Checking thread behavior and sequential posting

## Limitations

- Discord character limit: 2000 characters per message
- Deep research requires sufficient LLM context window
- Thread creation requires appropriate bot permissions
- Only works on Discord platform (not Telegram, Slack, etc.)

## Future Enhancements

- [ ] Citation tracking and source linking
- [ ] Image generation for research findings
- [ ] Export research to PDF/Markdown files
- [ ] Research history and caching
- [ ] Multi-language research support
- [ ] Interactive research refinement

## License

This plugin is part of the LLMKira project and follows the same license.
