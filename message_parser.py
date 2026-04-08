"""
Centraliza el parsing de respuestas del tipo [THOUGHT]...[MESSAGE]...

Elimina duplicación en: pbl_simulator.py, test_message_parsing.py
"""
from typing import Tuple


def parse_student_response(raw_response: str) -> Tuple[str, str]:
    """
    Parsea respuesta del estudiante en formato [THOUGHT]...[MESSAGE]...
    
    Args:
        raw_response: Respuesta cruda del LLM con delimitadores
        
    Returns:
        Tupla (thought, message) donde:
        - thought: Monólogo interno (no compartido)
        - message: Mensaje público o [SILENCE] si está vacío
        
    Example:
        >>> thought, msg = parse_student_response(
        ...     "[THOUGHT]Debo pensar...[MESSAGE]Mi opinión es...")
        >>> print(msg)
        "Mi opinión es..."
        
        >>> thought, msg = parse_student_response(
        ...     "[THOUGHT]No tengo nada[MESSAGE]")
        >>> print(msg)
        "[SILENCE]"
    """
    thought = ""
    message = raw_response
    
    if "[MESSAGE]" in raw_response:
        # Dividir por delimitador [MESSAGE]
        parts = raw_response.split("[MESSAGE]")
        
        # Extraer pensamiento (parte antes de [MESSAGE])
        thought = parts[0].replace("[THOUGHT]", "").strip()
        
        # Extraer mensaje (parte después de [MESSAGE])
        message = parts[1].strip() if len(parts) > 1 else ""
        
        # Si el mensaje está vacío, marcar como silencio
        if not message:
            message = "[SILENCE]"
    
    return thought, message


def parse_tutor_response(raw_response: str) -> Tuple[str, str]:
    """
    Parsea respuesta del tutor en formato [INTERNAL ANALYSIS]...[TUTOR INTERVENTION]...
    
    Args:
        raw_response: Respuesta cruda del LLM con delimitadores
        
    Returns:
        Tupla (analysis, intervention) donde:
        - analysis: Análisis interno del tutor (diagnóstico)
        - intervention: Mensaje público o "TUTOR REMAINS SILENT (FADING)"
        
    Example:
        >>> analysis, intervention = parse_tutor_response(
        ...     "[INTERNAL ANALYSIS]El grupo está dispuesto...[TUTOR INTERVENTION]¿Qué piensan?")
        >>> print(intervention)
        "¿Qué piensan?"
    """
    analysis = ""
    intervention = raw_response
    
    if "[TUTOR INTERVENTION]" in raw_response:
        parts = raw_response.split("[TUTOR INTERVENTION]")
        analysis = parts[0].replace("[INTERNAL ANALYSIS]", "").strip()
        intervention = parts[1].strip() if len(parts) > 1 else ""
    elif "[INTERNAL ANALYSIS]" in raw_response:
        # Si tiene el análisis pero se le olvidó el tag del mensaje
        parts = raw_response.split("[INTERNAL ANALYSIS]")
        # Suponiendo que el mensaje (o fading) está al final tras el análisis
        # Esto es más difícil de parsear sin el segundo tag, pero intentemos:
        content = parts[1].strip()
        if "TUTOR REMAINS SILENT" in content:
            analysis = content.split("TUTOR REMAINS SILENT")[0].strip()
            intervention = "TUTOR REMAINS SILENT (FADING)"
        else:
            analysis = content # Heuristic
            intervention = "TUTOR REMAINS SILENT (FADING)" # Fallback if intervention tag missing
    elif "TUTOR REMAINS SILENT" in raw_response:
        # Si solo envió el texto de fading, veamos si hay texto antes
        parts = raw_response.split("TUTOR REMAINS SILENT")
        analysis = parts[0].strip()
        intervention = "TUTOR REMAINS SILENT (FADING)"
    
    # Asegurar que la intervención tenga el formato correcto para los checks posteriores
    if not intervention:
        intervention = "TUTOR REMAINS SILENT (FADING)"
    
    return analysis, intervention


def is_silence(message: str) -> bool:
    """
    Verifica si un mensaje es silencio.
    
    Args:
        message: Mensaje a verificar
        
    Returns:
        True si es [SILENCE] o similar
        
    Example:
        >>> is_silence("[SILENCE]")
        True
    """
    return message == "[SILENCE]" or "[SILENCE]" in message
