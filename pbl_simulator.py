# pbl_simulator.py
# Core simulation logic for PBL discussions

from pbl_config import TUTOR_MESSAGE, INACTIVITY_THRESHOLD


class PBLSimulator:
    """Manages a Problem-Based Learning discussion between simulated students."""
    
    def __init__(self, students, max_ticks=6):
        """
        Initialize the PBL simulator.
        
        Args:
            students: List of SimulatedStudent instances
            max_ticks: Maximum number of discussion rounds
        """
        self.students = students
        self.max_ticks = max_ticks
        self.chat_history = []
        self.inactivity = {student.name: 0 for student in students}
    
    def run(self):
        """Execute the PBL simulation."""
        self._tutor_opening()
        
        for tick in range(1, self.max_ticks + 1):
            self._run_tick(tick)
            self._evaluate_and_intervene(tick)
    
    def _tutor_opening(self):
        """Start the discussion with the tutor's opening message."""
        print(f"[Tick 0] Tutor: {TUTOR_MESSAGE}")
        
        for student in self.students:
            student.receive_message("Tutor", TUTOR_MESSAGE)
    
    def _run_tick(self, tick):
        """Execute one round of discussion."""
        print(f"\n--- Minute {tick} ---")
        
        for student in self.students:
            response = student.generate_response().strip()
            
            if response == "[SILENCE]" or "[SILENCE]" in response:
                print(f"{student.name} decided not to speak.")
                student.history.pop()  # Remove the response from history
                self.inactivity[student.name] += 1
            else:
                print(f"{student.name} says: {response}")
                self.chat_history.append(f"{student.name}: {response}")
                self.inactivity[student.name] = 0  # Reset counter
                
                # Share response with other students
                for other_student in self.students:
                    if other_student.name != student.name:
                        other_student.receive_message(student.name, response)
    
    def _evaluate_and_intervene(self, tick):
        """
        Evaluate discussion status and intervene if needed (System B).
        
        Two intervention scenarios:
        1. Group silence: All students inactive for 3+ minutes
        2. Individual silence: One student inactive for 3+ minutes
        """
        # 1. Check for complete group silence
        if all(mins >= INACTIVITY_THRESHOLD for mins in self.inactivity.values()):
            self._group_intervention()
            return
        
        # 2. Check for individual silence
        for student_name, inactive_minutes in self.inactivity.items():
            if inactive_minutes >= INACTIVITY_THRESHOLD:
                self._individual_intervention(student_name)
                break  # Only one intervention per minute
    
    def _group_intervention(self):
        """Intervene when all students have gone silent."""
        intervention = "Team, the discussion seems to have paused. Considering the clinic has no prior labels, what specific type of learning approach does that require?"
        print(f"\n[SYSTEM B INTERVENES] Tutor: {intervention}")
        self.chat_history.append(f"Tutor: {intervention}")
        
        # Propagate to all students and reset counters
        for student in self.students:
            student.receive_message("Tutor", intervention)
            self.inactivity[student.name] = 0
    
    def _individual_intervention(self, student_name):
        """Intervene when a specific student has gone silent."""
        intervention = f"{student_name}, I notice you haven't participated in the last few minutes. Do you have any perspective on what is being discussed based on your notes?"
        print(f"\n[SYSTEM B INTERVENES] Tutor: {intervention}")
        self.chat_history.append(f"Tutor: {intervention}")
        
        # Propagate to all students for context
        for student in self.students:
            student.receive_message("Tutor", intervention)
        
        # Force immediate response from the addressed student
        target_student = next(s for s in self.students if s.name == student_name)
        forced_response = target_student.generate_response().strip()
        
        if forced_response == "[SILENCE]" or "[SILENCE]" in forced_response:
            print(f">> {student_name} remained silent despite the intervention.")
            target_student.history.pop()  # Remove silence from history
        else:
            print(f"{student_name} says: {forced_response}")
            self.chat_history.append(f"{student_name}: {forced_response}")
            
            # Share response with other students
            for other_student in self.students:
                if other_student.name != student_name:
                    other_student.receive_message(student_name, forced_response)
        
        # Reset counter to avoid infinite intervention loops
        self.inactivity[student_name] = 0
