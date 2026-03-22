"""
Main entry point for the PBL Simulator.

This script orchestrates a Problem-Based Learning discussion between simulated students
with different personas and viewpoints on machine learning concepts (KNN algorithm).
"""

from simulated_student import SimulatedStudent
from pbl_config import STUDENTS_CONFIG, MAX_TICKS
from pbl_simulator import PBLSimulator


def main():
    """Initialize and run the PBL simulation."""
    # Create student instances from configuration
    students = [
        SimulatedStudent(name, system_prompt)
        for name, system_prompt in STUDENTS_CONFIG
    ]
    
    # Run the simulation
    simulator = PBLSimulator(students, max_ticks=MAX_TICKS)
    simulator.run()


if __name__ == "__main__":
    main()