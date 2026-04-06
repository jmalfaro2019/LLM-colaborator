"""
Main entry point for the Dynamic PBL Simulator.

This script orchestrates a Problem-Based Learning discussion using dynamically
generated scenarios, knowledge stances, and personality archetypes.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

from simulated_student import SimulatedStudent
from simulated_tutor import SimulatedTutor
from pbl_simulator import PBLSimulator
import pbl_simulator  # Para modificar el TUTOR_MESSAGE global temporalmente
from pbl_config import MAX_TICKS
from pbl_factory import PBLFactory

def main():
    """Initialize and run the dynamic PBL simulation."""
    # Load environment variables
    load_dotenv()
    
    # Initialize Groq client for LLM calls
    llm_client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    # Choose system type: "A" (Transactivity) or "B" (Activity/Silence)
    system_type = "A"
    
    # 1. GENERATE DYNAMIC SCENARIO
    print("Generating random PBL scenario...")
    factory = PBLFactory()
    # Tip: Puedes usar force_scenario="KMEANS" si quieres probar uno específico.
    students_config, tutor_prompt, initial_problem, scenario_key = factory.generate_random_session(system_type=system_type)
    
    print(f"=== SIMULATION STARTED: {scenario_key} ===")
    
    # 2. CREATE STUDENT INSTANCES
    students = [
        SimulatedStudent(name, system_prompt)
        for name, system_prompt in students_config
    ]
    
    # 3. CREATE TUTOR INSTANCE
    tutor = SimulatedTutor("Tutor", tutor_prompt, system_type=system_type)
    
    # 4. OVERRIDE TUTOR OPENING MESSAGE DYNAMICALLY
    # Hacemos esto para que el tutor no hable de KNN si el escenario es K-Means
    problem_intro = initial_problem.split('.')[0].replace("Problem: ", "")
    pbl_simulator.TUTOR_MESSAGE = f"Team, we need to solve this: {problem_intro}. What should be our approach regarding the algorithm and the metrics?"
    
    # 5. RUN THE SIMULATOR
    simulator = PBLSimulator(
        students=students,
        tutor=tutor,
        llm_client=llm_client,
        max_ticks=MAX_TICKS,
        system_type=system_type,
        ground_truth=tutor_prompt
    )
    simulator.run()

if __name__ == "__main__":
    main()