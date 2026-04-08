import os
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai


class GeminiOpenAIWrapper:
    """
    Simula la interfaz de OpenAI (chat.completions.create) usando el SDK nativo de Gemini.
    Esto permite que los estudiantes y el tutor sigan funcionando sin cambios.
    """
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
    
    class Chat:
        class Completions:
            def create(self, model, messages, temperature=0.3, max_tokens=None):
                # Convertir formato de mensajes de OpenAI a Gemini
                gemini_model = genai.GenerativeModel(model)
                
                # Extraer system prompt y mensajes de usuario
                chat_history = []
                system_instruction = None
                
                for m in messages:
                    if m["role"] == "system":
                        system_instruction = m["content"]
                    elif m["role"] == "user":
                        chat_history.append({"role": "user", "parts": [m["content"]]})
                    elif m["role"] == "assistant":
                        chat_history.append({"role": "model", "parts": [m["content"]]})
                
                # Reiniciar modelo con instrucción del sistema si existe
                if system_instruction:
                    gemini_model = genai.GenerativeModel(
                        model_name=model,
                        system_instruction=system_instruction
                    )
                
                # Gemini usa historial + último mensaje
                # Pero aquí simulamos .create() que suele pasar todo el historial
                # Usaremos la última parte como el mensaje actual
                if chat_history:
                    last_msg = chat_history.pop()["parts"][0]
                else:
                    last_msg = ""
                    
                chat = gemini_model.start_chat(history=chat_history)
                response = chat.send_message(
                    last_msg, 
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                
                # Simular estructura de respuesta de OpenAI
                class MockResponse:
                    class Choice:
                        class Message:
                            def __init__(self, content):
                                self.content = content
                        def __init__(self, content):
                            self.message = self.Message(content)
                    def __init__(self, content):
                        self.choices = [self.Choice(content)]
                
                return MockResponse(response.text)

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.chat = self.Chat()


class LLMClientManager:
    """
    Manages multiple API keys and handles client/model rotation.
    Supports Groq (OpenAI) and Gemini (Native SDK via Wrapper).
    """
    def __init__(self):
        load_dotenv()
        self.configs = self._load_configs()
        self.current_index = 0
        
        if not self.configs:
            raise ValueError("No se encontraron llaves de API.")

    def _load_configs(self):
        configs = []
        
        # 1. Groq
        groq_keys = [os.getenv("GROQ_API_KEY")]
        i = 1
        while True:
            k = os.getenv(f"GROQ_API_KEY_{i}")
            if not k: break
            if k not in groq_keys: groq_keys.append(k)
            i += 1
        
        for k in groq_keys:
            if k:
                configs.append({
                    "provider": "groq",
                    "client": OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k),
                    "model": "llama-3.1-8b-instant"
                })
        
        # 2. Gemini (Usando Wrapper Nativo)
        gemini_keys = [os.getenv("GEMINI_API_KEY")]
        i = 1
        while True:
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if not k: break
            if k not in gemini_keys: gemini_keys.append(k)
            i += 1
            
        for k in gemini_keys:
            if k:
                configs.append({
                    "provider": "gemini",
                    "client": GeminiOpenAIWrapper(api_key=k),
                    "model": "gemini-flash-latest" # Alias al modelo estable más reciente
                })
        # 3. OpenRouter (OpenAI-compatible)
        openrouter_keys = [os.getenv("OPENROUTER_API_KEY"), os.getenv("OPEN_ROUTER_API_KEY")]
        i = 1
        while True:
            k = os.getenv(f"OPENROUTER_API_KEY_{i}") or os.getenv(f"OPEN_ROUTER_API_KEY_{i}")
            if not k: break
            if k not in openrouter_keys: openrouter_keys.append(k)
            i += 1
            
        for k in openrouter_keys:
            if k:
                configs.append({
                    "provider": "openrouter",
                    "client": OpenAI(base_url="https://openrouter.ai/api/v1", api_key=k),
                    "model": "qwen/qwen-2.5-72b-instruct"
                })
            
        return configs

    def get_active_config(self) -> dict:
        return self.configs[self.current_index]

    def rotate_key(self) -> bool:
        if self.current_index < len(self.configs) - 1:
            self.current_index += 1
            config = self.get_active_config()
            print(f"[API] Switching to {config['provider'].upper()} ({config['model']})")
            return True
        return False


_manager = None

def get_llm_client_manager() -> LLMClientManager:
    global _manager
    if _manager is None:
        _manager = LLMClientManager()
    return _manager

def get_groq_client_manager():
    return get_llm_client_manager()

def get_groq_client() -> OpenAI:
    return get_llm_client_manager().get_active_config()["client"]
