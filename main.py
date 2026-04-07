"""
Main entry point for the Dynamic PBL Simulator.

This script orchestrates a Problem-Based Learning discussion using dynamically
generated scenarios, knowledge stances, and personality archetypes.

Refactored for maintainability:
- Uses centralized llm_client.get_groq_client()
- Uses centralized pbl_session.setup_pbl_session()
- Eliminates code duplication from main.py, run_experiments.py, test_message_parsing.py
"""

from llm_client import get_groq_client
from pbl_session import setup_pbl_session, format_initial_tutor_message
from pbl_simulator import PBLSimulator
import pbl_simulator  # Para modificar TUTOR_MESSAGE si es necesario
from pbl_config import MAX_TICKS


def main():
    """Initialize and run the dynamic PBL simulation."""
    
    # 1. GET LLM CLIENT (centralized)
    llm_client = get_groq_client()
    
    # 2. CHOOSE SYSTEM TYPE
    # System B: Recommended (Activity-based) - interventions based on inactivity
    # System A: Advanced (Transactivity-based) - interventions based on dialogue quality
    system_type = "B"
    
    # 3. SETUP PBL SESSION (centralized)
    print("Generating random PBL scenario...")
    students, tutor, initial_problem, students_config, scenario_key = \
        setup_pbl_session(system_type=system_type, scenario=None)
    
    print(f"=== SIMULATION STARTED: {scenario_key} ===\n")
    
    # 4. SETUP INITIAL MESSAGE
    tutor_message = format_initial_tutor_message(initial_problem)
    pbl_simulator.TUTOR_MESSAGE = tutor_message
    
    # 5. RUN THE SIMULATOR
    simulator = PBLSimulator(
        students=students,
        tutor=tutor,
        llm_client=llm_client,
        max_ticks=MAX_TICKS,
        system_type=system_type,
        ground_truth=initial_problem
    )
    simulator.run()

if __name__ == "__main__":
    main()