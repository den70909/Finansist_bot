import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

import os
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "db.sqlite"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS work (
            id INTEGER PRIMARY KEY,
            usdt REAL DEFAULT 0,
            rub REAL DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            comment TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS savings (
            amount REAL DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT,
            amount REAL,
            currency TEXT
        )""")

        await db.commit()


# 💼 ДОБАВИТЬ РАБОТУ
@dp.message(Command("work"))
async def add_work(message: types.Message):
    text = message.text.replace("/work", "").strip()

    try:
        parts = text.split()
        usdt = float(parts[0])
        rub = float(parts[1]) if len(parts) > 1 else 0
    except:
        await message.answer("Формат: /work 100 9000")
        return

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT usdt, rub FROM work WHERE id=1")
        row = await cur.fetchone()

        if row:
            new_usdt = row[0] + usdt
            new_rub = row[1] + rub
            await db.execute("UPDATE work SET usdt=?, rub=? WHERE id=1",
                             (new_usdt, new_rub))
        else:
            await db.execute("INSERT INTO work(id, usdt, rub) VALUES(1, ?, ?)",
                             (usdt, rub))

        await db.commit()

    await message.answer(f"💼 Добавлено: {usdt} USDT ({rub} ₽)")


# 💸 РАСХОД
@dp.message(Command("expense"))
async def add_expense(message: types.Message):
    text = message.text.replace("/expense", "").strip()

    try:
        parts = text.split(maxsplit=1)
        amount = float(parts[0])
        comment = parts[1] if len(parts) > 1 else ""
    except:
        await message.answer("Формат: /expense 1200 еда")
        return

    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO expenses(amount, comment) VALUES(?, ?)",
                         (amount, comment))
        await db.commit()

    await message.answer(f"💸 Расход: {amount} ₽")


# 🐷 НАКОПЛЕНИЯ
@dp.message(Command("save"))
async def save_money(message: types.Message):
    amount = float(message.text.replace("/save", "").strip())

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT amount FROM savings")
        row = await cur.fetchone()

        if row:
            new = row[0] + amount
            await db.execute("UPDATE savings SET amount=?", (new,))
        else:
            await db.execute("INSERT INTO savings(amount) VALUES(?)", (amount,))

        await db.commit()

    await message.answer(f"🐷 Отложено: {amount} ₽")


# 📊 БАЛАНС
@dp.message(Command("balance"))
async def balance(message: types.Message):
    async with aiosqlite.connect(DB) as db:
        work = await (await db.execute("SELECT usdt, rub FROM work WHERE id=1")).fetchone()
        savings = await (await db.execute("SELECT amount FROM savings")).fetchone()

    usdt = work[0] if work else 0
    rub_work = work[1] if work else 0
    save = savings[0] if savings else 0

    await message.answer(
        f"""📊 Баланс:

💼 Работа:
- {usdt} USDT
- {rub_work} ₽

🐷 Накопления: {save} ₽
"""
    )


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
