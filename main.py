"""
Telegram bot with Guest Mode + Rich Messages support (Bot API 10.0 / 10.1)
Requires: pip install "aiogram>=3.28" --break-system-packages

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
from aiogram.types import Message
from aiogram.methods import AnswerGuestQuery

# Rich message building blocks (aiogram's typed wrappers around the
# InputRichMessage / RichBlock schema introduced in Bot API 10.1)
from aiogram.types import (
    InputRichMessage,
    RichBlockHeading,
    RichBlockParagraph,
    RichBlockList,
    RichBlockListItem,
    RichBlockCode,
)

router = Router()


def build_welcome_rich_message() -> InputRichMessage:
    """A structured rich message: heading, paragraph, list, code block."""
    return InputRichMessage(
        blocks=[
            RichBlockHeading(level=2, text="Hey, I'm online 👋"),
            RichBlockParagraph(
                text=(
                    "I can answer you here even though I'm not a member "
                    "of this chat -- that's Guest Mode."
                )
            ),
            RichBlockList(
                ordered=False,
                items=[
                    RichBlockListItem(text="Ask me anything, one reply per mention"),
                    RichBlockListItem(text="No chat history access (guest limitation)"),
                    RichBlockListItem(text="Add me to the chat for full conversations"),
                ],
            ),
            RichBlockCode(language="text", code="/start  -- see this menu again"),
        ]
    )


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot) -> None:
    """Normal /start in a regular chat where the bot IS a member."""
    rich = build_welcome_rich_message()
    await bot.send_rich_message(chat_id=message.chat.id, rich_message=rich)


@router.guest_message()
async def guest_handler(message: Message, bot: Bot) -> None:
    """
    Fired when someone @-mentions the bot in a chat it's NOT a member of.
    You get exactly one reply via answer_guest_query -- treat it as
    stateless, no history, no follow-ups.
    """
    guest_query_id = message.guest_query_id
    caller = message.guest_bot_caller_user

    rich = InputRichMessage(
        blocks=[
            RichBlockHeading(level=3, text=f"Hi {caller.first_name} 👋"),
            RichBlockParagraph(
                text=f"You asked: “{message.text}”. Here's a structured answer:"
            ),
            RichBlockList(
                ordered=True,
                items=[
                    RichBlockListItem(text="This reply is one-shot (guest mode limit)"),
                    RichBlockListItem(text="Add me to the chat for a real conversation"),
                ],
            ),
        ]
    )

    await bot(
        AnswerGuestQuery(
            guest_query_id=guest_query_id,
            rich_message=rich,
        )
    )


async def main() -> None:
    token = os.environ["8751987231:AAGxS58VSYSL8_3FUSBkHP6DAjZKamQuZ1M"]
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
