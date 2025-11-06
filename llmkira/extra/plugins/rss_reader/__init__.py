# -*- coding: utf-8 -*-
"""
RSS Reader Plugin for Personal Assistant
Fetches RSS feeds, summarizes content, and posts to Discord channels
"""

__package__name__ = "llmkira.extra.plugins.rss_reader"
__plugin_name__ = "rss_feed_reader"
__openapi_version__ = "20240416"

import os
import json
import hashlib
import asyncio
from typing import Union, Type, List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import html2text
import aiohttp
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger
import pytz
from tzlocal import get_localzone

# Plugin SDK imports
from llmkira.sdk.tools import PluginMetadata, verify_openapi_version
from llmkira.sdk.tools.schema import FuncPair, BaseTool
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Location, EventMessage, Sign, ToolResponse
from llmkira.openai.cell import Tool, ToolCall, class_tool
from llmkira.openapi.fuse import resign_plugin_executor
from llmkira.sdk.utils import sync
from app.receiver.aps import SCHEDULER

# Verify OpenAPI version
verify_openapi_version(__package__name__, __openapi_version__)

# Configuration
RSS_CONFIG_FILE = Path("/app/config_dir/rss_config.json")
SEEN_ARTICLES_FILE = Path("/app/config_dir/seen_articles.json")


class RSSFeedConfig(BaseModel):
    """Configuration for RSS feed subscription"""

    feed_url: str = Field(description="RSS feed URL to subscribe to")
    channel_id: str = Field(description="Discord channel ID to post updates")
    interval_minutes: int = Field(default=30, description="Check interval in minutes")
    max_items: int = Field(default=5, description="Maximum items to fetch per check")
    summary_enabled: bool = Field(default=True, description="Enable AI summarization")
    category: Optional[str] = Field(default=None, description="Feed category (news, tech, etc.)")
    model_config = ConfigDict(extra="allow")


class RSSManager:
    """Manages RSS feed subscriptions and article tracking"""

    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0
        self.seen_articles = self._load_seen_articles()
        self.feed_configs = self._load_feed_configs()

    def _load_seen_articles(self) -> set:
        """Load previously seen article IDs"""
        if SEEN_ARTICLES_FILE.exists():
            try:
                with open(SEEN_ARTICLES_FILE, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load seen articles: {e}")
        return set()

    def _save_seen_articles(self):
        """Save seen article IDs"""
        try:
            SEEN_ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SEEN_ARTICLES_FILE, 'w') as f:
                json.dump(list(self.seen_articles), f)
        except Exception as e:
            logger.error(f"Failed to save seen articles: {e}")

    def _load_feed_configs(self) -> Dict:
        """Load RSS feed configurations"""
        if RSS_CONFIG_FILE.exists():
            try:
                with open(RSS_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load RSS configs: {e}")
        return {}

    def _save_feed_configs(self):
        """Save RSS feed configurations"""
        try:
            RSS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(RSS_CONFIG_FILE, 'w') as f:
                json.dump(self.feed_configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save RSS configs: {e}")

    def add_feed(self, user_id: str, config: RSSFeedConfig) -> str:
        """Add a new RSS feed subscription"""
        feed_id = hashlib.md5(f"{user_id}:{config.feed_url}".encode()).hexdigest()[:8]

        self.feed_configs[feed_id] = {
            "user_id": user_id,
            "config": config.model_dump()
        }
        self._save_feed_configs()

        return feed_id

    def remove_feed(self, feed_id: str) -> bool:
        """Remove an RSS feed subscription"""
        if feed_id in self.feed_configs:
            del self.feed_configs[feed_id]
            self._save_feed_configs()
            return True
        return False

    def get_user_feeds(self, user_id: str) -> List[Dict]:
        """Get all feeds for a user"""
        user_feeds = []
        for feed_id, data in self.feed_configs.items():
            if data["user_id"] == user_id:
                user_feeds.append({
                    "id": feed_id,
                    **data["config"]
                })
        return user_feeds

    async def fetch_feed(self, feed_url: str, max_items: int = 5) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries[:max_items]:
                # Generate unique ID for article
                article_id = hashlib.md5(
                    entry.get('link', entry.get('id', '')).encode()
                ).hexdigest()

                # Skip if already seen
                if article_id in self.seen_articles:
                    continue

                # Parse article data
                title = entry.get('title', 'No title')
                link = entry.get('link', entry.get('id', ''))

                # Get content (try different fields)
                content = (
                    entry.get('summary', '') or
                    entry.get('description', '') or
                    entry.get('content', [{}])[0].get('value', '')
                )

                # Convert HTML to text
                content_text = self.h2t.handle(content)

                # Parse publication date
                published = None
                if hasattr(entry, 'published_parsed'):
                    published = datetime.fromtimestamp(
                        entry.published_parsed.tm_isdst
                    )
                elif hasattr(entry, 'updated_parsed'):
                    published = datetime.fromtimestamp(
                        entry.updated_parsed.tm_isdst
                    )

                # Skip old articles (>48 hours)
                if published:
                    if datetime.now() - published > timedelta(hours=48):
                        continue

                articles.append({
                    'id': article_id,
                    'title': title,
                    'link': link,
                    'content': content_text[:2000],  # Limit content length
                    'published': published.isoformat() if published else None,
                    'source': feed.feed.get('title', 'Unknown')
                })

                # Mark as seen
                self.seen_articles.add(article_id)

            # Save seen articles
            if articles:
                self._save_seen_articles()

            return articles

        except Exception as e:
            logger.error(f"Failed to fetch feed {feed_url}: {e}")
            return []

    async def summarize_article(
        self,
        article: Dict,
        model: str = "gpt-4o-mini"
    ) -> str:
        """Generate AI summary for an article"""
        try:
            from llmkira.openai import OpenAI

            # Get OpenAI client
            api_key = os.getenv("GLOBAL_OAI_KEY")
            if not api_key:
                return article['content'][:200] + "..."

            client = OpenAI(api_key=api_key)

            # Create summary prompt
            prompt = f"""
            Create a concise 2-3 sentence summary of this article:

            Title: {article['title']}
            Content: {article['content'][:1000]}

            Focus on:
            1. Main point or news
            2. Why it matters
            3. Key implications

            Keep the summary informative but brief.
            """

            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to summarize article: {e}")
            return article['content'][:200] + "..."

    def format_discord_message(
        self,
        articles: List[Dict],
        channel_type: str = "default",
        include_summary: bool = True
    ) -> str:
        """Format articles for Discord message"""

        if not articles:
            return "📭 No new articles found in the RSS feed."

        # Different formats based on channel type
        if channel_type == "news":
            # Detailed format for news channels
            messages = []
            for article in articles:
                summary = article.get('summary', article['content'][:200] + "...")
                msg = f"""**📰 {article['title']}**
*Source: {article['source']}*
{summary if include_summary else ''}
[Read more]({article['link']})
"""
                messages.append(msg.strip())

            header = f"📨 **RSS Update** - {len(articles)} new article(s)\n"
            return header + "\n\n---\n\n".join(messages)

        elif channel_type == "brief":
            # Brief format for general channels
            messages = []
            header = f"📋 **Quick Update** ({len(articles)} items)\n"

            for article in articles:
                msg = f"• [{article['title']}]({article['link']})"
                if include_summary and article.get('summary'):
                    msg += f" - {article['summary'][:100]}..."
                messages.append(msg)

            return header + "\n".join(messages)

        else:
            # Default format
            messages = []
            for article in articles:
                msg = f"**{article['title']}**\n"
                if include_summary and article.get('summary'):
                    msg += f"{article['summary']}\n"
                msg += f"[Link]({article['link']})"
                messages.append(msg)

            return "\n\n".join(messages)


# Global RSS manager instance
rss_manager = RSSManager()


@resign_plugin_executor(tool=RSSFeedConfig)
async def setup_rss_feed(
    feed_url: str,
    channel_id: str,
    interval_minutes: int = 30,
    max_items: int = 5,
    summary_enabled: bool = True,
    category: str = None,
    **kwargs
):
    """Set up RSS feed subscription"""
    return {
        "status": "configured",
        "feed_url": feed_url,
        "channel_id": channel_id,
        "interval": interval_minutes,
        "message": f"RSS feed {feed_url} will be checked every {interval_minutes} minutes"
    }


class RSSReaderTool(BaseTool):
    """RSS Feed Reader Tool"""

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = RSSFeedConfig
    keywords: list = ["rss", "feed", "subscribe", "news", "updates", "monitor"]
    env_required: List[str] = []
    env_prefix: str = "RSS_"

    def require_auth(self, env_map: dict) -> bool:
        """Check if authentication is required"""
        return False  # No auth required for RSS feeds

    @classmethod
    def env_help_docs(cls, empty_env: List[str]) -> str:
        """Provide help for environment variables"""
        return "RSS Reader is ready to use. No additional configuration required."

    def func_message(self, message_text: str, **kwargs):
        """Check if message should trigger this plugin"""
        message_lower = message_text.lower()

        # Check for keywords
        for keyword in self.keywords:
            if keyword in message_lower:
                return self.function

        # Check for RSS URL patterns
        if "http" in message_lower and any(
            term in message_lower for term in ["rss", "feed", "atom", "xml"]
        ):
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
        **kwargs
    ):
        """Handle plugin failure"""
        logger.error(f"RSS Reader failed: {exception}")

        meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"RSS setup failed: {str(exception)}",
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
                        text=f"❌ RSS Reader failed: {str(exception)}\n"
                             f"Please check the feed URL and try again.",
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
        """Main plugin execution"""

        # Parse configuration
        config = RSSFeedConfig.model_validate(arg)

        # Add feed to manager
        feed_id = rss_manager.add_feed(receiver.user_id, config)

        # Schedule periodic RSS checks
        async def check_rss_feed():
            """Fetch and post RSS feed updates"""
            try:
                # Fetch articles
                articles = await rss_manager.fetch_feed(
                    config.feed_url,
                    config.max_items
                )

                if not articles:
                    logger.info(f"No new articles for feed {config.feed_url}")
                    return

                # Add summaries if enabled
                if config.summary_enabled:
                    for article in articles:
                        article['summary'] = await rss_manager.summarize_article(
                            article,
                            model=env.get("GLOBAL_OAI_MODEL", "gpt-4o-mini")
                        )

                # Format message
                channel_type = config.category or "default"
                message_text = rss_manager.format_discord_message(
                    articles,
                    channel_type,
                    config.summary_enabled
                )

                # Send to Discord
                await Task.create_and_send(
                    queue_name=receiver.platform,
                    task=TaskHeader(
                        sender=task.sender,
                        receiver=Location(
                            platform=receiver.platform,
                            user_id=receiver.user_id,
                            chat_id=config.channel_id,  # Send to specified channel
                            thread_id=receiver.thread_id,
                            message_id=receiver.message_id,
                        ),
                        task_sign=Sign.from_root(
                            disable_tool_action=True,
                            response_snapshot=False,
                            memory_able=False,
                            platform=receiver.platform,
                        ),
                        message=[
                            EventMessage(
                                user_id=receiver.user_id,
                                chat_id=config.channel_id,
                                text=message_text,
                            )
                        ],
                    ),
                )

                logger.info(f"Posted {len(articles)} articles from {config.feed_url}")

            except Exception as e:
                logger.error(f"RSS check failed for {config.feed_url}: {e}")

        # Schedule the job
        try:
            tz = pytz.timezone(get_localzone().key)

            # Create job ID
            job_id = f"rss_{feed_id}"

            # Add or update job
            SCHEDULER.add_job(
                func=check_rss_feed,
                id=job_id,
                trigger="interval",
                minutes=config.interval_minutes,
                replace_existing=True,
                timezone=tz,
                name=f"RSS: {config.feed_url[:30]}",
                misfire_grace_time=60,
            )

            # Run immediately for testing
            await check_rss_feed()

            logger.info(f"Scheduled RSS feed {config.feed_url} with ID {job_id}")

            # Send success response
            meta = task.task_sign.reply(
                plugin_name=__plugin_name__,
                tool_response=[
                    ToolResponse(
                        name=__plugin_name__,
                        function_response=(
                            f"RSS feed subscription successful. "
                            f"Feed: {config.feed_url}, "
                            f"Channel: {config.channel_id}, "
                            f"Interval: {config.interval_minutes} minutes"
                        ),
                        tool_call_id=pending_task.id,
                        tool_call=pending_task,
                    )
                ],
            )

            # Get user's existing feeds
            user_feeds = rss_manager.get_user_feeds(receiver.user_id)
            feeds_list = "\n".join([
                f"• {feed['feed_url'][:50]}... (ID: {feed['id']})"
                for feed in user_feeds
            ])

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
                                f"✅ **RSS Feed Subscribed!**\n\n"
                                f"📡 **Feed:** {config.feed_url}\n"
                                f"📢 **Channel:** <#{config.channel_id}>\n"
                                f"⏰ **Update Interval:** Every {config.interval_minutes} minutes\n"
                                f"📊 **Max Items:** {config.max_items} per update\n"
                                f"🤖 **AI Summary:** {'Enabled' if config.summary_enabled else 'Disabled'}\n"
                                f"🏷️ **Category:** {config.category or 'General'}\n\n"
                                f"**Your Active Feeds:**\n{feeds_list}\n\n"
                                f"_First update has been sent to the channel. "
                                f"Use `/rss list` to see all subscriptions._"
                            ),
                        )
                    ],
                ),
            )

            return f"RSS feed {config.feed_url} subscribed successfully"

        except Exception as e:
            logger.error(f"Failed to schedule RSS feed: {e}")
            raise


# Plugin metadata
__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Subscribe to RSS feeds and get automatic updates with AI summaries",
    usage=(
        "Say 'subscribe to RSS feed [URL]' or 'monitor RSS [URL] in channel [ID]'\n"
        "Examples:\n"
        "• Subscribe to https://example.com/rss feed\n"
        "• Monitor RSS https://news.site/feed in channel 123456789\n"
        "• Add tech news feed with 15 minute updates"
    ),
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(RSSFeedConfig), tool=RSSReaderTool)},
    homepage="https://github.com/LlmKira/Openaibot",
)