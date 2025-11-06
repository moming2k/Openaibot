# -*- coding: utf-8 -*-
"""
FastAPI HTTP Server for Newsletter Content Submission
Allows submitting long-form content via HTTP POST that gets processed
as if it came from the newsletter Discord channel
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

# Use standard logging if loguru not available
try:
    from loguru import logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info = logging.info
    logger.warning = logging.warning
    logger.error = logging.error
    logger.exception = logging.exception

from llmkira.task import Task, TaskHeader
from llmkira.task.schema import EventMessage, Sign, Location


app = FastAPI(
    title="LLMKira Newsletter API",
    description="Submit content for newsletter processing and summarization",
    version="1.0.0"
)


class NewsletterSubmission(BaseModel):
    """Request model for newsletter content submission"""
    content: str = Field(
        ...,
        description="The content to analyze and summarize",
        min_length=1,
        max_length=100000
    )
    channel_id: Optional[str] = Field(
        None,
        description="Override the default newsletter channel ID"
    )


class NewsletterResponse(BaseModel):
    """Response model for newsletter submission"""
    success: bool
    message: str
    task_id: Optional[str] = None


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request header"""
    expected_key = os.getenv("NEWSLETTER_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server"
        )
    if x_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "LLMKira Newsletter API",
        "version": "1.0.0",
        "endpoints": {
            "POST /newsletter/submit": "Submit content for newsletter processing"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/newsletter/submit", response_model=NewsletterResponse)
async def submit_newsletter_content(
    submission: NewsletterSubmission,
    api_key: str = Depends(verify_api_key)
):
    """
    Submit content for newsletter processing

    This endpoint accepts long-form content and processes it as if it was
    posted to the Discord newsletter channel. The content will be:
    1. Summarized into 3-5 key bullet points
    2. Analyzed for actionable items
    3. Translated to Traditional Chinese if the content is in English

    **Authentication**: Requires X-API-Key header

    **Example**:
    ```bash
    curl -X POST "http://localhost:8765/newsletter/submit" \\
         -H "X-API-Key: your-api-key-here" \\
         -H "Content-Type: application/json" \\
         -d '{"content": "Your long article content here..."}'
    ```
    """
    try:
        # Get newsletter channel ID
        newsletter_channel_id = submission.channel_id or os.getenv("PLUGIN_NEWS_CHANNEL_ID")
        if not newsletter_channel_id:
            raise HTTPException(
                status_code=500,
                detail="Newsletter channel not configured"
            )

        logger.info(f"📰 API: Received newsletter submission ({len(submission.content)} chars)")

        # Prepare instruction for newsletter processing
        newsletter_instruction = (
            "[SYSTEM INSTRUCTION: You are a newsletter content analyzer. "
            "Provide: 1) 📋 摘要 (Summary) with 3-5 key bullet points, "
            "2) ✅ 行動項目 (Action Items) with specific actionable steps. "
            "If content is English, translate your response to Traditional Chinese (繁體中文). "
            "If no actionable items, state '無明確行動項目'.]\n\n"
            f"Content to analyze:\n{submission.content}"
        )

        # Create event message
        event_message = EventMessage(
            user_id="api_user",
            chat_id=newsletter_channel_id,
            thread_id=None,
            text=newsletter_instruction,
            files=[],
            created_at=str(__import__("time").time())
        )

        # Create task sign
        sign = Sign.from_root(
            disable_tool_action=True,  # Disable function calling for summaries
            response_snapshot=True,
            platform="discord_hikari",
        )

        # Create task header
        task = TaskHeader.from_sender(
            event_messages=[event_message],
            task_sign=sign,
            chat_id=newsletter_channel_id,
            user_id="api_user",
            message_id=None,
            platform="discord_hikari",
        )

        # Send task to processing queue
        _task = Task()
        success, logs = await _task.send_task(task=task)

        if success:
            logger.info(f"✅ API: Newsletter task submitted successfully")
            return NewsletterResponse(
                success=True,
                message="Content submitted for processing. Response will be sent to Discord channel.",
                task_id=task.task_sign.task_id
            )
        else:
            logger.error(f"❌ API: Failed to submit task: {logs}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit task: {logs}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing newsletter submission: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("NEWSLETTER_API_PORT", "8765"))
    host = os.getenv("NEWSLETTER_API_HOST", "0.0.0.0")

    logger.info(f"🚀 Starting Newsletter API server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
