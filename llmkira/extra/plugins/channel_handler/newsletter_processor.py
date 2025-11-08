# -*- coding: utf-8 -*-
"""
Newsletter Content Processor
Automatically summarizes content and provides action items
"""

import os
from typing import List, Tuple
from loguru import logger
from pydantic import ConfigDict

from llmkira.openapi.hook import Hook, resign_hook, Trigger
from llmkira.task.schema import Location, EventMessage


@resign_hook()
class NewsletterProcessorHook(Hook):
    """Hook to process newsletter channel messages"""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    trigger: Trigger = Trigger.RECEIVER
    priority: int = 1  # High priority to run first

    async def trigger_hook(self, *args, **kwargs) -> bool:
        """Check if this hook should run"""
        platform = kwargs.get("platform", "")
        locate = kwargs.get("locate")

        if platform != "discord_hikari" or not locate:
            return False

        # Check if this is the newsletter channel
        newsletter_channel = os.getenv("PLUGIN_NEWS_CHANNEL_ID")

        # Debug logging
        logger.debug(f"Newsletter hook: chat_id={locate.chat_id} (type={type(locate.chat_id)}), newsletter_channel={newsletter_channel} (type={type(newsletter_channel)})")

        # Convert to string for comparison
        is_newsletter = str(locate.chat_id) == newsletter_channel

        if is_newsletter:
            logger.info(f"📰 Newsletter processor activated for channel {newsletter_channel}")

        return is_newsletter

    async def hook_run(
        self,
        *args,
        **kwargs
    ) -> Tuple[Tuple, dict]:
        """Process newsletter messages with summarization and translation"""

        # Extract arguments from kwargs
        platform = kwargs.get("platform", "")
        messages = kwargs.get("messages", [])
        locate = kwargs.get("locate")

        if not locate or not messages:
            return (platform, messages, locate), kwargs

        newsletter_channel = os.getenv("PLUGIN_NEWS_CHANNEL_ID")
        translate_to_zh = os.getenv("PLUGIN_NEWS_TRANSLATE_TO_ZH_TW", "true").lower() == "true"

        if str(locate.chat_id) != newsletter_channel:
            return (platform, messages, locate), kwargs

        # Build enhanced system prompt for newsletter processing
        system_prompt = """You are a newsletter content analyzer. Your task is to:

1. **Summarize** the provided content concisely (3-5 key points)
2. **Extract Action Items**: Identify concrete, actionable steps from the content
3. **Language Handling**:
   - If the content is in English, provide your summary and action items in Traditional Chinese (繁體中文)
   - If the content is already in Chinese, maintain the same language

Format your response as follows:

📋 **摘要 (Summary)**
[List 3-5 key points in bullet format]

✅ **行動項目 (Action Items)**
[List specific actionable steps in bullet format. If none, state "無明確行動項目"]

---
*Note: 
Don't make any content that is not in the original content.
If original content is in English, the summary above is translated to Traditional Chinese. Original language detected: [EN/ZH]*
"""

        # Update kwargs with newsletter-specific settings
        kwargs["system_prompt"] = system_prompt
        kwargs["temperature"] = 0.3  # Lower temperature for more consistent summaries
        kwargs["max_tokens"] = 2000  # Balanced summaries
        kwargs["functions_enabled"] = False  # Disable function calling for summaries
        kwargs["memory_able"] = False  # Don't save newsletter summaries to conversation history

        # No need to modify message text - system_prompt handles instructions
        logger.info(f"📰 Newsletter processor activated for channel {newsletter_channel}")

        return (platform, messages, locate), kwargs
