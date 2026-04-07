import os
from openai import OpenAI
from dotenv import load_dotenv

# M4: Limitar historial para evitar token creep
MAX_HISTORY_LENGTH = 50  # Últimos 50 mensajes (además del system prompt)


class SimulatedStudent:
    """Simulates a student with a specific persona in a group chat."""
    
    def __init__(self, name, system_prompt, model_name="llama-3.1-8b-instant"):
        """
        Initialize a simulated student.
        
        Args:
            name: Student's name
            system_prompt: System prompt defining the student's personality and knowledge
            model_name: LLM model to use (default: Groq's llama-3.1-8b-instant)
        """
        load_dotenv()  # Load variables from .env
        
        self.name = name
        self.system_prompt = system_prompt
        self.model = model_name
        self.history = [{"role": "system", "content": system_prompt}]
        self.max_history = MAX_HISTORY_LENGTH
        
        # Initialize Groq client (free tier with good speed)
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )
    
    def receive_message(self, sender, message):
        """
        Add a message from another participant to the chat history.
        
        Implements sliding window to prevent token creep: mantiene último N mensajes
        además del system prompt al inicio.
        
        Args:
            sender: Name of the person sending the message
            message: Content of the message
        """
        self.history.append({"role": "user", "content": f"{sender}: {message}"})
        
        # M4: VENTANA DESLIZANTE - Mantener historial bajo límite
        # Nunca eliminar el system prompt (position 0)
        system_prompt = self.history[0]
        other_messages = self.history[1:]
        
        if len(other_messages) > self.max_history:
            # Mantener solo los últimos N mensajes
            other_messages = other_messages[-self.max_history:]
            self.history = [system_prompt] + other_messages
            # Silenciosamente mantener límite, sin avisar cada vez
    
    def generate_response(self):
        """
        Generate a response to the current conversation context.
        
        Returns:
            The student's response as a string
            
        Raises:
            Exception: If LLM call fails after retries
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.3,
            )
            
            response_content = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": response_content})
            
            return response_content
        except Exception as e:
            # Log error pero no crash - devolver silencio
            print(f"[WARNING] Error en {self.name}.generate_response(): {e}")
            fallback = "[THOUGHT]Error en LLM[MESSAGE][SILENCE]"
            self.history.append({"role": "assistant", "content": fallback})
            return fallback