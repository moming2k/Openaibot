# -*- coding: utf-8 -*-
"""
Deep Research Plugin for Discord
Performs comprehensive research on topics and posts results in thread format
"""

__package_name__ = "llmkira.extra.plugins.deep_research"
__plugin_name__ = "deep_research"
__openapi_version__ = "20240416"

import os
import re
from typing import Union, Type, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger

# Plugin SDK imports
from llmkira.sdk.tools import PluginMetadata, verify_openapi_version
from llmkira.sdk.tools.schema import FuncPair, BaseTool
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Location, EventMessage, ToolResponse
from llmkira.openai.cell import Tool, ToolCall, class_tool
from llmkira.openapi.fuse import resign_plugin_executor
from llmkira.openapi.hook import Hook, resign_hook, Trigger

# Verify OpenAPI version
verify_openapi_version(__package_name__, __openapi_version__)


def chunk_message(text: str, max_length: int = 1900) -> List[str]:
    """
    Split message into chunks that fit Discord's character limit.
    Uses 1900 to leave room for formatting.

    :param text: The text to split
    :param max_length: Maximum characters per chunk
    :return: List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        # If adding this paragraph exceeds the limit
        if len(current_chunk) + len(para) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # If paragraph itself is too long, split by sentences
            if len(para) > max_length:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
                    else:
                        current_chunk += sentence + " "
            else:
                current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"

    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


class DeepResearch(BaseModel):
    """Deep research tool input schema"""
    topic: str = Field(description="The topic to perform deep research on")
    aspects: Optional[str] = Field(
        default=None,
        description="Specific aspects or angles to focus on (optional)"
    )
    depth: Optional[str] = Field(
        default="comprehensive",
        description="Research depth: 'overview', 'comprehensive', or 'detailed'"
    )

    model_config = ConfigDict(extra="allow")


@resign_plugin_executor(tool=DeepResearch)
async def perform_deep_research(
    topic: str,
    aspects: str = None,
    depth: str = "comprehensive",
    **kwargs
):
    """
    Execute deep research on a topic.
    This is called by the LLM to gather information.
    """

    # Build research prompt based on depth
    if depth == "overview":
        prompt = f"Provide a comprehensive overview of: {topic}"
    elif depth == "detailed":
        prompt = f"Provide an in-depth, detailed analysis of: {topic}"
    else:  # comprehensive
        prompt = f"Perform comprehensive research on: {topic}"

    if aspects:
        prompt += f"\n\nFocus on these specific aspects: {aspects}"

    prompt += """

Please structure your research as follows:
1. 📋 Executive Summary
2. 🔍 Key Findings
3. 📊 Detailed Analysis
4. 💡 Insights & Implications
5. 🔗 Related Topics
6. ✅ Conclusions

Provide thorough, well-researched content with specific details and examples."""

    return {
        "research_instruction": prompt,
        "topic": topic,
        "status": "initiated"
    }


class DeepResearchTool(BaseTool):
    """
    Deep Research Tool for comprehensive topic analysis
    """

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = DeepResearch
    keywords: list = [
        "research",
        "deep research",
        "analyze",
        "comprehensive",
        "detailed analysis",
        "investigate",
        "study",
        "explore"
    ]
    env_required: List[str] = []
    env_prefix: str = "DEEP_RESEARCH_"

    def require_auth(self, env_map: dict) -> bool:
        """No special authentication required"""
        return False

    def func_message(self, message_text, message_raw, address, **kwargs):
        """
        Check if message should trigger deep research
        """
        message_lower = message_text.lower()

        # Check for deep research keywords
        for keyword in self.keywords:
            if keyword in message_lower:
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
        refer_llm_result: dict = None,
        **kwargs,
    ):
        """Handle research failure"""
        logger.error(f"Deep research failed: {exception}")

        meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Research failed: {exception}",
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
                        thread_id=receiver.thread_id,
                        text=f"❌ Deep research failed: {exception}",
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
        refer_llm_result: dict = None,
        **kwargs,
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
        refer_llm_result: dict = None,
    ):
        """
        Execute deep research and handle response
        """

        # Parse research parameters
        research_args = DeepResearch.model_validate(arg)

        logger.info(f"Starting deep research on topic: {research_args.topic}")

        # Execute research
        result = await perform_deep_research(**research_args.model_dump())

        # Send research instruction back to LLM for processing
        meta = task.task_sign.reprocess(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Research initiated for: {research_args.topic}. {result['research_instruction']}",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )

        # Create a new task with the research instruction
        await Task.create_and_send(
            queue_name=receiver.platform,
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_sign=meta,
                message=[],  # Empty - LLM will generate the research response
            ),
        )


@resign_hook()
class DeepResearchChannelHook(Hook):
    """
    Hook for processing messages in deep research channel.
    Automatically chunks and sends long responses in threads.
    """

    trigger: Trigger = Trigger.SENDER
    priority = 2

    async def trigger_hook(self, *args, **kwargs) -> bool:
        """Check if this hook should run"""
        platform = kwargs.get("platform", "")
        task = kwargs.get("task", None)

        # Only process Discord messages
        if platform != "discord_hikari":
            return False

        # Check if this is for the deep research channel
        research_channel_id = os.getenv("PLUGIN_DEEP_RESEARCH_CHANNEL_ID")
        if not research_channel_id:
            return False

        if not task or not task.receiver:
            return False

        # Check if chat_id matches the research channel
        is_research_channel = str(task.receiver.chat_id) == research_channel_id

        if is_research_channel:
            logger.info(f"Deep research hook triggered for channel {research_channel_id}")

        return is_research_channel

    async def hook_run(
        self,
        task: "TaskHeader",
        platform: str,
        **kwargs
    ) -> "TaskHeader":
        """
        Process messages for deep research channel.
        Split long messages into chunks and ensure they go to a thread.
        """

        if not task.message:
            return task

        logger.info(f"Processing {len(task.message)} messages for deep research channel")

        # Process each message
        new_messages = []
        for idx, message in enumerate(task.message):
            if not message.text:
                new_messages.append(message)
                continue

            # Get the original text
            original_text = message.text

            # Check if message needs chunking
            if len(original_text) > 1900:
                logger.info(f"Chunking message of length {len(original_text)}")

                # Split into chunks
                chunks = chunk_message(original_text, max_length=1900)

                logger.info(f"Split into {len(chunks)} chunks")

                # Create a message for each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    # Add header to first chunk
                    if chunk_idx == 0:
                        chunk_text = f"🔬 **Deep Research Results** (Part {chunk_idx + 1}/{len(chunks)})\n\n{chunk}"
                    else:
                        chunk_text = f"📄 **Continued** (Part {chunk_idx + 1}/{len(chunks)})\n\n{chunk}"

                    # Create new message for this chunk
                    chunk_message = EventMessage(
                        user_id=message.user_id,
                        chat_id=message.chat_id,
                        thread_id=message.thread_id or task.receiver.thread_id,
                        text=chunk_text,
                        files=message.files if chunk_idx == 0 else [],  # Only attach files to first chunk
                        created_at=message.created_at,
                    )
                    new_messages.append(chunk_message)
            else:
                # Message is short enough, just add research header
                message.text = f"🔬 **Deep Research Results**\n\n{original_text}"

                # Ensure thread_id is set
                if not message.thread_id and task.receiver.thread_id:
                    message.thread_id = task.receiver.thread_id

                new_messages.append(message)

        # Update task with new messages
        task.message = new_messages

        logger.info(f"Processed messages: {len(task.message)} total messages")

        return task


# Plugin metadata
__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Perform deep research on topics and post results in threaded messages",
    usage=(
        "Request deep research on any topic. The bot will:\n"
        "1. Analyze the topic comprehensively\n"
        "2. Generate detailed research with multiple sections\n"
        "3. Automatically split long responses into chunks\n"
        "4. Post all chunks sequentially in a thread\n\n"
        "Examples:\n"
        "• 'Research the impact of AI on healthcare'\n"
        "• 'Deep research on quantum computing applications'\n"
        "• 'Analyze the effects of climate change on biodiversity'\n\n"
        "Configure with: PLUGIN_DEEP_RESEARCH_CHANNEL_ID=your_channel_id"
    ),
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(DeepResearch), tool=DeepResearchTool)},
    homepage="https://github.com/LlmKira/Openaibot",
)
