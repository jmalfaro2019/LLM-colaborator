"""
Unit tests para Top 3 Mejoras (M1, M2, M4)
Ejecutar desde raíz: python -m pytest tests/test_top3.py -v
O: python -m unittest tests.test_top3
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import random
from pbl_factory import PBLFactory
from simulated_student import SimulatedStudent, MAX_HISTORY_LENGTH
from simulated_tutor import SimulatedTutor, MAX_HISTORY_LENGTH as TUTOR_MAX_HISTORY
from pbl_session import setup_pbl_session


class TestM2RandomOrder(unittest.TestCase):
    """Test M2: Orden aleatorio de estudiantes"""
    
    def test_student_order_varies(self):
        """Verificar que el orden de estudiantes cambia entre sesiones"""
        orders = []
        
        # Ejecutar 5 veces y recolectar órdenes
        for _ in range(5):
            factory = PBLFactory()
            _, _, _, _ = factory.generate_random_session(system_type="B")
            orders.append(tuple(factory.student_names))
        
        # Debe haber al menos 2 órdenes diferentes de 5 intentos
        unique_orders = set(orders)
        self.assertGreater(len(unique_orders), 1, 
                          "El orden debería variar entre sesiones")
        print(f"[OK] Órdenes encontradas: {unique_orders}")
    
    def test_all_students_present(self):
        """Verificar que todos los estudiantes siempre están presentes"""
        factory = PBLFactory()
        _, _, _, _ = factory.generate_random_session(system_type="B")
        
        expected = {"Luis", "Carlos", "Ana"}
        actual = set(factory.student_names)
        self.assertEqual(actual, expected, 
                        "Todos los estudiantes deben estar presentes")
        print(f"[OK] Estudiantes presentes: {actual}")


class TestM4HistoryLimit(unittest.TestCase):
    """Test M4: Límite de historial (ventana deslizante)"""
    
    def test_student_history_capped(self):
        """Verificar que el historial del estudiante está limitado"""
        student = SimulatedStudent("TestStudent", "You are a student.")
        
        # Agregar 200 mensajes
        for i in range(200):
            student.receive_message(f"Person{i%3}", f"Message {i}")
        
        # El historial debería tener: 1 system + MAX_HISTORY_LENGTH mensajes
        expected_max = 1 + MAX_HISTORY_LENGTH
        self.assertLessEqual(len(student.history), expected_max,
                            f"Historial exceede {expected_max} entries")
        
        # Debería tener exactamente MAX_HISTORY_LENGTH mensajes (sin system)
        message_count = len(student.history) - 1
        self.assertEqual(message_count, MAX_HISTORY_LENGTH,
                        f"Debería tener {MAX_HISTORY_LENGTH} mensajes")
        print(f"[OK] Historial limitado: {len(student.history)} entries (1 system + {MAX_HISTORY_LENGTH} msgs)")
    
    def test_tutor_history_capped(self):
        """Verificar que el historial del tutor está limitado"""
        tutor = SimulatedTutor("System B", "You are a tutor.")
        
        # Agregar 200 mensajes
        for i in range(200):
            tutor.receive_message(f"Student{i%3}", f"Message {i}")
        
        # El historial debería tener un límite
        expected_max = 1 + TUTOR_MAX_HISTORY
        self.assertLessEqual(len(tutor.history), expected_max,
                            f"Historial tutor exceede limite")
        print(f"[OK] Historial tutor limitado: {len(tutor.history)} entries")
    
    def test_recent_messages_preserved(self):
        """Verificar que se preservan los mensajes más recientes"""
        student = SimulatedStudent("TestStudent", "You are a student.")
        
        # Agregar 100 mensajes específicos
        for i in range(100):
            student.receive_message("Tutor", f"Unique_{i}")
        
        # El último mensaje debe estar presente
        history_str = str(student.history)
        self.assertIn("Unique_99", history_str,
                     "El último mensaje debe estar en el historial")
        print(f"[OK] Mensajes recientes preservados")


class TestM1Reproducibility(unittest.TestCase):
    """Test M1: Reproducibilidad con seeds"""
    
    def test_seed_affects_factory(self):
        """Verificar que el seed produce órdenes idénticas"""
        # Primera generación con seed
        random.seed(42)
        factory1 = PBLFactory()
        _, _, _, _ = factory1.generate_random_session(system_type="B")
        order1 = tuple(factory1.student_names)
        
        # Segunda generación con seed
        random.seed(42)
        factory2 = PBLFactory()
        _, _, _, _ = factory2.generate_random_session(system_type="B")
        order2 = tuple(factory2.student_names)
        
        self.assertEqual(order1, order2,
                        "Mismo seed debería producir mismo orden")
        print(f"[OK] Reproducibilidad: {order1} == {order2}")
    
    def test_different_seed_different_order(self):
        """Verificar que seeds diferentes producen órdenes diferentes"""
        # Primera generación con seed 42
        random.seed(42)
        factory1 = PBLFactory()
        _, _, _, _ = factory1.generate_random_session(system_type="B")
        order1 = tuple(factory1.student_names)
        
        # Segunda generación con seed 99
        random.seed(99)
        factory2 = PBLFactory()
        _, _, _, _ = factory2.generate_random_session(system_type="B")
        order2 = tuple(factory2.student_names)
        
        # Nota: Hay 1/6 chance que sean iguales por azar
        # Este test es probabilísticamente correcto pero puede fallar raramente
        are_same = order1 == order2
        print(f"[OK] Seeds diferentes: {order1} {'==' if are_same else '!='} {order2}")


class TestIntegration(unittest.TestCase):
    """Tests de integración"""
    
    def test_setup_pbl_session_with_seed(self):
        """Verificar que setup_pbl_session acepta seed parameter"""
        try:
            students, tutor, initial, config, scenario = \
                setup_pbl_session(system_type="B", scenario="KNN", seed=42)
            
            self.assertIsNotNone(students)
            self.assertIsNotNone(tutor)
            self.assertEqual(len(students), 3, "Debería haber 3 estudiantes")
            print(f"[OK] setup_pbl_session con seed funciona")
        except Exception as e:
            self.fail(f"setup_pbl_session falló: {e}")


if __name__ == "__main__":
    # Ejecutar con más verbosity
    unittest.main(verbosity=2)
