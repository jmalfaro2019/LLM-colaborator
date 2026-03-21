# pbl_prompts.py

from simulated_student import SimulatedStudent

# 1. El Escenario que todos los agentes conocerán
PBL_SCENARIO = """
Situación actual: El equipo de estudiantes debe resolver un problema de Machine Learning.
Problema: Una clínica tiene miles de historiales médicos de pacientes sin ninguna etiqueta o diagnóstico previo clasificado. Quieren encontrar patrones ocultos en los síntomas para ver si existen nuevas variantes de una enfermedad. 
Objetivo del equipo: Discutir y decidir si deben aplicar un enfoque de Aprendizaje Supervisado o No Supervisado, y proponer al menos un algoritmo (ej. K-Means, Random Forest, etc.).
"""

# 2. Prompts de Personalidad (Optimizados para Llama 3 / Mistral)
PROMPT_DOMINANTE = f"""Eres Carlos, un estudiante de ingeniería de software en un chat grupal.

{PBL_SCENARIO}

Tu personalidad:
- Eres dominante, impaciente y muy seguro de tus conocimientos técnicos.
- Quieres imponer tu solución (ej. enfoque no supervisado).

REGLAS ESTRICTAS DE SALIDA:
1. Analiza los últimos mensajes. Si tu personalidad dicta que no intervendrías en este momento, responde ÚNICAMENTE con la palabra: [SILENCIO].
2. Si decides hablar, NO uses preámbulos, empieza directamente tu respuesta en 1 o 2 oraciones.

EJEMPLO DE RESPUESTA DE ABSTINENCIA:
[SILENCIO]
"""
PROMPT_PASIVO = f"""Eres Ana, una estudiante de ingeniería de software en un chat grupal.
{PBL_SCENARIO}

Tu personalidad:
- Eres insegura de tus conocimientos técnicos.
- Sueles estar de acuerdo con el estudiante dominante para evitar conflictos.
- Tienes alta probabilidad de no participar a menos que te pregunten directamente o haya un silencio largo.

REGLAS ESTRICTAS DE SALIDA:
1. Analiza los últimos mensajes. Si tu personalidad dicta que no intervendrías en este momento, responde ÚNICAMENTE con la palabra: [SILENCIO].
2. Si decides hablar, NO uses preámbulos, empieza directamente tu respuesta en 1 o 2 oraciones.

EJEMPLO DE RESPUESTA DE ABSTINENCIA:
[SILENCIO]
"""

PROMPT_REFLEXIVO = f"""Eres Luis, un estudiante de ingeniería de software en un chat grupal.
{PBL_SCENARIO}
Tu personalidad:
- Eres analítico, mediador y fomentas la 'transactividad'.
- SIEMPRE construyes sobre las ideas de los demás (menciona a Carlos o Ana).
- Te enfocas en entender el "por qué" y evalúas pros y contras.

REGLAS ESTRICTAS DE SALIDA:
1. Analiza los últimos mensajes. Si tu personalidad dicta que no intervendrías en este momento, responde ÚNICAMENTE con la palabra: [SILENCIO].
2. Si decides hablar, NO uses preámbulos, empieza directamente tu respuesta en 1 o 2 oraciones.

EJEMPLO DE RESPUESTA DE ABSTINENCIA:
[SILENCIO]
"""


def simulador_pbl_con_sistema_b(agentes, max_ticks=6):
    historial_chat = []
    # Diccionario para rastrear la inactividad de cada estudiante
    inactividad = {agente.name: 0 for agente in agentes}
    
    mensaje_tutor = "Hola equipo. Tenemos los historiales médicos sin etiquetas. ¿Deberíamos usar aprendizaje supervisado o no supervisado?"
    historial_chat.append(f"Tutor: {mensaje_tutor}")
    print(f"[Tick 0] Tutor: {mensaje_tutor}")

    for agente in agentes:
        agente.receive_message("Tutor", mensaje_tutor)

    for tick in range(1, max_ticks + 1):
        print(f"\n--- Minuto {tick} ---")

        for agente in agentes:
            respuesta = agente.generate_response().strip()
            
            if respuesta == "[SILENCIO]" or "[SILENCIO]" in respuesta:
                print(f"{agente.name} decidió no hablar.")
                agente.history.pop() 
                inactividad[agente.name] += 1 # Aumenta contador de inactividad
            else:
                print(f"{agente.name} dice: {respuesta}")
                historial_chat.append(f"{agente.name}: {respuesta}")
                inactividad[agente.name] = 0 # Reinicia contador al hablar
                
                for otro_agente in agentes:
                    if otro_agente.name != agente.name:
                        otro_agente.receive_message(agente.name, respuesta)

        # Evaluación del Sistema B al finalizar el minuto (tick)
        for nombre_agente, minutos_inactivo in inactividad.items():
            if minutos_inactivo >= 3:
                intervencion = f"{nombre_agente}, noto que no has participado en los últimos minutos. ¿Tienes alguna perspectiva sobre lo que se está discutiendo?"
                print(f"\n[SISTEMA B INTERVIENE] Tutor: {intervencion}")
                historial_chat.append(f"Tutor: {intervencion}")
                
                # 1. Propagamos la intervención a TODOS los agentes (para contexto)
                for agente in agentes:
                    agente.receive_message("Tutor", intervencion)
                
                # 2. Forzamos la respuesta INMEDIATA solo del agente interpelado
                agente_objetivo = next(a for a in agentes if a.name == nombre_agente)
                respuesta_forzada = agente_objetivo.generate_response().strip()
                
                if respuesta_forzada == "[SILENCIO]" or "[SILENCIO]" in respuesta_forzada:
                    print(f">> {nombre_agente} se mantuvo en silencio pese a la intervención.")
                    agente_objetivo.history.pop() # Purgar el silencio
                else:
                    print(f"{nombre_agente} dice: {respuesta_forzada}")
                    historial_chat.append(f"{nombre_agente}: {respuesta_forzada}")
                    
                    # 3. Propagamos su respuesta a los demás agentes
                    for otro_agente in agentes:
                        if otro_agente.name != nombre_agente:
                            otro_agente.receive_message(nombre_agente, respuesta_forzada)
                
                # Reiniciamos el contador del agente para evitar bucles infinitos de intervención
                inactividad[nombre_agente] = 0
                break # Solo 1 intervención del tutor por minuto
# --- EJECUCIÓN ---
carlos = SimulatedStudent("Carlos", PROMPT_DOMINANTE)
ana = SimulatedStudent("Ana", PROMPT_PASIVO)
luis = SimulatedStudent("Luis", PROMPT_REFLEXIVO)
#simulador_pbl_con_tiempo([carlos, ana, luis], max_ticks=5)
simulador_pbl_con_sistema_b([carlos, ana, luis], max_ticks=6)