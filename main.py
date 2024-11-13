import asyncio
import logging
import sys
from collections.abc import Iterator
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hbold

# Bot token can be obtained via https://t.me/BotFather
TOKEN: str = getenv("STRESS_BOT_TOKEN") or ""
assert TOKEN != ""

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

with open("dict.txt", encoding="utf-8") as f:
    _dict = set((line.strip() for line in f))


def _read_words() -> Iterator[str]:
    while True:
        for w in _dict:
            yield w


wrds = _read_words()
VOWELS = "уеыаоэяиюё"


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if not message.from_user:
        return
    await message.answer(
        f"Даров, {hbold(message.from_user.full_name)}!\n\n"
        "Я бот, созданный Семёном для того, чтобы ты выучил ударения!"
        "Нажми /play для начала игры")


@dp.message(Command("play"))
async def play_handler(msg: types.Message):
    if not msg.from_user:
        return
    score[msg.from_user.id] = 0
    await msg.reply("Начинаем игру!")
    await suggest(msg)


async def suggest(msg: types.Message):
    if not msg.from_user:
        return
    w = _remove_parens(next(wrds))
    prev[msg.from_user.id] = w
    kb = ReplyKeyboardBuilder()
    for nw in _word_variants(w):
        kb.button(text=nw)
    sz = [1 for _ in range(len(list(kb.buttons)))]
    kb.adjust(*sz)
    await msg.reply(f"<i>Слово</i>: {w.lower()}", reply_markup=kb.as_markup())


def _remove_parens(s: str) -> str:
    if "(" not in s:
        return s
    return s[:s.find("(") - 1]


def _word_variants(word: str) -> Iterator[str]:
    word = word.lower()
    for i in range(len(word)):
        if word[i] in VOWELS:
            yield word[:i] + word[i].upper() + word[i + 1:]


@dp.message(Command("/quiz"))
async def quiz() -> None:
    pass


score = {}
prev = {}


@dp.message()
async def msg_handler(msg: types.Message) -> None:
    if not msg.from_user:
        return

    if msg.from_user.id not in score:
        await msg.reply("Начни игру, брат, /play")
        return

    choice = msg.text
    right = prev[msg.from_user.id]

    if not choice:
        await msg.reply("Брат, никаких стикеров, только текст /play")
        return

    if choice == right:
        score[msg.from_user.id] += 1
        await msg.reply("🤝 Верно")
        await suggest(msg)
        return

    sc = score[msg.from_user.id]
    await msg.reply(
        f"🐈 Не Верно ({right} - правильный)\n\nВаш результат: {sc}\n\n /play")
    del prev[msg.from_user.id]
    del score[msg.from_user.id]


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API
    # calls
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
