# pbl_simulator.py
# Core simulation logic for PBL discussions

from pbl_config import TUTOR_MESSAGE, INACTIVITY_THRESHOLD, PROMPT_TRANSACTIVITY_CLASSIFIER




# --- MAIN SIMULATOR CLASS ---
class PBLSimulator:
    """Manages a Problem-Based Learning discussion between simulated students."""
    
    def __init__(self, students, tutor, llm_client, max_ticks=6, system_type="B", ground_truth="Basic Machine Learning Theory"):
        """
        Initialize the PBL simulator.
        
        Args:
            students: List of SimulatedStudent instances
            tutor: Instance of SimulatedTutor
            llm_client: API client for the quick transactivity classifier
            max_ticks: Maximum number of discussion rounds
            system_type: "A" (Transactivity) or "B" (Activity)
            ground_truth: the theory of the theme in discussion
        """
        self.students = students
        self.tutor = tutor
        self.llm_client = llm_client
        self.max_ticks = max_ticks
        self.system_type = system_type
        
        self.chat_history = []
        self.inactivity = {student.name: 0 for student in students}
        self.non_transactive_turns = 0
        self.problem_ground_truth = ground_truth
    
    def run(self):
        """Execute the PBL simulation."""
        self._tutor_opening()
        
        for tick in range(1, self.max_ticks + 1):
            self._run_tick(tick)
            self._evaluate_and_intervene(tick)
    
    def _tutor_opening(self):
        """Start the discussion with the tutor's opening message."""
        print(f"[Tick 0] Tutor: {TUTOR_MESSAGE}")
        self.chat_history.append({
            "name": "Tutor",
            "message": TUTOR_MESSAGE,
            "transactivity": None
        })
        
        # Share the initial message with all students
        for student in self.students:
            student.receive_message("Tutor", TUTOR_MESSAGE)
            
        # Give the tutor initial context about what they just said
        self.tutor.receive_message("System", f"You opened the discussion with: {TUTOR_MESSAGE}")
    
    def _run_tick(self, tick):
        """Execute one round of discussion with Chain of Thought parsing."""
        print(f"\n--- Minute {tick} ---")
        has_transactivity_this_turn = False
        
        for student in self.students:
            # 1. Get raw response from student (contains thought and message)
            raw_response = student.generate_response().strip()
            
            # 2. Initialize parsing variables
            thought = ""
            public_message = raw_response  # Fallback if LLM forgets format
            
            # 3. Extract [THOUGHT] and [MESSAGE]
            if "[MESSAGE]" in raw_response:
                parts = raw_response.split("[MESSAGE]")
                # Clean the thought text
                thought = parts[0].replace("[THOUGHT]", "").strip()
                # Clean the final message text - extract after [MESSAGE] delimiter
                public_message = parts[1].strip() if len(parts) > 1 else ""
                
                # If message is empty after parsing, default to SILENCE
                if not public_message:
                    public_message = "[SILENCE]"
            
            # 4. Print thought to console ONLY for researcher/debugging
            if thought:
                print(f"[{student.name} THINKING]: {thought}")
            
            # 5. Normal simulation logic but using ONLY the public_message
            if public_message == "[SILENCE]" or "[SILENCE]" in public_message:
                print(f"{student.name} decided not to speak.")
                self.inactivity[student.name] += 1
                # Don't add SILENCE to chat history
            else:
                self.inactivity[student.name] = 0  # Reset counter
                print(f"{student.name} says: {public_message}")
                
                # Initialize message entry
                message_entry = {
                    "name": student.name,
                    "message": public_message,
                    "transactivity": None
                }
                
                # --- SYSTEM A: Evaluate transactivity using only the public message ---
                if self.system_type == "A":
                    classification = self.evaluate_transactivity(
                        self.chat_history, 
                        student.name, 
                        public_message, 
                        self.llm_client
                    )
                    print(f"  -> {classification}")
                    message_entry["transactivity"] = classification
                
                self.chat_history.append(message_entry)
                
                # Share ONLY the public message with other students
                for other_student in self.students:
                    if other_student.name != student.name:
                        other_student.receive_message(student.name, public_message)
                
                # Pass the message to the Tutor (the Tutor will read tags from chat_history)
                self.tutor.receive_message(student.name, public_message)

    
    def _evaluate_and_intervene(self, tick):
        """
        Evaluate discussion status and intervene if needed.
        """
        # --- SYSTEM B LOGIC (Activity/Silence based) ---
        if self.system_type == "B":
            # 1. Check for complete group silence
            if all(mins >= INACTIVITY_THRESHOLD for mins in self.inactivity.values()):
                instruction = "SYSTEM INSTRUCTION: The entire group has been silent for 3 minutes. Generate a brief scaffolding question (max 2 sentences) to restart the debate without giving the answer."
                self._trigger_tutor_intervention(instruction)
                
                # Reset all counters
                for name in self.inactivity:
                    self.inactivity[name] = 0
                return
            
            # 2. Check for individual silence
            for student_name, inactive_minutes in self.inactivity.items():
                if inactive_minutes >= INACTIVITY_THRESHOLD:
                    # General question without directly calling out the student
                    instruction = (
                        f"SYSTEM INSTRUCTION: {student_name} has been silent for {INACTIVITY_THRESHOLD} minutes because they might feel intimidated. "
                        f"DO NOT address {student_name} directly by name. "
                        f"Generate a brief, open scaffolding question addressed to the WHOLE TEAM that introduces a new angle related to the dataset size or evaluation metrics, making it easier for a quiet student to jump in naturally."
                    )
                    self._trigger_tutor_intervention(instruction)
                    
                    self.inactivity[student_name] = 0  # Reset individual counter
                    break  # Only one intervention per minute

        # --- SYSTEM A LOGIC (Transactivity based) ---
        elif self.system_type == "A":
            # Provide the Tutor with full context (Messages + Transactivity Tags)
            enriched_history = ""
            for msg in self.chat_history[-10:]:  # Last 10 messages
                if msg["name"] != "Tutor":
                    # Extract the evaluation tag
                    tag = msg.get("transactivity", "[NOT EVALUATED]")
                    enriched_history += f"{msg['name']}: {msg['message']}\n>> Evaluation: {tag}\n\n"
                else:
                    enriched_history += f"Tutor: {msg['message']}\n\n"

            # Prepare dynamic base instruction for the System Prompt
            instruction = f"""TUTOR AUTONOMOUS EVALUATION:
            Review the following recent history and transactivity evaluations.
            Compare the discussion with the GROUND TRUTH: {getattr(self, 'problem_ground_truth', 'Not defined')}
            
            ENRICHED HISTORY:
            {enriched_history}
            
            Perform your [INTERNAL ANALYSIS] and decide your move. If the team is collaborating well and heading in the right direction, you MUST respond with 'TUTOR REMAINS SILENT (FADING)'."""
            
            # Trigger tutor. They will decide internally whether to speak or stay silent.
            self._trigger_tutor_intervention(instruction)


    def _trigger_tutor_intervention(self, system_instruction):
        """
        Helper method to inject a hidden instruction to the SimulatedTutor 
        and propagate its response to the chat.
        """
        from message_parser import parse_tutor_response
        
        # 1. Send the hidden context instruction to the tutor
        self.tutor.receive_message("System", system_instruction)
        
        # 2. Generate the dynamic scaffolding intervention
        raw_response = self.tutor.generate_response().strip()
        
        # 3. Parse response using centralized parser (English only, Spanish is dead code)
        analysis, intervention = parse_tutor_response(raw_response)
        
        # Display the analysis in console (debug)
        print(f"\n>>> [Tutor PEDAGOGICAL REASONING]:\n{analysis}")

        # 4. EVALUATE FADING (SILENCE)
        if "TUTOR REMAINS SILENT" in intervention:
            print(">>> [Tutor decided to apply FADING and remain silent]")
            return  # Stop here, no message is sent.

        # 5. Propagate the tutor's message to chat and all students
        print(f"\n[SYSTEM {self.system_type} INTERVENES] Tutor: {intervention}")
        
        # Use dictionary format for chat_history consistency
        self.chat_history.append({"name": "Tutor", "message": intervention})
        
        for student in self.students: 
            student.receive_message("Tutor", intervention)
        
    @staticmethod
    def evaluate_transactivity(chat_history, student_name, current_message, llm_client):
        """
        Evaluates if a student's message is transactive (builds on previous ideas).
        Only used in System A (Transactivity-based evaluation).
        """
        if len(chat_history) < 3:
            return "[TRANSACTIVE]"  # Allow flow if discussion just started

        # Extract text from chat history (handling both dict and string formats)
        previous_messages = []
        for msg in chat_history[-3:]:
            if isinstance(msg, dict):
                previous_messages.append(f"{msg['name']}: {msg['message']}")
            else:
                previous_messages.append(msg)
        previous_context = "\n".join(previous_messages)
        formatted_prompt = PROMPT_TRANSACTIVITY_CLASSIFIER.format(
            previous_context=previous_context,
            student_name=student_name,
            current_message=current_message
        )
        
        try:
            response = llm_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=0.0,
                max_tokens=150  # Increased to allow reasoning space
            )
            raw_output = response.choices[0].message.content.strip()
            
            # 1. By default, assume transactive if parsing fails
            final_label = "[TRANSACTIVE]" 
            
            # 2. Extract the exact label
            if "[NON_TRANSACTIVE]" in raw_output:
                final_label = "[NON_TRANSACTIVE]"
            elif "[NEUTRAL]" in raw_output:
                final_label = "[NEUTRAL]"
            elif "[TRANSACTIVE]" in raw_output:
                final_label = "[TRANSACTIVE]"
            
            # 3. Clean text to show only the reasoning
            reasoning_text = raw_output.replace(final_label, "").replace("[LABEL]", "").replace("[REASONING]", "").strip()
            
            # 4. Print the evaluator's reasoning in console
            print(f"    [Evaluator THINKING about {student_name}]: {reasoning_text}")
            
            # 5. Return ONLY the label
            return final_label
            
        except Exception as e:
            print(f"Error evaluating transactivity: {e}")
            return "[TRANSACTIVE]"  # Fallback on network error
