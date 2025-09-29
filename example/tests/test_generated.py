import unittest
from hello import add, subtract, multiply, divide, Calculator

class TestMathFunctions(unittest.TestCase):
    """Tests for the basic arithmetic functions."""
    
    def test_add(self):
        """Test the add function with various inputs."""
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(-1, -1), -2)
    
    def test_subtract(self):
        """Test the subtract function with various inputs."""
        self.assertEqual(subtract(2, 1), 1)
        self.assertEqual(subtract(-1, 1), -2)
        self.assertEqual(subtract(-1, -1), 0)
    
    def test_multiply(self):
        """Test the multiply function with various inputs."""
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(-1, 1), -1)
        self.assertEqual(multiply(-1, -1), 1)
    
    def test_divide(self):
        """Test the divide function with various inputs."""
        self.assertEqual(divide(6, 3), 2)
        self.assertEqual(divide(-1, 1), -1)
        self.assertEqual(divide(-1, -1), 1)
        with self.assertRaises(ValueError):
            divide(1, 0)

class TestCalculator(unittest.TestCase):
    """Tests for the Calculator class."""
    
    def test_init(self):
        """Test the initialization of the Calculator class."""
        calc = Calculator()
        self.assertEqual(calc.value, 0)
        calc = Calculator(10)
        self.assertEqual(calc.value, 10)
    
    def test_add_to_value(self):
        """Test the add_to_value method of the Calculator class."""
        calc = Calculator()
        calc.add_to_value(5)
        self.assertEqual(calc.value, 5)
        calc.add_to_value(-3)
        self.assertEqual(calc.value, 2)
    
    def test_get_value(self):
        """Test the get_value method of the Calculator class."""
        calc = Calculator(10)
        self.assertEqual(calc.get_value(), 10)
        calc.add_to_value(5)
        self.assertEqual(calc.get_value(), 15)

if __name__ == '__main__':
    unittest.main()