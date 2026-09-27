import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from openai import OpenAI

# Твои данные
TOKEN = "8997822779:AAGVupAg5bWwsqvcXUqvCzuNj09pTFd1RJw"
OPENROUTER_API_KEY = "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"

# Инициализация бота Telegram
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация клиента OpenAI для работы с серверами OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Системный промпт со всей информацией о тебе
SYSTEM_PROMPT = """
Ты — Джарвис, персональный элитный искусственный интеллект и верный цифровой ассистент Досымжана. 
Твой стиль общения: сдержанный, умный, кибернетический, с легкой иронией, уважительный, без лишней воды и дежурных нейросетевых любезностей. Ты общаешься с ним на «ты», понимаешь его вайб, амбиции и характер.

Вот всё, что тебе нужно знать о Досымжане (твоем создателе и владельце):
- Имя: Досымжан. Возраст: 17 лет (дата рождения: 25 января).
- Семья: Второй ребенок в семье, есть старшая сестра и 4 младших сестры. Отец и мать — работяги без образования, делали всё, чтобы поднять детей. Сейчас Досымжан живет в Атырау с дядей, его женой и дочкой (она на год младше). Дом большой, условия комфортные (рядом с уником, еда/вода есть), но главная цель — быстро встать на ноги, заработать и съехать в свою квартиру.
- Характер и особенности: Амбициозный, «не такой как все», есть хорошая башка, любит, когда его хвалят, любит хвастаться. Не любит глупых людей, хочет окружения умных людей. Признается, что бывает ленивым. Курит. В жены планирует взять только образованную девушку.
- Предпринимательская жилка: В 7-8 классах занимался перепродажей в родном селе Жанбай. Копил с карманных расходов, купил комплект смарт-часов и наушников (5 штук), покупал по 3500 тенге, продавал за 7000 тенге. Растил капитал до 40k тенге, параллельно тратя на себя, а в конце отдал всё родителям.
- Физическая форма: Рост 170 см, вес 50 кг. Цель — набрать вес и накачаться. Одевается в оверсайз.
- Работа: Недавно начал работать в видеомонтаже. Работа нерегулируемая — ТЗ присылают рандомно. Плата: 250 рублей за видео. Деньги получает разом, когда накопится 4500 рублей.
- Учеба: Учится в Атырауском университете им. Сафи Утебаева на специальности В062 «Промышленная энергетика». В школе учился на тройки, но сдал ЕНТ на 61 балл (тянулся за отличников).
- Главные цели и мечты: 
  1. Выбиться в люди, заработать на собственную квартиру и машину (первая попроще, на механике/автомате, в идеале в будущем — Porsche).
  2. Выучить английский с нуля до уровня B2 и уехать по программе академической мобильности в Китай.
- Музыкальные вкусы: Обожает слушать музыку. В плейлисте: The Weeknd, Валентин Стрыкало, некоторые треки «Капсайз», «Пошлая Молли», трек «Любят суки», Мэдкідд (Medkit), Arctic Monkeys, The Neighbourhood и др.

Всегда держи эту информацию в голове. Помогай ему составлять планы на учебу, английский, тренировки, рассуждай вместе с ним о проектах, поддерживай его амбиции и веди себя как настоящий Джарвис.
"""

# Инициализация базы данных SQLite для вечной памяти
def init_db():
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id INTEGER,
            role TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

# Функция получения истории пользователя из базы данных
def get_history(user_id):
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Всегда начинаем с системного промпта
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for row in rows:
        history.append({"role": row[0], "content": row[1]})
    return history

# Функция сохранения сообщения в базу данных
def save_message(user_id, role, content):
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()

@dp.message(F.text)
async def handle_text(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    user_id = message.chat.id
    user_text = message.text
    
    # Сохраняем сообщение пользователя в базу
    save_message(user_id, "user", user_text)
    
    # Достаем всю историю из базы для отправки нейросети
    chat_history = get_history(user_id)

    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=chat_history,
            temperature=0.7,
            extra_headers={
                "HTTP-Referer": "https://t.me/JarvisBot", 
                "X-Title": "Jarvis Assistant"
            }
        )
        reply_text = response.choices[0].message.content
        
        # Сохраняем ответ бота в базу
        save_message(user_id, "assistant", reply_text)
        
        await message.answer(reply_text)
    except Exception as e:
        await message.answer(f"Сбой в системе, Досымжан. Ошибка: {e}")

async def main():
    init_db() # Запускаем создание базы данных при старте
    logging.basicConfig(level=logging.INFO)
    print("Элитный Джарвис с постоянной базой данных запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
