import os
from openai import OpenAI
from dotenv import load_dotenv


class SimulatedTutor:
    """Simulates a tutor that facilitates PBL discussions."""
    
    def __init__(self, name, system_prompt, model_name="llama-3.1-8b-instant"):
        """
        Initialize a simulated tutor.
        
        Args:
            name: Tutor's name
            system_prompt: System prompt defining the tutor's role and approach
            model_name: LLM model to use (default: Groq's llama-3.1-8b-instant)
        """
        load_dotenv()  # Load variables from .env
        
        self.name = name
        self.system_prompt = system_prompt
        self.model = model_name
        self.history = [{"role": "system", "content": system_prompt}]
        
        # Initialize Groq client (free tier with good speed)
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )
    
    def receive_message(self, sender, message):
        """
        Add a message from a participant to the chat history.
        
        Args:
            sender: Name of the person sending the message
            message: Content of the message
        """
        self.history.append({"role": "user", "content": f"{sender}: {message}"})
    
    def generate_response(self):
        """
        Generate a tutor response to the current conversation context.
        
        Returns:
            The tutor's response as a string
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.3,
        )
        
        response_content = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": response_content})
        
        return response_content