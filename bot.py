import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from ai import MistralAI
from db import db

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

mistral = MistralAI()
MODEL = "mistral-large-latest"
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID', 0))

thread_histories = {}

@client.event
async def on_ready():
    print(f'✅ Бот запущен как {client.user}')
    db.init_db()

@client.event
async def on_thread_create(thread):
    if thread.parent_id != FORUM_CHANNEL_ID:
        return
    thread_histories[thread.id] = [{
        "role": "system",
        "content": "Ты полезный ассистент, отвечай кратко и по делу."
    }]

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.Thread) and message.channel.parent_id == FORUM_CHANNEL_ID:
        thread_id = message.channel.id

        if thread_id not in thread_histories:
            thread_histories[thread_id] = [{
                "role": "system",
                "content": "Ты полезный ассистент, отвечай кратко и по делу."
            }]

        thread_histories[thread_id].append({
            "role": "user",
            "content": message.content
        })

        try:
            # Используем асинхронный метод из класса
            reply = await mistral.get_response(thread_histories[thread_id])

            thread_histories[thread_id].append({
                "role": "assistant",
                "content": reply
            })

            # Ограничиваем историю
            if len(thread_histories[thread_id]) > 10:
                thread_histories[thread_id] = [thread_histories[thread_id][0]] + thread_histories[thread_id][-9:]

            await message.channel.send(reply)

        except Exception as e:
            print(f"Ошибка при обращении к Mistral: {e}")
            await message.channel.send("Произошла ошибка при обращении к нейросети.")

client.run(os.getenv('TOKEN'))
