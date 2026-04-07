"""
Batch experiment runner for PBL simulations.

Refactored for maintainability:
- Uses centralized llm_client.get_groq_client()
- Uses centralized pbl_session.setup_pbl_session()
- Uses centralized message_parser functions
- Eliminates ~95 lines of duplicated code

Checkpoint/Resume support:
- Automatically saves progress when rate limit is hit
- Resume from last checkpoint with resume_batch_experiments()
"""

import os
import json
from datetime import datetime
from llm_client import get_groq_client
from pbl_session import setup_pbl_session, format_initial_tutor_message
from pbl_simulator import PBLSimulator
import pbl_simulator
from pbl_config import MAX_TICKS


def clean_chat_history(history):
    """
    Clean the chat history to contain ONLY:
    - Speaker name
    - Public message
    Removes: student thinking, tutor analysis, transactivity tags
    """
    cleaned = []
    for entry in history:
        if isinstance(entry, dict):
            cleaned.append({
                "name": entry.get("name"),
                "message": entry.get("message")
            })
        else:
            # Handle string format if any
            cleaned.append({"message": entry})
    return cleaned

def save_simulation_log(scenario, system, run_id, history, students_config, folder="results"):
    """Save the conversation and initial context to a JSON file (without thinking processes or labels)."""
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    filename = f"{folder}/sim_{scenario}_Sys{system}_run{run_id}.json"
    
    # Extract only student names and initial stances for judge context
    student_profiles = [{"name": name, "prompt": prompt} for name, prompt in students_config]
    
    # Clean the history to show only conversation
    cleaned_history = clean_chat_history(history)
    
    data = {
        "scenario": scenario,
        "system": system,
        "run_id": run_id,
        "student_profiles": student_profiles,
        "chat_history": cleaned_history
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[OK] Saved: {filename}")


def save_checkpoint(resume_state, checkpoint_dir="checkpoints"):
    """
    Guarda el progreso actual cuando se agota el quota de tokens.
    
    Args:
        resume_state: Dict con estado actual {
            'scenarios': [...],
            'systems': [...],
            'runs_per_combination': int,
            'completed_runs': [(scenario, system, run_id), ...],
            'current_run': int,
            'total_runs': int,
            'last_error': str (opcional),
            'timestamp': timestamp
        }
    """
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    
    filename = f"{checkpoint_dir}/checkpoint_latest.json"
    backup_filename = f"{checkpoint_dir}/checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Guardar con timestamp
    resume_state['timestamp'] = datetime.now().isoformat()
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resume_state, f, indent=4)
    
    # Hacer backup también
    with open(backup_filename, "w", encoding="utf-8") as f:
        json.dump(resume_state, f, indent=4)
    
    print(f"\n[CHECKPOINT] Saved to: {filename}")
    print(f"[CHECKPOINT] Backup to: {backup_filename}")
    print(f"[INFO] Resume with: resume_batch_experiments()")


def load_checkpoint(checkpoint_dir="checkpoints"):
    """
    Carga el último checkpoint guardado.
    
    Returns:
        Dict con estado anterior, o None si no hay checkpoint
    """
    filename = f"{checkpoint_dir}/checkpoint_latest.json"
    
    if not os.path.exists(filename):
        return None
    
    with open(filename, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    print(f"[CHECKPOINT] Loaded from: {filename}")
    print(f"[INFO] Completed {len(state.get('completed_runs', []))} runs")
    print(f"[INFO] Progress: {state.get('current_run', 0)}/{state.get('total_runs', 0)}")
    
    return state


def _run_simulation(scenario, system, run_id, llm_client, max_ticks=MAX_TICKS, seed=None):
    """
    Ejecuta una simulación individual.
    
    Patrón centralizado para evitar duplicación entre quick_test y batch.
    
    Args:
        scenario: Escenario (KNN, KMEANS, TREES)
        system: Sistema (A o B)
        run_id: ID de la ejecución
        llm_client: Cliente Groq/OpenAI
        max_ticks: Duración
        seed: (M1) Seed para reproducibilidad, o None para aleatorio
    """
    students, tutor, initial_problem, students_config, scenario_key = \
        setup_pbl_session(system_type=system, scenario=scenario, seed=seed)
    
    tutor_message = format_initial_tutor_message(initial_problem)
    pbl_simulator.TUTOR_MESSAGE = tutor_message
    
    simulator = PBLSimulator(
        students=students, tutor=tutor, llm_client=llm_client,
        max_ticks=max_ticks, system_type=system
    )
    simulator.run()
    
    return simulator, students_config, scenario_key


def run_quick_test(scenario="KMEANS", system="B", max_ticks=3):
    """Run a single quick test to verify the system works correctly."""
    llm_client = get_groq_client()
    
    print(f"\n{'='*50}")
    print(f"[QUICK TEST] {scenario} - System {system} - Run 1")
    print(f"{'='*50}\n")
    
    simulator, students_config, scenario_key = _run_simulation(
        scenario=scenario, system=system, run_id=1,
        llm_client=llm_client, max_ticks=max_ticks
    )
    
    save_simulation_log(scenario, system, 1, simulator.chat_history, students_config)
    
    print(f"\n[OK] Quick test ({scenario} - System {system}) completed successfully!")
    print(f"[INFO] Check results/sim_{scenario}_Sys{system}_run1.json to verify formatting\n")


def run_quick_test_system_a(scenario="KMEANS", max_ticks=3):
    """Run a quick test for System A (Transactivity-based)."""
    run_quick_test(scenario=scenario, system="A", max_ticks=max_ticks)


def run_quick_test_system_b(scenario="KMEANS", max_ticks=3):
    """Run a quick test for System B (Activity-based). RECOMMENDED."""
    run_quick_test(scenario=scenario, system="B", max_ticks=max_ticks)



def run_batch_experiments(scenarios=None, systems=None, runs_per_combination=1):
    """
    Run batch of PBL simulations with automatic checkpoint on rate limit.
    
    Si se agota el quota de tokens (Error 429):
    - Guarda checkpoint automáticamente
    - Puedes continuar después con resume_batch_experiments()
    
    Args:
        scenarios: List of scenarios ["KNN", "KMEANS", "TREES"] or None for all
        systems: List of systems ["A", "B"] or None for all
        runs_per_combination: How many runs per scenario-system combo
        
    Example:
        >>> run_batch_experiments()  # Todos los scenarios, sistemas, 1 run = 6 total
        >>> run_batch_experiments(scenarios=["KNN"], systems=["B"])  # Solo KNN con B
        
    Si se agota quota:
        >>> resume_batch_experiments()  # Continúa desde donde dejó
    """
    if scenarios is None:
        scenarios = ["KNN", "KMEANS", "TREES"]
    if systems is None:
        systems = ["A", "B"]
    
    llm_client = get_groq_client()
    
    total_runs = len(scenarios) * len(systems) * runs_per_combination
    current_run = 0
    completed_runs = []

    try:
        for scenario in scenarios:
            for system in systems:
                for run_id in range(1, runs_per_combination + 1):
                    current_run += 1
                    print(f"\n{'='*50}")
                    print(f"[RUNNING] SIMULATION {current_run}/{total_runs}")
                    print(f"Scenario: {scenario} | Tutor: System {system} | Run: {run_id}")
                    print(f"{'='*50}\n")
                    
                    try:
                        # Ejecutar simulación
                        simulator, students_config, scenario_key = _run_simulation(
                            scenario=scenario, system=system, run_id=run_id,
                            llm_client=llm_client, max_ticks=MAX_TICKS
                        )
                        
                        # Guardar resultados
                        save_simulation_log(scenario, system, run_id, simulator.chat_history, students_config)
                        completed_runs.append((scenario, system, run_id))
                        
                    except Exception as e:
                        error_msg = str(e)
                        # Detectar rate limit error (429)
                        if "429" in error_msg or "rate_limit" in error_msg.lower():
                            print(f"\n[ERROR] Rate limit reached (429)")
                            print(f"[ERROR] {error_msg[:100]}...")
                            
                            # Guardar checkpoint
                            checkpoint_state = {
                                'scenarios': scenarios,
                                'systems': systems,
                                'runs_per_combination': runs_per_combination,
                                'completed_runs': completed_runs,
                                'current_run': current_run,
                                'total_runs': total_runs,
                                'last_error': error_msg[:200]
                            }
                            save_checkpoint(checkpoint_state)
                            
                            return  # Detener aquí
                        else:
                            # Otro tipo de error, reintentar en siguiente iteración
                            print(f"[WARNING] Simulation failed: {error_msg[:100]}")
                            
    except KeyboardInterrupt:
        print(f"\n[INTERRUPTED] Simulación interrumpida por usuario")
        
        # Guardar checkpoint
        checkpoint_state = {
            'scenarios': scenarios,
            'systems': systems,
            'runs_per_combination': runs_per_combination,
            'completed_runs': completed_runs,
            'current_run': current_run,
            'total_runs': total_runs,
            'last_error': 'User interrupted'
        }
        save_checkpoint(checkpoint_state)
        return
    
    # Si completó todo sin errores
    print(f"\n{'='*50}")
    print(f"[OK] Batch experiments completed!")
    print(f"[INFO] {current_run}/{total_runs} simulations completed successfully")
    print(f"{'='*50}\n")


def resume_batch_experiments():
    """
    Resume batch experiments from last checkpoint.
    
    Carga el último checkpoint y continúa desde donde dejó.
    
    Example:
        >>> run_batch_experiments()  # Sale con error 429
        >>> resume_batch_experiments()  # Continúa desde donde paró
    """
    state = load_checkpoint()
    
    if state is None:
        print("[ERROR] No checkpoint found. Run run_batch_experiments() first.")
        return
    
    print(f"\n[RESUMING] Batch experiments from checkpoint")
    print(f"[INFO] Last error: {state.get('last_error', 'None')}")
    print(f"\n")
    
    # Continuar desde donde dejó
    run_batch_experiments(
        scenarios=state['scenarios'],
        systems=state['systems'],
        runs_per_combination=state['runs_per_combination']
    )


if __name__ == "__main__":
    """
    Ejecutar batch experiments con soporte para checkpoint/resume:
    
    OPCIÓN 1 - Ejecución normal (se detiene automáticamente si se agota quota):
        python run_experiments.py
    
    OPCIÓN 2 - Continuar desde el último checkpoint:
        python -c "from run_experiments import resume_batch_experiments; resume_batch_experiments()"
    
    OPCIÓN 3 - Batch personalizado (solo KNN, solo Sistema B):
        python -c "from run_experiments import run_batch_experiments; run_batch_experiments(scenarios=['KNN'], systems=['B'])"
    """
    
    # For batch experiments (short batch: 1 run per combination = 6 total runs)
    # Will automatically checkpoint if rate limit is hit
    run_batch_experiments(runs_per_combination=5)