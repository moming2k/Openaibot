# -*- coding: utf-8 -*-
"""
Newsletter Content Processor
Automatically summarizes content and provides action items
"""

import os
from typing import List, Tuple
from loguru import logger

from llmkira.openapi.hook import Hook, resign_hook, Trigger
from llmkira.task.schema import Location, EventMessage


@resign_hook()
class NewsletterProcessorHook(Hook):
    """Hook to process newsletter channel messages"""

    trigger: Trigger = Trigger.RECEIVER
    priority = 1  # High priority to run first

    async def trigger_hook(self, *args, **kwargs) -> bool:
        """Check if this hook should run"""
        platform = kwargs.get("platform_name", "")
        locate = kwargs.get("locate")

        if platform != "discord_hikari" or not locate:
            return False

        # Check if this is the newsletter channel
        newsletter_channel = os.getenv("PLUGIN_NEWS_CHANNEL_ID")
        return locate.chat_id == newsletter_channel

    async def hook_run(
        self,
        platform_name: str,
        messages: List[EventMessage],
        locate: Location = None,
        **kwargs
    ) -> Tuple[Tuple, dict]:
        """Process newsletter messages with summarization and translation"""

        if not locate or not messages:
            return (platform_name, messages, locate), kwargs

        newsletter_channel = os.getenv("PLUGIN_NEWS_CHANNEL_ID")
        translate_to_zh = os.getenv("PLUGIN_NEWS_TRANSLATE_TO_ZH_TW", "true").lower() == "true"

        if locate.chat_id != newsletter_channel:
            return (platform_name, messages, locate), kwargs

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
*Note: If original content is in English, the summary above is translated to Traditional Chinese. Original language detected: [EN/ZH]*
"""

        # Update kwargs with newsletter-specific settings
        kwargs["system_prompt"] = system_prompt
        kwargs["temperature"] = 0.3  # Lower temperature for more consistent summaries
        kwargs["max_tokens"] = 1000  # Allow longer responses for summaries
        kwargs["functions_enabled"] = False  # Disable function calling for summaries

        # Prefix the message to trigger summarization
        for message in messages:
            original_text = message.text
            message.text = f"""Please analyze and summarize the following newsletter content:

---
{original_text}
---

Provide:
1. A concise summary (3-5 key points)
2. Actionable steps extracted from the content
3. If the content is in English, translate your summary and action items to Traditional Chinese"""

        logger.info(f"📰 Newsletter processor activated for channel {newsletter_channel}")

        return (platform_name, messages, locate), kwargs
