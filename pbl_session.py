"""
Centraliza la creación completa de sesiones PBL.

Elimina duplicación en: main.py, run_experiments.py, test_message_parsing.py
"""
from typing import Tuple, Optional
from pbl_factory import PBLFactory
from simulated_student import SimulatedStudent
from simulated_tutor import SimulatedTutor
from pbl_config import MAX_TICKS


def setup_pbl_session(
    system_type: str,
    scenario: str = None,
    seed: Optional[int] = None,
) -> Tuple[list, SimulatedTutor, str, list, str]:
    """
    Setup completo de una sesión PBL con factory, estudiantes y tutor.
    
    Reemplaza el patrón repetido en 5 ubicaciones:
    - Factory + random session
    - Estudiantes creados
    - Tutor creado con system_type
    
    Args:
        system_type: "A" (Transactivity-based) o "B" (Activity-based)
        scenario: Escenario específico (KNN, KMEANS, TREES) o None para aleatorio
        seed: (M1) Seed para reproducibilidad, o None para verdaderamente aleatorio
    
    Returns:
        Tupla (students, tutor, initial_problem, students_config, scenario_key)
        
    Raises:
        ValueError: Si system_type no es "A" o "B"
        
    Example:
        >>> # Reproducible
        >>> students, tutor, problem, config, scenario = setup_pbl_session("B", seed=42)
        >>> # Aleatorio
        >>> students, tutor, problem, config, scenario = setup_pbl_session("B")
    """
    if system_type not in ("A", "B"):
        raise ValueError(f"system_type debe ser 'A' o 'B', recibió: {system_type}")
    
    # M1: GENERADOR DE SESIONES CON SEED
    if seed is not None:
        import random
        random.seed(seed)
        print(f"[LOCK] [M1: REPRODUCIBILIDAD] seed={seed}")
    
    # 1. Generar configuración dinámica
    factory = PBLFactory()
    students_config, tutor_prompt, initial_problem, scenario_key = \
        factory.generate_random_session(
            system_type=system_type,
            force_scenario=scenario
        )
    
    # 2. Instanciar estudiantes
    students = [
        SimulatedStudent(name, prompt)
        for name, prompt in students_config
    ]
    
    # 3. Instanciar tutor
    tutor = SimulatedTutor(
        name="Tutor",
        system_prompt=tutor_prompt,
        system_type=system_type
    )
    
    return students, tutor, initial_problem, students_config, scenario_key


def format_initial_tutor_message(initial_problem: str) -> str:
    """
    Formatea el problema inicial en un mensaje del tutor.
    
    Maneja parsing robusto del problema.
    
    Args:
        initial_problem: Descripción del problema completa
        
    Returns:
        Mensaje formateado para el tutor
        
    Example:
        >>> problem = "Problem: Usar KNN. La tarea es..."
        >>> msg = format_initial_tutor_message(problem)
        >>> print(msg)
        "Team, we need to solve this: Usar KNN. What should be our approach?"
    """
    # Extraer parte principal del problema (antes del punto)
    if '.' in initial_problem:
        problem_intro = initial_problem.split('.')[0]
    else:
        problem_intro = initial_problem
    
    # Limpiar prefijo "Problem: " si existe
    if "Problem: " in problem_intro:
        problem_intro = problem_intro.replace("Problem: ", "").strip()
    elif "Problema: " in problem_intro:
        problem_intro = problem_intro.replace("Problema: ", "").strip()
    
    return f"Team, we need to solve this: {problem_intro}. What should be our approach?"
