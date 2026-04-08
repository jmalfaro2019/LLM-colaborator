import os
from openai import OpenAI
from dotenv import load_dotenv

# M4: Limitar historial para evitar token creep
MAX_HISTORY_LENGTH = 50  # Últimos 50 mensajes (además del system prompt)


class SimulatedTutor:
    """Simulates a tutor that facilitates PBL discussions."""
    
    def __init__(self, name, system_prompt, system_type="B", model_name="llama-3.1-8b-instant"):
        """
        Initialize a simulated tutor.
        """
        from llm_client import get_groq_client_manager
        
        self.name = name
        self.system_prompt = system_prompt
        self.system_type = system_type
        self.model = model_name
        self.history = [{"role": "system", "content": system_prompt}]
        self.pending_instruction = None
        self.max_history = MAX_HISTORY_LENGTH
        self.manager = get_groq_client_manager()
    
    def receive_message(self, sender, message):
        # ... (keep existing implementation)
        if sender == "System":
            self.pending_instruction = message
        else:
            self.history.append({"role": "user", "content": f"{sender}: {message}"})
            
            system_prompt = self.history[0]
            other_messages = self.history[1:]
            
            if len(other_messages) > self.max_history:
                other_messages = other_messages[-self.max_history:]
                self.history = [system_prompt] + other_messages

    def generate_response(self):
        """
        Generate a response with automatic API key rotation on rate limits.
        """
        while True:
            config = self.manager.get_active_config()
            client = config["client"]
            model = config["model"]
            
            try:
                messages_to_send = self.history.copy()
                if self.pending_instruction:
                    messages_to_send.append({"role": "system", "content": self.pending_instruction})
                    
                response = client.chat.completions.create(
                    model=model,
                    messages=messages_to_send,
                    temperature=0.3,
                )
                
                response_content = response.choices[0].message.content
                self.history.append({"role": "assistant", "content": response_content})
                self.pending_instruction = None
                
                return response_content
            except Exception as e:
                error_msg = str(e)
                if any(x in error_msg.lower() for x in ["429", "rate_limit", "resource_exhausted", "resourceexhausted"]):
                    if self.manager.rotate_key():
                        print(f"[RETRY] Tutor retrying with next API key/provider...")
                        continue
                    else:
                        print(f"[FATAL] Tutor: All API keys exhausted.")
                        raise e
                else:
                    print(f"[ERROR] Tutor: {error_msg}")
                    raise e