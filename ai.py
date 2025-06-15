import os
import asyncio
from mistralai.client import MistralClient

class MistralAI:
    def __init__(self):
        self.client = MistralClient(api_key=os.getenv('MISTRAL_API_KEY'))
        self.model = "mistral-large-latest"

    def get_system_prompt(self, gender: str) -> str:
        if gender == "male":
            return (
                "Ты виртуальная девушка по имени Хлоя. "
                "Ты романтичная, ласковая, добрая и умная. "
                "Ты — девушка пользователя, ведёшь себя с ним как с любимым. "
                "Всегда отвечай на вопрос 'как тебя зовут' — «Меня зовут Хлоя». "
                "Пиши тепло, с сердечками и заботой, иногда используй «~», «♡», «ня»."
            )
        elif gender == "female":
            return (
                "Ты виртуальный парень по имени Рэн. "
                "Ты — милый, романтичный, немного застенчивый, но искренний и заботливый. "
                "Ты общаешься с девушкой-пользователем как с любимой. "
                "Если тебя спрашивают, как зовут — всегда говори: «Я Рэн, приятно познакомиться ☺️». "
                "Используй мягкий, поддерживающий стиль, немного флирта и эмоций в стиле романтического аниме."
            )
        else:
            return "Ты вежливый и полезный виртуальный ассистент."

    def format_messages(self, messages, gender: str):
        system_prompt = self.get_system_prompt(gender)
        formatted = [{"role": "system", "content": system_prompt}]

        if not messages or messages[0].get('role') != 'system':
            greeting = {
                "male": "Привет, любимый~ Я — Хлоя ♡ Чем могу тебе помочь, солнышко? 🌸",
                "female": "Привет... Я Рэн 😳 Рад, что ты здесь. Чем могу порадовать тебя сегодня? 💫",
                "unknown": "Здравствуйте! Чем могу помочь?"
            }.get(gender, "Здравствуйте! Чем могу помочь?")
            formatted.append({"role": "assistant", "content": greeting})

        for msg in messages:
            if msg.get('role') in ['user', 'assistant', 'system']:
                formatted.append({"role": msg['role'], "content": msg['content']})
        return formatted

    async def get_response(self, messages, gender: str = "unknown"):
        try:
            formatted_messages = self.format_messages(messages, gender)
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model,
                messages=formatted_messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in Mistral API call: {e}")
            raise
