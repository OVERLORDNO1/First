"""Telegram interface — reach JARVIS from any browser or phone.

Requires the ``telegram`` extra (``pip install jarvis-assistant[telegram]``),
a bot token from @BotFather, and your numeric Telegram user ID. Only the
allowlisted user ID is ever answered; everyone else is ignored.

The bot uses long polling (outbound connections only), so no public endpoint
or open port is required wherever JARVIS is hosted.
"""

from __future__ import annotations

import asyncio
import logging

from ..agent import Jarvis
from ..scheduler import ReminderService

log = logging.getLogger(__name__)


def run_telegram(jarvis: Jarvis) -> None:
    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            ContextTypes,
            MessageHandler,
            filters,
        )
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Telegram support is not installed. Run: pip install 'jarvis-assistant[telegram]'"
        ) from exc

    token = jarvis.settings.telegram_bot_token
    allowed_id = jarvis.settings.telegram_allowed_user_id
    if not token or not allowed_id:
        raise SystemExit(
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID to use the Telegram interface."
        )

    app = Application.builder().token(token).build()

    async def handle(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.effective_user.id != allowed_id:
            log.warning(
                "ignoring message from unauthorized user %s",
                getattr(update.effective_user, "id", "?"),
            )
            return
        if update.message is None or not update.message.text:
            return
        # converse() is synchronous — run it off the event loop.
        reply = await asyncio.to_thread(jarvis.converse, update.message.text)
        await update.message.reply_text(reply)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    def notify(text: str) -> None:
        """Deliver scheduler events (reminders, briefings) as Telegram messages."""
        loop = getattr(app, "_notify_loop", None)
        if loop is None or not loop.is_running():
            log.warning("no running event loop; dropping notification: %s", text)
            return
        asyncio.run_coroutine_threadsafe(
            app.bot.send_message(chat_id=allowed_id, text=text), loop
        )

    service = ReminderService(
        jarvis.store,
        notify,
        poll_seconds=jarvis.settings.reminder_poll_seconds,
        briefing_time=jarvis.settings.briefing_time,
        briefing=lambda: jarvis.converse("Give me my daily briefing."),
    )

    async def post_init(application: Application) -> None:
        application._notify_loop = asyncio.get_running_loop()  # noqa: SLF001
        service.start()
        await application.bot.send_message(chat_id=allowed_id, text=jarvis.greeting())

    async def post_shutdown(_: Application) -> None:
        service.stop()

    app.post_init = post_init
    app.post_shutdown = post_shutdown
    log.info("Telegram interface starting (long polling)…")
    app.run_polling()
