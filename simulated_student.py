import os
from openai import OpenAI
from dotenv import load_dotenv

class SimulatedStudent:
    def __init__(self, name, persona, model_name="llama-3.1-8b-instant"):
        # We use Groq as an example due to its speed in the free tier
        load_dotenv()  # Load variables from .env
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1", 
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.name = name
        self.persona = persona
        self.model = model_name
        self.history = [{"role": "system", "content": persona}]

    def receive_message(self, sender, message):
        self.history.append({"role": "user", "content": f"{sender}: {message}"})

    def generate_response(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.3,
        )
        msg_content = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": msg_content})
        return msg_content