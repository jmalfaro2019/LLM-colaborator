# pbl_simulator.py
# Core simulation logic for PBL discussions

from pbl_config import TUTOR_MESSAGE, INACTIVITY_THRESHOLD, PROMPT_TRANSACTIVITY_CLASSIFIER




# --- MAIN SIMULATOR CLASS ---
class PBLSimulator:
    """Manages a Problem-Based Learning discussion between simulated students."""
    
    def __init__(self, students, tutor, llm_client, max_ticks=6, system_type="B", ground_truth="Teoría básica de machine learning"):
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
                self.inactivity[student.name] += 1
            else:
                self.inactivity[student.name] = 0  # Reset counter
            
            print(f"{student.name} says: {public_message}")
            self.chat_history.append(f"{student.name}: {public_message}")
            
            
            # --- SYSTEM A: Evaluate transactivity using only the public message ---
            if self.system_type == "A":
                classification = self.evaluate_transactivity(
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
        # En la función _evaluate_and_intervene de pbl_simulator.py
                # --- SYSTEM A LOGIC (Transactivity + Epistemic Check) ---
        elif self.system_type == "A":
            # 1. EVALUACIÓN RELACIONAL (El problema de la falta de transactividad)
            umbral_relacional = 2 if getattr(self, 'transactive_streak', 0) < 5 else 4 
            
            if getattr(self, 'non_transactive_turns', 0) >= umbral_relacional:
                instruction = """SYSTEM INSTRUCTION: The students are monologuing or ignoring each other. 
                Perform a 'Reflective Toss'. Identify two disconnected ideas from the recent chat, mention 
                the students by name, and ask a single question forcing them to bridge the gap."""
                #Esta instrucción debería dejar que el tutor evalue la situación y escoja que hacer si no está
                # siendo transactiva la discución
                self._trigger_tutor_intervention(instruction)
                
                # Reiniciamos contadores
                self.non_transactive_turns = 0
                self.transactive_streak = 0
                return # Salimos para que no evalúe nada más en este turno

            # 2. EVALUACIÓN EPISTEMOLÓGICA (El problema del falso consenso)
            # Si llevan 4 turnos colaborando bien, revisamos hacia dónde van.
            umbral_epistemico = 4 
            
            if getattr(self, 'transactive_streak', 0) >= umbral_epistemico:
                
                # Necesitaremos una función que llame al LLM rápido para evaluar la dirección
                # pasándole los últimos mensajes y el ground_truth del problema.
                direccion = self._evaluate_epistemic_direction() 
                
                if direccion == "[OFF_TRACK]":
                    instruction = f"""SYSTEM INSTRUCTION: The students are collaborating well, but they are heading towards an INCORRECT technical conclusion. 
                    GROUND TRUTH: {self.problem_ground_truth}
                    CURRENT DISCUTION: {"\n".join(self.chat_history[-6:])}
                    Perform a 'Socratic Redirect'. Acknowledge their teamwork (e.g. "You are making a great point about..."), but ask a specific technical question that exposes the flaw in their current logic based on the Ground Truth. Do NOT give them the answer."""
                    
                    self._trigger_tutor_intervention(instruction)
                
                # Reseteamos la racha transactiva (haya intervenido o no) para 
                # que el sistema espere otros 'umbral_epistemico' turnos antes de volver a auditar.
                self.transactive_streak = 0


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
            
    def _evaluate_epistemic_direction(self):
        """
        Evalúa si el consenso técnico del grupo va por buen camino
        comparándolo con el Ground Truth del problema.
        """
        # 1. Tomamos los últimos 4 a 6 mensajes para dar contexto al evaluador
        recent_history = self.chat_history[-6:]
        context_str = "\n".join([f"{msg['name']}: {msg['message']}" for msg in recent_history if msg['name'] != "Tutor"])
        
        # Asumimos que tienes importado PROMPT_EPISTEMIC_EVALUATOR desde pbl_config
        from pbl_config import PROMPT_EPISTEMIC_EVALUATOR
        
        # 2. Formateamos el prompt
        prompt = PROMPT_EPISTEMIC_EVALUATOR.format(
            ground_truth=getattr(self, 'problem_ground_truth', 'No ground truth provided.'),
            recent_context=context_str
        )
        
        # 3. Llamada rápida al LLM (Temperatura 0 para ser determinista)
        try:
            response = self.llm_client.chat.completions.create(
                model="llama3-70b-8192", # O el modelo rápido que estés usando en Groq
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10
            )
            result = response.choices[0].message.content.strip().upper()
            
            # Limpiamos el output por si el LLM añade puntuación extra
            if "[OFF_TRACK]" in result:
                return "[OFF_TRACK]"
            else:
                return "[ON_TRACK]"
                
        except Exception as e:
            print(f"Error in epistemic evaluation: {e}")
            return "[ON_TRACK]" # Ante la duda o error de red, asumimos que van bien para no interrumpir
        
        
    @staticmethod
    def evaluate_transactivity(chat_history, student_name, current_message, llm_client):
        """
        Evaluates if a student's message is transactive (builds on previous ideas).
        Only used in System A (Transactivity-based evaluation).
        """
        if len(chat_history) < 3:
            return "[TRANSACTIVE]"  # Allow flow if discussion just started

        previous_context = "\n".join(chat_history[-3:])
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
                max_tokens=150  # ¡INCREMENTADO! Para darle espacio a razonar
            )
            raw_output = response.choices[0].message.content.strip()
            
            # 1. Por defecto, asumimos que es transactivo si hay algún error de parseo
            final_label = "[TRANSACTIVE]" 
            
            # 2. Extraemos la etiqueta exacta
            if "[NON_TRANSACTIVE]" in raw_output:
                final_label = "[NON_TRANSACTIVE]"
            elif "[NEUTRAL]" in raw_output:
                final_label = "[NEUTRAL]"
            elif "[TRANSACTIVE]" in raw_output:
                final_label = "[TRANSACTIVE]"
            
            # 3. Limpiamos el texto para dejar solo el razonamiento y mostrarlo
            reasoning_text = raw_output.replace(final_label, "").replace("[LABEL]", "").replace("[REASONING]", "").strip()
            
            # 4. Imprimimos el pensamiento del evaluador en la consola
            # Usamos un print con indentación para que se distinga de los estudiantes
            print(f"    [Evaluator THINKING about {student_name}]: {reasoning_text}")
            
            # 5. Devolvemos SOLO la etiqueta para que el simulador cuente los turnos correctamente
            return final_label
            
        except Exception as e:
            print(f"Error evaluating transactivity: {e}")
            return "[TRANSACTIVE]"  # Fallback on network error
