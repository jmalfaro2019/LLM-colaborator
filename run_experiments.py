import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from simulated_student import SimulatedStudent
from simulated_tutor import SimulatedTutor
from pbl_simulator import PBLSimulator
import pbl_simulator
from pbl_config import MAX_TICKS
from pbl_factory import PBLFactory

def save_simulation_log(scenario, system, run_id, history, students_config, folder="results"):
    """Guarda el historial de la charla y el contexto inicial en un JSON."""
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    filename = f"{folder}/sim_{scenario}_Sys{system}_run{run_id}.json"
    
    # Extraemos solo los nombres y posturas iniciales para contexto del juez
    student_profiles = [{"name": name, "prompt": prompt} for name, prompt in students_config]
    
    data = {
        "scenario": scenario,
        "system": system,
        "run_id": run_id,
        "student_profiles": student_profiles,
        "chat_history": history
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Guardado: {filename}")

def run_batch_experiments():
    load_dotenv()
    llm_client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    factory = PBLFactory()
    scenarios = ["KNN", "KMEANS", "TREES"]
    systems = ["A", "B"]
    runs_per_combination = 5
    
    total_runs = len(scenarios) * len(systems) * runs_per_combination
    current_run = 0

    for scenario in scenarios:
        for system in systems:
            for run_id in range(1, runs_per_combination + 1):
                current_run += 1
                print(f"\n{'='*50}")
                print(f"🚀 EJECUTANDO SIMULACIÓN {current_run}/{total_runs}")
                print(f"Escenario: {scenario} | Tutor: Sistema {system} | Intento: {run_id}")
                print(f"{'='*50}\n")
                
                # 1. Generar la configuración aleatoria para esta corrida
                students_config, tutor_prompt, initial_problem, _ = factory.generate_random_session(
                    system_type=system, 
                    force_scenario=scenario
                )
                
                # 2. Instanciar agentes
                students = [SimulatedStudent(name, prompt) for name, prompt in students_config]
                tutor = SimulatedTutor("Tutor", tutor_prompt, system_type=system)
                
                # 3. Ajustar el mensaje inicial
                problem_intro = initial_problem.split('.')[0].replace("Problem: ", "")
                pbl_simulator.TUTOR_MESSAGE = f"Team, we need to solve this: {problem_intro}. What should be our approach?"
                
                # 4. Correr la simulación
                simulator = PBLSimulator(
                    students=students, tutor=tutor, llm_client=llm_client,
                    max_ticks=MAX_TICKS, system_type=system
                )
                simulator.run()
                
                # 5. Guardar los resultados
                save_simulation_log(scenario, system, run_id, simulator.chat_history, students_config)

if __name__ == "__main__":
    run_batch_experiments()