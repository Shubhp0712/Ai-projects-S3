def add(a, b):
    """Adds two numbers."""
    return a + b

def subtract(a, b):
    """Subtracts two numbers."""
    return a - b

def multiply(a, b):
    """Multiplies two numbers."""
    return a * b

def divide(a, b):
    """
    Divides two numbers.
    
    Raises a ValueError for division by zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    """A simple calculator class."""
    
    def __init__(self, initial_value=0):
        self.value = initial_value

    def add_to_value(self, number):
        """Adds a number to the calculator's current value."""
        self.value += number
        return self.value

    def get_value(self):
        """Returns the current value of the calculator."""
        return self.value
