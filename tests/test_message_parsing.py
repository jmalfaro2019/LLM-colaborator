"""
Diagnostic test to understand message parsing and empty messages.
This will run a minimal simulation with detailed logging.

Ejecutar desde raíz: python tests/test_message_parsing.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from simulated_student import SimulatedStudent
from simulated_tutor import SimulatedTutor
from pbl_simulator import PBLSimulator
from pbl_factory import PBLFactory
import pbl_simulator

def test_message_parsing():
    """Run a single test iteration with detailed message parsing diagnostics."""
    load_dotenv()
    llm_client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    factory = PBLFactory()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC TEST: Message Parsing Investigation")
    print("="*60 + "\n")
    
    # Generate configuration
    students_config, tutor_prompt, initial_problem, _ = factory.generate_random_session(
        system_type="A",
        force_scenario="KNN"
    )
    
    # Instantiate agents
    students = [SimulatedStudent(name, prompt) for name, prompt in students_config]
    tutor = SimulatedTutor("Tutor", tutor_prompt, system_type="A")
    
    # Set the initial message
    problem_intro = initial_problem.split('.')[0].replace("Problem: ", "")
    pbl_simulator.TUTOR_MESSAGE = f"Team, we need to solve this: {problem_intro}. What should be our approach?"
    
    # Create custom simulator with diagnostic instrumentation
    simulator = PBLSimulator(
        students=students, tutor=tutor, llm_client=llm_client,
        max_ticks=2, system_type="A"
    )
    
    # Hook into the actual message processing
    original_run_tick = simulator._run_tick
    
    def instrumented_run_tick(tick):
        """Run tick with detailed message logging."""
        print(f"\n{'='*60}")
        print(f"--- MINUTE {tick} ---")
        print('='*60)
        
        for student in simulator.students:
            print(f"\n[INFO] Generating response from {student.name}...")
            raw_response = student.generate_response().strip()
            
            # Log the raw response (first 200 chars)
            print(f"  Raw response length: {len(raw_response)} chars")
            print(f"  First 200 chars: {raw_response[:200]}")
            
            # Parse manually for diagnostics
            thought = ""
            public_message = raw_response
            
            if "[MESSAGE]" in raw_response:
                parts = raw_response.split("[MESSAGE]")
                thought = parts[0].replace("[THOUGHT]", "").strip()
                public_message = parts[1].strip() if len(parts) > 1 else ""
                
                print(f"  [OK] Found [MESSAGE] delimiter")
                print(f"    Thought length: {len(thought)}")
                print(f"    Expected message length before processing: {len(parts[1] if len(parts) > 1 else '')}")
                print(f"    Actual public_message after strip: '{public_message}'")
                print(f"    Is empty? {not public_message}")
                
                # If message is empty after parsing, default to SILENCE
                if not public_message:
                    print(f"    -> Converting empty message to [SILENCE]")
                    public_message = "[SILENCE]"
            else:
                print(f"  [WARNING] NO [MESSAGE] delimiter found!")
            
            # Check silence status
            is_silence = public_message == "[SILENCE]" or "[SILENCE]" in public_message
            print(f"  Final decision: {public_message if not is_silence else '[SILENCE - will not add to history]'}")
            
            # Check current chat history before adding
            print(f"  Chat history size before: {len(simulator.chat_history)} entries")
            
            # Simulate the actual logic from _run_tick
            if not is_silence:
                message_entry = {
                    "name": student.name,
                    "message": public_message,
                    "transactivity": None
                }
                simulator.chat_history.append(message_entry)
                print(f"  [OK] Added to chat_history: {message_entry}")
            else:
                print(f"  [SKIP] Skipped (SILENCE)")
            
            print(f"  Chat history size after: {len(simulator.chat_history)} entries")
        
        # Now run the original logic (this will process again, but that's OK for diagnostics)
        print(f"\n[INFO] Running original _run_tick logic...")
        original_run_tick(tick)
    
    # Replace with instrumented version
    simulator._run_tick = instrumented_run_tick
    
    # Run the simulation
    simulator.run()
    
    # Print final chat history
    print(f"\n{'='*60}")
    print("FINAL CHAT HISTORY")
    print('='*60)
    for i, entry in enumerate(simulator.chat_history):
        print(f"{i}. {entry['name']}: '{entry.get('message', '[NO MESSAGE KEY]')}'")
    
    # Check for empty messages
    empty_messages = [e for e in simulator.chat_history if e.get('message') == '']
    if empty_messages:
        print(f"\n[WARNING] FOUND {len(empty_messages)} EMPTY MESSAGES!")
        for e in empty_messages:
            print(f"   - {e}")
    else:
        print("\n[OK] No empty messages found!")
    
    # Print JSON output
    print(f"\n{'='*60}")
    print("JSON OUTPUT (as would be saved)")
    print('='*60 + "\n")
    
    # Simulate clean_chat_history
    cleaned = []
    for entry in simulator.chat_history:
        if isinstance(entry, dict):
            cleaned.append({
                "name": entry.get("name"),
                "message": entry.get("message")
            })
    
    output = {
        "scenario": "KNN",
        "system": "A",
        "chat_history": cleaned
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_message_parsing()
