"""
Main entry point for the PBL Simulator.

This script orchestrates a Problem-Based Learning discussion between simulated students
with different personas and viewpoints on machine learning concepts (KNN algorithm).
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

from simulated_student import SimulatedStudent
from simulated_tutor import SimulatedTutor
from pbl_config import STUDENTS_CONFIG, MAX_TICKS, PROMPT_TUTOR_SYSTEM_B, PROMPT_TUTOR_SYSTEM_A
from pbl_simulator import PBLSimulator


def main():
    """Initialize and run the PBL simulation."""
    # Load environment variables
    load_dotenv()
    
    # Initialize Groq client for LLM calls
    llm_client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    # Choose system type: "A" (Transactivity) or "B" (Activity/Silence)
    system_type = "B"
    
    # Select the appropriate tutor prompt based on system type
    tutor_prompt = PROMPT_TUTOR_SYSTEM_B if system_type == "B" else PROMPT_TUTOR_SYSTEM_A
    
    # Create student instances from configuration
    students = [
        SimulatedStudent(name, system_prompt)
        for name, system_prompt in STUDENTS_CONFIG
    ]
    
    # Create tutor instance with the appropriate system type and prompt
    tutor = SimulatedTutor("Tutor", tutor_prompt, system_type=system_type)
    
    # Run the simulation
    simulator = PBLSimulator(
        students=students,
        tutor=tutor,
        llm_client=llm_client,
        max_ticks=MAX_TICKS,
        system_type=system_type
    )
    simulator.run()


if __name__ == "__main__":
    main()