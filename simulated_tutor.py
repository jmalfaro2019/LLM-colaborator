import os
from openai import OpenAI
from dotenv import load_dotenv


class SimulatedTutor:
    """Simulates a tutor that facilitates PBL discussions."""
    
    def __init__(self, name, system_prompt, system_type="B", model_name="llama-3.1-8b-instant"):
        """
        Initialize a simulated tutor.
        
        Args:
            name: Tutor's name
            system_prompt: System prompt defining the tutor's pedagogy
            system_type: "A" (Transactivity-based) or "B" (Activity-based)
            model_name: LLM model to use
        """
        load_dotenv()
        
        self.name = name
        self.system_prompt = system_prompt
        self.system_type = system_type
        self.model = model_name
        self.history = [{"role": "system", "content": system_prompt}]
        self.pending_instruction = None  # Stores temporary system instructions from the orchestrator
        
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )
    
    def receive_message(self, sender, message):
        """
        Add a message from a participant to the chat history.
        
        Args:
            sender: Name of the sender
            message: Content of the message
        """
        # If the message comes from the System (Orchestrator), save it as temporary instruction
        if sender == "System":
            self.pending_instruction = message
        else:
            # If it's a normal student, it stays in permanent history
            self.history.append({"role": "user", "content": f"{sender}: {message}"})
    
    def generate_response(self):
        """
        Generate a tutor response to the current conversation context.
        
        Returns:
            The tutor's response as a string
        """
        # Create a temporary copy of the history for this call
        messages_to_send = self.history.copy()
        
        # If the orchestrator injected an instruction, add it now
        if self.pending_instruction:
            messages_to_send.append({"role": "system", "content": self.pending_instruction})
            self.pending_instruction = None  # Clear the instruction after using it
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages_to_send,
            temperature=0.3,  # Keep low for focused responses
        )
        
        response_content = response.choices[0].message.content
        
        # Save the tutor's intervention in permanent history
        self.history.append({"role": "assistant", "content": response_content})
        
        return response_content