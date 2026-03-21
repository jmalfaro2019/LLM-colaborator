# pbl_prompts.py

from simulated_student import SimulatedStudent

# 1. The Scenario that all agents will know
PBL_SCENARIO = """
Current situation: The team of students must solve a Machine Learning problem.
Problem: A clinic has thousands of patient medical records without any labels or prior classified diagnoses. They want to find hidden patterns in symptoms to see if new variants of a disease exist. 
Team objective: Discuss and decide whether to apply a Supervised or Unsupervised Learning approach, and propose at least one algorithm (e.g., K-Means, Random Forest, etc.).
"""

# 2. Personality Prompts (Optimized for Llama 3 / Mistral)
PROMPT_DOMINANT = f"""You are Carlos, a software engineering student in a group chat.

{PBL_SCENARIO}

Your personality:
- You are dominant, impatient, and very confident in your technical knowledge.
- You want to impose your solution (e.g., unsupervised approach).

STRICT OUTPUT RULES:
1. Analyze the latest messages. If your personality dictates that you would not intervene at this moment, respond ONLY with the word: [SILENCE].
2. If you decide to speak, DO NOT use preambles; start your response directly in 1 or 2 sentences.

EXAMPLE OF ABSTENTION RESPONSE:
[SILENCE]
"""

PROMPT_PASSIVE = f"""You are Ana, a software engineering student in a group chat.
{PBL_SCENARIO}

Your personality:
- You are unsure about your technical knowledge.
- You tend to agree with the dominant student to avoid conflict.
- You have a high probability of not participating unless directly asked or there is a long silence.

STRICT OUTPUT RULES:
1. Analyze the latest messages. If your personality dictates that you would not intervene at this moment, respond ONLY with the word: [SILENCE].
2. If you decide to speak, DO NOT use preambles; start your response directly in 1 or 2 sentences.

EXAMPLE OF ABSTENTION RESPONSE:
[SILENCE]
"""

PROMPT_REFLECTIVE = f"""You are Luis, a software engineering student in a group chat.
{PBL_SCENARIO}

Your personality:
- You are analytical, a mediator, and you promote "transactivity".
- You ALWAYS build on others' ideas (mention Carlos or Ana).
- You focus on understanding the "why" and evaluate pros and cons.

STRICT OUTPUT RULES:
1. Analyze the latest messages. If your personality dictates that you would not intervene at this moment, respond ONLY with the word: [SILENCE].
2. If you decide to speak, DO NOT use preambles; start your response directly in 1 or 2 sentences.

EXAMPLE OF ABSTENTION RESPONSE:
[SILENCE]
"""


def pbl_simulator_with_system_b(agents, max_ticks=6):
    chat_history = []
    # Dictionary to track inactivity of each student
    inactivity = {agent.name: 0 for agent in agents}
    
    tutor_message = "Hello team. We have unlabeled medical records. Should we use supervised or unsupervised learning?"
    chat_history.append(f"Tutor: {tutor_message}")
    print(f"[Tick 0] Tutor: {tutor_message}")

    for agent in agents:
        agent.receive_message("Tutor", tutor_message)

    for tick in range(1, max_ticks + 1):
        print(f"\n--- Minute {tick} ---")

        for agent in agents:
            response = agent.generate_response().strip()
            
            if response == "[SILENCE]" or "[SILENCE]" in response:
                print(f"{agent.name} decided not to speak.")
                agent.history.pop()
                inactivity[agent.name] += 1  # Increase inactivity counter
            else:
                print(f"{agent.name} says: {response}")
                chat_history.append(f"{agent.name}: {response}")
                inactivity[agent.name] = 0  # Reset counter when speaking
                
                for other_agent in agents:
                    if other_agent.name != agent.name:
                        other_agent.receive_message(agent.name, response)

        # System B evaluation at the end of the minute (tick)
        for agent_name, inactive_minutes in inactivity.items():
            if inactive_minutes >= 3:
                intervention = f"{agent_name}, I notice you haven't participated in the last few minutes. Do you have any perspective on what is being discussed?"
                print(f"\n[SYSTEM B INTERVENES] Tutor: {intervention}")
                chat_history.append(f"Tutor: {intervention}")
                
                # 1. Propagate intervention to ALL agents (for context)
                for agent in agents:
                    agent.receive_message("Tutor", intervention)
                
                # 2. Force IMMEDIATE response only from the addressed agent
                target_agent = next(a for a in agents if a.name == agent_name)
                forced_response = target_agent.generate_response().strip()
                
                if forced_response == "[SILENCE]" or "[SILENCE]" in forced_response:
                    print(f">> {agent_name} remained silent despite the intervention.")
                    target_agent.history.pop()  # Purge silence
                else:
                    print(f"{agent_name} says: {forced_response}")
                    chat_history.append(f"{agent_name}: {forced_response}")
                    
                    # 3. Propagate response to other agents
                    for other_agent in agents:
                        if other_agent.name != agent_name:
                            other_agent.receive_message(agent_name, forced_response)
                
                # Reset counter to avoid infinite intervention loops
                inactivity[agent_name] = 0
                break  # Only 1 tutor intervention per minute


# --- EXECUTION ---
carlos = SimulatedStudent("Carlos", PROMPT_DOMINANT)
ana = SimulatedStudent("Ana", PROMPT_PASSIVE)
luis = SimulatedStudent("Luis", PROMPT_REFLECTIVE)

pbl_simulator_with_system_b([carlos, ana, luis], max_ticks=6)