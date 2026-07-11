"""
Telegram bot with Guest Mode + Rich Messages support (Bot API 10.0 / 10.1)
Requires: pip install "aiogram>=3.29" --break-system-packages

Setup in BotFather before running:
  1. /mybots -> your bot -> Bot Settings -> Guest Mode -> Enable
     (this lets Telegram deliver `guest_message` updates when someone
      @-mentions your bot in a chat it isn't a member of)
  2. Nothing extra needed to enable Rich Messages -- any bot on API 10.1+
     can call sendRichMessage.

Env var required: BOT_TOKEN
"""

import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InputRichMessage

router = Router()


def welcome_markdown(name: str = "there") -> str:
    """
    Rich messages are authored as one HTML or Markdown string -- Telegram
    parses headings, lists, code fences, etc. out of it server-side.
    (Not a tree of block objects -- that was wrong in an earlier draft.)
    """
    return (
        f"## Hey {name} 👋\n\n"
        "I can answer you here even though I'm not a member of this chat "
        "-- that's **Guest Mode**.\n\n"
        "- Ask me anything, one reply per mention\n"
        "- No chat history access (guest limitation)\n"
        "- Add me to the chat for full conversations\n\n"
        "```\n/start -- see this menu again\n```"
    )


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot) -> None:
    """Normal /start in a regular chat where the bot IS a member."""
    rich = InputRichMessage(markdown=welcome_markdown(message.from_user.first_name))
    await bot.send_rich_message(chat_id=message.chat.id, rich_message=rich)


@router.guest_message()
async def guest_handler(message: Message, bot: Bot) -> None:
    """
    Fired when someone @-mentions the bot in a chat it's NOT a member of.
    You get exactly one reply via answer_guest_query -- treat it as
    stateless, no history, no follow-ups.
    """
    caller = message.guest_bot_caller_user
    reply_md = (
        f"### Hi {caller.first_name} 👋\n\n"
        f"You asked: *{message.text}*. Here's a structured answer:\n\n"
        "1. This reply is one-shot (guest mode limit)\n"
        "2. Add me to the chat for a real conversation\n"
    )
    rich = InputRichMessage(markdown=reply_md)

    # Shortcut method -- equivalent to calling AnswerGuestQuery directly
    await message.answer_guest_query(rich_message=rich)


async def main() -> None:
    token = os.environ["BOT_TOKEN"]
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
