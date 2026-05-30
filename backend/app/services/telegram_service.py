import asyncio
import logging
import os
import threading

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.db.database import SessionLocal
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

_bot_thread: threading.Thread | None = None


async def _start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm Yuno AI Agent.\n\n"
        "Send me any task and I'll run a multi-agent workflow to analyze it.\n\n"
        "Example: *Analyze Tesla's market position in 2025*",
        parse_mode="Markdown",
    )


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id

    await update.message.reply_text("⏳ Running multi-agent workflow... This may take 30-60 seconds.")
    logger.info(f"Telegram task received: {user_message[:100]}")

    db = SessionLocal()
    try:
        workflows = WorkflowService.get_workflows(db)
        workflow = workflows[0] if workflows else None

        if workflow is None:
            from app.models.workflow import Workflow
            workflow = Workflow(id=0, name="Telegram Workflow", graph={})

        from app.runtime.runtime_engine import RuntimeEngine
        execution = RuntimeEngine.execute_workflow(db, workflow, input_task=user_message)

        output = execution.final_output or "No output generated."
        if len(output) > 3800:
            output = output[:3800] + "\n\n_[Output truncated — see web UI for full report]_"

        tokens = execution.tokens_used or 0
        cost = execution.cost_usd or 0.0

        reply = (
            f"✅ Workflow Complete\n\n"
            f"{output}\n\n"
            f"---\n"
            f"Tokens: {tokens} | Cost: ${cost:.4f}"
        )

        await context.bot.send_message(chat_id=chat_id, text=reply)

    except Exception as e:
        logger.error(f"Telegram handler error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Workflow failed: {str(e)[:200]}\n\nCheck the web UI for details.",
        )
    finally:
        db.close()


async def _run_bot_async(token: str):
    """
    Runs the bot using low-level updater API — avoids signal handler
    registration which is only allowed from the main thread.
    """
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", _start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message))

    await app.initialize()
    await app.updater.start_polling(drop_pending_updates=True)
    await app.start()

    logger.info("Telegram bot polling started (thread-safe mode).")

    # Keep running until the event loop is stopped
    try:
        await asyncio.Event().wait()  # Block forever
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def _run_in_thread(token: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_bot_async(token))
    except Exception as e:
        logger.error(f"Telegram bot thread exited: {e}")
    finally:
        loop.close()


def start_bot():
    """Starts the Telegram bot in a background daemon thread."""
    global _bot_thread

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token or token == "your_telegram_bot_token_here":
        logger.warning("TELEGRAM_BOT_TOKEN not configured — Telegram bot disabled.")
        return

    if _bot_thread and _bot_thread.is_alive():
        return

    _bot_thread = threading.Thread(target=_run_in_thread, args=(token,), daemon=True)
    _bot_thread.start()
    logger.info("Telegram bot thread started.")