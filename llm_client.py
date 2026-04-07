"""
Centraliza la inicialización del cliente Groq/OpenAI.

Elimina duplicación en: main.py, run_experiments.py, test_message_parsing.py
"""
import os
from openai import OpenAI
from dotenv import load_dotenv


def get_groq_client() -> OpenAI:
    """
    Obtiene cliente OpenAI configurado para Groq API.
    
    Returns:
        OpenAI: Cliente inicializado con Groq endpoint
        
    Raises:
        ValueError: Si GROQ_API_KEY no está configurada
        
    Example:
        >>> client = get_groq_client()
        >>> response = client.chat.completions.create(...)
    """
    load_dotenv()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY no configurada. "
            "Por favor, crea archivo .env con: GROQ_API_KEY=tu_clave_aqui"
        )
    
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )
