# pbl_simulator.py
# Core simulation logic for PBL discussions

from pbl_config import TUTOR_MESSAGE, INACTIVITY_THRESHOLD, PROMPT_TRANSACTIVITY_CLASSIFIER


def evaluate_transactivity(chat_history, student_name, current_message, llm_client):
    """
    Evaluates if a student's message is transactive (builds on previous ideas).
    Only used in System A (Transactivity-based evaluation).
    
    Args:
        chat_history: List of previous messages
        student_name: Name of the student
        current_message: Student's current message
        llm_client: LLM client for classification
        
    Returns:
        "[TRANSACTIVE]" or "[NON_TRANSACTIVE]"
    """
    if len(chat_history) < 2:
        return "[TRANSACTIVE]"  # Allow flow if discussion just started

    previous_context = "\n".join(chat_history[-2:])
    formatted_prompt = PROMPT_TRANSACTIVITY_CLASSIFIER.format(
        previous_context=previous_context,
        student_name=student_name,
        current_message=current_message
    )
    
    try:
        response = llm_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": formatted_prompt}],
            temperature=0.0,  # Strict classifier
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error evaluating transactivity: {e}")
        return "[TRANSACTIVE]"  # Fallback on network error


# --- MAIN SIMULATOR CLASS ---
class PBLSimulator:
    """Manages a Problem-Based Learning discussion between simulated students."""
    
    def __init__(self, students, tutor, llm_client, max_ticks=6, system_type="B"):
        """
        Initialize the PBL simulator.
        
        Args:
            students: List of SimulatedStudent instances
            tutor: Instance of SimulatedTutor
            llm_client: API client for the quick transactivity classifier
            max_ticks: Maximum number of discussion rounds
            system_type: "A" (Transactivity) or "B" (Activity)
        """
        self.students = students
        self.tutor = tutor
        self.llm_client = llm_client
        self.max_ticks = max_ticks
        self.system_type = system_type
        
        self.chat_history = []
        self.inactivity = {student.name: 0 for student in students}
        self.non_transactive_turns = 0
    
    def run(self):
        """Execute the PBL simulation."""
        self._tutor_opening()
        
        for tick in range(1, self.max_ticks + 1):
            self._run_tick(tick)
            self._evaluate_and_intervene(tick)
    
    def _tutor_opening(self):
        """Start the discussion with the tutor's opening message."""
        print(f"[Tick 0] Tutor: {TUTOR_MESSAGE}")
        self.chat_history.append(f"Tutor: {TUTOR_MESSAGE}")
        
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
                # Clean the final message text
                public_message = parts[1].strip()
            
            # 4. Print thought to console ONLY for researcher/debugging
            if thought:
                print(f"[{student.name} THINKING]: {thought}")
            
            # 5. Normal simulation logic but using ONLY the public_message
            if public_message == "[SILENCE]" or "[SILENCE]" in public_message:
                print(f"{student.name} decided not to speak.")
                student.history.pop()  # Remove the entire response from history
                self.inactivity[student.name] += 1
            else:
                print(f"{student.name} says: {public_message}")
                self.chat_history.append(f"{student.name}: {public_message}")
                self.inactivity[student.name] = 0  # Reset counter
                
                # --- SYSTEM A: Evaluate transactivity using only the public message ---
                if self.system_type == "A":
                    classification = evaluate_transactivity(
                        self.chat_history, 
                        student.name, 
                        public_message, 
                        self.llm_client
                    )
                    print(f"  -> {classification}")
                    if "[TRANSACTIVE]" in classification:
                        has_transactivity_this_turn = True
                
                # Share ONLY the public message with other students
                for other_student in self.students:
                    if other_student.name != student.name:
                        other_student.receive_message(student.name, public_message)
                
                # Pass ONLY the public message to the Tutor
                self.tutor.receive_message(student.name, public_message)
                
        # --- SYSTEM A: Update metrics at end of turn ---
        if self.system_type == "A":
            if has_transactivity_this_turn:
                self.non_transactive_turns = 0  # Group is doing well, reset
            else:
                self.non_transactive_turns += 1  # Isolated monologues continue
    
    
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
            if getattr(self, 'non_transactive_turns', 0) >= 2:
                instruction = "SYSTEM INSTRUCTION: The students are monologuing or agreeing without depth. Generate a brief scaffolding question that highlights a contradiction in their recent statements and forces them to cross-reference their ideas."
                self._trigger_tutor_intervention(instruction)
                
                self.non_transactive_turns = 0  # Reset counter after intervention


    def _trigger_tutor_intervention(self, system_instruction):
        """
        Helper method to inject a hidden instruction to the SimulatedTutor 
        and propagate its response to the chat.
        """
        # 1. Send the hidden context instruction to the tutor
        self.tutor.receive_message("System", system_instruction)
        
        # 2. Generate the dynamic scaffolding intervention
        intervention = self.tutor.generate_response().strip()
        
        print(f"\n[SYSTEM {self.system_type} INTERVENES] Tutor: {intervention}")
        self.chat_history.append(f"Tutor: {intervention}")
        
        # 3. Propagate the tutor's message to all students
        for student in self.students: 
            student.receive_message("Tutor", intervention)