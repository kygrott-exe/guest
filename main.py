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
import re

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, InputRichMessage

router = Router()

# ---------------------------------------------------------------------------
# Your fixed posts live here. Add as many as you want -- the key is what
# people type after /post (e.g. "/post promo" -> the "promo" entry below).
# Each value is Markdown; Telegram renders headings/lists/bold/code from it.
# ---------------------------------------------------------------------------
POSTS: dict[str, str] = {
    "promo": (
        "## 🎉 Our Weekly Promo\n\n"
        "- 20% off all plans this week\n"
        "- Use code **SAVE20** at checkout\n"
        "- Offer ends Sunday\n\n"
        "```\n/post promo -- share this again\n```"
    ),
    "rules": (
        "## 📋 Group Rules\n\n"
        "1. Be respectful\n"
        "2. No spam or self-promo without permission\n"
        "3. Keep discussion on-topic\n"
    ),
    # Add more named posts here.
}
DEFAULT_POST = "promo"  # used when someone runs /post with no name


def resolve_post(name: str | None) -> str:
    """Look up a post by name, falling back to DEFAULT_POST, then a helper message."""
    key = (name or DEFAULT_POST).strip().lower()
    if key in POSTS:
        return POSTS[key]
    available = ", ".join(sorted(POSTS))
    return f"⚠️ No post named **{key}**.\n\nAvailable posts: {available}"


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


@router.message(Command("post"))
async def post_handler(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    /post           -> sends the DEFAULT_POST
    /post promo     -> sends POSTS["promo"]
    Works in any chat the bot is a member of, including groups.
    """
    post_name = command.args  # text after "/post ", or None
    rich = InputRichMessage(markdown=resolve_post(post_name))
    await bot.send_rich_message(chat_id=message.chat.id, rich_message=rich)


def extract_guest_command_args(text: str, command: str) -> str | None:
    """
    Guest-mode messages arrive as the raw mention text, e.g.
    "@yourbot /post promo" or "/post promo@yourbot". Strip the mention
    and the command name, return whatever's left (or None if the command
    isn't present).
    """
    if not text:
        return None
    # Drop any @mentions anywhere in the text (bot's own handle included).
    cleaned = re.sub(r"@\w+", "", text).strip()
    pattern = rf"^/{command}(?:\s+(.*))?$"
    match = re.match(pattern, cleaned, flags=re.IGNORECASE)
    if not match:
        return None
    # Command was present -- return its args, or "" if none were given
    # (as opposed to None, which means the command wasn't present at all).
    return match.group(1) or ""


@router.guest_message()
async def guest_handler(message: Message, bot: Bot) -> None:
    """
    Fired when someone @-mentions the bot in a chat it's NOT a member of.
    You get exactly one reply via answer_guest_query -- treat it as
    stateless, no history, no follow-ups.
    """
    post_args = extract_guest_command_args(message.text or "", "post")

    if post_args is not None:
        # "@bot /post promo" in a group the bot isn't in -> post the preset
        rich = InputRichMessage(markdown=resolve_post(post_args))
        await message.answer_guest_query(rich_message=rich)
        return

    # Fallback: anything else mentioned to the bot gets the generic welcome
    caller = message.guest_bot_caller_user
    reply_md = (
        f"### Hi {caller.first_name} 👋\n\n"
        f"You asked: *{message.text}*. Here's a structured answer:\n\n"
        "1. This reply is one-shot (guest mode limit)\n"
        "2. Try `/post promo` or `/post rules` to share a fixed post\n"
        "3. Add me to the chat for a real conversation\n"
    )
    rich = InputRichMessage(markdown=reply_md)
    await message.answer_guest_query(rich_message=rich)


async def main() -> None:
    token = os.environ["BOT_TOKEN"]
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
