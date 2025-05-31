import os
import asyncio
from mistralai.client import MistralClient

class MistralAI:
    def __init__(self):
        self.client = MistralClient(api_key=os.getenv('MISTRAL_API_KEY'))
        self.model = "mistral-large-latest"
        self.system_prompt = "Ты полезный ассистент, отвечай кратко и по делу."

    def format_messages(self, messages):
        formatted = []
        if not messages or messages[0].get('role') != 'system':
            formatted.append({"role": "system", "content": self.system_prompt})
        for msg in messages:
            if msg.get('role') in ['user', 'assistant', 'system']:
                formatted.append({"role": msg['role'], "content": msg['content']})
        return formatted

    async def get_response(self, messages):
        try:
            formatted_messages = self.format_messages(messages)
            # Новый клиент - вызов sync, оборачиваем в to_thread для async
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model,
                messages=formatted_messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in Mistral API call: {e}")
            raise
