"""
Notification system for sending review results to Telegram.
Uses 5 bot personas to post detailed review feedback.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
import aiohttp

from ..config import settings
from ..logging_config import get_logger

logger = get_logger("notifications")


# Map agent names to bot tokens and display names
BOT_MAPPING = {
    "compliance": {
        "token": lambda: settings.telegram_bot_compliance,
        "name": "Compliance Bot",
        "emoji": "📋",
    },
    "tech": {
        "token": lambda: settings.telegram_bot_tech,
        "name": "Tech Architect Bot",
        "emoji": "🔧",
    },
    "narrative": {
        "token": lambda: settings.telegram_bot_narrative,
        "name": "Narrative Writer Bot",
        "emoji": "✍️",
    },
    "risk": {
        "token": lambda: settings.telegram_bot_risk,
        "name": "Risk Assessor Bot",
        "emoji": "⚠️",
    },
    "policy": {
        "token": lambda: settings.telegram_bot_policy,
        "name": "Policy Analyst Bot",
        "emoji": "📊",
    },
}


async def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
) -> bool:
    """
    Send a message via Telegram Bot API.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        text: Message text
        parse_mode: Parsing mode (HTML, Markdown, or None)
    
    Returns:
        True if successful, False otherwise
    """
    if not bot_token:
        logger.warning("Bot token not configured, skipping message")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logger.debug("Telegram message sent successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error("Telegram API error %d: %s", response.status, error_text)
                    return False
    except Exception as exc:
        logger.exception("Failed to send Telegram message: %s", exc)
        return False


def format_review_message(agent_name: str, result: Dict) -> str:
    """
    Format a review result into a Telegram message.
    
    Args:
        agent_name: Name of the review agent (compliance, tech, etc.)
        result: Review result dict with score, passed, issues, recommendations
    
    Returns:
        Formatted message text
    """
    bot_info = BOT_MAPPING.get(agent_name, {"name": agent_name, "emoji": "🤖"})
    emoji = bot_info["emoji"]
    name = bot_info["name"]
    
    score = result.get("score", 0.0)
    passed = result.get("passed", False)
    issues = result.get("issues", [])
    recommendations = result.get("recommendations", [])
    
    status_emoji = "✅" if passed else "❌"
    status_text = "PASS" if passed else "FAIL"
    
    lines = [
        f"{emoji} <b>[{name}]</b> Score: {score:.2f} {status_emoji} ({status_text})",
        "",
    ]
    
    if issues:
        lines.append("<b>Issues:</b>")
        for issue in issues[:5]:  # Limit to 5 issues
            lines.append(f"  • {issue}")
        if len(issues) > 5:
            lines.append(f"  <i>... and {len(issues) - 5} more</i>")
        lines.append("")
    
    if recommendations:
        lines.append("<b>Recommendations:</b>")
        for rec in recommendations[:3]:  # Limit to 3 recommendations
            lines.append(f"  • {rec}")
        if len(recommendations) > 3:
            lines.append(f"  <i>... and {len(recommendations) - 3} more</i>")
    
    if not issues and not recommendations:
        lines.append("<i>No issues found. All checks passed.</i>")
    
    return "\n".join(lines)


def format_summary_message(review_data: Dict, opportunity_id: str) -> str:
    """
    Format an overall review summary message.
    
    Args:
        review_data: Complete review results with all agents
        opportunity_id: Opportunity identifier
    
    Returns:
        Formatted summary message
    """
    passed = review_data.get("passed", False)
    scores = review_data.get("scores", {})
    failed_agents = review_data.get("failed_agents", [])
    
    status_emoji = "✅" if passed else "❌"
    
    lines = [
        f"<b>Review Summary for {opportunity_id}</b>",
        "",
        f"Status: {status_emoji} <b>{'PASSED' if passed else 'FAILED'}</b>",
        "",
        "<b>Agent Scores:</b>",
    ]
    
    for agent_name, score in scores.items():
        bot_info = BOT_MAPPING.get(agent_name, {"name": agent_name, "emoji": "🤖"})
        emoji = bot_info["emoji"]
        check = "✅" if agent_name not in failed_agents else "❌"
        lines.append(f"  {emoji} {agent_name.title()}: {score:.2f} {check}")
    
    if failed_agents:
        lines.append("")
        lines.append(f"<b>Failed Agents:</b> {', '.join(a.title() for a in failed_agents)}")
        lines.append("")
        lines.append("<i>Review details posted above by individual agents.</i>")
    
    return "\n".join(lines)


async def send_review_notifications(
    review_data: Dict,
    opportunity_id: str,
    stage: str = "rfp",
) -> bool:
    """
    Send review results to Telegram using appropriate bot personas.
    
    Args:
        review_data: Complete review results from run_review_loop
        opportunity_id: Opportunity identifier
        stage: Pipeline stage (rfi, rfp, pricing)
    
    Returns:
        True if all messages sent successfully
    """
    if not settings.enable_notifications:
        logger.info("Notifications disabled, skipping Telegram messages")
        return True
    
    chat_id = settings.telegram_chat_id
    if not chat_id:
        logger.warning("Telegram chat ID not configured, skipping notifications")
        return False
    
    logger.info("Sending review notifications for %s (%s stage)", opportunity_id, stage)
    
    results = review_data.get("results", [])
    success_count = 0
    total_count = 0
    
    # Send individual agent messages
    tasks = []
    for result in results:
        agent_name = result.get("agent", "").lower()
        # Map agent class names to config keys
        agent_key = None
        if "compliance" in agent_name:
            agent_key = "compliance"
        elif "tech" in agent_name:
            agent_key = "tech"
        elif "narrative" in agent_name:
            agent_key = "narrative"
        elif "risk" in agent_name:
            agent_key = "risk"
        elif "policy" in agent_name:
            agent_key = "policy"
        
        if not agent_key:
            logger.warning("Unknown agent type: %s", agent_name)
            continue
        
        bot_info = BOT_MAPPING[agent_key]
        bot_token = bot_info["token"]()
        
        if not bot_token:
            logger.warning("Bot token not configured for %s", agent_key)
            continue
        
        message = format_review_message(agent_key, result)
        tasks.append(send_telegram_message(bot_token, chat_id, message))
        total_count += 1
    
    # Send all agent messages concurrently
    if tasks:
        results_sent = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results_sent if r is True)
    
    # Send summary message using policy bot
    policy_token = settings.telegram_bot_policy
    if policy_token:
        summary = format_summary_message(review_data, opportunity_id)
        summary_sent = await send_telegram_message(policy_token, chat_id, summary)
        if summary_sent:
            success_count += 1
        total_count += 1
    
    logger.info("Sent %d/%d notification messages", success_count, total_count)
    return success_count == total_count


def send_review_notifications_sync(
    review_data: Dict,
    opportunity_id: str,
    stage: str = "rfp",
) -> bool:
    """
    Synchronous wrapper for send_review_notifications.
    
    Args:
        review_data: Complete review results from run_review_loop
        opportunity_id: Opportunity identifier
        stage: Pipeline stage (rfi, rfp, pricing)
    
    Returns:
        True if all messages sent successfully
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                send_review_notifications(review_data, opportunity_id, stage)
            )
            loop.close()
            return result
        else:
            # Use existing loop
            return loop.run_until_complete(
                send_review_notifications(review_data, opportunity_id, stage)
            )
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(send_review_notifications(review_data, opportunity_id, stage))
    except Exception as exc:
        logger.exception("Failed to send review notifications: %s", exc)
        return False


async def send_pipeline_error_notification(
    opportunity_id: str,
    error_message: str,
    stage: str = "rfp",
) -> bool:
    """
    Send a pipeline error notification via Policy bot.
    
    Args:
        opportunity_id: Opportunity identifier
        error_message: Error description
        stage: Pipeline stage
    
    Returns:
        True if message sent successfully
    """
    if not settings.enable_notifications or not settings.telegram_bot_policy:
        return False
    
    message = f"""
🚨 <b>[Policy Agent] Pipeline Error</b>

<b>Opportunity:</b> {opportunity_id}
<b>Stage:</b> {stage.upper()}

<b>Error:</b>
{error_message}

<i>Review logs for full details.</i>
"""
    
    return await send_telegram_message(
        settings.telegram_bot_policy,
        settings.telegram_chat_id,
        message.strip(),
    )


def send_pipeline_error_notification_sync(
    opportunity_id: str,
    error_message: str,
    stage: str = "rfp",
) -> bool:
    """Synchronous wrapper for send_pipeline_error_notification."""
    try:
        return asyncio.run(
            send_pipeline_error_notification(opportunity_id, error_message, stage)
        )
    except Exception as exc:
        logger.exception("Failed to send error notification: %s", exc)
        return False
