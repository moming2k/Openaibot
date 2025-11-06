# -*- coding: utf-8 -*-
"""
Channel Handler Plugin for Discord
Provides channel-specific behavior and message processing
"""

__package__name__ = "llmkira.extra.plugins.channel_handler"
__plugin_name__ = "channel_handler"
__openapi_version__ = "20240416"

import os
import json
from typing import Union, Type, List, Dict, Optional, Tuple
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from loguru import logger

# Plugin SDK imports
from llmkira.sdk.tools import PluginMetadata, verify_openapi_version
from llmkira.sdk.tools.schema import FuncPair, BaseTool
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Location, EventMessage, ToolResponse
from llmkira.openai.cell import Tool, ToolCall, class_tool
from llmkira.openapi.fuse import resign_plugin_executor
from llmkira.openapi.trigger import resign_trigger
from llmkira.openapi.trigger import Trigger as TriggerClass
from llmkira.openapi.hook import Hook, resign_hook, Trigger

# Verify OpenAPI version
verify_openapi_version(__package__name__, __openapi_version__)

# Configuration file
CHANNEL_CONFIG_FILE = Path("/app/config_dir/channel_config.json")


class ChannelType(str, Enum):
    """Types of Discord channels"""
    NEWS = "news"
    TECH = "tech"
    GENERAL = "general"
    SUPPORT = "support"
    ANNOUNCEMENT = "announcement"
    DEEP_RESEARCH = "deep_research"
    CUSTOM = "custom"


class ChannelBehavior(BaseModel):
    """Behavior configuration for a channel"""

    # Response settings
    response_style: str = Field(
        default="normal",
        description="Response style: normal, technical, casual, formal"
    )
    prefix: Optional[str] = Field(
        default=None,
        description="Prefix to add to all messages"
    )
    suffix: Optional[str] = Field(
        default=None,
        description="Suffix to add to all messages"
    )

    # Feature toggles
    functions_enabled: bool = Field(
        default=True,
        description="Enable function calling"
    )
    web_search_enabled: bool = Field(
        default=False,
        description="Enable web search"
    )
    code_interpreter_enabled: bool = Field(
        default=False,
        description="Enable code interpreter"
    )
    summarization_enabled: bool = Field(
        default=True,
        description="Enable automatic summarization"
    )

    # Behavior settings
    auto_respond: bool = Field(
        default=False,
        description="Automatically respond to all messages"
    )
    require_mention: bool = Field(
        default=False,
        description="Only respond when mentioned"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that trigger response"
    )
    blocked_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that prevent response"
    )

    # LLM settings
    model_override: Optional[str] = Field(
        default=None,
        description="Override default model for this channel"
    )
    temperature: float = Field(
        default=0.7,
        description="Temperature for responses (0.0-1.0)"
    )
    max_tokens: int = Field(
        default=500,
        description="Maximum tokens in response"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for this channel"
    )

    model_config = ConfigDict(extra="allow")


class ChannelConfig(BaseModel):
    """Configuration for a Discord channel"""

    channel_id: str = Field(description="Discord channel ID")
    channel_type: ChannelType = Field(
        default=ChannelType.GENERAL,
        description="Type of channel"
    )
    channel_name: Optional[str] = Field(
        default=None,
        description="Human-readable channel name"
    )
    behavior: ChannelBehavior = Field(
        default_factory=ChannelBehavior,
        description="Channel behavior settings"
    )
    active: bool = Field(
        default=True,
        description="Whether the channel handler is active"
    )

    model_config = ConfigDict(extra="allow")


class ChannelManager:
    """Manages channel configurations"""

    def __init__(self):
        self.configs: Dict[str, ChannelConfig] = self._load_configs()
        self._initialize_defaults()

    def _load_configs(self) -> Dict[str, ChannelConfig]:
        """Load channel configurations from file"""
        if CHANNEL_CONFIG_FILE.exists():
            try:
                with open(CHANNEL_CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    return {
                        channel_id: ChannelConfig.model_validate(config)
                        for channel_id, config in data.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load channel configs: {e}")
        return {}

    def _save_configs(self):
        """Save channel configurations to file"""
        try:
            CHANNEL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CHANNEL_CONFIG_FILE, 'w') as f:
                data = {
                    channel_id: config.model_dump()
                    for channel_id, config in self.configs.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save channel configs: {e}")

    def _initialize_defaults(self):
        """Initialize default channel configurations from environment"""

        # News Channel / Newsletter
        if news_id := os.getenv("PLUGIN_NEWS_CHANNEL_ID"):
            if news_id not in self.configs or news_id == "1435035369975447662":
                # Check if translation is enabled
                translate_enabled = os.getenv("PLUGIN_NEWS_TRANSLATE_TO_ZH_TW", "true").lower() == "true"
                auto_respond = os.getenv("PLUGIN_NEWS_AUTO_RESPOND", "true").lower() == "true"

                self.configs[news_id] = ChannelConfig(
                    channel_id=news_id,
                    channel_type=ChannelType.NEWS,
                    channel_name="Newsletter Channel",
                    behavior=ChannelBehavior(
                        response_style="formal",
                        prefix="📰 [NEWSLETTER]",
                        functions_enabled=False,  # Disable for summaries
                        web_search_enabled=False,
                        summarization_enabled=True,
                        auto_respond=auto_respond,  # Auto-respond to all messages
                        require_mention=False,  # Don't require mentions
                        keywords=[],  # Respond to all messages, not just keywords
                        system_prompt=(
                            "You are a newsletter content analyzer. "
                            "Summarize content and extract actionable steps. "
                            + ("Translate to Traditional Chinese if content is in English." if translate_enabled else "")
                        )
                    )
                )

        # Tech Channel
        if tech_id := os.getenv("PLUGIN_TECH_CHANNEL_ID"):
            if tech_id not in self.configs:
                self.configs[tech_id] = ChannelConfig(
                    channel_id=tech_id,
                    channel_type=ChannelType.TECH,
                    channel_name="Tech Support",
                    behavior=ChannelBehavior(
                        response_style="technical",
                        prefix="💻 [TECH]",
                        functions_enabled=True,
                        code_interpreter_enabled=True,
                        web_search_enabled=True,
                        keywords=["code", "debug", "error", "help", "how to"],
                        system_prompt="You are a technical assistant. Provide detailed technical help."
                    )
                )

        # General Channel
        if general_id := os.getenv("PLUGIN_GENERAL_CHANNEL_ID"):
            if general_id not in self.configs:
                self.configs[general_id] = ChannelConfig(
                    channel_id=general_id,
                    channel_type=ChannelType.GENERAL,
                    channel_name="General Chat",
                    behavior=ChannelBehavior(
                        response_style="casual",
                        prefix="💬",
                        functions_enabled=False,
                        require_mention=True,
                        system_prompt="You are a friendly chat assistant. Be conversational and helpful."
                    )
                )

        # Deep Research Channel
        if research_id := os.getenv("PLUGIN_DEEP_RESEARCH_CHANNEL_ID"):
            if research_id not in self.configs:
                self.configs[research_id] = ChannelConfig(
                    channel_id=research_id,
                    channel_type=ChannelType.DEEP_RESEARCH,
                    channel_name="Deep Research",
                    behavior=ChannelBehavior(
                        response_style="technical",
                        prefix="🔬",
                        functions_enabled=True,
                        web_search_enabled=True,
                        code_interpreter_enabled=False,
                        auto_respond=True,
                        require_mention=False,
                        max_tokens=2000,
                        temperature=0.7,
                        system_prompt=(
                            "You are a research assistant specializing in comprehensive, in-depth analysis. "
                            "Provide structured research with: Executive Summary, Key Findings, Detailed Analysis, "
                            "Insights & Implications, Related Topics, and Conclusions. "
                            "Be thorough, well-researched, and include specific details and examples."
                        )
                    )
                )

        # Save if new defaults were added
        self._save_configs()

    def get_channel_config(self, channel_id: str) -> Optional[ChannelConfig]:
        """Get configuration for a channel"""
        return self.configs.get(channel_id)

    def set_channel_config(
        self,
        channel_id: str,
        config: ChannelConfig
    ) -> ChannelConfig:
        """Set configuration for a channel"""
        config.channel_id = channel_id
        self.configs[channel_id] = config
        self._save_configs()
        return config

    def remove_channel_config(self, channel_id: str) -> bool:
        """Remove configuration for a channel"""
        if channel_id in self.configs:
            del self.configs[channel_id]
            self._save_configs()
            return True
        return False

    def list_channels(self) -> List[ChannelConfig]:
        """List all configured channels"""
        return list(self.configs.values())


# Global channel manager instance
channel_manager = ChannelManager()


# Channel-specific triggers
@resign_trigger(
    TriggerClass(
        on_platform="discord_hikari",
        action="allow",
        priority=10,
        function_enable=True,
        name="channel_specific_trigger"
    )
)
async def channel_trigger(
    message: str,
    chat_id: str,
    user_id: str,
    platform: str = "discord_hikari",
    **kwargs
) -> bool:
    """Determine if bot should respond based on channel configuration"""

    # Get channel configuration
    config = channel_manager.get_channel_config(chat_id)

    if not config or not config.active:
        # No configuration or inactive - use default behavior
        return False

    behavior = config.behavior

    # Check blocked keywords first
    message_lower = message.lower()
    if behavior.blocked_keywords:
        for keyword in behavior.blocked_keywords:
            if keyword.lower() in message_lower:
                logger.debug(f"Message blocked by keyword '{keyword}' in channel {chat_id}")
                return False

    # Check if mention is required
    if behavior.require_mention:
        # Check for bot mention (simplified check)
        if "@" not in message:
            return False

    # Check for trigger keywords
    if behavior.keywords:
        for keyword in behavior.keywords:
            if keyword.lower() in message_lower:
                logger.debug(f"Message triggered by keyword '{keyword}' in channel {chat_id}")
                return True

    # Check auto-respond
    if behavior.auto_respond:
        return True

    # Default behavior based on channel type
    if config.channel_type == ChannelType.NEWS:
        # News channels: respond to questions and news requests
        return any(
            term in message_lower
            for term in ["?", "news", "update", "summary", "what", "how", "why"]
        )
    elif config.channel_type == ChannelType.TECH:
        # Tech channels: respond to technical questions
        return any(
            term in message_lower
            for term in ["?", "error", "bug", "help", "code", "debug", "how to"]
        )
    elif config.channel_type == ChannelType.SUPPORT:
        # Support channels: always respond
        return True
    elif config.channel_type == ChannelType.DEEP_RESEARCH:
        # Deep research channels: respond to research requests
        return any(
            term in message_lower
            for term in ["research", "analyze", "study", "investigate", "explore", "?"]
        )

    return False


# Channel-specific message processing hook
@resign_hook()
class ChannelProcessingHook(Hook):
    """Hook to process messages based on channel configuration"""

    trigger: Trigger = Trigger.RECEIVER
    priority = 5

    async def trigger_hook(self, *args, **kwargs) -> bool:
        """Check if this hook should run"""
        platform = kwargs.get("platform_name", "")
        return platform == "discord_hikari"

    async def hook_run(
        self,
        platform_name: str,
        messages: List[EventMessage],
        locate: Location = None,
        **kwargs
    ) -> Tuple[Tuple, dict]:
        """Process messages based on channel configuration"""

        if not locate:
            return (platform_name, messages, locate), kwargs

        # Get channel configuration
        config = channel_manager.get_channel_config(locate.chat_id)

        if not config or not config.active:
            return (platform_name, messages, locate), kwargs

        behavior = config.behavior

        # Process each message
        for message in messages:
            # Add prefix
            if behavior.prefix:
                message.text = f"{behavior.prefix} {message.text}"

            # Add suffix
            if behavior.suffix:
                message.text = f"{message.text} {behavior.suffix}"

            # Apply response style transformations
            if behavior.response_style == "technical":
                # Add technical context
                message.text = self._apply_technical_style(message.text)
            elif behavior.response_style == "casual":
                # Apply casual style
                message.text = self._apply_casual_style(message.text)
            elif behavior.response_style == "formal":
                # Apply formal style
                message.text = self._apply_formal_style(message.text)

        # Update kwargs with channel-specific settings
        if behavior.model_override:
            kwargs["model"] = behavior.model_override

        if behavior.system_prompt:
            kwargs["system_prompt"] = behavior.system_prompt

        kwargs["temperature"] = behavior.temperature
        kwargs["max_tokens"] = behavior.max_tokens
        kwargs["functions_enabled"] = behavior.functions_enabled
        kwargs["web_search_enabled"] = behavior.web_search_enabled
        kwargs["code_interpreter_enabled"] = behavior.code_interpreter_enabled

        return (platform_name, messages, locate), kwargs

    def _apply_technical_style(self, text: str) -> str:
        """Apply technical writing style"""
        # Could add more sophisticated transformations
        return text

    def _apply_casual_style(self, text: str) -> str:
        """Apply casual conversational style"""
        # Could add more sophisticated transformations
        return text

    def _apply_formal_style(self, text: str) -> str:
        """Apply formal writing style"""
        # Could add more sophisticated transformations
        return text


# Channel configuration tool
class ConfigureChannel(BaseModel):
    """Configure channel-specific behavior"""

    channel_id: str = Field(description="Discord channel ID to configure")
    channel_type: str = Field(
        default="general",
        description="Channel type: news, tech, general, support, announcement, custom"
    )
    response_style: str = Field(
        default="normal",
        description="Response style: normal, technical, casual, formal"
    )
    prefix: Optional[str] = Field(
        default=None,
        description="Prefix for all messages in this channel"
    )
    functions_enabled: bool = Field(
        default=True,
        description="Enable function calling in this channel"
    )
    auto_respond: bool = Field(
        default=False,
        description="Automatically respond to all messages"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords that trigger response"
    )

    model_config = ConfigDict(extra="allow")


@resign_plugin_executor(tool=ConfigureChannel)
async def configure_channel_behavior(
    channel_id: str,
    channel_type: str = "general",
    response_style: str = "normal",
    prefix: str = None,
    functions_enabled: bool = True,
    auto_respond: bool = False,
    keywords: List[str] = None,
    **kwargs
):
    """Configure channel-specific behavior"""

    # Create behavior configuration
    behavior = ChannelBehavior(
        response_style=response_style,
        prefix=prefix,
        functions_enabled=functions_enabled,
        auto_respond=auto_respond,
        keywords=keywords or []
    )

    # Create channel configuration
    config = ChannelConfig(
        channel_id=channel_id,
        channel_type=ChannelType(channel_type),
        behavior=behavior
    )

    # Save configuration
    saved_config = channel_manager.set_channel_config(channel_id, config)

    return {
        "status": "configured",
        "channel_id": channel_id,
        "channel_type": channel_type,
        "settings": saved_config.behavior.model_dump()
    }


class ChannelHandlerTool(BaseTool):
    """Channel Handler Configuration Tool"""

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = ConfigureChannel
    keywords: list = ["configure", "channel", "setup", "behavior", "customize"]
    env_required: List[str] = []
    env_prefix: str = "CHANNEL_"

    def require_auth(self, env_map: dict) -> bool:
        """Check if authentication is required"""
        # Require admin authentication for channel configuration
        return True

    def func_message(self, message_text: str, **kwargs):
        """Check if message should trigger this plugin"""
        message_lower = message_text.lower()

        for keyword in self.keywords:
            if keyword in message_lower and "channel" in message_lower:
                return self.function

        return None

    async def failed(
        self,
        task: "TaskHeader",
        receiver: "Location",
        exception,
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        **kwargs
    ):
        """Handle plugin failure"""
        logger.error(f"Channel configuration failed: {exception}")

        meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Configuration failed: {str(exception)}",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )

        await Task.create_and_send(
            queue_name=receiver.platform,
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_sign=meta,
                message=[
                    EventMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"❌ Channel configuration failed: {str(exception)}",
                    )
                ],
            ),
        )

    async def callback(
        self,
        task: "TaskHeader",
        receiver: "Location",
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        **kwargs
    ):
        """Post-execution callback"""
        return True

    async def run(
        self,
        task: "TaskHeader",
        receiver: "Location",
        arg: dict,
        env: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None
    ):
        """Configure channel behavior"""

        # Parse configuration
        config_args = ConfigureChannel.model_validate(arg)

        # Configure channel
        result = await configure_channel_behavior(**config_args.model_dump())

        # Get all configured channels
        all_channels = channel_manager.list_channels()
        channel_list = "\n".join([
            f"• <#{ch.channel_id}> ({ch.channel_type.value}): "
            f"{'Active' if ch.active else 'Inactive'}"
            for ch in all_channels
        ])

        # Send response
        meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Channel {config_args.channel_id} configured successfully",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )

        await Task.create_and_send(
            queue_name=receiver.platform,
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_sign=meta,
                message=[
                    EventMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=(
                            f"✅ **Channel Configured!**\n\n"
                            f"📢 **Channel:** <#{config_args.channel_id}>\n"
                            f"🏷️ **Type:** {config_args.channel_type}\n"
                            f"🎨 **Style:** {config_args.response_style}\n"
                            f"{'🔤 **Prefix:** ' + config_args.prefix if config_args.prefix else ''}\n"
                            f"⚙️ **Functions:** {'Enabled' if config_args.functions_enabled else 'Disabled'}\n"
                            f"🤖 **Auto-respond:** {'Yes' if config_args.auto_respond else 'No'}\n\n"
                            f"**All Configured Channels:**\n{channel_list}"
                        ),
                    )
                ],
            ),
        )

        return "Channel configured successfully"


# Plugin metadata
__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Configure channel-specific behavior for Discord channels",
    usage=(
        "Configure different behaviors for different Discord channels.\n"
        "Examples:\n"
        "• Configure news channel with formal style\n"
        "• Setup tech support channel with code interpreter\n"
        "• Create casual chat channel with mention-only responses"
    ),
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(ConfigureChannel), tool=ChannelHandlerTool)},
    homepage="https://github.com/LlmKira/Openaibot",
)

# Import newsletter processor to register hooks
try:
    from . import newsletter_processor
    logger.info("📰 Newsletter processor loaded successfully")
except Exception as e:
    logger.warning(f"Newsletter processor not loaded: {e}")