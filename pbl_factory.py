import random
from pbl_config import (
    SCENARIOS_DB, PERSONALITIES, COGNITIVE_BLOCK, OUTPUT_RULES,
    TUTOR_SYSTEM_A_BASE, TUTOR_SYSTEM_B_BASE
)

class PBLFactory:
    """Generates random dynamic configurations for PBL Simulations."""
    
    def __init__(self):
        self.base_student_names = ["Carlos", "Ana", "Luis"]
        self.student_names = None  # Será aleatorizado en generate_random_session

    def generate_random_session(self, system_type="B", force_scenario=None):
        """
        Returns the prompts needed to instantiate the students and tutor.
        """
        # 0. RANDOMIZE STUDENT ORDER (M2: Eliminar sesgo de participación)
        self.student_names = self.base_student_names.copy()
        random.shuffle(self.student_names)
        print(f">> Student order: {' -> '.join(self.student_names)}")
        
        # 1. Pick a scenario (KNN, KMEANS, or TREES)
        scenario_key = force_scenario if force_scenario else random.choice(list(SCENARIOS_DB.keys()))
        scenario_data = SCENARIOS_DB[scenario_key]
        
        # 2. Build the dynamic Tutor prompt
        tutor_base = TUTOR_SYSTEM_A_BASE if system_type == "A" else TUTOR_SYSTEM_B_BASE
        tutor_prompt = tutor_base.format(tutor_bg=scenario_data["tutor_bg"])
        
        # 3. Build the dynamic Students config (List of tuples: (name, system_prompt))
        students_config = []
        for name in self.student_names:
            stance = random.choice(scenario_data["stances"])
            personality = random.choice(PERSONALITIES)
            
            student_prompt = f"""You are {name}, a student in a group chat.

{scenario_data["problem"]}

{stance}

{personality}

{COGNITIVE_BLOCK}
{OUTPUT_RULES}
"""
            students_config.append((name, student_prompt))
            
        return students_config, tutor_prompt, scenario_data["problem"], scenario_key