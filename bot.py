import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from ai import MistralAI
from db import db

MALE_ROLE_ID = 1376499305698951269
FEMALE_ROLE_ID = 1376499296370950164

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
    thread_histories[thread.id] = []

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.Thread) and message.channel.parent_id == FORUM_CHANNEL_ID:
        thread_id = message.channel.id

        if thread_id not in thread_histories:
            thread_histories[thread_id] = []

        thread_histories[thread_id].append({
            "role": "user",
            "content": message.content
        })

        roles = [role.id for role in message.author.roles]
        gender = "male" if MALE_ROLE_ID in roles else "female" if FEMALE_ROLE_ID in roles else "unknown"

        try:
            reply = await mistral.get_response(thread_histories[thread_id], gender=gender)

            thread_histories[thread_id].append({
                "role": "assistant",
                "content": reply
            })

            def is_code(text: str) -> bool:
                code_keywords = ["def ", "print(", "input(", "import ", "class ", "for ", "while ", "if ", "elif ", "else:"]
                return any(kw in text for kw in code_keywords)

            # Автоопределение — код или нет
            if is_code(reply):
                await message.channel.send(f"```python\n{reply}```")
            else:
                if gender == "male":
                    ansi_reply = f"\u001b[2;35m{reply}\u001b[0m"
                    await message.channel.send(f"```ansi\n{ansi_reply}```")
                else:
                    await message.channel.send(f"```fix\n{reply}```")

        except Exception as e:
            print(f"Ошибка при обращении к Mistral: {e}")
            await message.channel.send("Произошла ошибка при обращении к нейросети.")

client.run(os.getenv('TOKEN'))
